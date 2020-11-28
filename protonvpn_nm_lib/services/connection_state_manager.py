
import time

from ..enums import ConnectionMetadataEnum, MetadataEnum, MetadataActionEnum
from .metadata_manager import MetadataManager


class ConnectionStateManager(MetadataManager):

    def save_servername(self, servername):
        """Save connected servername metadata.

        Args:
            servername (string): servername [PT#1]
        """
        metadata = {ConnectionMetadataEnum.SERVER: servername}
        self.write_connection_metadata(MetadataEnum.CONNECTION, metadata)
        self.write_connection_metadata(MetadataEnum.LAST_CONNECTION, metadata)

    def save_connected_time(self):
        """Save connected time metdata."""
        metadata = self.get_connection_metadata(MetadataEnum.CONNECTION)
        metadata[ConnectionMetadataEnum.CONNECTED_TIME] = str(int(time.time()))
        self.write_connection_metadata(MetadataEnum.CONNECTION, metadata)

    def save_protocol(self, protocol):
        metadata = self.get_connection_metadata(MetadataEnum.CONNECTION)
        metadata[ConnectionMetadataEnum.PROTOCOL] = protocol
        self.write_connection_metadata(MetadataEnum.CONNECTION, metadata)

    def save_server_ip(self, ip):
        metadata = {
            "last_connect_ip": ip
        }
        self.write_connection_metadata(MetadataEnum.LAST_CONNECTION, metadata)

    def get_server_ip(self):
        return self.get_connection_metadata(
            MetadataEnum.LAST_CONNECTION
        )["last_connect_ip"]

    def get_connection_metadata(self, metadata_type):
        """Get connection state metadata.

        Returns:
            dict
        """
        return self.manage_metadata(
            MetadataActionEnum.GET, metadata_type
        )

    def write_connection_metadata(self, metadata_type, metadata):
        """Save metadata to file."""
        self.manage_metadata(
            MetadataActionEnum.WRITE,
            metadata_type,
            metadata
        )

    def remove_connection_metadata(self, metadata_type):
        """Remove metadata file."""
        self.manage_metadata(
            MetadataActionEnum.REMOVE,
            metadata_type
        )
