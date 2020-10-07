import distro
import proton

from ..constants import (
    APP_VERSION
)
from ..enums import ClientSuffixEnum, KeyringEnum
from ..logger import logger
from .. import exceptions
from .user_session_manager import UserSessionManager


class UserManager(UserSessionManager):
    def __init__(
        self,
        keyring_service=KeyringEnum.DEFAULT_KEYRING_SERVICE,
        keyring_sessiondata=KeyringEnum.DEFAULT_KEYRING_SESSIONDATA,
        keyring_userdata=KeyringEnum.DEFAULT_KEYRING_USERDATA
    ):
        self.keyring_service = keyring_service
        self.keyring_sessiondata = keyring_sessiondata
        self.keyring_userdata = keyring_userdata

        logger.info(
            "Initialized UserManager: service-> \"{}\"; ".format(
                self.keyring_service
            ) + "users-> \"[{}, {}]\"".format(
                self.keyring_sessiondata,
                self.keyring_userdata
            )
        )
        super().__init__()

    def login(self, username, password):
        """Login ProtonVPN user.

        Args:
            username (string): ProtonVPN username
            password (string): ProtonVPN password
        """
        self.validate_username_password(username, password)

        session = proton.Session(
            api_url="https://api.protonvpn.ch",
            appversion="LinuxVPN_" + APP_VERSION,
            user_agent=self.get_distro_info()
        )

        try:
            session.authenticate(username, password)
        except proton.api.ProtonError as e:
            logger.exception("[!] API ProtonError: {}".format(e))
            if e.code == 8002:
                raise exceptions.IncorrectCredentialsError(e)
            else:
                raise exceptions.APIAuthenticationError(e)
        else:
            self.store_data(
                session.dump(),
                self.keyring_sessiondata,
                self.keyring_service
            )

        user_data = session.api_request('/vpn')

        self.store_data(
            user_data,
            self.keyring_userdata,
            self.keyring_service
        )

    def get_distro_info(self):
        distribution, version, code_nome = distro.linux_distribution()
        return "ProtonVPN (Linux; {}/{})".format(distribution, version)

    def logout(self):
        """Logout ProtonVPN user."""
        self.delete_stored_data(
            self.keyring_sessiondata, self.keyring_service
        )
        self.delete_stored_data(
            self.keyring_userdata, self.keyring_service
        )

    def get_stored_vpn_credentials(self, session=False):
        """Get OpenVPN credentials from keyring."""
        stored_user_data = self.get_stored_data(
            self.keyring_userdata,
            self.keyring_service,
        )

        return (
            self.append_suffix(stored_user_data["username"]),
            stored_user_data["password"]
        )

    def cache_user_data(self, session=False):
        """Cache user data from API."""
        if not session:
            session = self.load_session()

        user_data = session.api_request('/vpn')

        self.store_data(
            user_data,
            self.keyring_userdata,
            self.keyring_service
        )

    def append_suffix(self, username):
        suffixes = [
            ClientSuffixEnum.PLATFORM
        ]

        _username = username + "+" + "+".join(
            suffix for suffix in suffixes
        )

        return _username

    def load_session(self):
        """Load ProtonVPN user session."""
        return self.load_stored_user_session()

    def validate_username_password(self, username, password):
        """Validate ProtonVPN username and password.

        Args:
            username (string): ProtonVPN username
            password (string): ProtonVPN password
        """
        if not isinstance(username, str):
            err_msg = "Incorrect object type, "\
                "str is expected but got {} instead.".format(type(username))
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)
        elif not isinstance(password, str):
            err_msg = "Incorrect object type, "\
                "str is expected but got {} instead.".format(type(password))
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)
        elif not username.strip() or not password.strip():
            err_msg = "Both username and password must be provided."
            logger.error(
                "[!] ValueError: {}. Raising exception.".format(err_msg)
            )
            raise ValueError(err_msg)

    @property
    def tier(self):
        stored_user_data = self.get_stored_data(
            self.keyring_userdata,
            self.keyring_service,
        )

        return int(stored_user_data["tier"])
