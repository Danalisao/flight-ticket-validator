from flask import Flask
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from app.routes import bp

# Load environment variables
load_dotenv()

def create_app(testing=False):
    """Create and configure the Flask application"""
    
    app = Flask(__name__)
    
    # Configure app
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_SIZE', 10 * 1024 * 1024))  # Default 10MB
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['TESTING'] = testing
    
    # Configure logging
    if not testing:
        configure_logging(app)
    
    # Register blueprints
    app.register_blueprint(bp)
    
    return app

def configure_logging(app):
    """Configure application logging"""
    
    # Set log level
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure file handler
    file_handler = RotatingFileHandler(
        os.getenv('LOG_FILE', 'logs/app.log'),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    
    # Configure formatters
    file_formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(numeric_level)
    
    # Add handlers
    app.logger.addHandler(file_handler)
    app.logger.setLevel(numeric_level)
    
    # Log application startup
    app.logger.info('Flight Ticket Validator startup')

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
