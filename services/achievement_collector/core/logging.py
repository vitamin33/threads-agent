# Logging Configuration

import logging
import sys
from typing import Optional


def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """Setup structured logging"""
    
    # Create logger
    logger = logging.getLogger(name or "achievement_collector")
    
    # Only configure if not already configured
    if not logger.handlers:
        # Set level
        logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger