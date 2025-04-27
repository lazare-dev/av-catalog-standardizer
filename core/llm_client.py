"""
AV Catalog Standardizer - LLM Client
---------------------------------------------
LLM client implementation for text generation.
"""

import os
import json
import logging
import time
import hashlib
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Try importing torch with error handling
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logging.warning("Torch could not be imported. Running in limited functionality mode.")

# Try importing transformers with error handling
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning("Transformers could not be imported. Running in limited functionality mode.")

from config.settings import (
    PHI_MODEL_ID, 
    PHI_QUANTIZATION,
    MAX_NEW_TOKENS,
    TEMPERATURE,
    TOP_P,
    CACHE_ENABLED,
    CACHE_DIR
)

logger = logging.getLogger(__name__)

class PhiClient:
    """Client for LLM text generation."""
    
    def __init__(self, model_id: str = PHI_MODEL_ID, cache_dir: str = CACHE_DIR):
        """
        Initialize the LLM client.
        
        Args:
            model_id: ID of the model to use (default: config.PHI_MODEL_ID)
            cache_dir: Directory to cache prompts and responses
        """
        self.model_id = model_id
        self.cache_dir = cache_dir
        self.model = None
        self.tokenizer = None
        self.pipe = None
        
        # Ensure cache directory exists
        if CACHE_ENABLED:
            os.makedirs(cache_dir, exist_ok=True)
            
        # Load model on initialization
        if HAS_TORCH and HAS_TRANSFORMERS:
            self._load_model()
        else:
            logger.warning("Running in mock mode due to missing dependencies")
    
    def _load_model(self) -> None:
        """Load the model and tokenizer."""
        logger.info(f"Loading model: {self.model_id}")
        
        try:
            # Set environment variable to avoid warnings
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=True
            )
            
            # Ensure the pad token is set for GPT-2 models
            if "gpt2" in self.model_id.lower() and self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Simple model loading with minimal parameters for compatibility
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                device_map="auto"
            )
            
            # Create a pipeline
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map="auto"
            )
            
            logger.info(f"Model {self.model_id} loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            logger.warning("Falling back to mock mode")
            self.pipe = None
    
    def _get_cache_key(self, prompt: str) -> str:
        """
        Generate a cache key for the prompt.
        
        Args:
            prompt: The prompt to generate a cache key for
            
        Returns:
            Cache key as string
        """
        # Create a hash of the prompt for use as cache key
        prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
        return prompt_hash
    
    def _check_cache(self, cache_key: str) -> Optional[str]:
        """
        Check if a cached response exists for the given key.
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            Cached response or None if not found
        """
        if not CACHE_ENABLED:
            return None
            
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_data.get("response")
            except Exception as e:
                logger.warning(f"Error reading cache: {str(e)}")
                
        return None
    
    def _save_to_cache(self, cache_key: str, prompt: str, response: str) -> None:
        """
        Save a response to the cache.
        
        Args:
            cache_key: Cache key
            prompt: Original prompt
            response: Generated response
        """
        if not CACHE_ENABLED:
            return
            
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            cache_data = {
                "prompt": prompt,
                "response": response,
                "timestamp": time.time()
            }
            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"Saved response to cache: {cache_key}")
        
        except Exception as e:
            logger.warning(f"Error saving to cache: {str(e)}")
    
    def generate(self, prompt: str, max_new_tokens: int = MAX_NEW_TOKENS, 
                temperature: float = TEMPERATURE, top_p: float = TOP_P) -> str:
        """
        Generate a response to the given prompt.
        
        Args:
            prompt: Text prompt to generate from
            max_new_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated response as string
        """
        # Check cache first if enabled
        cache_key = self._get_cache_key(prompt)
        cached_response = self._check_cache(cache_key)
        
        if cached_response is not None:
            return cached_response
        
        logger.debug(f"Generating response for prompt: {prompt[:100]}...")
        
        # If we don't have a working model, return a mock response
        if self.pipe is None:
            # Generate a mock response based on the prompt
            response = self._generate_mock_response(prompt)
            self._save_to_cache(cache_key, prompt, response)
            return response
        
        try:
            # Generate response with the actual model
            output = self.pipe(
                prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract generated text
            generated_text = output[0]["generated_text"]
            
            # Remove the original prompt from the response
            if generated_text.startswith(prompt):
                response = generated_text[len(prompt):].strip()
            else:
                response = generated_text.strip()
            
            # Cache the response
            self._save_to_cache(cache_key, prompt, response)
            
            return response
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            # Fall back to mock response on error
            response = self._generate_mock_response(prompt)
            self._save_to_cache(cache_key, prompt, response)
            return response
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate a mock response for development purposes."""
        # Return a basic mock response for now
        return "This is a mock response used for development. The LLM is not available."
    
    def generate_json(self, prompt: str, max_attempts: int = 3, **kwargs) -> Dict:
        """
        Generate a JSON response to the given prompt.
        
        Args:
            prompt: Text prompt to generate from
            max_attempts: Maximum number of attempts to generate valid JSON
            **kwargs: Additional arguments to pass to generate()
            
        Returns:
            Generated response as Dict
        """
        # If we don't have a working model, return a mock JSON response
        if self.pipe is None:
            return self._generate_mock_json(prompt)
        
        prompt_with_json = f"{prompt}\n\nRespond with valid JSON only."
        
        for attempt in range(max_attempts):
            try:
                response_text = self.generate(prompt_with_json, **kwargs)
                
                # Try to extract JSON from the response
                # Look for JSON-like content (between curly braces)
                import re
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1)
                    
                    # Parse JSON
                    response_json = json.loads(json_str)
                    return response_json
                
                # If no JSON-like content was found, try the full response
                response_json = json.loads(response_text)
                return response_json
                
            except json.JSONDecodeError:
                logger.warning(f"Attempt {attempt+1}/{max_attempts}: Invalid JSON response")
                
                if attempt == max_attempts - 1:
                    # Last attempt, fall back to mock JSON
                    logger.error(f"Failed to generate valid JSON after {max_attempts} attempts")
                    return self._generate_mock_json(prompt)
        
        # This should never be reached due to the exception in the loop
        return self._generate_mock_json(prompt)
    
    def _generate_mock_json(self, prompt: str) -> Dict:
        """Generate a mock JSON response for development purposes."""
        # Generate a different response based on the prompt type
        prompt_lower = prompt.lower()
        
        if "structure_analysis" in prompt_lower:
            return {
                "format": "CSV",
                "headers": ["SKU", "Description", "Price", "Category"],
                "data_start_row": 1,
                "non_data_rows": []
            }
        elif "field_mapping" in prompt_lower:
            return {
                "field_mappings": {
                    "SKU": {"standard_field": "SKU"},
                    "Description": {"standard_field": "Short_Description"},
                    "Price": {"standard_field": "MSRP_USD"},
                    "Category": {"standard_field": "Category"}
                },
                "manufacturer_detection": {
                    "name": "Sample Manufacturer"
                }
            }
        elif "category_extraction" in prompt_lower:
            return {
                "default_category": {
                    "category_group": "Audio",
                    "category": "Speakers"
                }
            }
        else:
            return {"result": "mock_response"}
    
    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Generate responses for multiple prompts.
        
        Args:
            prompts: List of prompts to generate from
            **kwargs: Additional arguments to pass to generate()
            
        Returns:
            List of generated responses
        """
        responses = []
        
        for prompt in prompts:
            response = self.generate(prompt, **kwargs)
            responses.append(response)
        
        return responses

# Create a singleton instance for global use
phi_client = PhiClient()