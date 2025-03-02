import re
import argparse
import html
import multiprocessing
import tempfile
import os
from typing import Optional, Dict, List
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging
import codecs

# Constants for clarity and maintenance
HTML_PARSER = "html.parser"
DETAILS_TAG = "details"
DATA_LEVEL_ATTR = "data-level"
DEFAULT_EXCLUDED_SECTIONS = {
    "Traduccions",
    "Miscel·lània",
    "Vegeu també",
    "Translations",
    "Miscellany",
    "See also",
}


def setup_logger():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


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
        help="Number of files to process in each batch (default: 1000)",
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
    return parser.parse_args()


def process_file(
    file_path: Path, source_lang: str, entry_lang: Optional[str] = None
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
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, HTML_PARSER)
    except (
        IsADirectoryError,
        UnicodeDecodeError,
        FileNotFoundError,
        PermissionError,
    ) as e:
        logging.debug(f"Error processing {file_path}: {str(e)}")
        return None  # Skip problem files in worker processes

    word = file_path.name  # Use the full filename as the word

    # Extract the language section
    lang_code = entry_lang if entry_lang else source_lang
    lang_span = soup.find("span", id=lang_code)
    if not lang_span:
        return None

    lang_section = lang_span.find_parent(DETAILS_TAG)
    if not lang_section:
        return None

    # Extract definitions
    definitions = extract_definitions(lang_section, DEFAULT_EXCLUDED_SECTIONS)
    return {"word": word, "definitions": definitions} if definitions else None


def process_file_batch(
    file_batch: List[Path],
    source_lang: str,
    entry_lang: Optional[str],
    num_workers: int,
) -> List[Dict]:
    """Process a batch of files in parallel and return the entries."""
    with multiprocessing.Pool(processes=num_workers) as pool:
        results = pool.starmap(
            process_file, [(f, source_lang, entry_lang) for f in file_batch]
        )

    return [entry for entry in results if entry is not None]


def extract_definitions(
    section: BeautifulSoup, excluded_sections: set
) -> Dict[str, List[str]]:
    """Extract parts of speech and definitions from language section."""
    definitions = {}

    for pos_section in section.find_all(DETAILS_TAG, {DATA_LEVEL_ATTR: "3"}):
        heading = pos_section.find(["h3", "h4"])
        if not heading:
            continue

        pos = clean_text(heading.get_text(strip=True))
        if pos in excluded_sections:
            continue

        def_items = [
            clean_text(li.get_text(" ", strip=True))
            for ol in pos_section.find_all("ol")
            for li in ol.find_all("li")
        ]

        if def_items:
            definitions[pos] = def_items

    return definitions


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove HTML tags if any remain
    text = re.sub(r"<[^>]+>", "", text)

    # Remove spaces around parentheses
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)

    # Remove spaces before punctuation (commas, periods, colons, semicolons, etc.)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    # Normalize whitespace (replace multiple spaces with a single space)
    text = re.sub(r"\s+", " ", text.strip())

    # Handle special characters and entities
    text = html.unescape(text)  # Convert HTML entities

    return text


def format_lingvo_entry(entry: dict) -> str:
    """Format a dictionary entry into Lingvo DSL format."""
    lines = [entry["word"].replace("_", " ")]
    for pos, defs in entry["definitions"].items():
        # Add part of speech with standard DSL markup
        lines.append(f"  [c]{pos}[/c]")
        # Add definitions
        for d in defs:
            lines.append(f"  {d}")
    # Add empty line to separate entries
    lines.append("")
    return "\n".join(lines)


def format_xdxf_entry(entry: dict) -> str:
    """Format a dictionary entry into XDXF format."""
    word = html.escape(entry["word"].replace("_", " "))
    lines = [f"<ar><k>{word}</k>"]

    for pos, defs in entry["definitions"].items():
        # Add part of speech
        lines.append(f"<pos>{html.escape(pos)}</pos>")
        # Add definitions with each in its own def tag
        for d in defs:
            lines.append(f"<def>{html.escape(d)}</def>")

    lines.append("</ar>")
    return "\n".join(lines)


def write_dsl_header(f, dict_name, source_lang, target_lang):
    """Write properly formatted DSL header with charset information."""
    # Escape quotes in names to avoid breaking the DSL format
    dict_name = dict_name.replace('"', '\\"')
    source_lang = source_lang.replace('"', '\\"')
    target_lang = target_lang.replace('"', '\\"')

    f.write(f'#NAME "{dict_name}"\n')
    f.write(f'#INDEX_LANGUAGE "{source_lang}"\n')
    f.write(f'#CONTENTS_LANGUAGE "{target_lang}"\n')
    f.write("#CHARSET UTF-8\n")
    f.write("\n")


def write_xdxf_header(f, dict_name, source_lang, target_lang):
    """Write properly formatted XDXF header."""
    f.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
    f.write(
        '<!DOCTYPE xdxf SYSTEM "https://raw.github.com/soshial/xdxf_makedict/master/format_standard/xdxf_strict.dtd">\n'
    )
    f.write(
        f'<xdxf lang_from="{source_lang.lower()}" lang_to="{target_lang.lower()}" format="visual">\n'
    )
    f.write(f"<full_name>{html.escape(dict_name)}</full_name>\n")
    f.write("<description>Converted from Wiktionary</description>\n")
    f.write("<abbreviations>\n")
    f.write("</abbreviations>\n")
    f.write("<xdxf_body>\n")


def write_xdxf_footer(f):
    """Write XDXF footer."""
    f.write("</xdxf_body>\n")
    f.write("</xdxf>\n")


def get_language_name(lang_code):
    """Convert language code to full language name."""
    language_names = {
        "ca": "Catalan",
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "oc": "Occitan",
        # Add more languages as needed
    }
    if not lang_code:
        return "Unknown"
    return language_names.get(lang_code.lower(), lang_code.capitalize())


def main():
    """Main processing pipeline with single-phase approach."""
    setup_logger()
    args = parse_arguments()

    # Ensure multiprocessing works correctly on all platforms
    if os.name == "nt":  # Windows specific fix
        multiprocessing.freeze_support()

    input_dir = Path(args.input)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Setup temp directory
    temp_dir = args.temp_dir if args.temp_dir else tempfile.gettempdir()
    os.makedirs(temp_dir, exist_ok=True)

    # Get all files without extensions (ignoring hidden files)
    files = [
        f
        for f in input_dir.iterdir()
        if f.is_file() and not f.suffix and not f.name.startswith(".")
    ]
    logging.info(f"Found {len(files)} files to process")

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
    files.sort(key=lambda f: f.name.lower())

    # Number of worker processes
    num_workers = min(args.jobs, len(files))
    logging.info(f"Using {num_workers} parallel processes")

    # Prepare output file
    with codecs.open(str(output_file), "w", encoding="utf-8") as f:
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
        if args.format == "lingvo":
            write_dsl_header(f, dict_name, source_lang_full, target_lang_full)
        elif args.format == "xdxf":
            write_xdxf_header(f, dict_name, source_lang_full, target_lang_full)

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
                batch, args.source_lang, args.entry_lang, num_workers
            )

            # Write entries directly to the output file
            for entry in entries:
                if args.format == "lingvo":
                    f.write(format_lingvo_entry(entry))
                elif args.format == "xdxf":
                    f.write(format_xdxf_entry(entry) + "\n")

            # Force write to disk after each batch
            f.flush()

            # Update counters
            processed_files += len(entries)
            skipped_files += len(batch) - len(entries)

            logging.info(
                f"Batch {i+1}: {len(entries)} processed, {len(batch) - len(entries)} skipped"
            )

        # Write footer if needed
        if args.format == "xdxf":
            write_xdxf_footer(f)

    logging.info(f"Total: Processed {processed_files} files successfully")
    logging.info(f"Total: Skipped {skipped_files} files (no valid content or errors)")
    logging.info(f"Successfully wrote {args.format.upper()} file to {output_file}")


if __name__ == "__main__":
    main()
