class ProtonVPNBaseException(BaseException):
    def __init__(self, message):
        self.message = message
        super(ProtonVPNBaseException, self).__init__(self.message)


class AccessKeyringError(ProtonVPNBaseException):
    """Python-keyring error occured."""


class AddConnectionCredentialsError(ProtonVPNBaseException):
    """Add credentials to connection error."""


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


class IllegalAuthData(ProtonVPNBaseException):
    """Unexpected AuthData type"""


class JSONAuthDataEmptyError(ProtonVPNBaseException):
    """JSON AuthData empty error"""


class JSONAuthDataNoneError(ProtonVPNBaseException):
    """JSON AuthData none error"""


class JSONAuthDataError(ProtonVPNBaseException):
    """JSON AuthData error"""


class OptimumBackendNotFound(ProtonVPNBaseException):
    """Optimum keyring backend not found"""


class SessionError(ProtonVPNBaseException):
    """Session error"""


class StoredSessionNotFound(ProtonVPNBaseException):
    """Stored session was not found"""


class IllegalServername(ProtonVPNBaseException):
    """Unexpected servername"""


class EmptyServerListError(ProtonVPNBaseException):
    """Empty server list error"""
