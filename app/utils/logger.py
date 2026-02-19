"""
Configuration du système de logging
"""
import logging
import sys
from pathlib import Path
from app.config import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Configure un logger avec sortie console + fichier
    
    Args:
        name: Nom du logger (généralement __name__ du module)
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    
    # Éviter duplication si déjà configuré
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Format commun
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler 1 : Console (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler 2 : Fichier (logs/app.log)
    log_file = settings.log_path / "app.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger