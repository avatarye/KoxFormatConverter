"""KoxFormatConverter - Convert Kox.moe ePub files to CBZ format."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("koxformatconverter")
except PackageNotFoundError:
    __version__ = "0.1.1"  # fallback for development

from koxformatconverter.kox_epub import ePubFile
from koxformatconverter.exceptions import (
    KoxConverterError,
    InvalidEpubFileError,
    ExtractionError,
    PageParsingError,
    ImageNotFoundError,
    CBZGenerationError,
    InvalidOutputDirectoryError,
)

__all__ = [
    "__version__",
    "ePubFile",
    "KoxConverterError",
    "InvalidEpubFileError",
    "ExtractionError",
    "PageParsingError",
    "ImageNotFoundError",
    "CBZGenerationError",
    "InvalidOutputDirectoryError",
]
