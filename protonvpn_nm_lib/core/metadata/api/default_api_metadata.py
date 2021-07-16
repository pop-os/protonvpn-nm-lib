
import json
import os
import time

from .... import exceptions
from ....constants import API_METADATA_FILEPATH, API_URL
from ....enums import MetadataActionEnum, MetadataEnum, APIMetadataEnum
from ....logger import logger
from .api_metadata_backend import APIMetadataBackend


class APIMetadata(APIMetadataBackend):
    """
    Read/Write API metadata. Stores
    metadata about the current connection
    for displaying connection status and also
    stores for metadata for future reconnections.
    """
    api_metadata = "default"
    METADATA_DICT = {
        MetadataEnum.API: API_METADATA_FILEPATH
    }
    ONE_DAY_IN_SECONDS = 86400

    def save_time_and_url_of_last_original_call(self, url):
        """Save connected time metadata."""
        metadata = self.get_connection_metadata(MetadataEnum.API)
        metadata[APIMetadataEnum.LAST_API_CALL_TIME.value] = str(
            int(time.time())
        )
        metadata[APIMetadataEnum.URL.value] = url

        self.__write_metadata(MetadataEnum.API, metadata)
        logger.info("Saved last API attempt with original URL")

    def should_use_original_url(self):
        """Determine if next api call should use the original URL or not.

        Check API_URL constant to determine what is original URL.
        """
        try:
            time_since_last_original_api = int(
                self.get_connection_metadata(MetadataEnum.API)[
                    APIMetadataEnum.LAST_API_CALL_TIME.value
                ]
            )
        except KeyError:
            time_since_last_original_api = int(time.time())

        if (time_since_last_original_api + self.ONE_DAY_IN_SECONDS) > time.time():
            return False

        return True

    def get_alternative_url(self):
        """Get alternative URL form metadata file."""
        try:
            return self.get_connection_metadata(MetadataEnum.API)[APIMetadataEnum.URL.value]
        except KeyError:
            return API_URL

    def get_connection_metadata(self, metadata_type):
        """Get connection state metadata.

        Args:
            metadata_type (MetadataEnum): type of metadata to save

        Returns:
            dict: connection metadata
        """
        try:
            return self.manage_metadata(
                MetadataActionEnum.GET, metadata_type
            )
        except FileNotFoundError:
            return {}

    def __write_metadata(self, metadata_type, metadata):
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

    def remove_all_metadata(self):
        """Remove all metadata connection files."""
        self.manage_metadata(
            MetadataActionEnum.REMOVE,
            MetadataEnum.CONNECTION
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
