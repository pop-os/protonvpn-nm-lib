from ... import exceptions
from ...logger import logger
from ...constants import APP_VERSION
from ..utilities import Utilities
import re
from .proton_session_wrapper import ProtonSessionWrapper
from ..keyring import KeyringOVPN, KeyringProton, KeyringSession, keyring_adapter


class Session:
    """Session Class.

    This class should be userd everything that is related to the API.
    Thus it should be used to login, logout, get user session,
    check if session exists and ensure that a session is valid.

    Exposes methods:
        login(username, password)
        logout()
        cache_user_data()
        get_session()
        refresh_servers()
        check_session_exists()
        ensure_session_is_valid(session: ProtonSessionWrapper)
    """
    def __init__(
        self,
        proton_session_wrapper=ProtonSessionWrapper,
        keyring_session=KeyringSession(keyring_adapter),
        keyring_ovpn=KeyringOVPN(keyring_adapter),
        keyring_proton=KeyringProton(keyring_adapter)
    ):
        # proton_session_wrapper is
        # an uninstatiated ProtonSessionWrapper object
        self._proton_session_wrapper = proton_session_wrapper
        self._keyring_session = keyring_session
        self._keyring_ovpn = keyring_ovpn
        self._keyring_proton = keyring_proton
        self._keyring_list = [
            self._keyring_session, self._keyring_ovpn, self._keyring_proton
        ]

    def reload_keyring_properties(self):
        for keyring in self._keyring_list:
            keyring.reload_properties()

    @property
    def proton_session_wrapper(self):
        return self._proton_session_wrapper

    @property
    def keyring_session(self):
        return self._keyring_session

    @property
    def keyring_ovpn(self):
        return self._keyring_ovpn

    @property
    def keyring_proton(self):
        return self._keyring_proton

    def login(self, username, password):
        """Login ProtonVPN user.

        Args:
            protonvpn_user (ProtonVPNUser)
        """
        self.validate_username_and_password(username, password)
        self.ensure_username_is_valid(username)

        session = self._generate_local_session()
        session.authenticate(username, password)
        user_data = session.api_request("/vpn")

        self.keyring_session.store(session.dump())
        self.keyring_ovpn.store(user_data)
        self.keyring_proton.store(
            {"proton_username": username}
        )

    def _generate_local_session(self):
        session = self.proton_session_wrapper(
            api_url="https://api.protonvpn.ch",
            appversion="LinuxVPN_" + APP_VERSION,
            user_agent=Utilities.get_distro_info(),
            keyring_session=self.keyring_session
        )

        return session

    def cache_user_data(self, session=False):
        """Cache user data from API.

        Should be used when keyring_ovpn throws complains
        that there is no data stored in that keyring entry.
        """
        logger.info("Caching user data")
        if not session:
            logger.info("Session not provided, loading session")
            session = self._load_session()

        logger.info("Calling api")
        user_data = session.api_request("/vpn")

        self.keyring_ovpn.store(user_data)

    def get_session(self):
        """Get user session.

        Returns:
            ProtonSessionWrapper
        """
        try:
            return self._get_existing_session()
        except exceptions.StoredSessionNotFound as e:
            raise exceptions.StoredSessionNotFound(e)
        except exceptions.IllegalSessionData as e:
            raise exceptions.IllegalSessionData(e)
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)

    def check_session_exists(self):
        """Check if sessions exists.

        Returns:
            bool
        """
        try:
            return self._get_existing_session(return_bool=True)
        except (exceptions.ProtonVPNException, Exception):
            return False

    def ensure_session_is_valid(self, session):
        """Ensure that provided session is valid.

        Args:
            session (proton.api.Session): current user session
        """
        logger.info("Validating session")

        if not isinstance(session, self.proton_session_wrapper):
            err_msg = "Incorrect object type, "\
                "{} is expected "\
                "but got {} instead".format(
                    self.proton_session_wrapper, session
                )
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise TypeError(err_msg)

    def refresh_servers(self):
        """Refresh cached server list."""
        session = self.get_session()
        # TO-DO: Should be moved outside. Client could watch for this.
        # if killswitch_setting != KillswitchStatusEnum.HARD:
        try:
            session.cache_servers()
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)

    def _load_session(self):
        """Load ProtonVPN user session.

        Returns:
            Instance of ProtonSessionWrapper
        """
        self.keyring_session.reload_properties()
        return self._convert_to_proton_session(self.keyring_session.session)

    def logout(self, session=None, _pass_check=None, _removed=None):
        logger.info("Attemping to logout...")

        if _pass_check is None and _removed is None:
            logger.info("First logout round")

            session = self.get_session()

            try:
                session.logout()
            except (
                exceptions.ProtonSessionWrapperError,
                AttributeError
            ):
                logger.info("Unable to logout from API")

            _pass_check = []
            _removed = []

        try:
            self._recursive_logout(_pass_check, _removed)
        except exceptions.StoredProtonUsernameNotFound:
            logger.info("Recursive logout: StoredProtonUsernameNotFound")
            _pass_check.append(exceptions.StoredProtonUsernameNotFound)
            self.logout(session, _pass_check, _removed)
        except exceptions.StoredUserDataNotFound:
            logger.info("Recursive logout: StoredUserDataNotFound")
            _pass_check.append(exceptions.StoredUserDataNotFound)
            self.logout(session, _pass_check, _removed)
        except exceptions.StoredSessionNotFound:
            logger.info("Recursive logout: StoredSessionNotFound")
            _pass_check.append(exceptions.StoredSessionNotFound)
            self.logout(session, _pass_check, _removed)
        except exceptions.KeyringDataNotFound as e:
            logger.exception(e)
            raise Exception(e)
        except exceptions.AccessKeyringError as e:
            logger.exception(e)
            raise Exception(e)
        except exceptions.KeyringError as e:
            logger.exception(e)
            raise Exception(e)
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(
                "Unknown error: {}".format(e)
            )
            raise Exception("Unknown error occured: {}.".format(e))

        logger.info("Successful logout.")

    def _recursive_logout(self, _pass_check, _removed):
        """Logout ProtonVPN user."""
        if (
            exceptions.StoredProtonUsernameNotFound in _pass_check
        ) and (
            exceptions.StoredUserDataNotFound in _pass_check
        ) and (
            exceptions.StoredSessionNotFound in _pass_check
        ):
            if len(_removed) == 0:
                raise exceptions.KeyringDataNotFound(
                    "No session data was found in keyring. Please login first."
                )

            return

        if exceptions.StoredProtonUsernameNotFound not in _pass_check:
            try:
                self.keyring_proton.delete()
                _removed.append("StoredProtonUsername")
            except exceptions.KeyringDataNotFound:
                raise exceptions.StoredProtonUsernameNotFound(
                    "Proton username not found"
                )

        if exceptions.StoredUserDataNotFound not in _pass_check:
            try:
                self.keyring_ovpn.delete()
                _removed.append("StoredUserData")
            except exceptions.KeyringDataNotFound:
                raise exceptions.StoredUserDataNotFound(
                    "User data not found"
                )

        if exceptions.StoredSessionNotFound not in _pass_check:
            try:
                self.keyring_session.delete()
                _removed.append("StoredSession")
            except exceptions.KeyringDataNotFound:
                raise exceptions.StoredSessionNotFound("Session not found")

    def _convert_to_proton_session(self, stored_session_data):
        """Convert session data (json) to Proton Session.

        Args:
            stored_session_data(json dict)

        Returns:
            Instance of ProtonSessionWrapper
        """
        return self.proton_session_wrapper.load(
            stored_session_data,
            self.keyring_session
        )

    def _get_existing_session(
        self, return_bool=False
    ):
        """Private method.

        Gets the session. Default behaviour is
        return the session. It can also return bool
        if return_bool=True, returning True if session exists,
        False otherwise.

        Args:
            return_bool (bool):
                (optional) should be true if
                boolean is value requested.
        """
        logger.info("Attempting to get existing session")
        session = None
        try:
            session = self._load_session()
        except exceptions.JSONDataEmptyError:
            raise exceptions.IllegalSessionData(
                "The stored session might be corrupted. "
                + "Please, try to login again."
            )
        except (
            exceptions.JSONDataError,
            exceptions.JSONDataNoneError,
        ):
            raise exceptions.StoredSessionNotFound(
                "There is no stored session. Please, login first."
            )
        except exceptions.AccessKeyringError as e:
            logger.exception(e)
            raise Exception(
                "Unable to load session. Could not access keyring."
            )
        except exceptions.KeyringError as e:
            logger.exception(e)
            raise Exception("Unknown keyring error occured: {}".format(e))
        except TypeError:
            pass

        logger.info("Session found.")

        if return_bool:
            return True if session else False

        return session

    def ensure_username_is_valid(self, username):
        """Ensure that the provided username is valid.

        This is done automatically during protonvpn._login(),
        but can be used at any time to check if the provided username
        follows the full Proton account.

        Expected:
            protonvpn@protonmail.com
            username@protonvpn.com
            username@customdns.com
        """
        re_username = re.compile(
            r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        )
        if not re_username.search(username):
            raise exceptions.InvalidUsernameFormat(
                "The provided username \"{}\" is invalid."
                "\nPlease provide your full Proton account username, ie: "
                "username@protonmail.com".format(
                    username
                )
            )

    def validate_username_and_password(self, username, password):
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
