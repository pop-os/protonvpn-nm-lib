import keyring
import keyring.backends.kwallet
import keyring.backends.SecretService

from .. import exceptions
from ..enums import KeyringEnum
from ..logger import logger
from . import capture_exception
from .keyring_backend import KeyringBackend


class KeyringWrapper:
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

    def __init__(self):
        self.set_optimum_keyring_backend()

    def set_optimum_keyring_backend(self):
        """Determines the optimum keyring backend to be used.

        Default backend: SecretService
        """
        logger.info("Setting optimum backend")
        optimum_backend = None

        for backend in keyring.backend.get_all_keyring():
            keyring_backend = KeyringBackend(backend)
            keyring_backend.generate_backend_object()

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
            optimum_backend = KeyringBackend.get_default_keyring()

        logger.info("Keyring backend: {}".format(optimum_backend))
        keyring.set_keyring(optimum_backend.object)

    def get_password(self, keyring_service, keyring_username):
        try:
            return keyring.get_password(
                keyring_service,
                keyring_username
            )
        except (keyring.errors.InitError, keyring.errors.KeyringLocked) as e:
            logger.exception("[!] AccessKeyringError: {}".format(e))
            raise exceptions.AccessKeyringError(
                "Could not fetch from keychain: {}".format(e)
            )
        except Exception as e:
            logger.exception("[!] KeyringError: {}".format(e))
            capture_exception(e)
            raise exceptions.KeyringError(e)

    def delete_password(self, keyring_service, keyring_username):
        try:
            keyring.delete_password(
                keyring_service,
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
            capture_exception(e)

    def set_password(self, keyring_service, keyring_username, data):
        try:
            keyring.set_password(
                keyring_service,
                keyring_username,
                data
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
            capture_exception(e)
