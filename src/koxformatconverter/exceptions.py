"""Custom exceptions for KoxFormatConverter."""


class KoxConverterError(Exception):
    """Base exception for all KoxFormatConverter errors."""
    pass


class InvalidEpubFileError(KoxConverterError):
    """Raised when the ePub file is invalid or corrupted."""
    pass


class ExtractionError(KoxConverterError):
    """Raised when extraction of ePub file fails."""
    pass


class PageParsingError(KoxConverterError):
    """Raised when parsing page HTML fails."""
    pass


class ImageNotFoundError(KoxConverterError):
    """Raised when expected image files are not found."""
    pass


class CBZGenerationError(KoxConverterError):
    """Raised when CBZ file generation fails."""
    pass


class InvalidOutputDirectoryError(KoxConverterError):
    """Raised when the output directory is invalid."""
    pass
