from ..logger import logger
from ..enums import MetadataEnum, ConnectionMetadataEnum, ConnectionTypeEnum


class ProtonVPNReconnect:
    """Reconnect Class.
    Use it to reconnect to previously connected server.

    Exposes method:
        _setup_reconnect()

    Description:
    _setup_reconnect()
        Simillar to connect._setup_connection(). Use it before
        attempting to connect to VPN via connect._connect().
    """
    def __init__(self, connect, server_manager, user_conf_manager):
        # library
        self.connect = connect

        # services
        self.__server_manager = server_manager
        self.__user_conf_manager = user_conf_manager

    def _setup_reconnection(self):
        """Setup connection to reconnect to previously connected server.

        Returns:
            dict: connect._setup_connection()
        """
        logger.info("Attemtping to recconnect to previous server")
        self.__server_manager.killswitch_status = self.__user_conf_manager.killswitch # noqa
        last_connection_metadata = self.__get_last_connection_metadata()

        try:
            previous_server = last_connection_metadata[
                ConnectionMetadataEnum.SERVER.value
            ]
        except KeyError:
            logger.error(
                "File exists but servername field is missing, exitting"
            )
            raise Exception(
                "No previous connection data was found, "
                "please first connect to a server."
            )

        try:
            protocol = last_connection_metadata[
                ConnectionMetadataEnum.PROTOCOL.value
            ]
        except KeyError:
            protocol = None

        logger.info("Passed all check, will reconnecto to \"{}\"".format(
            previous_server
        ))

        connection_info = self.connect._setup_connection(
            connection_type=ConnectionTypeEnum.SERVERNAME,
            connection_type_extra_arg=previous_server,
            protocol=protocol
        )

        return connection_info

    def __get_last_connection_metadata(self):
        """Get metadata of last made connection.

        Returns:
            dict
        """
        try:
            return self.__server_manager.get_connection_metadata(
                MetadataEnum.LAST_CONNECTION
            )
        except FileNotFoundError as e:
            logger.exception(e)
            return {}
