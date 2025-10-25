# KoxFormatConverter

Convert ePub files from kox.moe to CBZ format.

## Installation

```bash
pip install koxformatconverter
```

## Usage

### Basic Conversion

Convert a single ePub file:

```bash
krun path/to/file.epub
```

The output CBZ file will be saved in the same directory as the input file.

### Batch Conversion

Use `??` as a placeholder for numbers in filenames:

```bash
krun path/to/file_??.epub
```

This will find and convert all matching files (e.g., `file_01.epub`, `file_02.epub`, etc.).

Use `*` as a wildcard for any characters:

```bash
krun path/to/*.epub
```

## Requirements

- Python 3.12 - 3.14

## License

MIT License - see [LICENSE](LICENSE) file for details.
