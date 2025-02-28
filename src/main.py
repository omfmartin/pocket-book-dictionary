import re
import argparse
from typing import Optional, Dict, List
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging


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
        description="Convert Wiktionary HTML files to Lingvo DSL format"
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Input directory containing files"
    )
    parser.add_argument("-o", "--output", required=True, help="Output DSL file path")
    parser.add_argument(
        "-s",
        "--source-lang",
        required=True,
        help="Source language code (e.g., ca for Catalan)",
    )
    parser.add_argument(
        "-t",
        "--target-lang",
        help="Target language code for translations",
    )
    return parser.parse_args()


def process_file(file_path: Path, lang_code: str) -> Optional[dict]:
    """Process a single file and extract definitions for the specified language."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
    except (IsADirectoryError, UnicodeDecodeError) as e:
        logging.warning(f"Skipping {file_path}: {str(e)}")
        return None

    word = file_path.name  # Use the full filename as the word
    lang_section = extract_language_section(soup, lang_code)

    if not lang_section:
        return None

    definitions = extract_definitions(lang_section)
    return {"word": word, "definitions": definitions} if definitions else None


def extract_language_section(
    soup: BeautifulSoup, lang_code: str
) -> Optional[BeautifulSoup]:
    """Extract the language section from parsed HTML using language code."""
    lang_span = soup.find("span", id=lang_code)
    return lang_span.find_parent("details") if lang_span else None


def extract_definitions(section: BeautifulSoup) -> Dict[str, List[str]]:
    """Extract parts of speech and definitions from language section."""
    definitions = {}
    excluded_sections = {
        "Traduccions",
        "Miscel·lània",
        "Vegeu també",
        "Translations",
        "Miscellany",
        "See also",
    }

    for pos_section in section.find_all("details", {"data-level": "3"}):
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
    # Remove spaces around parentheses
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)

    # Remove spaces before punctuation (commas, periods, colons, semicolons, etc.)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    # Normalize whitespace (replace multiple spaces with a single space)
    text = re.sub(r"\s+", " ", text.strip())

    return text


def format_lingvo_entry(entry: dict) -> str:
    """Format a dictionary entry into Lingvo DSL format."""
    lines = [entry["word"]]
    for pos, defs in entry["definitions"].items():
        # Add part of speech with markup
        lines.append(f"  [m1]{pos}[/m]")
        # Add definitions
        for d in defs:
            lines.append(f"  {d}")
    # Add empty line to separate entries
    lines.append("")
    return "\n".join(lines)


def main():
    """Main processing pipeline."""
    setup_logger()
    args = parse_arguments()

    input_dir = Path(args.input)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    processed_files = 0
    skipped_files = 0

    # Get all files without extensions
    files = [f for f in input_dir.iterdir() if f.is_file() and not f.suffix]
    logging.info(f"Found {len(files)} files to process")

    for file_path in tqdm(files, desc="Processing files"):
        entry = process_file(file_path, args.source_lang)
        if entry:
            entries.append(entry)
            processed_files += 1
        else:
            skipped_files += 1

    logging.info(f"Processed {processed_files} files successfully")
    logging.info(f"Skipped {skipped_files} files (no valid content or errors)")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            # Write DSL header
            f.write(f"# Language: {args.source_lang}\n")
            f.write(f"# Target Language: {args.target_lang}\n\n")

            # Write entries
            for entry in entries:
                f.write(format_lingvo_entry(entry) + "\n")
        logging.info(f"Successfully wrote Lingvo DSL file to {output_file}")
    except IOError as e:
        logging.error(f"Failed to write output file: {str(e)}")


if __name__ == "__main__":
    main()
