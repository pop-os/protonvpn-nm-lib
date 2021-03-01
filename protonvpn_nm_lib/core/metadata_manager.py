import json
import os

from ..constants import (CACHE_METADATA_FILEPATH, CONNECTION_STATE_FILEPATH,
                         LAST_CONNECTION_METADATA_FILEPATH)
from ..enums import MetadataEnum, MetadataActionEnum
from .. import exceptions
from ..logger import logger


class MetadataManager():
    METADATA_DICT = {
        MetadataEnum.CONNECTION: CONNECTION_STATE_FILEPATH,
        MetadataEnum.LAST_CONNECTION: LAST_CONNECTION_METADATA_FILEPATH,
        MetadataEnum.SERVER_CACHE: CACHE_METADATA_FILEPATH
    }

    def manage_metadata(self, action, metadata_type, metadata=None):
        """Metadata manager."""
        logger.debug(
            "Metadata manager \"action: {} - Metadata type: {}\"".format(
                action,
                metadata_type
            )
        )
        metadata_action_dict = {
            MetadataActionEnum.GET: self.get_metadata_from_file,
            MetadataActionEnum.WRITE: self.write_metadata_to_file,
            MetadataActionEnum.REMOVE: self.remove_metadata_file
        }

        if action not in metadata_action_dict:
            raise exceptions.IllegalMetadataActionError(
                "Illegal {} metadata action".format(action)
            )

        self.ensure_metadata_type_is_valid(metadata_type)

        metadata_from_file = metadata_action_dict[action](
            metadata_type, metadata
        )
        return metadata_from_file

    def get_metadata_from_file(self, metadata_type, _):
        """Get state metadata.

        Returns:
            json/dict
        """
        logger.debug("Getting metadata from \"{}\"".format(metadata_type))
        with open(self.METADATA_DICT[metadata_type]) as f:
            metadata = json.load(f)
            logger.debug("Successfully fetched metadata from file")
            return metadata

    def write_metadata_to_file(self, metadata_type, metadata):
        """Save metadata to file."""
        with open(self.METADATA_DICT[metadata_type], "w") as f:
            json.dump(metadata, f)
            logger.debug(
                "Successfully saved metadata to \"{}\"".format(metadata_type)
            )

    def remove_metadata_file(self, metadata_type, _):
        """Remove metadata file."""
        filepath = self.METADATA_DICT[metadata_type]

        if os.path.isfile(filepath):
            os.remove(filepath)

    def ensure_metadata_type_is_valid(self, metadata_type):
        """Check metedata type."""
        logger.debug("Checking if {} is valid".format(metadata_type))
        if metadata_type not in self.METADATA_DICT:
            raise exceptions.IllegalMetadataTypeError(
                "Metadata type not found"
            )
        logger.debug("\"{}\" is valid metadata type".format(metadata_type))

    def check_metadata_exists(self, metadata_type):
        """Check if metadata file exists."""
        logger.debug("Checking if \"{}\" exists".format(metadata_type))
        self.ensure_metadata_type_is_valid(metadata_type)

        metadata_exists = False
        if os.path.isfile(self.METADATA_DICT[metadata_type]):
            metadata_exists = True

        logger.debug(
            "Metadata \"{}\" \"{}\"".format(
                metadata_type,
                ("exists" if metadata_exists else "does not exist")
            )
        )
        return metadata_exists
