import re

import keyring
import keyring.backends.kwallet
import keyring.backends.SecretService

from ....logger import logger
# from . import capture_exception


class KeyringBackend:
    """KeyringBackend class.

    Represents a keyring backend object (keyring.backends)
    """
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

    def generate_keyring_backend(self):
        """Generates the backend objects.

        Given that the specified back-end exists,
        it will generate the backend by setting
        the all object properties.
        """
        if (
            self.check_if_backend_exist()
            and self.get_backend_name() in self.SUPPORTED_BACKENDS
        ):
            self.set_backend_properties()

    def check_if_backend_exist(self):
        """Checks if backend exists.

        It does so by attempting to extract the backend name.
        Check self.get_backend_name()

        Returns:
            bool
        """
        try:
            self.get_backend_name()
        except Exception as e:
            logger.exception("[!] Unknown exception: {}".format(e))
            # capture_exception(e)
            return False

        return True

    def set_backend_properties(self):
        """Set object properties."""
        self.object = self.__keyring_backend
        self.name = self.get_backend_name()
        self.priority = self.get_backend_priority()

    def get_backend_path_string(self):
        """Gets a backends path.

        Returns:
            str
        """
        return self.__keyring_backend_in_string_type.split()[0]

    def get_backend_name(self):
        """Gets a backends name, by splitting the name.

        Returns:
            str
        """
        backend_path_string = self.get_backend_path_string()
        return backend_path_string.split(".")[2]

    def get_backend_priority(self):
        """Get backend priority.

        The backend priority is searched from within a backend
        string type via regex.

        Returns:
            float
        """
        backend_priority = re.search(
            r"\(\w+:\W(\d+\.?\d*)\)", self.__keyring_backend_in_string_type
        )
        return float(backend_priority.group(1))

    @staticmethod
    def get_default_keyring():
        """Get default keyring.

        This method should be used only if no other backends were
        successfully found.

        Returns:
            Backend
        """
        default_keyring_backend = KeyringBackend(
            keyring.backends.SecretService.Keyring()
        )
        default_keyring_backend.generate_keyring_backend()
        return default_keyring_backend
