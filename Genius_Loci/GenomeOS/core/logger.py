import logging
from config.hw_config import LOGGING_CONFIG

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(LOGGING_CONFIG["level"])
        formatter = logging.Formatter(LOGGING_CONFIG["format"])
        for handler in LOGGING_CONFIG["handlers"]:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger