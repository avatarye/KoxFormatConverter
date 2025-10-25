"""Constants for KoxFormatConverter."""

# File extensions
EPUB_EXTENSION = '.epub'
CBZ_EXTENSION = '.cbz'
ZIP_EXTENSION = '.zip'
HTML_EXTENSION = '.html'

# Directory names within ePub structure
HTML_DIR = 'html'
IMAGE_DIR = 'image'

# Image file names
COVER_IMAGE = 'cover.jpg'
COVER_IMAGE_RENAMED = '000.jpg'

# Regex patterns for parsing Kox.moe ePub files
# Pattern to match Chinese page numbering: "第 X 頁"
PAGE_NUMBER_PATTERN = r'<title>第\s*(\d+)\s*頁</title>'
IMAGE_SRC_PATTERN = r'<img\s+[^>]*src="([^"]+)"'

# HTML tags to search for
TITLE_TAG = '<title>'
IMG_TAG = '<img src='

# File naming
IMAGE_NAME_FORMAT = '{:03d}'  # 001, 002, etc.

# Default encoding
DEFAULT_ENCODING = 'utf-8'

# Wildcard characters
WILDCARD_QUESTION = '?'
WILDCARD_ASTERISK = '*'
