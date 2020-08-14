from lib import exceptions
from lib.constants import DEFAULT_KEYRING_SERVICE, DEFAULT_KEYRING_USERNAME
import json
import os
import re

import keyring

import proton


class UserSessionManager:
    KEYRING_BACKENDS = [
        keyring.backends.kwallet.DBusKeyring,
        keyring.backends.SecretService.Keyring,
    ]

    def __init__(self):
        self.set_optimum_keyring_backend()
        current_DE = os.getenv("XDG_CURRENT_DESKTOP", "")
        print(
            "Current DE:",
            "None" if len(str(current_DE)) == 0 else current_DE
        )

    def load_stored_user_session(
        self,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        """Load a stored user session from keychain.

        Args:
            keyring_service (string): the keyring servicename (optional)
            keyring_username (string): the keyring username (optional)
        """
        stored_session = self.get_stored_user_session(
            keyring_service,
            keyring_username
        )

        # Needs to be catched
        try:
            return proton.Session.load(stored_session)
        except KeyError as e:
            raise Exception(e)

    def store_user_session(
        self,
        auth_data,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        """Store a user session in the keychain.

        Args:
            keyring_service (string): the keyring servicename (optional)
            keyring_username (string): the keyring username (optional)
        """
        json_auth_data = self.json_session_transform(
            auth_data,
            "save"
        )

        if auth_data is None or len(auth_data) < 1:
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
            raise exceptions.AccessKeyringError(
                "Could not access keychain: {}".format(e)
            )

    def get_stored_user_session(
        self,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        """Get the stored user session from keychain.

        Args:
            keyring_service (string): the keyring servicename (optional)
            keyring_username (string): the keyring username (optional)
        """
        try:
            stored_session = keyring.get_password(
                keyring_service,
                keyring_username
            )
        except (keyring.errors.InitError, keyring.errors.KeyringLocked) as e:
            raise exceptions.AccessKeyringError(
                "Could not fetch from keychain: {}".format(e)
            )
        try:
            return self.json_session_transform(
                stored_session,
                "load"
            )
        except json.decoder.JSONDecodeError as e:
            raise exceptions.JSONAuthDataEmptyError(e)
        except TypeError as e:
            raise exceptions.JSONAuthDataNoneError(e)
        except Exception as e:
            raise exceptions.JSONAuthDataError(e)

    def delete_user_session(
        self,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        """Delete a stored user session from keychain.

        Args:
            keyring_service (string): the keyring servicename (optional)
            keyring_username (string): the keyring username (optional)
        """
        try:
            keyring.delete_password(
                keyring_service,
                keyring_username,
            )
        except (
                keyring.errors.InitError,
                keyring.errors.KeyringLocked,
                keyring.errors.PasswordSetError
        ) as e:
            raise Exception("Could not delete from keychain: {}".format(e))

    def json_session_transform(self, auth_data, action=["save", "load"]):
        """JSON encode/decode auth_data.

        Args:
            auth_data (string): api response containg json headers
            action (string): [save, load]
        """
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
        """Determines the optimum keyring backend to be used"""
        optimum_backend = None
        search_in_str = re.search
        supported_backends = ["kwallet", "SecretService"]

        for k in keyring.backend.get_all_keyring():
            backend_obj = k
            backend_str = str(k)

            backend_string_object = backend_str.split()[0]
            backend_name = backend_string_object.split(".")[2]
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

        print("Keyring backend:", optimum_backend[0])
        keyring.set_keyring(optimum_backend[2])
