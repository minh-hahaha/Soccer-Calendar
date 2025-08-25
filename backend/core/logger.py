"""
Logging Configuration
"""
import logging
import logging.config
from pathlib import Path
from .config import get_settings

settings = get_settings()


def setup_logging():
    """Setup application logging"""
    
    # Create logs directory
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
            },
            "detailed": {
                "format": "[%(asctime)s] %(levelname)s in %(name)s [%(filename)s:%(lineno)d]: %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": settings.LOG_FILE,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console", "file"],
        },
    }
    
    logging.config.dictConfig(logging_config)
    return logging.getLogger(__name__)
