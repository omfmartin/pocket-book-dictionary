#!/usr/bin/env python3
"""
Main entry point for the Wiktionary converter.
"""

import argparse
import multiprocessing
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging
from tqdm import tqdm

from .parsers import parse_html_file, find_language_section
from .extractors import extract_definitions
from .formatters import format_entry, open_output_file, write_header, write_footer
from .utils import setup_logger, is_file_in_scripts
from .config import DEFAULT_EXCLUDED_SECTIONS, LANGUAGE_NAMES, SCRIPT_RANGES


def parse_arguments():
    """Parse command-line arguments using argparse."""
    parser = argparse.ArgumentParser(
        description="Convert Wiktionary HTML files to dictionary formats"
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Input directory containing files"
    )
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "-s",
        "--source-lang",
        required=True,
        help="Source language code of the Wiktionary (e.g., en for English Wiktionary)",
    )
    parser.add_argument(
        "-t",
        "--target-lang",
        required=True,
        help="Target language code to extract (e.g., ru for Russian entries)",
    )
    parser.add_argument(
        "-e",
        "--entry-lang",
        help="Language of entries to extract (if different from source-lang). Use this to extract specific language entries.",
    )
    parser.add_argument(
        "-n",
        "--name",
        default="Wiktionary Dictionary",
        help="Dictionary name",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["lingvo", "xdxf"],
        default="xdxf",
        help="Output format",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=multiprocessing.cpu_count(),
        help="Number of parallel processes to use (default: number of CPU cores)",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=0,
        help="Limit the number of files to process (0 for no limit, default: 0)",
    )
    parser.add_argument(
        "-b",
        "--batch-size",
        type=int,
        default=10000,
        help="Number of files to process in each batch (default: 10000)",
    )
    parser.add_argument(
        "--temp-dir",
        help="Directory for temporary files (default: system temp directory)",
    )
    parser.add_argument(
        "--excluded-sections",
        nargs="+",
        default=list(DEFAULT_EXCLUDED_SECTIONS),
        help="Sections to exclude from extraction (default: Translations, etc.)",
    )
    parser.add_argument(
        "--scripts",
        nargs="+",
        choices=["all"] + list(SCRIPT_RANGES.keys()),
        default=["all"],
        help="Filter files by script",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for detailed information",
    )

    return parser.parse_args()


def process_file_wrapper(args):
    """Wrapper function for process_file to use with multiprocessing."""
    return process_file(*args)


def process_file(
    file_path: Path,
    source_lang: str,
    entry_lang: Optional[str] = None,
) -> Optional[Dict]:
    """
    Process a single file and extract definitions.

    Args:
        file_path: Path to the HTML file
        source_lang: Language code of the Wiktionary (e.g., 'en' for English Wiktionary)
        entry_lang: Language code of entries to extract (e.g., 'ru' for Russian entries)
                    If None, extracts entries for the source language

    Returns:
        Dictionary with word and definitions or None if no valid content
    """
    # Parse the HTML file
    tree = parse_html_file(file_path)
    if tree is None:
        return None

    word = file_path.name  # Use the full filename as the word

    # Extract the language section using the flexible detection
    lang_code = entry_lang if entry_lang else source_lang

    logging.debug(f"Looking for language section: {lang_code}")

    lang_section = find_language_section(tree, lang_code)

    if lang_section is None:
        logging.debug(
            f"No language section found for {file_path} with lang_code {lang_code}"
        )
        return None

    # Extract definitions
    excluded_sections = DEFAULT_EXCLUDED_SECTIONS

    definitions = extract_definitions(lang_section, excluded_sections)

    if not definitions:
        logging.debug(f"No definitions found for {file_path}")
        return None

    result = {"word": word, "definitions": definitions}

    return result


def process_file_batch(
    file_batch: List[Path],
    source_lang: str,
    entry_lang: Optional[str],
    num_workers: int,
) -> List[Dict]:
    """Process a batch of files in parallel and return the entries."""
    with multiprocessing.Pool(processes=num_workers) as pool:
        results = pool.map(
            process_file_wrapper,
            [(f, source_lang, entry_lang) for f in file_batch],
        )

    return [entry for entry in results if entry is not None]


def get_language_name(lang_code):
    """Convert language code to full language name."""
    if lang_code in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[lang_code]

    # Fall back to capitalize the code if not found
    return lang_code.capitalize() if lang_code else "Unknown"


def main():
    """Main processing pipeline."""

    # Setup
    start_time = time.time()
    args = parse_arguments()

    setup_logger(args.debug)

    input_dir = Path(args.input)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Get all files without extensions (ignoring hidden files)
    logging.info("Getting all files")
    all_files = [
        f
        for f in input_dir.iterdir()
        if f.is_file() and not f.suffix and not f.name.startswith(".")
    ]
    logging.info(f"Found {len(all_files)} files in total")

    # Filter files by script if needed
    script_start_time = time.time()
    if "all" not in args.scripts:
        logging.info(f"Filtering files by scripts: {', '.join(args.scripts)}")

        # Apply script filtering
        files = [f for f in all_files if is_file_in_scripts(f.name, args.scripts)]

        logging.info(f"After script filtering: {len(files)} files remaining")
    else:
        files = all_files
        logging.info("Processing all scripts")

    # Apply limit if specified
    if args.limit > 0 and args.limit < len(files):
        files = files[: args.limit]
        logging.info(f"Limiting to first {args.limit} files")

    # Determine language to extract
    if args.entry_lang:
        logging.info(
            f"Extracting {get_language_name(args.entry_lang)} entries from {get_language_name(args.source_lang)} Wiktionary"
        )
    else:
        logging.info(f"Extracting {get_language_name(args.source_lang)} entries")

    # Sort files alphabetically by filename (which is the word)
    logging.info("Sorting files")
    files.sort(key=lambda f: f.name.lower())

    # Number of worker processes
    num_workers = min(args.jobs, len(files))
    logging.info(f"Using {num_workers} parallel processes")

    # Prepare output file
    with open_output_file(str(output_file)) as f:
        # Get full language names
        source_lang_full = get_language_name(args.source_lang)
        target_lang_full = get_language_name(args.target_lang)

        # If extracting specific language entries, use that in the dictionary name
        if args.entry_lang:
            entry_lang_full = get_language_name(args.entry_lang)
            dict_name = f"{args.name} ({entry_lang_full}-{target_lang_full})"
        else:
            dict_name = f"{args.name} ({source_lang_full}-{target_lang_full})"

        # Write appropriate header based on the selected format
        write_header(f, args.format, dict_name, source_lang_full, target_lang_full)

        # Process files in batches to avoid memory issues
        processed_files = 0
        skipped_files = 0
        batch_size = args.batch_size
        file_batches = [
            files[i : i + batch_size] for i in range(0, len(files), batch_size)
        ]

        for i, batch in enumerate(tqdm(file_batches, desc="Processing files")):
            logging.info(
                f"Processing batch {i+1}/{len(file_batches)} ({len(batch)} files)"
            )

            # Process this batch of files
            entries = process_file_batch(
                batch,
                args.source_lang,
                args.entry_lang,
                num_workers,
            )

            # Write entries directly to the output file
            for entry in entries:
                f.write(format_entry(entry, args.format))

            # Force write to disk after each batch
            f.flush()

            # Update counters
            processed_files += len(entries)
            skipped_files += len(batch) - len(entries)

            logging.info(
                f"Batch {i+1}: {len(entries)} processed, {len(batch) - len(entries)} skipped"
            )

        # Write footer if needed
        write_footer(f, args.format)

    total_time = time.time() - start_time
    logging.info(f"Total: Processed {processed_files} files successfully")
    logging.info(f"Total: Skipped {skipped_files} files (no valid content or errors)")
    logging.info(f"Successfully wrote {args.format.upper()} file to {output_file}")
    logging.info(f"Total execution time: {total_time:.2f}s")


if __name__ == "__main__":
    main()
