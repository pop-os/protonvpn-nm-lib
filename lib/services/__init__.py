import sentry_sdk
from sentry_sdk import capture_exception  # noqa
from sentry_sdk.integrations.logging import ignore_logger

from lib.constants import APP_VERSION, LOGGER_NAME, APP_CONFIG
import configparser

ignore_logger(LOGGER_NAME)
config = configparser.ConfigParser()
config.read(APP_CONFIG)

sentry_sdk.init(
    dsn=config["sentry"]["dsn"],
    release=APP_VERSION,
    ignore_errors=["KeyboardInterrupt"]
)
