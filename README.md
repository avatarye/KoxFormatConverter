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

Or use as a Python module:

```bash
python -m koxformatconverter path/to/file.epub
```

### Output Directory

By default, the output directory is automatically extracted from the filename. Kox.moe files follow the pattern `[Source][SeriesName]Volume.epub`:

```bash
krun "[Kmoe][SeriesName]vol01.epub"
# Output: ./SeriesName/SeriesName_vol01.cbz
```

You can also specify a custom output directory:

```bash
krun path/to/file.epub output/directory/
```

### Batch Conversion

Use `??` as a placeholder for numbers in filenames:

```bash
krun "path/to/file_??.epub"
```

This will find and convert all matching files (e.g., `file_01.epub`, `file_02.epub`, etc.).

Use `*` as a wildcard for any characters:

```bash
krun "path/to/*.epub"
```

### Parallel Processing

Use multiple workers for faster batch conversion:

```bash
krun "path/to/*.epub" -j 4      # Use 4 workers
krun "path/to/*.epub" -j -1     # Use all CPU cores
```

## Requirements

- Python 3.12 - 3.14

## License

MIT License - see [LICENSE](LICENSE) file for details.
