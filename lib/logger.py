import os
import logging
from logging.handlers import RotatingFileHandler

from lib.constants import PROTON_XDG_CACHE_HOME_LOGS, LOGGER_NAME


def get_logger():
    """Create the logger."""
    FORMATTER = logging.Formatter(
        "%(asctime)s — %(filename)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s" # noqa
    )

    if not os.path.isdir(PROTON_XDG_CACHE_HOME_LOGS):
        os.makedirs(PROTON_XDG_CACHE_HOME_LOGS)

    LOGFILE = os.path.join(PROTON_XDG_CACHE_HOME_LOGS, "protonvpn.log")

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(FORMATTER)

    # Only log to console when using PROTONVPN_DEBUG=1
    if os.environ.get("PROTONVPN_DEBUG", 0) == "1":
        logger.addHandler(console_handler)

    # Starts a new file at 3MB size limit
    file_handler = RotatingFileHandler(
        LOGFILE, maxBytes=3145728, backupCount=3
    )
    file_handler.setFormatter(FORMATTER)
    logger.addHandler(file_handler)

    return logger


logger = get_logger()