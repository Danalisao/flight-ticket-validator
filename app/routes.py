from flask import Blueprint, request, jsonify, render_template, current_app
from .services.validation_service import ValidationService
import logging

bp = Blueprint('main', __name__)
validation_service = ValidationService()
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/api/validate', methods=['POST'])
def validate_ticket():
    try:
        if 'ticket_image' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['ticket_image']
        if not file.filename:
            return jsonify({'error': 'Invalid filename'}), 400

        # Check file type
        if not file.content_type.startswith(('image/', 'application/pdf')):
            return jsonify({'error': 'Unsupported file type'}), 400

        # Process the file with validation service
        validation_result = validation_service.validate_ticket(file)
        
        return jsonify(validation_result)

    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    try:
        validation_service.clear_cache()
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({'error': 'Failed to clear cache'}), 500

@bp.route('/favicon.ico')
def favicon():
    return current_app.send_from_directory('static', 'favicon.ico')
