class ProtonVPNBaseException(BaseException):
    def __init__(self, message):
        self.message = message
        super(ProtonVPNBaseException, self).__init__(self.message)


class AccessKeyringError(ProtonVPNBaseException):
    """Python-keyring error occured."""


class AddConnectionCredentialsError(ProtonVPNBaseException):
    """Add credentials to connection error."""


class AddServerCertificateCheckError(ProtonVPNBaseException):
    """Add server certificate check error"""


class IncorrectCredentialsError(ProtonVPNBaseException):
    """Incorrect credentials error."""


class APIAuthenticationError(ProtonVPNBaseException):
    """Incorrect credentials error."""


class ImportConnectionError(ProtonVPNBaseException):
    """Import connection configurations error."""


class VirtualDeviceNotFound(ProtonVPNBaseException):
    """Virtual device could not be found."""


class IllegalVirtualDevice(ProtonVPNBaseException):
    """Unexpeced virtual device."""


class AddConnectionFinishError(ProtonVPNBaseException):
    """Add connection finish error."""


class StartConnectionFinishError(ProtonVPNBaseException):
    """Start connection finish error."""


class StopConnectionFinishError(ProtonVPNBaseException):
    """Stop connection finish error."""


class RemoveConnectionFinishError(ProtonVPNBaseException):
    """Remove connection finish error."""


class IllegalVPNProtocol(ProtonVPNBaseException):
    """Unexpexted plugin for specified protocol."""


class ProtocolPluginNotFound(ProtonVPNBaseException):
    """Plugin for specified protocol was not found."""


class ConnectionNotFound(ProtonVPNBaseException):
    """ProtonVPN connection not found"""


class ProtocolNotFound(ProtonVPNBaseException):
    """Protocol not found upon generate certificate"""


class OptimumBackendNotFound(ProtonVPNBaseException):
    """Optimum keyring backend not found"""


class SessionError(ProtonVPNBaseException):
    """Session error"""


class IllegalServername(ProtonVPNBaseException):
    """Unexpected servername"""


class EmptyServerListError(ProtonVPNBaseException):
    """Empty server list error"""



class IllegalData(ProtonVPNBaseException): # noqa
    """Illegal/unexpected data type"""


class IllegalSessionData(IllegalData):
    """Illegal/unexpected SessionData type"""


class IllegalUserData(IllegalData):
    """Illegal/unexpected UserData type"""



class JSONError(ProtonVPNBaseException): # noqa
    """JSON generated errors"""


class JSONSDataEmptyError(JSONError):
    """JSON SessionData empty error"""


class JSONDataNoneError(JSONError):
    """JSON SessionData none error"""


class JSONDataError(JSONError):
    """JSON SessionData error"""



class CacheServersError(ProtonVPNBaseException): # noqa
    """Cache servers error"""


class CacheLogicalServersError(CacheServersError):
    """Cache logical servers error"""


class CacheLogicalServersFallbackError(CacheServersError):
    """Cache logical servers fallback error"""



class KeyringDataNotFound(ProtonVPNBaseException): # noqa
    """Keyring data not found"""


class StoredSessionNotFound(KeyringDataNotFound):
    """Stored session was not found"""


class StoredUserDataNotFound(KeyringDataNotFound):
    """Stored user data was not found"""


class StoredProtonUsernameNotFound(KeyringDataNotFound):
    """Stored user data was not found"""


class SelectedOptionError(ProtonVPNBaseException):
    """Selected option error"""
