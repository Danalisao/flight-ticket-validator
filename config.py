import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Application Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_for_development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    # API Keys and Credentials
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    AMADEUS_CLIENT_ID = os.getenv('AMADEUS_CLIENT_ID')
    AMADEUS_CLIENT_SECRET = os.getenv('AMADEUS_CLIENT_SECRET')
    
    # OCR and Validation Configuration
    OCR_PROVIDER = os.getenv('OCR_PROVIDER', 'claude')
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', '10 * 1024 * 1024'))  # 10 MB default
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # Caching Configuration
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DIR = os.getenv('CACHE_DIR', 'cache')
    
    @classmethod
    def validate_config(cls):
        """
        Validate critical configuration parameters
        """
        errors = []
        
        if not cls.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is missing")
        
        if not cls.AMADEUS_CLIENT_ID or not cls.AMADEUS_CLIENT_SECRET:
            errors.append("Amadeus API credentials are incomplete")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True

# Validate configuration on import
Config.validate_config()
