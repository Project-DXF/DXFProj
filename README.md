# DXF Profile Analyzer

A comprehensive tool for analyzing extrusion die profiles from DXF files. This application provides feature extraction, profile matching, and performance prediction capabilities for manufacturing and engineering applications.

## Features

- **DXF File Processing**: Load and analyze DXF files with advanced parsing capabilities
- **Profile Visualization**: Interactive 2D/3D visualization of extrusion die profiles
- **Feature Extraction**: Automated extraction of geometric features and measurements
- **Profile Matching**: Compare and match profiles against a database of known designs
- **Performance Prediction**: Predict manufacturing performance based on profile characteristics
- **Database Integration**: Store and manage profile data with PostgreSQL backend
- **Modern GUI**: User-friendly PyQt5-based interface

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL (optional, for database features)

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/your-org/dxf-profile-analyzer.git
cd dxf-profile-analyzer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

4. Run the application:
```bash
python main.py
```

### Development Installation

For development with additional tools:

```bash
pip install -e ".[dev]"
```

For machine learning features:
```bash
pip install -e ".[ml]"
```

For image processing capabilities:
```bash
pip install -e ".[image]"
```

## Project Structure

```
dxf-profile-analyzer/
├── src/
│   └── dxf_analyzer/           # Main package
│       ├── core/               # Core application logic
│       ├── gui/                # User interface components
│       ├── processing/         # DXF processing and analysis
│       ├── utils/              # Utility functions
│       ├── database/           # Database management
│       └── models/             # Data models
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── docs/                       # Documentation
├── config/                     # Configuration files
├── data/                       # Data files and samples
├── scripts/                    # Utility scripts
├── assets/                     # Static assets (icons, etc.)
├── requirements.txt            # Dependencies
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

## Usage

### Basic Usage

1. Launch the application:
```bash
python main.py
```

2. Load a DXF file using the File menu
3. Analyze the profile using the available tools
4. Export results or save to database

### Command Line Interface

```bash
# Run with specific DXF file
dxf-analyzer --file path/to/profile.dxf

# Batch processing
dxf-analyzer --batch path/to/dxf/directory/
```

## Configuration

Configuration settings can be modified in `config/settings.py`:

- Database connection parameters
- GUI preferences
- Processing parameters
- File paths and directories

Environment variables can be used to override default settings:
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/dxf_analyzer

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Building Documentation

```bash
cd docs/
make html
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [https://dxf-profile-analyzer.readthedocs.io](https://dxf-profile-analyzer.readthedocs.io)
- Issues: [GitHub Issues](https://github.com/your-org/dxf-profile-analyzer/issues)
- Email: contact@dxfanalyzer.com

## Acknowledgments

- Built with [ezdxf](https://github.com/mozman/ezdxf) for DXF file handling
- GUI powered by [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- Visualization with [pyqtgraph](https://pyqtgraph.readthedocs.io/) and [matplotlib](https://matplotlib.org/) 
