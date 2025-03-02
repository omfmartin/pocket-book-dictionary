"""
Logging utilities for the Wiktionary converter.
"""

import logging


def setup_logger(debug: bool = False):
    """
    Configure logging for the script.

    Args:
        debug: Enable debug logging level if True
    """
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
