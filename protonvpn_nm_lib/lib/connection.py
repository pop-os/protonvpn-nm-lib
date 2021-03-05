import dbus

from ..enums import MetadataEnum, NetworkManagerConnectionTypeEnum
from ..logger import logger


class ProtonVPNConnection:
    """Connection Class.
    User it to fetch the vpn connection object and/or
    metadata about the VPN connection.

    Exposes methods:
        _get_connection_metadata(
            network_manager_connection_type: NetworkManagerConnectionTypeEnum
        )
        _get_protonvpn_connection(
            network_manager_connection_type: NetworkManagerConnectionTypeEnum
        )

    Description:
    _get_connection_metadata()
        Fetch connection metadata. By default, it searches
        for the VPN within the provided option of connections.

    _get_protonvpn_connection()
        Get active ProtonVPN connection object. If it does not find
        and active connection it means tha the VPN is not running.
        It can though search through all conenctions if
        NetworkManagerConnectionTypeEnum.ALL is passed.
    """
    def __init__(
        self,
        connection_manager,
        connection_metadata
    ):
        self.__connection_manager = connection_manager
        self.__connection_metadata = connection_metadata

    def _get_connection_metadata(
        self,
        network_manager_connection_type=NetworkManagerConnectionTypeEnum.ACTIVE
    ):
        """Get connection metadata of active ProtonVPN connection.

        Returns:
            dict
        """
        connection_exists = self._get_protonvpn_connection(
            network_manager_connection_type
        )

        if len(connection_exists) == 0:
            return {}

        return self.__connection_metadata.get_connection_metadata(
            MetadataEnum.CONNECTION
        )

    def _get_protonvpn_connection(self, network_manager_connection_type):
        """Get ProtonVPN connection.

        Args:
            network_manager_connection_type (NetworkManagerConnectionTypeEnum)

        Returns:
            list
        """
        try:
            return self.__connection_manager.get_protonvpn_connection(
                network_manager_connection_type
            )
        except (dbus.DBusException, Exception) as e:
            logger.exception(e)
            return []
