from ..logger import logger
from ..enums import MetadataEnum, ConnectionMetadataEnum, ConnectionTypeEnum


class Reconnect():
    """Reconnect Class

    Exposes one method _setup_reconnect(), that should be
    used before attempting to connect.
    To connect to VPN, the exposed method provided
    by connect._connect(), can be used.
    """
    def _setup_reconnect(self):
        """Public method.

        Setup connection to reconnect to previously connected server.
        """
        logger.info("Attemtping to recconnect to previous server")
        self.server_manager.killswitch_status = self.user_conf_manager.killswitch # noqa
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

        # Public method provided by connect.py
        connection_info = self._setup_connection(
            connection_type=ConnectionTypeEnum.SERVERNAME,
            connection_type_extra_arg=previous_server,
            protocol=protocol
        )

        return connection_info

    def __get_last_connection_metadata(self):
        """Private method.

        Get metadata of last made connection.
        """
        try:
            return self.server_manager.get_connection_metadata(
                MetadataEnum.LAST_CONNECTION
            )
        except FileNotFoundError:
            logger.error("No previous connection data was found, exitting")
            raise Exception(
                "No previous connection data was found, "
                "please first connect to a server."
            )
