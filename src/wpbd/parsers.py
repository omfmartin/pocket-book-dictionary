"""
HTML parsing and language section detection for Wiktionary pages.
"""

import logging
from pathlib import Path
from typing import Optional

from lxml import etree, html as lxml_html

from .config import DETAILS_TAG, LANGUAGE_NAMES
from .utils.text import get_text_content, copy_element


# Create custom lxml HTML parser with faster settings
PARSER = lxml_html.HTMLParser(
    remove_blank_text=True, remove_comments=True, remove_pis=True, encoding="utf-8"
)


def parse_html_file(file_path: Path) -> Optional[etree._Element]:
    """
    Parse an HTML file into an lxml tree.

    Args:
        file_path: Path to the HTML file

    Returns:
        lxml HTML tree or None if there was an error
    """
    try:
        return lxml_html.parse(str(file_path), parser=PARSER).getroot()
    except (
        IsADirectoryError,
        UnicodeDecodeError,
        FileNotFoundError,
        PermissionError,
        etree.XMLSyntaxError,
    ) as e:
        logging.debug(f"Error parsing {file_path}: {str(e)}")
        return None


def get_parent_details(element: etree._Element) -> Optional[etree._Element]:
    """
    Get the parent 'details' element for a given element.

    Args:
        element: lxml Element to find details parent for

    Returns:
        Parent details element or None
    """
    current = element
    while current is not None:
        if current.tag == DETAILS_TAG:
            return current
        current = current.getparent()
    return None


def find_language_section(
    tree: etree._Element, lang_code: str
) -> Optional[etree._Element]:
    """
    Find the language section in a Wiktionary page using multiple detection methods.
    Works across different Wiktionary language editions by trying several patterns.

    Args:
        tree: lxml HTML tree
        lang_code: Language code to find (e.g., 'en', 'ru', 'ca', 'oc')

    Returns:
        lxml Element containing the language section or None if not found
    """
    # Method 1: Look for span with id matching language code (Catalan style)
    lang_spans = tree.xpath(f"//span[@id='{lang_code}']")
    if len(lang_spans) > 0:
        parent_details = get_parent_details(lang_spans[0])
        if parent_details is not None:
            return parent_details

    # Method 2: Look for span with id matching capitalized language code (variant)
    lang_spans = tree.xpath(f"//span[@id='{lang_code.capitalize()}']")
    if len(lang_spans) > 0:
        parent_details = get_parent_details(lang_spans[0])
        if parent_details is not None:
            return parent_details

    # Method 3: Look for h2 with id matching language name (English/Russian style)
    if lang_code in LANGUAGE_NAMES:
        lang_name = LANGUAGE_NAMES[lang_code]
        # Try both exact match and partial match
        heading_elems = tree.xpath(
            f"//*[self::h2 or self::h3][@id='{lang_name}' or contains(@id, '{lang_name}')]"
        )
        for heading_elem in heading_elems:
            parent_details = get_parent_details(heading_elem)
            if parent_details is not None:
                return parent_details

    # Method 4: Look for any h2 containing the language code or name
    heading_elems = tree.xpath("//h2")
    for heading_elem in heading_elems:
        heading_text = get_text_content(heading_elem).lower()
        if lang_code.lower() in heading_text or (
            lang_code in LANGUAGE_NAMES
            and LANGUAGE_NAMES[lang_code].lower() in heading_text
        ):
            parent_details = get_parent_details(heading_elem)
            if parent_details is not None:
                return parent_details

    # Method 5: Look for a span with mw-headline that contains the language name
    if lang_code in LANGUAGE_NAMES:
        lang_name = LANGUAGE_NAMES[lang_code]
        span_elems = tree.xpath("//span[contains(@class, 'mw-headline')]")
        for span_elem in span_elems:
            if lang_name.lower() in get_text_content(span_elem).lower():
                parent_details = get_parent_details(span_elem)
                if parent_details is not None:
                    return parent_details

    # Method 6: Special case for Wiktionaries with different structure
    title_section = tree.xpath("//div[@id='title_0']")
    if len(title_section) > 0:
        parent_div = title_section[0].getparent()
        if parent_div is not None:
            heading_elems = parent_div.xpath(".//*[self::h2 or self::h3]")
            for heading_elem in heading_elems:
                heading_text = get_text_content(heading_elem).lower()
                if lang_code.lower() in heading_text or (
                    lang_code in LANGUAGE_NAMES
                    and LANGUAGE_NAMES[lang_code].lower() in heading_text
                ):
                    parent_details = get_parent_details(heading_elem)
                    if parent_details is not None:
                        return parent_details

    # Method 7: Check if the page itself is for the target language
    # This is common in monolingual dictionaries
    page_language_markers = tree.xpath(
        f"//*[contains(@class, '{lang_code}') or contains(@lang, '{lang_code}')]"
    )
    if len(page_language_markers) > 0:
        # Return the main content element
        content_div = tree.xpath("//div[contains(@class, 'mw-parser-output')]")
        if len(content_div) > 0:
            return content_div[0]

    # Fallback: try to find any details element that might contain our language
    detail_elements = tree.xpath(f"//{DETAILS_TAG}")
    for detail in detail_elements:
        heading_elements = detail.xpath(".//*[self::h2 or self::h3]")
        if len(heading_elements) > 0 and (
            lang_code.lower() in get_text_content(heading_elements[0]).lower()
            or (
                lang_code in LANGUAGE_NAMES
                and LANGUAGE_NAMES[lang_code].lower()
                in get_text_content(heading_elements[0]).lower()
            )
        ):
            return detail

    return None


def extract_virtual_section(heading: etree._Element) -> etree._Element:
    """
    Create a virtual section from a heading for Wiktionaries without detail elements.

    Args:
        heading: lxml Element (h2, h3, h4, etc.)

    Returns:
        lxml Element containing the heading and its content
    """

    # Create a new div element
    virtual_section = etree.Element("div")

    # Clone the heading
    virtual_section.append(copy_element(heading))

    # Get content until next heading of same or higher level
    current = heading.getnext()
    while current is not None:
        if current.tag in ["h2", "h3", "h4"] and current.tag <= heading.tag:
            break
        if current.tag:  # Only append actual elements, not text nodes
            virtual_section.append(copy_element(current))
        current = current.getnext()

    return virtual_section
