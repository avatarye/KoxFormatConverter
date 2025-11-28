# Development Guide

## Setup

### Option 1: Using uv (recommended)

```bash
uv sync
```

### Option 2: Using pip

```bash
pip install -e .
```

## Running from Source

```bash
python src/koxformatconverter/run.py <input_file>
```

Or using the installed script:

```bash
krun <input_file>
```

## Project Structure

```
src/koxformatconverter/
├── run.py           # Main entry point
├── kox_epub.py      # ePub to CBZ conversion logic
├── constants.py     # Project constants
└── exceptions.py    # Custom exceptions

test/
└── test_kox_epub.py # Tests
```

## Building

### Development Dependencies

Install development dependencies:

```bash
# Using uv
uv sync --dev

# Using pip
pip install -e ".[dev]"
```

### Creating Executables

Build standalone executables using PyInstaller:

```bash
pyinstaller --onefile src/koxformatconverter/run.py
```

## Testing

Run tests:

```bash
python -m pytest test/
```

## Version Management

Update version in `pyproject.toml`:

```toml
[project]
version = "x.y.z"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
