"""
Text processing utilities for cleaning and normalizing text.
"""

import re
import html
from lxml import etree

# Precompile regex patterns for text cleaning
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
PAREN_SPACE_START_PATTERN = re.compile(r"\(\s+")
PAREN_SPACE_END_PATTERN = re.compile(r"\s+\)")
SPACE_PUNCT_PATTERN = re.compile(r"\s+([,.;:!?])")
MULTI_SPACE_PATTERN = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """
    Clean and normalize text content using precompiled regex patterns.

    Args:
        text: Text to clean

    Returns:
        Cleaned and normalized text
    """
    # Skip processing for empty text
    if not text:
        return ""

    # First strip whitespace to handle the simple case efficiently
    text = text.strip()

    # Optimization: Skip regex processing if no HTML tags are present
    if "<" in text:
        # Remove HTML tags
        text = HTML_TAG_PATTERN.sub("", text)

    # Remove spaces around parentheses
    text = PAREN_SPACE_START_PATTERN.sub("(", text)
    text = PAREN_SPACE_END_PATTERN.sub(")", text)

    # Remove spaces before punctuation
    text = SPACE_PUNCT_PATTERN.sub(r"\1", text)

    # Normalize whitespace
    text = MULTI_SPACE_PATTERN.sub(" ", text)

    # Handle special characters and entities
    text = html.unescape(text)

    return text


def get_text_content(element: etree._Element) -> str:
    """
    Get the text content of an element and its descendants.

    Args:
        element: lxml Element

    Returns:
        Concatenated text content
    """
    return " ".join(element.xpath(".//text()")).strip()


def copy_element(element: etree._Element) -> etree._Element:
    """
    Create a deep copy of an lxml element.

    Args:
        element: lxml Element to copy

    Returns:
        Copy of the element
    """
    return etree.fromstring(etree.tostring(element))
