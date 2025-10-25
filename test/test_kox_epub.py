"""Tests for KoxFormatConverter."""

import logging
from pathlib import Path
import unittest

from koxformatconverter.exceptions import InvalidEpubFileError, PageParsingError
from koxformatconverter.kox_epub import ePubFile

# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestKoxEpub(unittest.TestCase):
    """Test suite for ePubFile class."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        # Use relative path to test data
        cls.test_dir = Path(__file__).parent
        cls.data_dir = cls.test_dir / 'data'
        cls.test_epub = cls.data_dir / '[Kox][非常家庭]卷01.kepub.epub'

    def tearDown(self):
        """Clean up after each test."""
        # Remove any generated CBZ files
        for cbz_file in self.data_dir.glob('*.cbz'):
            cbz_file.unlink()

    def test_init_valid_file(self):
        """Test initialization with a valid ePub file."""
        converter = ePubFile(self.test_epub)
        self.assertEqual(converter.file_path, self.test_epub)
        self.assertIsNone(converter.temp_dir)
        self.assertIsNone(converter.image_files_in_order)

    def test_init_nonexistent_file(self):
        """Test initialization with a nonexistent file."""
        with self.assertRaises(InvalidEpubFileError):
            ePubFile('nonexistent.epub')

    def test_init_invalid_extension(self):
        """Test initialization with wrong file extension."""
        # Create a temporary file with wrong extension
        invalid_file = self.data_dir / 'test.txt'
        invalid_file.touch()
        try:
            with self.assertRaises(InvalidEpubFileError):
                ePubFile(invalid_file)
        finally:
            invalid_file.unlink()

    def test_convert_creates_cbz(self):
        """Test that conversion creates a CBZ file."""
        converter = ePubFile(self.test_epub)
        output_path = converter.convert()

        # Check that CBZ file was created
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.suffix, '.cbz')
        self.assertEqual(output_path.stem, self.test_epub.stem)

    def test_convert_with_output_dir(self):
        """Test conversion with custom output directory."""
        output_dir = self.data_dir / 'output'
        output_dir.mkdir(exist_ok=True)

        try:
            converter = ePubFile(self.test_epub)
            output_path = converter.convert(output_dir)

            # Check that CBZ was created in the right location
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.parent, output_dir)

        finally:
            # Clean up output directory
            for file in output_dir.glob('*'):
                file.unlink()
            output_dir.rmdir()

    def test_convert_overwrites_existing(self):
        """Test that conversion overwrites existing CBZ files."""
        converter = ePubFile(self.test_epub)

        # Convert twice
        output_path1 = converter.convert()
        converter = ePubFile(self.test_epub)  # Need new instance
        output_path2 = converter.convert()

        # Should have same path and file should still exist
        self.assertEqual(output_path1, output_path2)
        self.assertTrue(output_path2.exists())


class TestGetEpubFiles(unittest.TestCase):
    """Test suite for get_epub_files function."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.test_dir = Path(__file__).parent
        cls.data_dir = cls.test_dir / 'data'

    def test_single_file(self):
        """Test getting a single file without wildcards."""
        from koxformatconverter.run import get_epub_files
        test_file = self.data_dir / '[Kox][非常家庭]卷01.kepub.epub'
        files = get_epub_files(str(test_file))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], test_file)

    def test_nonexistent_file(self):
        """Test with a nonexistent file."""
        from koxformatconverter.run import get_epub_files
        files = get_epub_files('nonexistent.epub')
        self.assertEqual(len(files), 0)

    def test_asterisk_wildcard(self):
        """Test asterisk wildcard."""
        from koxformatconverter.run import get_epub_files
        pattern = str(self.data_dir / '*.epub')
        files = get_epub_files(pattern)
        # Should find at least one epub file
        self.assertGreater(len(files), 0)

    def test_quoted_path(self):
        """Test that quoted paths are handled correctly."""
        from koxformatconverter.run import get_epub_files
        test_file = self.data_dir / '[Kox][非常家庭]卷01.kepub.epub'
        files = get_epub_files(f'"{test_file}"')
        self.assertEqual(len(files), 1)


if __name__ == '__main__':
    unittest.main()
