import keyring
import keyring.backends.kwallet
import keyring.backends.SecretService
import json

from .... import exceptions
from ....enums import KeyringEnum
from ....logger import logger
# from ... import ca


class KeyringWrapper:
    """KeyringWrapper class.

    This class wraps around the python-keyring module:
    https://github.com/jaraco/keyring
    """
    KEYRING_BACKENDS = [
        keyring.backends.kwallet.DBusKeyring,
        keyring.backends.SecretService.Keyring,
    ]

    EXCEPTIONS_DICT = {
        KeyringEnum.DEFAULT_KEYRING_SESSIONDATA: {
            "display": "IllegalSessionData",
            "exception": exceptions.IllegalSessionData,
        },
        KeyringEnum.DEFAULT_KEYRING_USERDATA: {
            "display": "IllegalUserData",
            "exception": exceptions.IllegalUserData
        }
    }

    def __init__(self, keyring_backend):
        # keyring_backend is an uninstatiated KeyringBackend object
        self.keyring_backend = keyring_backend
        self.keyring_service = KeyringEnum.DEFAULT_KEYRING_SERVICE.value
        self.set_optimum_keyring_backend()

    def set_optimum_keyring_backend(self):
        """Sets the optimum keyring backend to be used.

        Default backend: SecretService
        """
        logger.info("Setting optimum backend")
        optimum_backend = None

        for backend in keyring.backend.get_all_keyring():
            keyring_backend = self.keyring_backend(backend)
            keyring_backend.generate_keyring_backend()

            if (
                keyring_backend.priority != None
                and (
                    optimum_backend is None
                    or (
                        keyring_backend.priority
                        > optimum_backend.priority
                    )
                )
            ):
                optimum_backend = keyring_backend

        if optimum_backend is None:
            optimum_backend = self.keyring_backend.get_default_keyring()

        logger.info("Keyring backend: {}".format(optimum_backend))
        keyring.set_keyring(optimum_backend.object)

    def get_entry(self, keyring_username):
        """Get keyring entry.

        Args:
            keyring_username (string): the keyring username
            keyring_service (string): the keyring servicename

        Returns:
            dict
        """

        try:
            stored_data = keyring.get_password(
                self.keyring_service,
                keyring_username
            )
        except (keyring.errors.InitError, keyring.errors.KeyringLocked) as e:
            logger.exception("[!] AccessKeyringError: {}".format(e))
            raise exceptions.AccessKeyringError(
                "Could not fetch from keychain: {}".format(e)
            )
        except Exception as e:
            logger.exception("[!] KeyringError: {}".format(e))
            # capture_exception(e)
            raise exceptions.KeyringError(e)

        try:
            return self.convert_from_json_to_dict_format(stored_data)
        except json.decoder.JSONDecodeError as e:
            logger.exception("[!] JSONDataEmptyError: {}".format(e))
            raise exceptions.JSONDataEmptyError(e)
        except TypeError as e:
            logger.exception("[!] JSONDataNoneError: {}".format(e))
            raise exceptions.JSONDataNoneError(e)
        except Exception as e:
            logger.exception("[!] JSONDataError: {}".format(e))
            raise exceptions.JSONDataError(e)

    def delete_entry(self, keyring_username):
        """Delete keyring entry.

        Args:
            keyring_username (string): the keyring username
            keyring_service (string): the keyring servicename
        """
        try:
            keyring.delete_password(
                self.keyring_service,
                keyring_username,
            )
        except (
                keyring.errors.InitError,
                keyring.errors.KeyringLocked
        ) as e:
            logger.exception("[!] AccessKeyringError: {}".format(e))
            raise exceptions.AccessKeyringError(
                "Could not access keychain: {}".format(e)
            )
        except keyring.errors.PasswordDeleteError as e:
            logger.exception("[!] KeyringDataNotFound: {}".format(e))
            raise exceptions.KeyringDataNotFound(e)
        except Exception as e:
            logger.exception("[!] Unknown exception: {}".format(e))
            # capture_exception(e)

    def add_entry(self, keyring_username, data):
        """Add data entry to keyring.

        Args:
            data (dict(json)): data to be stored
            keyring_username (string): the keyring username
            keyring_service (string): the keyring servicename
        """
        json_data = self.convert_from_dict_to_json_format(data)
        try:
            keyring.set_password(
                self.keyring_service,
                keyring_username,
                json_data
            )
        except (
            keyring.errors.InitError,
            keyring.errors.KeyringLocked,
            keyring.errors.PasswordSetError
        ) as e:
            logger.exception("[!] AccessKeyringError: {}".format(e))
            raise exceptions.AccessKeyringError(
                "Could not access keychain: {}".format(e)
            )
        except Exception as e:
            logger.error("[!] Exception: {}".format(e))
            # capture_exception(e)

    def convert_from_dict_to_json_format(self, dict_data):
        """Convert provided dict object to json string.

        Args:
            dict

        Returns:
            json string
        """
        return json.dumps(dict_data)

    def convert_from_json_to_dict_format(self, json_string):
        """Convert provided json string to python dict.

        Args:
            json_string

        Returns:
            dict
        """
        return json.loads(json_string)
