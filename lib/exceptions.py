class CustomBaseException(BaseException):
    def __init__(self, message):
        self.message = message
        super(CustomBaseException, self).__init__(self.message)


class AccessKeyringError(CustomBaseException):
    """Python-keyring error occured."""


class AddConnectionCredentialsError(CustomBaseException):
    """Add credentials to connection error."""


class IncorrectCredentialsError(CustomBaseException):
    """Incorrect credentials error."""


class APIAuthenticationError(CustomBaseException):
    """Incorrect credentials error."""


class ImportConnectionError(CustomBaseException):
    """Import connection configurations error."""


class VirtualDeviceNotFound(CustomBaseException):
    """Virtual device could not be found."""


class IllegalVirtualDevice(CustomBaseException):
    """Unexpeced virtual device."""


class AddConnectionFinishError(CustomBaseException):
    """Add connection finish error."""


class StartConnectionFinishError(CustomBaseException):
    """Start connection finish error."""


class StopConnectionFinishError(CustomBaseException):
    """Stop connection finish error."""


class RemoveConnectionFinishError(CustomBaseException):
    """Remove connection finish error."""


class IllegalVPNProtocol(CustomBaseException):
    """Unexpexted plugin for specified protocol."""


class ProtocolPluginNotFound(CustomBaseException):
    """Plugin for specified protocol was not found."""


class ConnectionNotFound(CustomBaseException):
    """ProtonVPN connection not found"""


class ProtocolNotFound(CustomBaseException):
    """Protocol not found upon generate certificate"""


class IllegalAuthData(CustomBaseException):
    """Unexpected AuthData type"""


class JSONAuthDataEmptyError(CustomBaseException):
    """JSON AuthData empty error"""


class JSONAuthDataNoneError(CustomBaseException):
    """JSON AuthData none error"""


class JSONAuthDataError(CustomBaseException):
    """JSON AuthData error"""


class OptimumBackendNotFound(CustomBaseException):
    """Optimum keyring backend not found"""


class SessionError(CustomBaseException):
    """Session error"""


class StoredSessionNotFound(CustomBaseException):
    """Stored session was not found"""


class IllegalServername(CustomBaseException):
    """Unexpected servername"""
