import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure logging with rotation"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    
    fh = RotatingFileHandler(
        'app.log',
        maxBytes=1_000_000,
        backupCount=3,
        encoding='utf-8'
    )
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)