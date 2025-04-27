"""
AV Catalog Standardizer - Settings
---------------------------------
Application settings and configurations.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# File upload settings
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

# Microsoft Phi Model Settings
PHI_MODEL_ID = "gpt2"  # Lightweight model with excellent compatibility
PHI_QUANTIZATION = None  # No need for quantization with this small model
MAX_NEW_TOKENS = 1024
TEMPERATURE = 0.7
TOP_P = 0.95

# Processing settings
CHUNK_SIZE = 10  # Number of rows to process at once
BATCH_SIZE = 32  # Batch size for model inference
CACHE_ENABLED = True
CACHE_DIR = os.path.join(BASE_DIR, 'cache')

# Output schema configuration
REQUIRED_FIELDS = [
    "SKU",
    "Short_Description", 
    "Manufacturer", 
    "Unit_Of_Measure"
]

# Logging
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'app.log')

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)