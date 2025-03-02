#!/usr/bin/env python3
"""
Main entry point for the Wiktionary converter.
"""

import argparse
import multiprocessing
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

from tqdm import tqdm

from .parsers import parse_html_file, find_language_section
from .extractors import extract_definitions
from .formatters import format_entry, open_output_file, write_header, write_footer
from .utils import setup_logger, log_timing, is_file_in_scripts
from .config import DEFAULT_EXCLUDED_SECTIONS, LANGUAGE_NAMES


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

    # Argument for script filtering
    parser.add_argument(
        "--scripts",
        nargs="+",
        choices=list(
            [
                "latin",
                "cyrillic",
                "greek",
                "chinese",
                "japanese",
                "korean",
                "arabic",
                "hebrew",
                "devanagari",
                "thai",
                "all",
            ]
        ),
        default=["all"],
        help="Filter files by script (e.g., latin, cyrillic, greek, chinese, japanese)",
    )

    # Debug and profile flags
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for detailed information",
    )

    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable timing measurements for performance analysis",
    )

    return parser.parse_args()


def process_file_wrapper(args):
    """Wrapper function for process_file to use with multiprocessing."""
    return process_file(*args)


def process_file(
    file_path: Path,
    source_lang: str,
    entry_lang: Optional[str] = None,
    debug: bool = False,
    profile: bool = False,
) -> Optional[Dict]:
    """
    Process a single file and extract definitions.

    Args:
        file_path: Path to the HTML file
        source_lang: Language code of the Wiktionary (e.g., 'en' for English Wiktionary)
        entry_lang: Language code of entries to extract (e.g., 'ru' for Russian entries)
                    If None, extracts entries for the source language
        debug: Enable debug logging
        profile: Enable performance profiling

    Returns:
        Dictionary with word and definitions or None if no valid content
    """
    if profile:
        start_time = time.time()

    # Parse the HTML file
    tree = parse_html_file(file_path)
    if tree is None:
        return None

    word = file_path.name  # Use the full filename as the word

    # Extract the language section using the flexible detection
    lang_code = entry_lang if entry_lang else source_lang

    if debug:
        print(f"Looking for language section: {lang_code}")

    if profile:
        section_start_time = time.time()

    lang_section = find_language_section(tree, lang_code)

    if profile:
        section_time = time.time() - section_start_time
        log_timing("Language section detection", section_time)

    if lang_section is None:
        if debug:
            print(
                f"No language section found for {file_path} with lang_code {lang_code}"
            )
        return None

    # Extract definitions
    excluded_sections = DEFAULT_EXCLUDED_SECTIONS

    if profile:
        extract_start_time = time.time()

    definitions = extract_definitions(lang_section, excluded_sections, debug)

    if profile:
        extract_time = time.time() - extract_start_time
        log_timing("Definition extraction", extract_time)

    if not definitions:
        if debug:
            print(f"No definitions found for {file_path}")
        return None

    result = {"word": word, "definitions": definitions}

    if profile:
        total_time = time.time() - start_time
        log_timing(f"Total processing for {file_path}", total_time)

    return result


def process_file_batch(
    file_batch: List[Path],
    source_lang: str,
    entry_lang: Optional[str],
    num_workers: int,
    debug: bool = False,
    profile: bool = False,
) -> List[Dict]:
    """Process a batch of files in parallel and return the entries."""
    with multiprocessing.Pool(processes=num_workers) as pool:
        results = pool.map(
            process_file_wrapper,
            [(f, source_lang, entry_lang, debug, profile) for f in file_batch],
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
    args = parse_arguments()

    # Setup logging based on debug flag
    setup_logger(args.debug)

    # Ensure multiprocessing works correctly on all platforms
    if os.name == "nt":  # Windows specific fix
        multiprocessing.freeze_support()

    start_time = time.time()

    input_dir = Path(args.input)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Setup temp directory
    temp_dir = args.temp_dir if args.temp_dir else tempfile.gettempdir()
    os.makedirs(temp_dir, exist_ok=True)

    # Get all files without extensions (ignoring hidden files)
    all_files = [
        f
        for f in input_dir.iterdir()
        if f.is_file() and not f.suffix and not f.name.startswith(".")
    ]
    print(f"Found {len(all_files)} files in total")

    # Filter files by script if needed
    script_start_time = time.time()
    if "all" not in args.scripts:
        print(f"Filtering files by scripts: {', '.join(args.scripts)}")

        # Apply script filtering
        files = [f for f in all_files if is_file_in_scripts(f.name, args.scripts)]

        print(f"After script filtering: {len(files)} files remaining")
    else:
        files = all_files
        print("Processing all scripts")

    if args.profile:
        script_time = time.time() - script_start_time
        log_timing("Script filtering", script_time)

    # Apply limit if specified
    if args.limit > 0 and args.limit < len(files):
        files = files[: args.limit]
        print(f"Limiting to first {args.limit} files")

    # Determine language to extract
    if args.entry_lang:
        print(
            f"Extracting {get_language_name(args.entry_lang)} entries from {get_language_name(args.source_lang)} Wiktionary"
        )
    else:
        print(f"Extracting {get_language_name(args.source_lang)} entries")

    # Sort files alphabetically by filename (which is the word)
    files.sort(key=lambda f: f.name.lower())

    # Number of worker processes
    num_workers = min(args.jobs, len(files))
    print(f"Using {num_workers} parallel processes")

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
        header_start = time.time()
        write_header(f, args.format, dict_name, source_lang_full, target_lang_full)

        if args.profile:
            header_time = time.time() - header_start
            log_timing("Header writing", header_time)

        # Process files in batches to avoid memory issues
        processed_files = 0
        skipped_files = 0
        batch_size = args.batch_size
        file_batches = [
            files[i : i + batch_size] for i in range(0, len(files), batch_size)
        ]

        for i, batch in enumerate(tqdm(file_batches, desc="Processing files")):
            batch_start = time.time()
            print(f"Processing batch {i+1}/{len(file_batches)} ({len(batch)} files)")

            # Process this batch of files
            entries = process_file_batch(
                batch,
                args.source_lang,
                args.entry_lang,
                num_workers,
                args.debug,
                args.profile,
            )

            # Write entries directly to the output file
            writing_start = time.time()
            for entry in entries:
                f.write(format_entry(entry, args.format))

            # Force write to disk after each batch
            f.flush()

            if args.profile:
                writing_time = time.time() - writing_start
                log_timing("Batch writing", writing_time)

            # Update counters
            processed_files += len(entries)
            skipped_files += len(batch) - len(entries)

            if args.profile:
                batch_time = time.time() - batch_start
                log_timing(f"Batch {i+1} processing", batch_time)
                print(f"Batch {i+1} entries: {len(entries)}")
            else:
                print(
                    f"Batch {i+1}: {len(entries)} processed, {len(batch) - len(entries)} skipped"
                )

        # Write footer if needed
        footer_start = time.time()
        write_footer(f, args.format)

        if args.profile:
            footer_time = time.time() - footer_start
            log_timing("Footer writing", footer_time)

    total_time = time.time() - start_time
    print(f"Total: Processed {processed_files} files successfully")
    print(f"Total: Skipped {skipped_files} files (no valid content or errors)")
    print(f"Successfully wrote {args.format.upper()} file to {output_file}")
    print(f"Total execution time: {total_time:.2f}s")


if __name__ == "__main__":
    main()
