from flask import Flask
from config import Config

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Register blueprints
    from app.routes import bp
    app.register_blueprint(bp)
    
    return app
