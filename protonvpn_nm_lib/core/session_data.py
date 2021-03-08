import json
import os

from .. import exceptions
from ..enums import JsonDataEnumAction, KeyringEnum
from ..logger import logger
from .keyring_wrapper import KeyringWrapper


class SessionData:
    """User Sesssion

    Stores and loads a user session data.
    """
    def __init__(self):
        self.keyring = KeyringWrapper()
        current_DE = str(os.getenv("XDG_CURRENT_DESKTOP"))
        logger.info("Current DE: \"{}\"".format(current_DE))

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
            JsonDataEnumAction.SAVE
        )

        self.keyring.set_password(
            keyring_service,
            keyring_username,
            json_data
        )

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
        stored_data = self.keyring.get_password(
            keyring_service,
            keyring_username
        )

        try:
            return self.json_session_transform(
                stored_data,
                JsonDataEnumAction.LOAD
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
        self.keyring.delete_password(
            keyring_service,
            keyring_username,
        )

    def json_session_transform(self, session_data, action):
        """JSON encode/decode session_data.

        Args:
            session_data (string): api response containg json headers
            action (JsonDataEnumAction): enum
        Returns:
            string or json
        """
        logger.info("Transforming session: \"{}\"".format(action))
        json_action = json.dumps

        if action == JsonDataEnumAction.LOAD:
            json_action = json.loads

        return json_action(session_data)
