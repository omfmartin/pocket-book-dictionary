"""
Output formatting for different dictionary formats.
"""

import html
import codecs
from typing import Dict, List, TextIO, Union


def format_lingvo_entry(entry: Dict[str, Union[str, Dict[str, List[str]]]]) -> str:
    """
    Format a dictionary entry into Lingvo DSL format.

    Args:
        entry: Dictionary entry with 'word' and 'definitions'

    Returns:
        Formatted DSL entry
    """
    word = entry["word"].replace("_", " ")
    lines = [word]

    for pos, defs in entry["definitions"].items():
        # Add part of speech with standard DSL markup
        lines.append(f"  [c]{pos}[/c]")
        # Add definitions
        for d in defs:
            lines.append(f"  {d}")

    # Add empty line to separate entries
    lines.append("")
    return "\n".join(lines)


def format_xdxf_entry(entry: Dict[str, Union[str, Dict[str, List[str]]]]) -> str:
    """
    Format a dictionary entry into XDXF format.

    Args:
        entry: Dictionary entry with 'word' and 'definitions'

    Returns:
        Formatted XDXF entry
    """
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


def write_dsl_header(
    f: TextIO, dict_name: str, source_lang: str, target_lang: str
) -> None:
    """
    Write properly formatted DSL header with charset information.

    Args:
        f: File object to write to
        dict_name: Name of the dictionary
        source_lang: Source language name
        target_lang: Target language name
    """
    # Escape quotes in names to avoid breaking the DSL format
    dict_name = dict_name.replace('"', '\\"')
    source_lang = source_lang.replace('"', '\\"')
    target_lang = target_lang.replace('"', '\\"')

    f.write(f'#NAME "{dict_name}"\n')
    f.write(f'#INDEX_LANGUAGE "{source_lang}"\n')
    f.write(f'#CONTENTS_LANGUAGE "{target_lang}"\n')
    f.write("#CHARSET UTF-8\n")
    f.write("\n")


def write_xdxf_header(
    f: TextIO, dict_name: str, source_lang: str, target_lang: str
) -> None:
    """
    Write properly formatted XDXF header.

    Args:
        f: File object to write to
        dict_name: Name of the dictionary
        source_lang: Source language name
        target_lang: Target language name
    """
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


def write_xdxf_footer(f: TextIO) -> None:
    """
    Write XDXF footer.

    Args:
        f: File object to write to
    """
    f.write("</xdxf_body>\n")
    f.write("</xdxf>\n")


def open_output_file(file_path: str) -> TextIO:
    """
    Open an output file with proper encoding.

    Args:
        file_path: Path to the output file

    Returns:
        File object
    """
    return codecs.open(file_path, "w", encoding="utf-8")


def format_entry(entry: Dict, output_format: str) -> str:
    """
    Format an entry according to the specified output format.

    Args:
        entry: Dictionary entry
        output_format: Format type ('lingvo' or 'xdxf')

    Returns:
        Formatted entry as string
    """
    if output_format == "lingvo":
        return format_lingvo_entry(entry)
    elif output_format == "xdxf":
        return format_xdxf_entry(entry) + "\n"
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def write_header(
    f: TextIO, output_format: str, dict_name: str, source_lang: str, target_lang: str
) -> None:
    """
    Write the appropriate header for the specified output format.

    Args:
        f: File object to write to
        output_format: Format type ('lingvo' or 'xdxf')
        dict_name: Name of the dictionary
        source_lang: Source language name
        target_lang: Target language name
    """
    if output_format == "lingvo":
        write_dsl_header(f, dict_name, source_lang, target_lang)
    elif output_format == "xdxf":
        write_xdxf_header(f, dict_name, source_lang, target_lang)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def write_footer(f: TextIO, output_format: str) -> None:
    """
    Write the appropriate footer for the specified output format.

    Args:
        f: File object to write to
        output_format: Format type ('lingvo' or 'xdxf')
    """
    if output_format == "xdxf":
        write_xdxf_footer(f)
