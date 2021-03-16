from .utils import Singleton


class ExecutionEnvironment(metaclass=Singleton):
    """This class hold all the system environment based elements.

    The goal is to abstract all differences between system and
    isolate them in one point.

    This is a singleton.
    """

    def __init__(self):
        self.__keyring = None
        self.__api_session = None

        self.__connection_backend = None
        self.__killswitch = None

    @property
    def keyring(self):
        """Return the keyring to use"""
        if self.__keyring is None:
            from .keyring import KeyringBackend
            self.__keyring = KeyringBackend.get_default()
        return self.__keyring

    @keyring.setter
    def keyring(self, newvalue):
        self.__keyring = newvalue

    @property
    def connection_backend(self):
        """Return the connection backend to use (nm, etc.)"""
        raise NotImplementedError()

    @connection_backend.setter
    def connection_backend(self, newvalue):
        self.__connection_backend = newvalue

    @property
    def api_session(self):
        """Return the session to the API"""
        if self.__api_session is None:
            from .session import APISession
            self.__api_session = APISession()
        return self.__api_session

    @api_session.setter
    def api_session(self, newvalue):
        self.__api_session = newvalue

    @property
    def user_agent(self):
        """Get user agent to use when communicating with API

        Returns:
            string: User-Agent
        """
        try:
            import distro
            distribution, version, code_nome = distro.linux_distribution()
            return "ProtonVPN (Linux; {}/{})".format(distribution, version)

        except ImportError:
            return "ProtonVPN (Linux; unknown distribution/unknown version)"
