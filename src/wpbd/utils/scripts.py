"""
Utilities for script detection and filtering.
"""

from pathlib import Path
from typing import List

from ..config import SCRIPT_RANGES


def is_in_script(char: str, script: str) -> bool:
    """
    Check if a character belongs to a specific script.

    Args:
        char: Character to check
        script: Script name (e.g., 'latin', 'cyrillic')

    Returns:
        True if the character belongs to the script, False otherwise
    """
    if script not in SCRIPT_RANGES:
        return False

    code_point = ord(char)

    for start, end in SCRIPT_RANGES[script]:
        if start <= code_point <= end:
            return True

    return False


def get_word_script(word: str) -> str:
    """
    Determine the dominant script of a word.

    Args:
        word: Word to analyze

    Returns:
        Name of the dominant script or "unknown"
    """
    # Remove any file extension if present
    word = Path(word).stem

    # Count characters by script
    script_counts = {script: 0 for script in SCRIPT_RANGES.keys()}

    for char in word:
        if not char.isalnum():
            continue  # Skip non-alphanumeric characters

        for script in SCRIPT_RANGES.keys():
            if is_in_script(char, script):
                script_counts[script] += 1
                break

    # Find the dominant script
    if not script_counts:
        return "unknown"

    dominant_script = max(script_counts.items(), key=lambda x: x[1])

    # Return the script name if there are any characters in that script
    if dominant_script[1] > 0:
        return dominant_script[0]

    return "unknown"


def is_file_in_scripts(filename: str, scripts: List[str]) -> bool:
    """
    Check if a file should be processed based on its script.

    Args:
        filename: Name of the file
        scripts: List of scripts to include

    Returns:
        True if the file should be processed, False otherwise
    """
    # If all scripts are requested, include everything
    if "all" in scripts:
        return True

    # Get the dominant script of the filename
    word = filename

    # Optimization: Quick check of first character for most cases
    if word and any(is_in_script(word[0], script) for script in scripts):
        return True

    # Fallback to full word analysis for edge cases
    word_script = get_word_script(word)

    return word_script in scripts
