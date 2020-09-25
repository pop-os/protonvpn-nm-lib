import configparser
import os

import sentry_sdk
from lib.constants import APP_CONFIG, APP_VERSION, LOGGER_NAME
from sentry_sdk import capture_exception  # noqa
from sentry_sdk.integrations.logging import ignore_logger

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
