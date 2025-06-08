import unittest

from koxformatconverter.kox_epub import ePubFile


class TestKoxEpub(unittest.TestCase):

    def test_kox_epub(self):
        epub_file = ePubFile(r'C:\TechDepot\Github\KoxFormatConverter\test\data\[Kox][非常家庭]卷01.kepub.epub')
        cbz_file = epub_file.file_path.with_suffix('.cbz')
        if cbz_file.exists():
            cbz_file.unlink()
        self.assertTrue(cbz_file.exists())
