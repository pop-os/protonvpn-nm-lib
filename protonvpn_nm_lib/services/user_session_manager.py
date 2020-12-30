import json
import os
import re

import keyring
import keyring.backends.kwallet
import keyring.backends.SecretService
from .proton_session_wrapper import ProtonSessionWrapper

from .. import exceptions
from ..enums import KeyringEnum
from ..logger import logger
from . import capture_exception


class UserSessionManager:
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
        current_DE = str(os.getenv("XDG_CURRENT_DESKTOP"))
        logger.info("Current DE: \"{}\"".format(current_DE))

    def load_stored_user_session(
        self,
        keyring_username=KeyringEnum.DEFAULT_KEYRING_SESSIONDATA,
        keyring_service=KeyringEnum.DEFAULT_KEYRING_SERVICE,
    ):
        """Load stored user session from keychain.

        Args:
            keyring_service (string): the keyring servicename (optional)
            keyring_username (string): the keyring username (optional)
        Returns:
            session (proton.api.Session)
        """
        logger.info("Loading stored user session")
        stored_session = self.get_stored_data(
            keyring_username,
            keyring_service,
        )

        # Needs to be catched
        try:
            return ProtonSessionWrapper.load(stored_session, self)
        except KeyError as e:
            logger.exception("[!] KeyError: {}".format(e))
            raise Exception(e)
        except Exception as e:
            logger.exception("[!] Exception: {}".format(e))
            capture_exception(e)

    def store_data(
        self,
        data,
        keyring_username,
        keyring_service=KeyringEnum.DEFAULT_KEYRING_SERVICE,
        store_user_data=False
    ):
        """Store data to keychain.

        Args:
            data (dict(json)): data to be stored
            keyring_username (string): the keyring username
            keyring_service (string): the keyring servicename (optional)
            store_user_data (bool): if data to be stored is user data
        """
        logger.info("Storing {}".format(keyring_username))
        if data is None or len(data) < 1:
            logger.error(
                "[!] IllegalData: Unexpected SessionData type. "
                + "Raising exception."
            )
            raise exceptions.IllegalData(
                "Unexpected SessionData type"
            )

        if store_user_data:
            data = {
                "username": data["VPN"]["Name"],
                "password": data["VPN"]["Password"],
                "tier": data["VPN"]["MaxTier"]
            }

        json_data = self.json_session_transform(
            data,
            "save"
        )

        try:
            keyring.set_password(
                keyring_service,
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
            capture_exception(e)

    def get_stored_data(
        self,
        keyring_username,
        keyring_service=KeyringEnum.DEFAULT_KEYRING_SERVICE,
    ):
        """Get stored data from keychain.

        Args:
            keyring_username (string): the keyring username
            keyring_service (string): the keyring servicename (optional)
        Returns:
            json: json encoded data
        """
        try:
            stored_data = keyring.get_password(
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

        try:
            return self.json_session_transform(
                stored_data,
                "load"
            )
        except json.decoder.JSONDecodeError as e:
            logger.exception("[!] JSONDataEmptyError: {}".format(e))
            raise exceptions.JSONDataEmptyError(e)
        except TypeError as e:
            logger.exception("[!] JSONDataNoneError: {}".format(e))
            raise exceptions.JSONDataNoneError(e)
        except Exception as e:
            logger.exception("[!] JSONDataError: {}".format(e))
            raise exceptions.JSONDataError(e)

    def delete_stored_data(
        self,
        keyring_username,
        keyring_service=KeyringEnum.DEFAULT_KEYRING_SERVICE,
    ):
        """Delete stored data from keychain.

        Args:
            keyring_username (string): the keyring username
            keyring_service (string): the keyring servicename (optional)
        """
        logger.info("Deleting stored {}".format(keyring_username))
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

    def json_session_transform(self, session_data, action=["save", "load"]):
        """JSON encode/decode session_data.

        Args:
            session_data (string): api response containg json headers
            action (string): [save, load]
        Returns:
            string or json
        """
        logger.info("Transforming session: \"{}\"".format(action))
        json_action = json.dumps

        if action == "load":
            json_action = json.loads

        return json_action(session_data)

    def set_optimum_keyring_backend(self):
        """Determines the optimum keyring backend to be used.

        Default backend: SecretService
        """
        logger.info("Setting optimum backend")
        optimum_backend = None
        search_in_str = re.search
        supported_backends = ["kwallet", "SecretService"]

        for k in keyring.backend.get_all_keyring():
            backend_obj = k
            backend_str = str(k)

            backend_string_object = backend_str.split()[0]

            try:
                backend_name = backend_string_object.split(".")[2]
            except IndexError:
                backend_priority = None
            except Exception as e:
                logger.exception("[!] Unknown exception: {}".format(e))
                capture_exception(e)
            else:
                backend_priority = search_in_str(
                    r"\(\w+:\W(\d+\.?\d*)\)", backend_str
                )

            if backend_priority is not None:
                try:
                    supported_backends.index(backend_name)
                except ValueError:
                    continue
                except Exception as e:
                    logger.exception("[!] Unknown exception: {}".format(e))
                    capture_exception(e)
                else:
                    backend_priority = backend_priority.group(1)
                    if (
                        optimum_backend is None
                        or float(backend_priority) > float(optimum_backend[1])
                    ):
                        optimum_backend = (
                            backend_name,
                            backend_priority,
                            backend_obj
                        )

        if optimum_backend is None:
            optimum_backend = (
                "SecretService",
                10,
                keyring.backends.SecretService.Keyring()
            )

        logger.info("Keyring backend: {}".format(optimum_backend))
        keyring.set_keyring(optimum_backend[2])
