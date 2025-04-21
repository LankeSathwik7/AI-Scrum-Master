from core.logger import logger

def log_error(error):
    logger.error(f"ERROR: {str(error)}")