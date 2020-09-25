import sentry_sdk
from sentry_sdk import capture_exception  # noqa
from sentry_sdk.integrations.logging import ignore_logger
import os
from lib.constants import APP_VERSION, LOGGER_NAME, APP_CONFIG
import configparser

ignore_logger(LOGGER_NAME)
config = configparser.ConfigParser()
config.read(APP_CONFIG)

env = "development" if os.environ.get("protonvpn_env") else "production"

sentry_sdk.init(
    dsn=config["sentry"]["dsn"],
    ignore_errors=["KeyboardInterrupt"],
    release="protonvpn-nm-core@" + APP_VERSION,
    environment=env
)
