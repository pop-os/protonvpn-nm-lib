import dbus

from .. import exceptions
from ..enums import MetadataEnum, NetworkManagerConnectionTypeEnum
from ..logger import logger


class ProtonVPNConnection:

    def __init__(
        self,
        connection_manager,
        user_conf_manager,
        ks_manager,
        ipv6_lp_manager,
        reconector_manager
    ):
        self.connection_manager = connection_manager
        self.user_conf_manager = user_conf_manager
        self.ks_manager = ks_manager
        self.ipv6_lp_manager = ipv6_lp_manager
        self.reconector_manager = reconector_manager

    def _get_connection_metadata(
        self,
        network_manager_connection_type=NetworkManagerConnectionTypeEnum.ACTIVE
    ):
        """Get connection metadata.

        Args:
            network_manager_connection_type (NetworkManagerConnectionTypeEnum)
                default: ACTIVE, but ALL can be used to access metadata
                if the current connection is not active.

        Returns:
            dict
        """
        connection_exists = self.connection_manager.get_protonvpn_connection(
            network_manager_connection_type
        )

        if not connection_exists[0]:
            return {}

        return self.connection_manager.get_connection_metadata(
            MetadataEnum.CONNECTION
        )

    def _remove_protonvpn_connection(self):
        """Remove ProtonVPN connection."""
        try:
            self.connection_manager.remove_connection(
                self.user_conf_manager,
                self.ks_manager,
                self.ipv6_lp_manager,
                self.reconector_manager
            )
        except exceptions.ConnectionNotFound:
            pass

    def _get_protonvpn_connection(self, network_manager_connection_type):
        """Get ProtonVPN connection.

        Args:
            network_manager_connection_type (NetworkManagerConnectionTypeEnum)

        Returns:
            list
        """
        try:
            return self.connection_manager.get_protonvpn_connection(
                network_manager_connection_type
            )
        except (dbus.DBusException, Exception) as e:
            logger.exception(e)
            return []

    def _ensure_connectivity(self):
        # check if there is internet connectivity
        try:
            self.connection_manager.is_internet_connection_available(
                self.user_conf_manager.killswitch
            )
        except exceptions.InternetConnectionError as e:
            raise Exception("\n{}".format(e))
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            raise Exception(e)

        # check if API is reachable
        try:
            self.connection_manager.is_api_reacheable(
                self.user_conf_manager.killswitch
            )
        except exceptions.APITimeoutError as e:
            raise Exception(
                "{}".format(e)
            )
        except exceptions.UnreacheableAPIError as e:
            raise Exception(
                "{}".format(e)
            )
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            raise Exception("{}".format(e))
