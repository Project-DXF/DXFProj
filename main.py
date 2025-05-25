#!/usr/bin/env python
"""
DXF Profile Analyzer - Main Application Entry Point

This application provides tools for analyzing extrusion die profiles from DXF files.
It includes feature extraction, profile matching, and performance prediction.
"""

from src.dxf_analyzer.core.application import DXFProfileAnalyzer

def main():
    """Main entry point for the DXF Profile Analyzer application."""
    DXFProfileAnalyzer.main()

if __name__ == '__main__':
    main()
