import json
from ...logger import logger
from ...enums import KeyringEnum
from ... import exceptions
from ._base import KeyringBackend


class KeyringBackendLinux(KeyringBackend):
    def __init__(self, keyring_backend):
        self.__keyring_backend = keyring_backend
        self.__keyring_service = KeyringEnum.DEFAULT_KEYRING_SERVICE.value

    def __getitem__(self, key):
        import keyring

        self._ensure_key_is_valid(key)

        try:
            stored_data = self.__keyring_backend.get_password(
                self.__keyring_service,
                key
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

        # Since we're borrowing the dict interface,
        # be consistent and throw a KeyError if it doesn't exist
        if stored_data is None:
            raise KeyError(key)

        try:
            return json.loads(stored_data)
        except json.decoder.JSONDecodeError as e:
            logger.exception("[!] JSONDataEmptyError: {}".format(e))
            raise exceptions.JSONDataEmptyError(e)
        except TypeError as e:
            logger.exception("[!] JSONDataNoneError: {}".format(e))
            raise exceptions.JSONDataNoneError(e)
        except Exception as e:
            logger.exception("[!] JSONDataError: {}".format(e))
            raise exceptions.JSONDataError(e)

    def __delitem__(self, key):
        import keyring

        self._ensure_key_is_valid(key)

        try:
            self.__keyring_backend.delete_password(self.__keyring_service, key)
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
            raise KeyError(key)
        except Exception as e:
            logger.exception("[!] Unknown exception: {}".format(e))
            # We shouldn't ignore exceptions!
            raise Exception(e)
            # capture_exception(e)

    def __setitem__(self, key, value):
        """Add data entry to keyring.

        Args:
            data (dict(json)): data to be stored
            keyring_username (string): the keyring username
            keyring_service (string): the keyring servicename
        """

        import keyring

        self._ensure_key_is_valid(key)
        self._ensure_value_is_valid(value)

        json_data = json.dumps(value)
        try:
            self.__keyring_backend.set_password(
                self.__keyring_service,
                key,
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


class KeyringBackendLinuxKwallet(KeyringBackendLinux):
    pass


class KeyringBackendLinuxSecretService(KeyringBackendLinux):
    priority = 5

    def __init__(self):
        from keyring.backends import SecretService
        super().__init__(SecretService.Keyring())
