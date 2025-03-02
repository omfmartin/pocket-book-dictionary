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


def log_timing(name: str, time_taken: float, debug: bool = False):
    """
    Log timing information for performance profiling.

    Args:
        name: Name of the operation
        time_taken: Time taken in seconds
        debug: Whether to log at debug level (otherwise info)
    """
    message = f"{name} took {time_taken:.4f}s"
    if debug:
        logging.debug(message)
    else:
        logging.info(message)
