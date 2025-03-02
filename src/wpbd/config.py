"""
Constants and configuration for the Wiktionary converter.
"""

# HTML parsing constants
DETAILS_TAG = "details"
DATA_LEVEL_ATTR = "data-level"

# Sections to exclude from extraction
DEFAULT_EXCLUDED_SECTIONS = {
    "Traduccions",
    "Miscel·lània",
    "Vegeu també",
    "Translations",
    "Miscellany",
    "See also",
    "References",
    "Referéncias",
    "Traduccions_2",
    "Traduccions_3",
}

# Script definitions using Unicode ranges
SCRIPT_RANGES = {
    "latin": [
        (0x0041, 0x005A),  # Latin uppercase
        (0x0061, 0x007A),  # Latin lowercase
        (0x00C0, 0x00FF),  # Latin-1 Supplement
        (0x0100, 0x017F),  # Latin Extended-A
        (0x0180, 0x024F),  # Latin Extended-B
    ],
    "cyrillic": [
        (0x0400, 0x04FF),  # Cyrillic
        (0x0500, 0x052F),  # Cyrillic Supplement
    ],
    "greek": [
        (0x0370, 0x03FF),  # Greek and Coptic
    ],
    "chinese": [
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
    ],
    "japanese": [
        (0x3040, 0x309F),  # Hiragana
        (0x30A0, 0x30FF),  # Katakana
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs (shared with Chinese)
    ],
    "korean": [
        (0xAC00, 0xD7AF),  # Hangul Syllables
        (0x1100, 0x11FF),  # Hangul Jamo
    ],
    "arabic": [
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
    ],
    "hebrew": [
        (0x0590, 0x05FF),  # Hebrew
    ],
    "devanagari": [
        (0x0900, 0x097F),  # Devanagari (Hindi, Sanskrit, etc.)
    ],
    "thai": [
        (0x0E00, 0x0E7F),  # Thai
    ],
}

# Mapping of language codes to their full names
LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Russian",
    "ca": "Català",
    "oc": "Occitan",
    "fr": "Français",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "uk": "Ukrainian",
    "be": "Belarusian",
    "nl": "Dutch",
    "pl": "Polish",
    "cs": "Czech",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "hu": "Hungarian",
    "el": "Greek",
    "tr": "Turkish",
    "ar": "Arabic",
    "he": "Hebrew",
    "hi": "Hindi",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
}
