
import time

from ...enums import (ConnectionMetadataEnum, LastConnectionMetadataEnum,
                      MetadataActionEnum, MetadataEnum)
from ...logger import logger
from .metadata import Metadata
from .connection_metadata_backend import ConnectionMetadataBackend


class ConnectionMetadata(ConnectionMetadataBackend):
    """
    Read/Write connection metadata. Stores
    metadata about the current connection
    for displaying connection status and also
    stores for metadata for future reconnections.
    """
    connection_metadata = "default"

    def __init__(self, metadata=None):
        super().__init__()
        self.metadata = metadata or Metadata()

    def save_servername(self, servername):
        """Save connected servername metadata.

        Args:
            servername (string): servername [PT#1]
        """
        last_metadata = self.get_connection_metadata(
            MetadataEnum.LAST_CONNECTION
        )
        real_metadata = self.get_connection_metadata(
            MetadataEnum.CONNECTION
        )

        real_metadata[ConnectionMetadataEnum.SERVER.value] = servername
        last_metadata[ConnectionMetadataEnum.SERVER.value] = servername

        logger.info("Saving servername \"{}\" on \"{}\"".format(
            servername, MetadataEnum.CONNECTION
        ))
        self.__write_connection_metadata(
            MetadataEnum.CONNECTION, real_metadata
        )

        logger.info("Saving servername \"{}\" on \"{}\"".format(
            servername, MetadataEnum.LAST_CONNECTION
        ))
        self.__write_connection_metadata(
            MetadataEnum.LAST_CONNECTION, last_metadata
        )

    def save_connect_time(self):
        """Save connected time metdata."""
        metadata = self.get_connection_metadata(MetadataEnum.CONNECTION)
        metadata[ConnectionMetadataEnum.CONNECTED_TIME.value] = str(
            int(time.time())
        )
        self.__write_connection_metadata(MetadataEnum.CONNECTION, metadata)
        logger.info("Saved connected time to file")

    def save_protocol(self, protocol):
        """Save connected protocol.

        Args:
            protocol (ProtocolEnum): TCP|UDP etc
        """
        real_metadata = self.get_connection_metadata(MetadataEnum.CONNECTION)
        last_metadata = self.get_connection_metadata(
            MetadataEnum.LAST_CONNECTION
        )
        real_metadata[ConnectionMetadataEnum.PROTOCOL.value] = protocol.value
        last_metadata[LastConnectionMetadataEnum.PROTOCOL.value] = protocol.value # noqa

        logger.info("Saving protocol \"{}\" on \"{}\"".format(
            protocol, MetadataEnum.CONNECTION
        ))
        self.__write_connection_metadata(
            MetadataEnum.CONNECTION, real_metadata
        )

        logger.info("Saving protocol \"{}\" on \"{}\"".format(
            protocol, MetadataEnum.LAST_CONNECTION
        ))
        self.__write_connection_metadata(
            MetadataEnum.LAST_CONNECTION, last_metadata
        )
        logger.info("Saved protocol to file")

    def save_display_server_ip(self, ip):
        real_metadata = self.get_connection_metadata(MetadataEnum.CONNECTION)
        real_metadata[ConnectionMetadataEnum.DISPLAY_SERVER_IP.value] = ip

        logger.info("Saving exit server IP \"{}\" on \"{}\"".format(
            ip, MetadataEnum.CONNECTION
        ))
        self.__write_connection_metadata(
            MetadataEnum.CONNECTION, real_metadata
        )

        logger.info("Saved exit ip to file")

    def save_server_ip(self, ip):
        """Save connected server IP.

        Args:
            IP (string): server IP
        """
        last_metadata = self.get_connection_metadata(
            MetadataEnum.LAST_CONNECTION
        )
        last_metadata[LastConnectionMetadataEnum.SERVER_IP.value] = ip
        logger.info("Saving server ip \"{}\" on \"{}\"".format(
            ip, MetadataEnum.LAST_CONNECTION
        ))
        self.__write_connection_metadata(
            MetadataEnum.LAST_CONNECTION, last_metadata
        )
        logger.info("Saved server IP to file")

    def get_server_ip(self):
        """Get server IP.

        Returns:
            list: contains server IPs
        """
        logger.info("Getting server IP")
        return self.get_connection_metadata(
            MetadataEnum.LAST_CONNECTION
        )[LastConnectionMetadataEnum.SERVER_IP.value]

    def get_connection_metadata(self, metadata_type):
        """Get connection state metadata.

        Args:
            metadata_type (MetadataEnum): type of metadata to save

        Returns:
            dict: connection metadata
        """
        try:
            return self.metadata.manage_metadata(
                MetadataActionEnum.GET, metadata_type
            )
            print("Return all")
        except FileNotFoundError:
            print("Returning empty")
            return {}

    def __write_connection_metadata(self, metadata_type, metadata):
        """Save metadata to file.

        Args:
            metadata_type (MetadataEnum): type of metadata to save
            metadata (dict): metadata content
        """
        self.metadata.manage_metadata(
            MetadataActionEnum.WRITE,
            metadata_type,
            metadata
        )

    def remove_connection_metadata(self, metadata_type):
        """Remove metadata file.

        Args:
            metadata_type (MetadataEnum): type of metadata to save
        """
        self.metadata.manage_metadata(
            MetadataActionEnum.REMOVE,
            metadata_type
        )
