
import json
import os
import time

from lib.constants import CONNECTION_STATE_FILEPATH
from lib.enums import ConnectionMetadataEnum


class ConnectionStateManager():
    FILEPATH = CONNECTION_STATE_FILEPATH

    def save_servername(self, servername):
        """Save connected servername metadata.

        Args:
            servername (string): servername [PT#1]
        """
        metadata = {ConnectionMetadataEnum.SERVER: servername}
        self.write_to_file(metadata)

    def save_connected_time(self):
        """Save connected time metdata."""
        metadata = self.get_connection_metadata()
        metadata[ConnectionMetadataEnum.CONNECTED_TIME] = str(int(time.time()))
        self.write_to_file(metadata)

    def save_protocol(self, protocol):
        metadata = self.get_connection_metadata()
        metadata[ConnectionMetadataEnum.PROTOCOL] = protocol
        self.write_to_file(metadata)

    def get_connection_metadata(self):
        """Get connection state metadata.

        Returns:
            dict
        """
        with open(self.FILEPATH) as f:
            return json.load(f)

    def write_to_file(self, metadata):
        """Save metadata to file."""
        with open(self.FILEPATH, "w") as f:
            json.dump(metadata, f)

    def remove_connection_metadata(self):
        """Remove metadata file."""
        os.remove(self.FILEPATH)
