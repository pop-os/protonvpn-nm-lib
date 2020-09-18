
import json
import os
import time

from lib.constants import CONNECTION_STATE_FILEPATH
from lib.enums import ConnectionMetadataEnum


class ConnectionStateManager():
    FILEPATH = CONNECTION_STATE_FILEPATH

    def save_servername(self, servername):
        """Save connected servername to metadata file.

        Args:
            servername (string): servername [PT#1]
        """
        with open(self.FILEPATH, "w") as f:
            json.dump({ConnectionMetadataEnum.SERVER: servername}, f)

    def save_connected_time(self):
        """Save connected time to metdata file."""
        metadata = self.get_connection_metadata()
        metadata[ConnectionMetadataEnum.CONNECTED_TIME] = str(int(time.time()))

        with open(self.FILEPATH, "w") as f:
            json.dump(metadata, f)

    def get_connection_metadata(self):
        """Get connection state metadata.

        Returns:
            dict
        """
        with open(self.FILEPATH) as f:
            return json.load(f)

    def remove_connection_metadata(self):
        """Remove connection state metadata."""
        os.remove(self.FILEPATH)
