"""
Definition extraction logic for Wiktionary pages.
"""

import logging
from typing import Dict, List, Set

from lxml import etree

from .config import DETAILS_TAG, DATA_LEVEL_ATTR
from .utils.text import clean_text, get_text_content
from .parsers import extract_virtual_section


def extract_definitions(
    section: etree._Element, excluded_sections: Set[str], debug: bool = False
) -> Dict[str, List[str]]:
    """
    Extract parts of speech and definitions from language section with early filtering.
    Enhanced to handle different Wiktionary formats.

    Args:
        section: lxml Element section to extract from
        excluded_sections: Set of section names to exclude
        debug: Enable debug logging

    Returns:
        Dictionary of part-of-speech -> definitions
    """
    definitions = {}

    # Early check: If there are no ordered lists, there are probably no definitions
    ol_elements = section.xpath(".//ol")
    if len(ol_elements) == 0:
        if debug:
            logging.debug("No ordered lists found in section, skipping")
        return definitions

    # Handle multiple potential part-of-speech section levels (2, 3, 4)
    pos_sections = []
    pos_sections.extend(
        section.xpath(f".//{DETAILS_TAG}[@{DATA_LEVEL_ATTR}='3']")
    )  # Russian, Catalan
    pos_sections.extend(
        section.xpath(f".//{DETAILS_TAG}[@{DATA_LEVEL_ATTR}='2']")
    )  # Occitan
    pos_sections.extend(
        section.xpath(f".//{DETAILS_TAG}[@{DATA_LEVEL_ATTR}='4']")
    )  # Other variants

    if debug:
        logging.debug(f"Found {len(pos_sections)} potential part-of-speech sections")

    # If no details found, try to find h3/h4 elements directly (English Wiktionary)
    if len(pos_sections) == 0:
        headings = section.xpath(".//h3 | .//h4")
        for heading in headings:
            # For each heading, consider the content until the next heading as a section
            pos_section = extract_virtual_section(heading)
            if pos_section is not None:
                pos_sections.append(pos_section)
                if debug:
                    logging.debug(
                        f"Created virtual section for: {get_text_content(heading)}"
                    )

    for pos_section in pos_sections:
        heading_elements = pos_section.xpath(".//*[self::h2 or self::h3 or self::h4]")
        if len(heading_elements) == 0:
            continue

        heading = heading_elements[0]
        pos = clean_text(get_text_content(heading))

        # Early filtering: Skip excluded sections immediately
        if any(excluded.lower() in pos.lower() for excluded in excluded_sections):
            if debug:
                logging.debug(f"Skipping excluded section: {pos}")
            continue

        # Early check: Skip sections without ordered lists (no definitions)
        ol_lists = pos_section.xpath(".//ol")
        if len(ol_lists) == 0:
            if debug:
                logging.debug(f"No definition lists found in section: {pos}")
            continue

        # Extract definition items
        def_items = []
        for ol in ol_lists:
            li_items = ol.xpath(".//li")
            # Only process if there are list items
            if len(li_items) > 0:
                def_items.extend([clean_text(get_text_content(li)) for li in li_items])

        # Only add non-empty definitions
        if len(def_items) > 0:
            definitions[pos] = def_items
            if debug:
                logging.debug(f"Added {len(def_items)} definitions for section: {pos}")

    return definitions
