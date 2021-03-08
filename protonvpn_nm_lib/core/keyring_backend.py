import re

import keyring
import keyring.backends.kwallet
import keyring.backends.SecretService

from ..logger import logger
from . import capture_exception


class KeyringBackend:
    SUPPORTED_BACKENDS = ["kwallet", "SecretService"]

    def __init__(
        self,
        keyring_backend=keyring.backends.SecretService.Keyring()
    ):
        self.__keyring_backend = keyring_backend
        self.__keyring_backend_in_string_type = str(self.__keyring_backend)

        self.object = None
        self.name = None
        self.priority = None

    def generate_backend_object(self):
        if (
            self.backend_exist()
            and self.get_backend_name() in self.SUPPORTED_BACKENDS
        ):
            self.set_properties()

    def backend_exist(self):
        try:
            self.get_backend_name()
        except Exception as e:
            logger.exception("[!] Unknown exception: {}".format(e))
            capture_exception(e)
            return False

        return True

    def set_properties(self):
        self.object = self.__keyring_backend
        self.name = self.get_backend_name()
        self.priority = self.get_backend_priority()

    def get_backend_path_string(self):
        return self.__keyring_backend_in_string_type.split()[0]

    def get_backend_name(self):
        backend_path_string = self.get_backend_path_string()
        return backend_path_string.split(".")[2]

    def get_backend_priority(self):
        backend_priority = re.search(
            r"\(\w+:\W(\d+\.?\d*)\)", self.__keyring_backend_in_string_type
        )
        return float(backend_priority.group(1))

    @staticmethod
    def get_default_keyring():
        default_keyring_backend = KeyringBackend(
            keyring.backends.SecretService.Keyring()
        )
        default_keyring_backend.generate_backend_object()
        return default_keyring_backend
