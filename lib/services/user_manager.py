from lib import exceptions
import proton
from .user_session_manager import UserSessionManager


class UserManager(UserSessionManager):
    def __init__(self):
        super().__init__()

    def login(self, username, password):
        session = proton.Session("https://api.protonvpn.ch")
        try:
            session.authenticate(username, password)
        except proton.api.ProtonError as e:
            if e.code == 8002:
                raise exceptions.IncorrectCredentialsError(e)
            else:
                raise exceptions.APIAuthenticationError(e)
        else:
            self.store_user_session(session.dump())

    def logout(self):
        self.delete_user_session()

    @property
    def vpn_credentials(self):
        session = self.load_session

        api_resp = session.api_request('/vpn')

        return (api_resp["VPN"]["Name"], api_resp["VPN"]["Password"])

    @property
    def load_session(self):
        return self.load_stored_user_session()
