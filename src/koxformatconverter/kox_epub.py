"""Module for converting Kox.moe ePub files to CBZ format."""

import logging
from pathlib import Path
import re
import shutil
import tempfile
from typing import Optional
import zipfile

from koxformatconverter.constants import (
    EPUB_EXTENSION,
    CBZ_EXTENSION,
    ZIP_EXTENSION,
    HTML_EXTENSION,
    HTML_DIR,
    IMAGE_DIR,
    COVER_IMAGE,
    COVER_IMAGE_RENAMED,
    PAGE_NUMBER_PATTERN,
    IMAGE_SRC_PATTERN,
    TITLE_TAG,
    IMG_TAG,
    IMAGE_NAME_FORMAT,
    DEFAULT_ENCODING,
)
from koxformatconverter.exceptions import (
    InvalidEpubFileError,
    ExtractionError,
    PageParsingError,
    ImageNotFoundError,
    CBZGenerationError,
    InvalidOutputDirectoryError,
)

logger = logging.getLogger(__name__)


class ePubFile:
    """
    Class to convert a Kox.moe ePub file to CBZ format.

    The ePub file will be extracted to a temporary directory,
    HTML pages will be parsed to determine image order,
    and images will be packaged into a CBZ file.

    Attributes:
        file_path: Path to the ePub file
        temp_dir: Temporary directory for extraction
        image_files_in_order: List of image files in page order

    Example:
        >>> converter = ePubFile('path/to/file.epub')
        >>> converter.convert(output_dir='output/')
    """

    def __init__(self, file_path: str | Path):
        """
        Initialize the ePubFile converter.

        Args:
            file_path: Path to the ePub file to convert

        Raises:
            InvalidEpubFileError: If the file doesn't exist or isn't a valid ePub
        """
        self.file_path = Path(file_path)
        self.temp_dir: Optional[Path] = None
        self.image_files_in_order: Optional[list[str]] = None

        # Validate file
        if not self.file_path.exists():
            raise InvalidEpubFileError(f"File not found: {self.file_path}")

        if not self.file_path.is_file():
            raise InvalidEpubFileError(f"Path is not a file: {self.file_path}")

        if self.file_path.suffix != EPUB_EXTENSION:
            raise InvalidEpubFileError(
                f"File must have {EPUB_EXTENSION} extension: {self.file_path}"
            )

        logger.info(f"Initialized converter for: {self.file_path}")

    def convert(self, output_dir: Optional[str | Path] = None) -> Path:
        """
        Convert the ePub file to CBZ format.

        Args:
            output_dir: Directory to save the CBZ file. If None, saves in the
                       same directory as the ePub file. Can be relative or absolute.

        Returns:
            Path to the generated CBZ file

        Raises:
            ExtractionError: If ePub extraction fails
            PageParsingError: If page parsing fails
            CBZGenerationError: If CBZ generation fails
        """
        try:
            logger.info(f"Starting conversion: {self.file_path.name}")

            # Extract ePub
            self.temp_dir = self._extract()
            logger.debug(f"Extracted to: {self.temp_dir}")

            # Parse pages to get image order
            self.image_files_in_order = self._parse_pages()
            logger.info(f"Found {len(self.image_files_in_order)} pages")

            # Generate CBZ
            output_path = self._generate_cbz(output_dir)
            logger.info(f"CBZ generated: {output_path}")

            return output_path

        finally:
            # Always clean up temporary files
            self._clean()

    def _extract(self) -> Path:
        """
        Extract the ePub file to a temporary directory.

        Returns:
            Path to the temporary directory

        Raises:
            ExtractionError: If extraction fails
        """
        try:
            temp_dir = Path(tempfile.mkdtemp())
            logger.debug(f"Created temp directory: {temp_dir}")

            with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            return temp_dir

        except zipfile.BadZipFile as e:
            raise ExtractionError(f"Invalid or corrupted ePub file: {self.file_path}") from e
        except (OSError, IOError) as e:
            raise ExtractionError(f"Failed to extract ePub: {e}") from e

    def _parse_pages(self) -> list[str]:
        """
        Parse HTML pages to extract image file paths in page order.
        Filters out non-manga pages (website watermarks, etc.).

        Returns:
            List of image file paths in page order

        Raises:
            PageParsingError: If parsing fails or pages are inconsistent
        """
        page_dict = {}
        html_dir = self.temp_dir / HTML_DIR

        if not html_dir.exists():
            raise PageParsingError(f"HTML directory not found: {html_dir}")

        page_html_files = list(html_dir.glob(f'*{HTML_EXTENSION}'))

        if not page_html_files:
            raise PageParsingError(f"No HTML files found in: {html_dir}")

        logger.debug(f"Parsing {len(page_html_files)} HTML files")

        filtered_count = 0

        # Parse each HTML file
        for page_html_file in page_html_files:
            page_number, image_path, is_valid = self._parse_page_html(page_html_file)

            if not is_valid:
                filtered_count += 1
                continue

            if page_number and image_path:
                page_dict[page_number] = image_path
                logger.debug(f"Page {page_number}: {image_path}")

        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} non-manga page(s)")

        # Validate page numbers are sequential
        if not page_dict:
            raise PageParsingError("No valid pages found in HTML files")

        sorted_pages = sorted(page_dict.keys(), key=int)
        largest_page_number = int(sorted_pages[-1])

        if len(page_dict) != largest_page_number:
            raise PageParsingError(
                f"Missing pages detected. Found {len(page_dict)} pages, "
                f"expected {largest_page_number}"
            )

        # Build ordered list of images
        images_in_page_order = [
            page_dict[str(i)] for i in range(1, largest_page_number + 1)
        ]

        return images_in_page_order

    def _parse_page_html(self, page_html_file: Path) -> tuple[Optional[str], Optional[str], bool]:
        """
        Parse a single HTML page to extract page number and image path.

        Args:
            page_html_file: Path to the HTML file

        Returns:
            Tuple of (page_number, image_path, is_valid), where is_valid indicates
            if this is a valid manga page (not a watermark/website page)
        """
        page_number = None
        image_path = None
        title = None

        try:
            with open(page_html_file, 'r', encoding=DEFAULT_ENCODING) as file:
                page_html = file.read()

                for line in page_html.split('\n'):
                    # Extract title
                    if TITLE_TAG in line:
                        # Get the full title first
                        title_match = re.search(r'<title>(.*?)</title>', line)
                        if title_match:
                            title = title_match.group(1)

                        # Check if it matches the page number pattern
                        match = re.search(PAGE_NUMBER_PATTERN, line)
                        if match:
                            page_number = match.group(1)

                    # Extract image source
                    if IMG_TAG in line:
                        match = re.search(IMAGE_SRC_PATTERN, line)
                        if match:
                            image_path = match.group(1)

        except (OSError, IOError) as e:
            logger.warning(f"Failed to parse {page_html_file.name}: {e}")
            return None, None, False

        # Filter out non-manga pages (website watermarks, etc.)
        # Valid pages must have the Chinese page number pattern "第 X 頁"
        if page_number is None:
            if title:
                logger.debug(f"Filtering out non-manga page: {page_html_file.name} (title: {title})")
            return None, None, False

        return page_number, image_path, True

    def _generate_cbz(self, output_dir: Optional[str | Path] = None) -> Path:
        """
        Generate CBZ file from extracted and parsed ePub.

        Args:
            output_dir: Directory to save the CBZ file

        Returns:
            Path to the generated CBZ file

        Raises:
            CBZGenerationError: If CBZ generation fails
            ImageNotFoundError: If expected images are missing
        """
        try:
            # Rename images in sequential order
            self._rename_images()

            # Handle cover image
            self._handle_cover_image()

            # Determine output directory
            output_path = self._resolve_output_path(output_dir)

            # Create CBZ (which is just a zip file)
            self._create_cbz_archive(output_path)

            return output_path

        except Exception as e:
            if isinstance(e, (CBZGenerationError, ImageNotFoundError, InvalidOutputDirectoryError)):
                raise
            raise CBZGenerationError(f"Failed to generate CBZ: {e}") from e

    def _rename_images(self):
        """
        Rename image files to sequential numbers (001, 002, etc.).
        Removes non-manga images (watermarks, templates, etc.).

        Raises:
            ImageNotFoundError: If an expected image file is missing
        """
        html_dir = self.temp_dir / HTML_DIR
        image_dir = self.temp_dir / IMAGE_DIR

        # Build set of images we want to keep (manga pages only)
        valid_images = set()
        for image_file in self.image_files_in_order:
            # Image paths in HTML are like "../image/moe-xxxxx.jpg"
            # Extract just the filename
            image_filename = Path(image_file).name
            valid_images.add(image_filename)

        # Also keep cover.jpg if it exists
        if (image_dir / COVER_IMAGE).exists():
            valid_images.add(COVER_IMAGE)

        # Remove all non-manga images from image directory
        removed_count = 0
        if image_dir.exists():
            for file in list(image_dir.iterdir()):
                if file.is_file() and file.name not in valid_images:
                    file.unlink()
                    logger.debug(f"Removed non-manga image: {file.name}")
                    removed_count += 1

        if removed_count > 0:
            logger.info(f"Removed {removed_count} non-manga image(s)")

        # Rename manga images to sequential numbers
        for i, image_file in enumerate(self.image_files_in_order):
            # Image paths in HTML are like "../image/moe-xxxxx.jpg"
            # Resolve relative to html directory
            abs_image_file = (html_dir / image_file).resolve()

            if not abs_image_file.exists():
                raise ImageNotFoundError(f"Image file not found: {abs_image_file}")

            new_filename = IMAGE_NAME_FORMAT.format(i + 1) + abs_image_file.suffix
            new_image_file = image_dir / new_filename

            shutil.move(str(abs_image_file), str(new_image_file))
            logger.debug(f"Renamed: {abs_image_file.name} -> {new_image_file.name}")

    def _handle_cover_image(self):
        """Move and rename cover image if it exists."""
        cover_image = self.temp_dir / IMAGE_DIR / COVER_IMAGE

        if cover_image.exists():
            new_cover = self.temp_dir / IMAGE_DIR / COVER_IMAGE_RENAMED
            shutil.move(str(cover_image), str(new_cover))
            logger.debug(f"Renamed cover: {COVER_IMAGE} -> {COVER_IMAGE_RENAMED}")

    def _resolve_output_path(self, output_dir: Optional[str | Path]) -> Path:
        """
        Resolve the output file path.

        Args:
            output_dir: Output directory (can be None, relative, or absolute)

        Returns:
            Resolved output file path

        Raises:
            InvalidOutputDirectoryError: If output directory is invalid
        """
        if output_dir is None:
            # Save in same directory as input file
            output_file_dir = self.file_path.parent
        else:
            output_dir = Path(output_dir)

            # Handle relative paths
            if not output_dir.is_absolute():
                output_file_dir = self.file_path.parent / output_dir
            else:
                output_file_dir = output_dir

            # Create directory if it doesn't exist
            try:
                output_file_dir.mkdir(parents=True, exist_ok=True)
            except (OSError, IOError) as e:
                raise InvalidOutputDirectoryError(
                    f"Cannot create output directory {output_file_dir}: {e}"
                ) from e

        output_file = output_file_dir / (self.file_path.stem + CBZ_EXTENSION)
        return output_file

    def _create_cbz_archive(self, output_file: Path):
        """
        Create the CBZ archive file.

        Args:
            output_file: Path where CBZ file should be created

        Raises:
            CBZGenerationError: If archive creation fails
        """
        try:
            # Remove existing file if present
            if output_file.exists():
                output_file.unlink()
                logger.debug(f"Removed existing file: {output_file}")

            # Create zip archive
            image_dir = self.temp_dir / IMAGE_DIR

            if not image_dir.exists() or not any(image_dir.iterdir()):
                raise CBZGenerationError(f"No images found in {image_dir}")

            shutil.make_archive(
                str(output_file.parent / output_file.stem),
                'zip',
                image_dir
            )

            # Rename .zip to .cbz
            zip_file = output_file.with_suffix(ZIP_EXTENSION)
            shutil.move(str(zip_file), str(output_file))

        except Exception as e:
            raise CBZGenerationError(f"Failed to create archive: {e}") from e

    def _clean(self):
        """Clean up temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temp directory: {self.temp_dir}")
            except (OSError, IOError) as e:
                logger.warning(f"Failed to clean up temp directory: {e}")
