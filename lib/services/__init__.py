import sentry_sdk
from sentry_sdk import capture_exception  # noqa
from sentry_sdk.integrations.logging import ignore_logger

from lib.constants import APP_VERSION, LOGGER_NAME

ignore_logger(LOGGER_NAME)
sentry_sdk.init(
    dsn="https://f9d7d18c83374b7a901f20036f8583e1@sentry.protontech.ch/62",
    release=APP_VERSION,
)
