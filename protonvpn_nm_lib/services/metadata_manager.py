import json
import os

from ..constants import (CACHE_METADATA_FILEPATH, CONNECTION_STATE_FILEPATH,
                         LAST_CONNECTION_METADATA_FILEPATH)
from ..enums import MetadataEnum, MetadataActionEnum
from .. import exceptions


class MetadataManager():
    METADATA_DICT = {
        MetadataEnum.CONNECTION: CONNECTION_STATE_FILEPATH,
        MetadataEnum.LAST_CONNECTION: LAST_CONNECTION_METADATA_FILEPATH,
        MetadataEnum.SERVER_CACHE: CACHE_METADATA_FILEPATH
    }

    def manage_metadata(self, action, metadata_type, metadata=None):
        """Metadata manager."""
        metadata_action_dict = {
            MetadataActionEnum.GET: self.get_metadata_from_file,
            MetadataActionEnum.WRITE: self.write_metadata_to_file,
            MetadataActionEnum.REMOVE: self.remove_metadata_file
        }

        if action not in metadata_action_dict:
            raise exceptions.IllegalMetadataActionError(
                "Illegal {} metadata action".format(action)
            )

        self.check_metadata_type(metadata_type)

        return metadata_action_dict[action](metadata_type, metadata)

    def get_metadata_from_file(self, metadata_type, _):
        """Get state metadata.

        Returns:
            json/dict
        """
        with open(self.METADATA_DICT[metadata_type]) as f:
            return json.load(f)

    def write_metadata_to_file(self, metadata_type, metadata):
        """Save metadata to file."""
        with open(self.METADATA_DICT[metadata_type], "w") as f:
            json.dump(metadata, f)

    def remove_metadata_file(self, metadata_type, _):
        """Remove metadata file."""
        filepath = self.METADATA_DICT[metadata_type]

        if os.path.isfile(filepath):
            os.remove(filepath)

    def check_metadata_type(self, metadata_type):
        """Check for metedata type."""
        if metadata_type not in self.METADATA_DICT:
            raise exceptions.IllegalMetadataTypeError(
                "Metadata type not found"
            )
