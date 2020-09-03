import proton

from lib import exceptions
from lib.constants import (APP_VERSION, DEFAULT_KEYRING_SERVICE,
                           DEFAULT_KEYRING_USERNAME)

from .user_session_manager import UserSessionManager


class UserManager(UserSessionManager):
    def __init__(
        self,
        keyring_service=DEFAULT_KEYRING_SERVICE,
        keyring_username=DEFAULT_KEYRING_USERNAME
    ):
        self.keyring_service = keyring_service
        self.keyring_username = keyring_username
        super().__init__()

    def login(self, username, password):
        """Login and store user session, with ProtonVPN credentials.

        Args:
            username (string): ProtonVPN username
            password (string): ProtonVPN password
        """
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

        session = proton.Session(
            api_url="https://api.protonvpn.ch",
            appversion="LinuxVPN_" + APP_VERSION
        )

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
                self.keyring_service,
                self.keyring_username
            )

    def logout(self):
        """Logout user."""
        self.delete_user_session(self.keyring_service, self.keyring_username)

    def fetch_vpn_credentials(self):
        """Fetch vpn credentials from api."""
        session = self.load_session()
        api_resp = session.api_request('/vpn')
        return (api_resp["VPN"]["Name"], api_resp["VPN"]["Password"])

    def load_session(self):
        """Load stored user session."""
        return self.load_stored_user_session(
            self.keyring_service, self.keyring_username
        )
