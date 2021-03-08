import distro
from .proton_session_wrapper import ProtonSessionWrapper

from ..constants import (
    APP_VERSION, NETSHIELD_STATUS_DICT
)
from ..enums import ClientSuffixEnum, KeyringEnum
from ..logger import logger
from .. import exceptions
from .session_data import SessionData


class UserManager:
    def __init__(
        self,
        user_conf_manager,
        keyring_service=KeyringEnum.DEFAULT_KEYRING_SERVICE.value,
        keyring_sessiondata=KeyringEnum.DEFAULT_KEYRING_SESSIONDATA.value,
        keyring_userdata=KeyringEnum.DEFAULT_KEYRING_USERDATA.value,
        keyring_proton_user=KeyringEnum.DEFAULT_KEYRING_PROTON_USER.value
    ):
        self.keyring_service = keyring_service
        self.keyring_sessiondata = keyring_sessiondata
        self.keyring_userdata = keyring_userdata
        self.keyring_proton_user = keyring_proton_user
        self.user_conf_manager = user_conf_manager
        self.session_data = SessionData()

        logger.info(

            "Initialized UserManager: service-> \"{}\"; ".format(
                self.keyring_service
            ) + "users-> \"[{}, {}, {}]\"".format(
                self.keyring_sessiondata,
                self.keyring_userdata,
                self.keyring_proton_user
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

        session = ProtonSessionWrapper(
            api_url="https://api.protonvpn.ch",
            appversion="LinuxVPN_" + APP_VERSION,
            user_agent=self.get_distro_info(),
            user_manager=self
        )
        session.authenticate(username, password)

        # fetch user data
        user_data = session.api_request("/vpn")

        # Store session data
        self.session_data.store_data(
            session.dump(),
            self.keyring_sessiondata,
            self.keyring_service
        )

        # Store user data
        self.session_data.store_data(
            user_data,
            self.keyring_userdata,
            self.keyring_service,
            store_user_data=True
        )

        # Store proton username
        self.session_data.store_data(
            {"proton_username": username},
            self.keyring_proton_user,
            self.keyring_service
        )

    def get_distro_info(self):
        """Get distribution version

        Returns:
            string: Linux distribution
        """
        distribution, version, code_nome = distro.linux_distribution()
        return "ProtonVPN (Linux; {}/{})".format(distribution, version)

    def logout(self, _pass_check, _removed):
        """Logout ProtonVPN user."""
        if (
            exceptions.StoredProtonUsernameNotFound in _pass_check
        ) and (
            exceptions.StoredUserDataNotFound in _pass_check
        ) and (
            exceptions.StoredSessionNotFound in _pass_check
        ):
            if len(_removed) == 0:
                raise exceptions.KeyringDataNotFound("No data was found")

            return

        if exceptions.StoredProtonUsernameNotFound not in _pass_check:
            try:
                self.session_data.delete_stored_data(
                    self.keyring_proton_user, self.keyring_service
                )
                _removed.append("StoredProtonUsername")
            except exceptions.KeyringDataNotFound:
                raise exceptions.StoredProtonUsernameNotFound(
                    "Proton username not found"
                )

        if exceptions.StoredUserDataNotFound not in _pass_check:
            try:
                self.session_data.delete_stored_data(
                    self.keyring_userdata, self.keyring_service
                )
                _removed.append("StoredUserData")
            except exceptions.KeyringDataNotFound:
                raise exceptions.StoredUserDataNotFound(
                    "User data not found"
                )

        if exceptions.StoredSessionNotFound not in _pass_check:
            try:
                self.session_data.delete_stored_data(
                    self.keyring_sessiondata, self.keyring_service
                )
                _removed.append("StoredSession")
            except exceptions.KeyringDataNotFound:
                raise exceptions.StoredSessionNotFound("Session not found")

    def get_stored_vpn_credentials(self, session=False):
        """Get OpenVPN credentials from keyring."""
        stored_user_data = self.session_data.get_stored_data(
            self.keyring_userdata,
            self.keyring_service,
        )

        return (
            self.append_suffix(stored_user_data["username"]),
            stored_user_data["password"]
        )

    def cache_user_data(self, session=False):
        """Cache user data from API."""
        logger.info("Caching user data")
        if not session:
            logger.info("Session not provided, loading session")
            session = self.load_session()

        logger.info("Calling api")
        user_data = session.api_request("/vpn")

        self.session_data.store_data(
            user_data,
            self.keyring_userdata,
            self.keyring_service,
            store_user_data=True
        )

    def append_suffix(self, username):
        """Append suffixes to OpenVPN username."""
        suffixes = [
            ClientSuffixEnum.PLATFORM,
            NETSHIELD_STATUS_DICT[self.user_conf_manager.netshield]
        ]

        _username = username + "+" + "+".join(
            suffix.value for suffix in suffixes
        )

        return _username

    def load_session(self):
        """Load ProtonVPN user session.

        Returns:
            Instance of ProtonSessionWrapper
        """
        session_data = self.session_data.get_stored_data(
            self.keyring_sessiondata,
            self.keyring_service
        )
        return self.convert_to_proton_session(session_data)

    def convert_to_proton_session(self, session_data):
        """Convert session data (json) to Proton Session.

        Args:
            session_data(json dict)

        Returns:
            Instance of ProtonSessionWrapper
        """
        try:
            return ProtonSessionWrapper.load(session_data, self)
        except KeyError as e:
            logger.exception("[!] KeyError: {}".format(e))
            raise KeyError(e)
        except Exception as e:
            logger.exception("[!] Exception: {}".format(e))
            raise Exception(e)

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
        """Tier property."""
        stored_user_data = self.session_data.get_stored_data(
            self.keyring_userdata,
            self.keyring_service,
        )

        return int(stored_user_data["tier"])

    @property
    def protonvpn_username(self):
        """ProtonVPN username property."""
        stored_user_data = self.session_data.get_stored_data(
            self.keyring_proton_user,
            self.keyring_service,
        )

        return stored_user_data
