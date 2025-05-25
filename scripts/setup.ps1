# Setup script for DXF Profile Analyzer project (PowerShell version)
# Assumes you're already inside your desired root folder

# Create virtual environment
python -m venv venv

# Create requirements.txt
@"
# Core dependencies
ezdxf>=1.0.0       # DXF file handling
numpy>=1.20.0      # Numerical computations
matplotlib>=3.5.0  # Basic plotting
scipy>=1.7.0       # Scientific computing (for feature extraction)

# GUI dependencies
PyQt5>=5.15.0      # Main GUI framework
pyqtgraph>=0.12.0  # Fast plotting for DXF visualization

# Image processing
opencv-python>=4.5.0  # For image-based comparison
scikit-image>=0.18.0  # Advanced image processing

# Machine learning dependencies (for later phases)
# scikit-learn>=1.0.0  # Basic machine learning
# tensorflow>=2.7.0    # Advanced machine learning (if needed)

# Database
# sqlalchemy>=1.4.0    # Database ORM
# pymongo>=4.0.0       # MongoDB client (if using NoSQL)

# Utility
tqdm>=4.62.0       # Progress bars
pytest>=6.2.0      # Testing framework
"@ | Set-Content -Path "requirements.txt"

# Install dependencies inside venv
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\venv\Scripts\python.exe" -m pip install -r requirements.txt

# Create project folders with __init__.py
$folders = @(
    "dxf_processing",
    "image_processing",
    "database",
    "profile_matching",
    "die_suggestion",
    "performance_prediction",
    "pdf_export",
    "data_upload",
    "gui",
    "utils",
    "tests"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    New-Item -ItemType File -Path "$folder\__init__.py" -Force | Out-Null
}

# Create main.py
@"
#!/usr/bin/env python
\"\"\"
DXF Profile Analyzer - Main Application Entry Point

This application provides tools for analyzing extrusion die profiles from DXF files.
It includes feature extraction, profile matching, and performance prediction.
\"\"\"

import sys
from gui.main_window import launch_app

if __name__ == '__main__':
    launch_app()
"@ | Set-Content -Path "main.py"

Write-Host "✅ Project setup complete!"
Write-Host "To start working:"
Write-Host "1. Run: .\venv\Scripts\activate"
Write-Host "2. Then: python main.py"
