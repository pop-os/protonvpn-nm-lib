
import time

from ..enums import (ConnectionMetadataEnum, LastConnectionMetadataEnum,
                     MetadataActionEnum, MetadataEnum)
from .metadata_manager import MetadataManager


class ConnectionStateManager(MetadataManager):

    def save_servername(self, servername):
        """Save connected servername metadata.

        Args:
            servername (string): servername [PT#1]
        """
        try:
            last_metadata = self.get_connection_metadata(
                MetadataEnum.LAST_CONNECTION
            )
        except FileNotFoundError:
            last_metadata = {ConnectionMetadataEnum.SERVER: servername}
        else:
            last_metadata[ConnectionMetadataEnum.SERVER] = servername

        real_metadata = {ConnectionMetadataEnum.SERVER: servername}
        self.write_connection_metadata(MetadataEnum.CONNECTION, real_metadata)
        self.write_connection_metadata(
            MetadataEnum.LAST_CONNECTION, last_metadata
        )

    def save_connected_time(self):
        """Save connected time metdata."""
        metadata = self.get_connection_metadata(MetadataEnum.CONNECTION)
        metadata[ConnectionMetadataEnum.CONNECTED_TIME] = str(int(time.time()))
        self.write_connection_metadata(MetadataEnum.CONNECTION, metadata)

    def save_protocol(self, protocol):
        """Save connected protocol.

        Args:
            protocol (ProtocolEnum): TCP|UDP etc
        """
        real_metadata = self.get_connection_metadata(MetadataEnum.CONNECTION)
        last_metadata = self.get_connection_metadata(
            MetadataEnum.LAST_CONNECTION
        )

        real_metadata[ConnectionMetadataEnum.PROTOCOL] = protocol
        last_metadata[LastConnectionMetadataEnum.PROTOCOL] = protocol

        self.write_connection_metadata(MetadataEnum.CONNECTION, real_metadata)
        self.write_connection_metadata(
            MetadataEnum.LAST_CONNECTION, last_metadata
        )

    def save_server_ip(self, ip):
        """Save connected server IP.

        Args:
            IP (list(string)): server IP
        """
        metadata = {
            LastConnectionMetadataEnum.SERVER_IP: ip
        }
        self.write_connection_metadata(MetadataEnum.LAST_CONNECTION, metadata)

    def get_server_ip(self):
        """Get server IP.

        Returns:
            list: contains server IPs
        """
        return self.get_connection_metadata(
            MetadataEnum.LAST_CONNECTION
        )[LastConnectionMetadataEnum.SERVER_IP]

    def get_connection_metadata(self, metadata_type):
        """Get connection state metadata.

        Returns:
            dict: connection metadata
        """
        return self.manage_metadata(
            MetadataActionEnum.GET, metadata_type
        )

    def write_connection_metadata(self, metadata_type, metadata):
        """Save metadata to file.

        Args:
            metadata_type (MetadataEnum): type of metadata to save
            metadata (dict): metadata content
        """
        self.manage_metadata(
            MetadataActionEnum.WRITE,
            metadata_type,
            metadata
        )

    def remove_connection_metadata(self, metadata_type):
        """Remove metadata file.

        Args:
            metadata_type (MetadataEnum): type of metadata to save
        """
        self.manage_metadata(
            MetadataActionEnum.REMOVE,
            metadata_type
        )
