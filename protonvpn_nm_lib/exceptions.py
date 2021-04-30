class ProtonVPNException(BaseException):
    def __init__(self, message, additional_info=None):
        self.message = message
        self.additional_context = additional_info
        super(ProtonVPNException, self).__init__(self.message)


class APISessionIsNotValidError(ProtonVPNException):
    """
    This exception is raised when a call requires a valid Proton API session,
    but we currently don't have one. This can be solved by doing a new login.
    """


class DBusException(ProtonVPNException):
    """DBus exception."""

class FinishError(DBusException): # noqa
    """Finish async callback error."""


class AddConnectionFinishError(DBusException):
    """Add connection finish error."""


class StartConnectionFinishError(DBusException):
    """Start connection finish error."""


class StopConnectionFinishError(DBusException):
    """Stop connection finish error."""


class RemoveConnectionFinishError(DBusException):
    """Remove connection finish error."""




class IllegalData(ProtonVPNException): # noqa
    """Illegal/unexpected data type"""


class IllegalSessionData(IllegalData):
    """Illegal/unexpected SessionData type"""


class IllegalUserData(IllegalData):
    """Illegal/unexpected UserData type"""



class JSONError(ProtonVPNException): # noqa
    """JSON generated errors"""


class JSONDataEmptyError(JSONError):
    """JSON SessionData empty error"""


class JSONDataNoneError(JSONError):
    """JSON SessionData none error"""


class JSONDataError(JSONError):
    """JSON SessionData error"""



class CacheError(ProtonVPNException): # noqa
    """Cache error base exception"""


class CacheServersError(CacheError):
    """Cache servers error"""


class CacheLogicalServersError(CacheServersError):
    """Cache logical servers error"""


class CacheLogicalServersFallbackError(CacheServersError):
    """Cache logical servers fallback error"""


class ServerCacheNotFound(CacheServersError):
    """Server cache was not found."""


class DefaultOVPNPortsNotFoundError(CacheError):
    """Default OpenVPN ports not found.
    Either cache is missing or unable to fetch from API.
    """



class KeyringError(ProtonVPNException):  # noqa
    """Keyring error"""


class OptimumBackendNotFound(KeyringError):
    """Optimum keyring backend not found"""


class AccessKeyringError(KeyringError):
    """Access keyring error."""


class KeyringDataNotFound(KeyringError): # noqa
    """Keyring data not found"""


class StoredSessionNotFound(KeyringDataNotFound):
    """Stored session was not found"""


class StoredUserDataNotFound(KeyringDataNotFound):
    """Stored user data was not found"""


class StoredProtonUsernameNotFound(KeyringDataNotFound):
    """Stored user data was not found"""


class UserSessionNotFound(KeyringError):
    """User session not found."""


class IPv6LeakProtectionError(ProtonVPNException): # noqa
    """IPv6 leak protection error."""


class IPv6LeakProtectionOptionError(IPv6LeakProtectionError):
    """IPv6 leak protection option error."""


class EnableIPv6LeakProtectionError(IPv6LeakProtectionError):
    """IPv6 leak protection subprocess add error."""


class DisableIPv6LeakProtectionError(IPv6LeakProtectionError):
    """IPv6 leak protection subprocess delete error."""




class ProtonSessionWrapperError(ProtonVPNException): # noqa
    """Proton session wrapper error."""


class API401Error(ProtonSessionWrapperError):
    """Error 401.
    
    Access token is invalid and should be refreshed.
    """


class API403Error(ProtonSessionWrapperError):
    """Error 403.

    Missing scopes. Client needs to re-authenticate.
    """


class API429Error(ProtonSessionWrapperError):
    """Error 429.

    Too many requests, try after time specified
    in header.
    """


class API503Error(ProtonSessionWrapperError):
    """Error 503.

    API unreacheable/unavailable, retry connecting to API.
    """


class API5002Error(ProtonSessionWrapperError):
    """Error 5002.

    Version is invalid.
    """


class API5003Error(ProtonSessionWrapperError):
    """Error 5003.

    Version is bad.
    """


class API8002Error(ProtonSessionWrapperError):
    """Error 8002.

    Wrong password.
    """


class API10013Error(ProtonSessionWrapperError):
    """Error 10013.

    Refresh token is invalid, re-authentication is required.
    """


class APITimeoutError(ProtonSessionWrapperError):
    """API timeout error."""


class ProtonSessionAPIError(ProtonSessionWrapperError):
    """Proton session API error."""


class APIError(ProtonSessionWrapperError):
    """API error."""


class UnhandledAPIError(ProtonSessionWrapperError):
    """Unhandled API error."""


class UnhandledAPIMethod(ProtonSessionWrapperError):
    """Unhandled API method error."""


class UnreacheableAPIError(ProtonSessionAPIError):
    """APIBlockError"""


class InternetConnectionError(ProtonSessionAPIError):
    """Internet connection error"""




class KillswitchError(ProtonVPNException): # noqa
    """Killswitch error."""


class KillswitchOptionError(KillswitchError):
    """Killswitch option error."""


class CreateKillswitchError(KillswitchError):
    """Create killswitch error"""


class CreateRoutedKillswitchError(CreateKillswitchError):
    """Create routed killswitch error"""


class CreateBlockingKillswitchError(CreateKillswitchError):
    """Create routed killswitch error"""


class DeleteKillswitchError(KillswitchError):
    """Delete killswitch error."""


class ActivateKillswitchError(KillswitchError):
    """Activate killswitch error."""


class DectivateKillswitchError(KillswitchError):
    """Deactivate killswitch error."""


class AvailableConnectivityCheckError(KillswitchError):
    """Available connectivity check error."""


class DisableConnectivityCheckError(KillswitchError):
    """Disable connectivity check error."""




class MetadataError(ProtonVPNException): # noqa
    """Metadata error."""


class IllegalMetadataActionError(MetadataError):
    """Illegal/unexpected metadata action error."""


class IllegalMetadataTypeError(MetadataError):
    """Illegal/unexpected metadata type error."""



class ConfigurationsSelectedOptionError(ProtonVPNException): # noqa
    """Selected option error."""


class AddConnectionCredentialsError(ProtonVPNException):
    """Add credentials to connection error."""


class AddServerCertificateCheckError(ProtonVPNException):
    """Add server certificate check error"""


class IncorrectCredentialsError(ProtonVPNException):
    """Incorrect credentials error."""


class APIAuthenticationError(ProtonVPNException):
    """API authentication error."""


class ImportConnectionError(ProtonVPNException):
    """Import connection configurations error."""


class VirtualDeviceNotFound(ProtonVPNException):
    """Virtual device could not be found."""


class IllegalVirtualDevice(ProtonVPNException):
    """Unexpeced virtual device."""


class IllegalVPNProtocol(ProtonVPNException):
    """Unexpexted plugin for specified protocol."""


class ProtocolPluginNotFound(ProtonVPNException):
    """Plugin for specified protocol was not found."""


class ConnectionNotFound(ProtonVPNException):
    """ProtonVPN connection not found."""


class ProtocolNotFound(ProtonVPNException):
    """Protocol not found upon generate certificate."""


class IllegalServername(ProtonVPNException):
    """Unexpected servername."""


class InvalidCountryCode(ProtonVPNException):
    """Illegal country code."""


class InvalidUsernameFormat(ProtonVPNException):
    """Invalid username format."""



class ServerListError(ProtonVPNException): # noqa
    """Server list error."""


# class Server


class EmptyServerListError(ServerListError):
    """Empty server list error."""


class FastestServerNotFound(EmptyServerListError):
    """Fastest server not found."""


class FastestServerInCountryNotFound(EmptyServerListError):
    """Fastest server in specified country not found."""


class FeatureServerNotFound(EmptyServerListError):
    """Server with specified feature was not found."""


class ServernameServerNotFound(EmptyServerListError):
    """Server with specified servername not found."""


class RandomServerNotFound(EmptyServerListError):
    """Random server not found."""
