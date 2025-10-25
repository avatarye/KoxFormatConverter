"""Command-line interface for KoxFormatConverter."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import os
from pathlib import Path
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from koxformatconverter.constants import WILDCARD_QUESTION, WILDCARD_ASTERISK
from koxformatconverter.exceptions import KoxConverterError
from koxformatconverter.kox_epub import ePubFile

logger = logging.getLogger(__name__)

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    # Reconfigure stdout and stderr for UTF-8
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

console = Console(force_terminal=True, legacy_windows=False)


def setup_logging(verbose: bool = False):
    """
    Set up logging configuration with Rich handler.

    Args:
        verbose: Enable debug logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


def get_epub_files(file_path: str) -> list[Path]:
    """
    Get a list of ePub files based on the file path and wildcard patterns.

    Supports both '?' and '*' wildcards:
    - '?' represents a numeric digit (e.g., ?? -> 01, 02, ..., 99)
    - '*' represents any character sequence (standard glob)

    Args:
        file_path: String path with optional wildcards

    Returns:
        List of ePub file paths that match the pattern

    Examples:
        >>> get_epub_files('book??.epub')  # Matches book01.epub, book02.epub, etc.
        >>> get_epub_files('book*.epub')   # Matches book1.epub, book_new.epub, etc.
    """
    # Remove quotes if present
    file_path = Path(file_path.lstrip('"').rstrip('"'))

    files = []

    # Handle '?' wildcard for numeric substitution
    if WILDCARD_QUESTION in file_path.name:
        n = file_path.name.count(WILDCARD_QUESTION)
        logger.debug(f"Processing '?' wildcard pattern with {n} positions")

        for i in range(10**n):
            file_path_to_search = file_path.parent / file_path.name.replace(
                WILDCARD_QUESTION * n, str(i).zfill(n)
            )
            if file_path_to_search.exists():
                files.append(file_path_to_search)
                logger.debug(f"Found file: {file_path_to_search}")

    # Handle '*' wildcard for glob matching
    elif WILDCARD_ASTERISK in file_path.name:
        logger.debug(f"Processing '*' wildcard pattern")

        # Clean up the pattern (remove brackets which might interfere)
        pattern = file_path.name.replace('[', '*').replace(']', '*').replace('**', '*')
        files = list(file_path.parent.glob(pattern))

        logger.debug(f"Found {len(files)} files matching pattern")

    # No wildcards - single file
    else:
        if file_path.exists():
            files = [file_path]
        else:
            logger.warning(f"File not found: {file_path}")

    return files


def convert_file(epub_file: Path, output_dir: Optional[str] = None) -> tuple[bool, Optional[Path]]:
    """
    Convert a single ePub file to CBZ format.

    Args:
        epub_file: Path to the ePub file
        output_dir: Optional output directory

    Returns:
        Tuple of (success: bool, output_path: Optional[Path])
    """
    try:
        converter = ePubFile(epub_file)
        output_path = converter.convert(output_dir)
        return True, output_path

    except KoxConverterError as e:
        logger.error(f"[bold red]Conversion failed[/bold red] for {epub_file.name}: {e}", extra={"markup": True})
        return False, None

    except Exception as e:
        logger.exception(f"[bold red]Unexpected error[/bold red] converting {epub_file.name}: {e}", extra={"markup": True})
        return False, None


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Convert Kox.moe ePub files to CBZ format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s book.epub                    # Convert single file
  %(prog)s book??.epub                  # Convert book01.epub, book02.epub, etc.
  %(prog)s "book*.epub"                 # Convert all matching files
  %(prog)s book.epub output/            # Specify output directory
  %(prog)s book.epub --verbose          # Enable detailed logging
  %(prog)s "book*.epub" -j 4            # Use 4 parallel workers
  %(prog)s "book*.epub" -j -1           # Use all CPU cores

Wildcards:
  ?  - Matches a numeric digit (use ?? for 01-99, ??? for 001-999)
  *  - Matches any character sequence (standard glob pattern)
        """
    )

    parser.add_argument(
        'input_path',
        help='Path to ePub file(s). Supports wildcards (? and *)'
    )

    parser.add_argument(
        'output_dir',
        nargs='?',
        default=None,
        help='Output directory for CBZ files (default: same as input)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '-j', '--jobs',
        type=int,
        default=1,
        metavar='N',
        help='Number of parallel jobs (default: 1). Use -1 for CPU count'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.1'
    )

    return parser.parse_args()


def main():
    """Main entry point for the CLI."""
    args = parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # Display header
    console.print(Panel.fit(
        "[bold cyan]KoxFormatConverter[/bold cyan]\n"
        "Convert Kox.moe ePub files to CBZ format",
        border_style="cyan"
    ))

    # Get list of files to process
    with console.status("[bold cyan]Searching for ePub files..."):
        epub_files = get_epub_files(args.input_path)

    if not epub_files:
        console.print(f"[bold red]Error:[/bold red] No ePub files found matching: {args.input_path}")
        sys.exit(1)

    # Determine number of workers
    max_workers = args.jobs
    if max_workers == -1:
        max_workers = os.cpu_count() or 1
    elif max_workers < 1:
        max_workers = 1

    jobs_info = f" (using {max_workers} worker{'s' if max_workers > 1 else ''})" if max_workers > 1 else ""
    console.print(f"\n[bold green]Found {len(epub_files)} ePub file(s) to process{jobs_info}[/bold green]\n")

    # Process files with progress bar
    success_count = 0
    fail_count = 0
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:

        task = progress.add_task("[cyan]Converting files...", total=len(epub_files))

        if max_workers == 1:
            # Sequential processing
            for epub_file in epub_files:
                progress.update(task, description=f"[cyan]Converting: {epub_file.name}")

                success, output_path = convert_file(epub_file, args.output_dir)

                if success:
                    success_count += 1
                    results.append((epub_file.name, "Success", output_path.name if output_path else ""))
                else:
                    fail_count += 1
                    results.append((epub_file.name, "Failed", ""))

                progress.advance(task)

        else:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_file = {
                    executor.submit(convert_file, epub_file, args.output_dir): epub_file
                    for epub_file in epub_files
                }

                # Process completed tasks
                for future in as_completed(future_to_file):
                    epub_file = future_to_file[future]

                    try:
                        success, output_path = future.result()

                        if success:
                            success_count += 1
                            results.append((epub_file.name, "Success", output_path.name if output_path else ""))
                        else:
                            fail_count += 1
                            results.append((epub_file.name, "Failed", ""))

                    except Exception as e:
                        logger.exception(f"Unexpected error in worker thread for {epub_file.name}: {e}")
                        fail_count += 1
                        results.append((epub_file.name, "Failed", ""))

                    progress.advance(task)

    # Sort results by input filename for consistent display
    results.sort(key=lambda x: x[0])

    # Display results table
    console.print()
    table = Table(title="Conversion Results", border_style="cyan")
    table.add_column("Input File", style="cyan", no_wrap=False)
    table.add_column("Status", justify="center")
    table.add_column("Output File", style="green", no_wrap=False)

    for input_file, status, output_file in results:
        status_style = "[bold green]" if status == "Success" else "[bold red]"
        table.add_row(
            input_file,
            f"{status_style}{status}[/]",
            output_file
        )

    console.print(table)

    # Summary
    console.print()
    if fail_count == 0:
        console.print(Panel(
            f"[bold green]All {success_count} file(s) converted successfully![/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold yellow]Conversion complete:[/bold yellow]\n"
            f"  [green]Success: {success_count}[/green]\n"
            f"  [red]Failed: {fail_count}[/red]",
            border_style="yellow"
        ))

    # Exit with appropriate code
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == '__main__':
    main()
