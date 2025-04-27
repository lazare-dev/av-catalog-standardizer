#!/usr/bin/env python3
"""
AV Catalog Standardizer - Main Application
-----------------------------------------
Main entry point for the AV Catalog Standardizer application.
"""

import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import tempfile
import json

from config.settings import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH
from core.data_processor import process_catalog
from services.validator import validate_output
from utils.helpers import create_response

# Initialize Flask application
app = Flask(__name__, 
            template_folder='web/templates',
            static_folder='web/static')

# Configure application
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the main upload page."""
    # Create an empty validation object to avoid template errors
    empty_validation = {
        "valid_count": 0, 
        "invalid_count": 0, 
        "errors": [], 
        "warnings": []
    }
    return render_template('index.html', validation=empty_validation, validation_summary="")

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and processing."""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            session_id = str(hash(filename + str(os.path.getmtime(filepath))))
            
            # Process the catalog file
            transformed_data, validation_results, field_mappings = process_catalog(filepath)
            
            # Save results to temp files
            temp_dir = os.path.join(tempfile.gettempdir(), session_id)
            os.makedirs(temp_dir, exist_ok=True)
            
            with open(os.path.join(temp_dir, 'mappings.json'), 'w') as f:
                json.dump(field_mappings, f)
            
            with open(os.path.join(temp_dir, 'data.json'), 'w') as f:
                json.dump(transformed_data, f)
                
            with open(os.path.join(temp_dir, 'validation.json'), 'w') as f:
                json.dump(validation_results, f)
            
            return redirect(url_for('mapping_review', session_id=session_id))
        
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('index'))
    
    flash('File type not allowed')
    return redirect(url_for('index'))

@app.route('/mapping-review/<session_id>')
def mapping_review(session_id):
    """Display the field mapping review page."""
    temp_dir = os.path.join(tempfile.gettempdir(), session_id)
    
    try:
        with open(os.path.join(temp_dir, 'mappings.json'), 'r') as f:
            field_mappings = json.load(f)
            
        with open(os.path.join(temp_dir, 'data.json'), 'r') as f:
            sample_data = json.load(f)[:5]  # First 5 rows for preview
        
        return render_template('mapping_review.html', 
                            field_mappings=field_mappings,
                            sample_data=sample_data,
                            session_id=session_id)
    
    except Exception as e:
        flash(f'Error loading mapping data: {str(e)}')
        return redirect(url_for('index'))

@app.route('/update-mappings/<session_id>', methods=['POST'])
def update_mappings(session_id):
    """Update field mappings based on user input."""
    temp_dir = os.path.join(tempfile.gettempdir(), session_id)
    
    try:
        updated_mappings = request.json.get('mappings', {})
        
        with open(os.path.join(temp_dir, 'mappings.json'), 'r') as f:
            original_mappings = json.load(f)
        
        # Update the mappings
        for field, mapping in updated_mappings.items():
            if field in original_mappings['field_mappings']:
                original_mappings['field_mappings'][field]['standard_field'] = mapping
        
        with open(os.path.join(temp_dir, 'mappings.json'), 'w') as f:
            json.dump(original_mappings, f)
        
        # Reprocess with updated mappings
        with open(os.path.join(temp_dir, 'data.json'), 'r') as f:
            data = json.load(f)
            
        # Logic to reapply mappings would go here
        # For now, just return success
        
        return jsonify(create_response(True, "Mappings updated successfully"))
    
    except Exception as e:
        return jsonify(create_response(False, f"Error updating mappings: {str(e)}"))

@app.route('/preview/<session_id>')
def preview(session_id):
    """Display preview of processed data."""
    temp_dir = os.path.join(tempfile.gettempdir(), session_id)
    
    try:
        with open(os.path.join(temp_dir, 'data.json'), 'r') as f:
            transformed_data = json.load(f)
            
        with open(os.path.join(temp_dir, 'validation.json'), 'r') as f:
            validation_results = json.load(f)
        
        return render_template('preview.html',
                            data=transformed_data[:20],  # First 20 rows
                            validation=validation_results,
                            session_id=session_id)
    
    except Exception as e:
        flash(f'Error loading preview data: {str(e)}')
        return redirect(url_for('index'))

@app.route('/export/<session_id>')
def export(session_id):
    """Export processed data to CSV."""
    temp_dir = os.path.join(tempfile.gettempdir(), session_id)
    export_format = request.args.get('format', 'csv')
    
    try:
        with open(os.path.join(temp_dir, 'data.json'), 'r') as f:
            transformed_data = json.load(f)
        
        # Create export file
        export_path = os.path.join(temp_dir, f'export.{export_format}')
        
        # We would have a more sophisticated export function here
        # For now, just dump to CSV
        import pandas as pd
        df = pd.DataFrame(transformed_data)
        
        if export_format == 'csv':
            df.to_csv(export_path, index=False)
        elif export_format == 'xlsx':
            df.to_excel(export_path, index=False)
        elif export_format == 'json':
            df.to_json(export_path, orient='records')
        else:
            flash(f'Unsupported export format: {export_format}')
            return redirect(url_for('preview', session_id=session_id))
        
        return send_file(export_path, 
                      mimetype='text/csv' if export_format == 'csv' else 'application/octet-stream',
                      as_attachment=True,
                      download_name=f'standardized_catalog.{export_format}')
    
    except Exception as e:
        flash(f'Error exporting data: {str(e)}')
        return redirect(url_for('preview', session_id=session_id))

if __name__ == '__main__':
    # Run the application in debug mode for development
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))