import re
import argparse
import html
from typing import Optional, Dict, List
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
import logging
import codecs  # Import for explicit encoding handling


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
        help="Source language code (e.g., ca for Catalan)",
    )
    parser.add_argument(
        "-t",
        "--target-lang",
        help="Target language code for translations",
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
    f.write(f'#NAME "{dict_name}"\n')
    f.write(f'#INDEX_LANGUAGE "{source_lang}"\n')
    f.write(f'#CONTENTS_LANGUAGE "{target_lang if target_lang else source_lang}"\n')
    f.write("#CHARSET UTF-8\n")
    f.write("\n")


def write_xdxf_header(f, dict_name, source_lang, target_lang):
    """Write properly formatted XDXF header."""
    f.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
    f.write(
        '<!DOCTYPE xdxf SYSTEM "https://raw.github.com/soshial/xdxf_makedict/master/format_standard/xdxf_strict.dtd">\n'
    )
    f.write(
        f'<xdxf lang_from="{source_lang.lower()}" lang_to="{(target_lang if target_lang else source_lang).lower()}" format="visual">\n'
    )
    f.write(f"<full_name>{dict_name}</full_name>\n")
    f.write("<description>Converted from Wiktionary</description>\n")
    f.write("<abbreviations>\n")
    f.write("</abbreviations>\n")
    f.write("<xdxf_body>\n")


def write_xdxf_footer(f):
    """Write XDXF footer."""
    f.write("</xdxf_body>\n")
    f.write("</xdxf>\n")


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
        with codecs.open(str(output_file), "w", encoding="utf-8") as f:
            # Get full language names
            source_lang_full = get_language_name(args.source_lang)
            target_lang_full = (
                get_language_name(args.target_lang)
                if args.target_lang
                else source_lang_full
            )
            dict_name = f"{args.name} ({source_lang_full}-{target_lang_full})"

            # Sort entries alphabetically
            entries.sort(key=lambda x: x["word"].lower())

            # Write appropriate header and format entries based on the selected format
            if args.format == "lingvo":
                # Write Lingvo DSL header
                write_dsl_header(f, dict_name, source_lang_full, target_lang_full)

                # Write entries in Lingvo format
                for entry in entries:
                    f.write(format_lingvo_entry(entry))

                logging.info(f"Successfully wrote Lingvo DSL file to {output_file}")

            elif args.format == "xdxf":
                # Write XDXF header
                write_xdxf_header(f, dict_name, source_lang_full, target_lang_full)

                # Write entries in XDXF format
                for entry in entries:
                    f.write(format_xdxf_entry(entry) + "\n")

                # Write XDXF footer
                write_xdxf_footer(f)

                logging.info(f"Successfully wrote XDXF file to {output_file}")

    except IOError as e:
        logging.error(f"Failed to write output file: {str(e)}")


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
    return language_names.get(lang_code, lang_code.capitalize())


if __name__ == "__main__":
    main()
