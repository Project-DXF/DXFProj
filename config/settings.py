"""
Application configuration settings.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
DXF_DATA_DIR = DATA_DIR / "DXF"
PROFILE_DATA_FILE = DATA_DIR / "profile_data.json"

# Assets directory
ASSETS_DIR = PROJECT_ROOT / "assets"

# Database configuration
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", 5432),
    "database": os.getenv("DB_NAME", "dxf_analyzer"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# GUI configuration
GUI_CONFIG = {
    "window_title": "DXF Profile Analyzer",
    "default_window_size": (1200, 800),
    "icon_path": ASSETS_DIR / "expand_icon.png",
}

# Processing configuration
PROCESSING_CONFIG = {
    "max_file_size_mb": 100,
    "supported_formats": [".dxf"],
    "default_precision": 0.001,
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": PROJECT_ROOT / "logs" / "dxf_analyzer.log",
} 