import os
import logging
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
def setup_logging(app):
    # Set up file handler for general logs
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Set up file handler for errors
    error_file_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    error_file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s [in %(pathname)s:%(lineno)d]:\n%(message)s'
    ))
    error_file_handler.setLevel(logging.ERROR)
    
    # Configure Flask app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Create a separate logger for API requests
    api_logger = logging.getLogger('api')
    api_logger.setLevel(logging.INFO)
    
    api_handler = RotatingFileHandler(
        'logs/api.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    api_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s'
    ))
    api_logger.addHandler(api_handler)
    
    return api_logger
