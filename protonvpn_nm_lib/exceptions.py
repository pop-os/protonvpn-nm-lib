class ProtonVPNBaseException(BaseException):
    def __init__(self, message, additional_info=None):
        self.message = message
        self.additional_context = additional_info
        super(ProtonVPNBaseException, self).__init__(self.message)


class FinishError(ProtonVPNBaseException): # noqa
    """Finish async callback error."""


class AddConnectionFinishError(FinishError):
    """Add connection finish error."""


class StartConnectionFinishError(FinishError):
    """Start connection finish error."""


class StopConnectionFinishError(FinishError):
    """Stop connection finish error."""


class RemoveConnectionFinishError(FinishError):
    """Remove connection finish error."""




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


class MissingCacheError(CacheServersError):
    """Missing cache error."""




class KeyringError(ProtonVPNBaseException):  # noqa
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




class IPv6LeakProtectionError(ProtonVPNBaseException): # noqa
    """IPv6 leak protection error."""


class IPv6LeakProtectionOptionError(IPv6LeakProtectionError):
    """IPv6 leak protection option error."""


class EnableIPv6LeakProtectionError(IPv6LeakProtectionError):
    """IPv6 leak protection subprocess add error."""


class DisableIPv6LeakProtectionError(IPv6LeakProtectionError):
    """IPv6 leak protection subprocess delete error."""




class ProtonSessionWrapperError(ProtonVPNBaseException): # noqa
    """Proton session wrapper error."""


class API401Error(ProtonSessionWrapperError):
    """Error 401."""


class API403Error(ProtonSessionWrapperError):
    """Error 403."""


class API429Error(ProtonSessionWrapperError):
    """Error 429."""


class API503Error(ProtonSessionWrapperError):
    """Error 503."""


class API5002Error(ProtonSessionWrapperError):
    """Error 5002."""


class API5003Error(ProtonSessionWrapperError):
    """Error 5003."""


class API8002Error(ProtonSessionWrapperError):
    """Error 8002."""


class API85032Error(ProtonSessionWrapperError):
    """Error 85032."""


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




class KillswitchError(ProtonVPNBaseException): # noqa
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




class ConfigurationsSelectedOptionError(ProtonVPNBaseException): # noqa
    """Selected option error."""


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


class IllegalVPNProtocol(ProtonVPNBaseException):
    """Unexpexted plugin for specified protocol."""


class ProtocolPluginNotFound(ProtonVPNBaseException):
    """Plugin for specified protocol was not found."""


class ConnectionNotFound(ProtonVPNBaseException):
    """ProtonVPN connection not found."""


class ProtocolNotFound(ProtonVPNBaseException):
    """Protocol not found upon generate certificate."""


class IllegalServername(ProtonVPNBaseException):
    """Unexpected servername."""


class EmptyServerListError(ProtonVPNBaseException):
    """Empty server list error."""
