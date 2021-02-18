from .logger import logger
from .enums import MetadataEnum, ConnectionMetadataEnum, ConnectionTypeEnum


class Reconnect():

    def setup_reconnect(self):
        """Reconnect to previously connected server."""
        logger.info("Attemtping to recconnect to previous server")
        self.get_existing_session()
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
            self.protocol = last_connection_metadata[
                ConnectionMetadataEnum.PROTOCOL.value
            ]
        except KeyError:
            self.protocol = None

        if not self.is_protocol_valid() or self.protocol is None:
            self.protocol = self.user_conf_manager.default_protocol

        self.connect_type = ConnectionTypeEnum.SERVERNAME
        self.connect_type_extra_arg = previous_server

        logger.info("Passed all check, will reconnecto to \"{}\"".format(
            previous_server
        ))

        self.setup_connection(servername=previous_server)
        connection_info = self.setup_connection()

        return connection_info

    def __get_last_connection_metadata(self):
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
