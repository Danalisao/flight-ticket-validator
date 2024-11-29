import logging
import logging.handlers
import os
from datetime import datetime

class LoggerConfig:
    def __init__(self, log_dir='logs'):
        """
        Configure le système de logging
        
        :param log_dir: Répertoire pour les fichiers de log
        """
        self.log_dir = log_dir
        self._ensure_log_directory()
        self._configure_logging()

    def _ensure_log_directory(self):
        """Crée le répertoire de logs s'il n'existe pas"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _configure_logging(self):
        """Configure les handlers et le format des logs"""
        # Format de base pour tous les logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Logger principal
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Handler pour les logs d'erreur
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'error.log'),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

        # Handler pour les logs d'information
        info_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'info.log'),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(formatter)
        root_logger.addHandler(info_handler)

        # Handler pour la console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Logger spécifique pour les validations de billets
        ticket_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'ticket_validation.log'),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        ticket_handler.setLevel(logging.INFO)
        ticket_handler.setFormatter(formatter)
        
        ticket_logger = logging.getLogger('ticket_validation')
        ticket_logger.addHandler(ticket_handler)
        ticket_logger.setLevel(logging.INFO)

        # Logger pour les appels API
        api_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'api_calls.log'),
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        api_handler.setLevel(logging.INFO)
        api_handler.setFormatter(formatter)
        
        api_logger = logging.getLogger('api_calls')
        api_logger.addHandler(api_handler)
        api_logger.setLevel(logging.INFO)

def log_api_call(func):
    """Décorateur pour logger les appels API"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('api_calls')
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"API Call - Function: {func.__name__} - "
                f"Duration: {duration:.2f}s - Success"
            )
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"API Call - Function: {func.__name__} - "
                f"Duration: {duration:.2f}s - Error: {str(e)}"
            )
            raise
            
    return wrapper

def log_validation(func):
    """Décorateur pour logger les validations de billets"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('ticket_validation')
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            is_valid = result[0] if isinstance(result, tuple) else result.get('is_valid')
            errors = result[1] if isinstance(result, tuple) else result.get('errors', [])
            
            log_message = (
                f"Ticket Validation - Duration: {duration:.2f}s - "
                f"Valid: {is_valid}"
            )
            
            if not is_valid:
                log_message += f" - Errors: {', '.join(errors)}"
            
            logger.info(log_message)
            
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Ticket Validation - Duration: {duration:.2f}s - "
                f"Error: {str(e)}"
            )
            raise
            
    return wrapper
