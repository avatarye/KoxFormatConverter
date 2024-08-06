from pathlib import Path
import re
import shutil
import tempfile
import zipfile


class ePubFile:

    file_path = None
    temp_dir = None
    image_files_in_order = None

    def __init__(self, file_path):
        self.file_path = Path(file_path)
        if not (self.file_path.exists() and self.file_path.is_file() and self.file_path.suffix == '.epub'):
           raise FileNotFoundError(f"File not found at {self.file_path}")
        self.temp_dir = self.extract()
        if self.temp_dir is None:
            raise Exception(f"Error extracting file at {self.file_path}")
        self.image_files_in_order = self.parse_pages()
        self.generate_cbz()
        self.clean()

    def extract(self) -> Path:
        """Extract the content of the ePub file to a temporary directory."""
        temp_dir = Path(tempfile.mkdtemp())
        with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        return temp_dir

    def parse_pages(self) -> list[str]:
        """Parse the content of the ePub file."""

        def parse_page_html(page_html_file):
            nonlocal page_dict
            page_number, image_path = None, None
            with open(page_html_file, 'r', encoding='utf-8') as file:
                page_html = file.read()
                for line in page_html.split('\n'):
                    if '<title>' in line:
                        match = re.search(r'<title>第\s*(\d+)\s*頁</title>', line)
                        if match:
                            page_number = match.group(1)
                    if '<img src=' in line:
                        match = re.search(r'<img\s+[^>]*src="([^"]+)"', line)
                        if match:
                            image_path = match.group(1)
            return page_number, image_path

        # Extract page number and corresponding image path from each page HTML file
        page_dict = {}
        page_html_files = list(self.temp_dir.glob('html/*.html'))
        for page_html_file in page_html_files:
            page_number, image_path = parse_page_html(page_html_file)
            if page_number and image_path:
                page_dict[page_number] = image_path
        # Verify the page dictionary
        largest_page_number = sorted(page_dict.keys(), key=lambda x: int(x))[-1]
        if len(page_dict) != int(largest_page_number):
            raise Exception("Error parsing pages")
        images_in_page_order = [page_dict[str(i)] for i in range(1, int(largest_page_number) + 1)]
        for page, image in enumerate(images_in_page_order):
            print(f'{str(page).zfill(3)}: {image}')
        return images_in_page_order

    def generate_cbz(self, output_file_dir=None):
        """Generate a CBZ file from the extracted ePub file."""
        # Rename the image files in order
        for i, image_file in enumerate(self.image_files_in_order):
            abs_image_file = self.temp_dir / 'html' / image_file
            new_image_file = abs_image_file.parent / f'{(i + 1):03d}{abs_image_file.suffix}'
            shutil.move(abs_image_file, new_image_file)
        # Handle cover image
        cover_image = self.temp_dir / 'image' / 'cover.jpg'
        if cover_image.exists():
            shutil.move(cover_image, self.temp_dir / 'image' / '000.jpg')
        # Zip the image dir to a CBZ file
        if output_file_dir is None:
            output_file_dir = self.file_path.parent
        output_file = output_file_dir / f'{self.file_path.stem}.cbz'
        if output_file.exists():
            output_file.unlink()
        shutil.make_archive(output_file.parent / output_file.stem, 'zip', self.temp_dir / 'image')
        # Rename the CBZ file to a ZIP file
        shutil.move(output_file.with_suffix('.zip'), output_file)
        print(f"CBZ file generated at {output_file}\n")

    def clean(self):
        """Delete the temporary directory regardless of the result."""
        shutil.rmtree(self.temp_dir)
