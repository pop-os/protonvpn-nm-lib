import json
import os
import re

import keyring
import proton

from lib import exceptions
from lib.constants import DEFAULT_KEYRING_SERVICE, DEFAULT_KEYRING_USERNAME
from lib.logger import logger


class UserSessionManager:
    KEYRING_BACKENDS = [
        keyring.backends.kwallet.DBusKeyring,
        keyring.backends.SecretService.Keyring,
    ]

    def __init__(self):
        self.set_optimum_keyring_backend()
        current_DE = os.getenv("XDG_CURRENT_DESKTOP", "")
        current_DE = "None" if len(str(current_DE)) == 0 else current_DE
        logger.info("Current DE: \"{}\"".format(current_DE))
        print("Current DE:", current_DE)

    def load_stored_user_session(
        self,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        """Load stored user session from keychain.

        Args:
            keyring_service (string): the keyring servicename (optional)
            keyring_username (string): the keyring username (optional)
        Returns:
            session (proton.api.Session)
        """
        logger.info("Loading stored user session")
        stored_session = self.get_stored_user_session(
            keyring_service,
            keyring_username
        )

        # Needs to be catched
        try:
            return proton.Session.load(stored_session)
        except KeyError as e:
            logger.exception("[!] Exception: {}".format(e))
            raise Exception(e)

    def store_user_session(
        self,
        auth_data,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        """Store user session in keychain.

        Args:
            keyring_service (string): the keyring servicename (optional)
            keyring_username (string): the keyring username (optional)
        """
        logger.info("Storing user session")
        json_auth_data = self.json_session_transform(
            auth_data,
            "save"
        )

        if auth_data is None or len(auth_data) < 1:
            logger.error(
                "[!] IllegalAuthData: Unexpected AuthData type. "
                + "Raising exception."
            )
            raise exceptions.IllegalAuthData("Unexpected AuthData type")

        try:
            keyring.set_password(
                keyring_service,
                keyring_username,
                json_auth_data
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

    def get_stored_user_session(
        self,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        """Get stored user session from keychain.

        Args:
            keyring_service (string): the keyring servicename (optional)
            keyring_username (string): the keyring username (optional)
        Returns:
            json: json encoded authentication data
        """
        try:
            stored_session = keyring.get_password(
                keyring_service,
                keyring_username
            )
        except (keyring.errors.InitError, keyring.errors.KeyringLocked) as e:
            logger.exception("[!] AccessKeyringError: {}".format(e))
            raise exceptions.AccessKeyringError(
                "Could not fetch from keychain: {}".format(e)
            )
        try:
            return self.json_session_transform(
                stored_session,
                "load"
            )
        except json.decoder.JSONDecodeError as e:
            logger.exception("[!] JSONAuthDataEmptyError: {}".format(e))
            raise exceptions.JSONAuthDataEmptyError(e)
        except TypeError as e:
            logger.exception("[!] JSONAuthDataNoneError: {}".format(e))
            raise exceptions.JSONAuthDataNoneError(e)
        except Exception as e:
            logger.exception("[!] JSONAuthDataError: {}".format(e))
            raise exceptions.JSONAuthDataError(e)

    def delete_user_session(
        self,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        """Delete stored user session from keychain.

        Args:
            keyring_service (string): the keyring servicename (optional)
            keyring_username (string): the keyring username (optional)
        """
        logger.info("Deleting user session")
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
            logger.exception("[!] StoredSessionNotFound: {}".format(e))
            raise exceptions.StoredSessionNotFound(e)

    def json_session_transform(self, auth_data, action=["save", "load"]):
        """JSON encode/decode auth_data.

        Args:
            auth_data (string): api response containg json headers
            action (string): [save, load]
        Returns:
            string or json
        """
        logger.info("Transforming session: \"{}\"".format(action))
        json_action = json.dumps

        if action == "load":
            json_action = json.loads

        # try:
        return json_action(auth_data)
        # except Exception as e:
        #     raise exceptions.JSONAuthDataError(e)
        # except json.decoder.JSONDecodeError as e:
        #     raise exceptions.JSONAuthDataEmptyError(e)
        # except TypeError as e:
        #     raise exceptions.JSONAuthDataNoneError(e)
        # except Exception as e:
        #     raise exceptions.JSONAuthDataError(e)

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
            else:
                backend_priority = search_in_str(
                    r"\(\w+:\W(\d+\.?\d*)\)", backend_str
                )

            if backend_priority is not None:
                try:
                    supported_backends.index(backend_name)
                except ValueError:
                    continue
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
        print("Keyring backend:", optimum_backend[0])
        keyring.set_keyring(optimum_backend[2])
