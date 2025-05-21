from pathlib import Path
import sys

from koxformatconverter.kox_epub import ePubFile


def get_epub_files(file_path: str) -> list[Path]:
    """
    Get a list of ePub files based on the file path and wildcard in the path. Both '?' and '*' are supported.

    :param file_path: a string of the file path
    :return: a list of ePub file paths
    """
    file_path = Path(file_path.lstrip('"').rstrip('"'))
    if '?' in file_path.name:
        files = []
        n = file_path.name.count('?')
        for i in range(10**n):
            file_path_to_search = file_path.parent / file_path.name.replace('?' * n, str(i).zfill(n))
            if file_path_to_search.exists():
                files.append(file_path_to_search)
    elif '*' in file_path.name:
        files = list(file_path.parent.glob(file_path.name.replace('[', '*').replace(']', '*').replace('**', '*')))
    else:
        files = [file_path]
    return files


def main():
    args = sys.argv[1:]
    if len(args) < 1:
        print('Please input the path of the ePub files. Wildcards (? and *) are supported.')
        sys.exit(1)
    epub_files = get_epub_files(args[0])
    output_dir = args[1] if len(args) > 1 else None
    print(f'Processing {len(epub_files)} ePub files...')
    for epub_file in epub_files:
        ePubFile(epub_file, output_dir)


if __name__ == '__main__':
    main()
