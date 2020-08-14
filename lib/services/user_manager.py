from lib import exceptions
from lib.constants import DEFAULT_KEYRING_SERVICE, DEFAULT_KEYRING_USERNAME
import proton
from .user_session_manager import UserSessionManager


class UserManager(UserSessionManager):
    def __init__(self):
        super().__init__()

    def login(
        self, username, password,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        if not isinstance(username, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(username))
            )
        elif not isinstance(password, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(password))
            )
        elif not username.strip() or not password.strip():
            raise ValueError("Both username and password must be provided")

        session = proton.Session("https://api.protonvpn.ch")

        try:
            session.authenticate(username, password)
        except proton.api.ProtonError as e:
            if e.code == 8002:
                raise exceptions.IncorrectCredentialsError(e)
            else:
                raise exceptions.APIAuthenticationError(e)
        else:
            self.store_user_session(
                session.dump(),
                keyring_service,
                keyring_username
            )

    def logout(
        self,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        if not keyring_service and not keyring_username:
            keyring_service = self.DEFAULT_KEYRING_SERVICE
            keyring_service = self.DEFAULT_KEYRING_USERNAME
        self.delete_user_session(keyring_service, keyring_username)

    def fetch_vpn_credentials(
        self,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        session = self.load_session(keyring_service, keyring_username)

        api_resp = session.api_request('/vpn')

        return (api_resp["VPN"]["Name"], api_resp["VPN"]["Password"])

    def load_session(
        self,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        return self.load_stored_user_session(keyring_service, keyring_username)
