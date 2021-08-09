from abc import ABCMeta, abstractmethod
from ...utils import SubclassesMixin
from ....logger import logger


class APIMetadataBackend(SubclassesMixin, metaclass=ABCMeta):

    @classmethod
    def get_backend(cls, api_metadata_backend="default"):
        subclasses_dict = cls._get_subclasses_dict("api_metadata")
        if api_metadata_backend not in subclasses_dict:
            raise NotImplementedError(
                "API Metadata Backend not implemented"
            )
        logger.info("API metadata backend: {}".format(
            subclasses_dict[api_metadata_backend]
        ))

        return subclasses_dict[api_metadata_backend]()

    @staticmethod
    @abstractmethod
    def save_time_and_url_of_last_original_call():
        """Save time and URL of when last API call was made to original URL.

        Check API_URL constant to determine what is original URL.
        """
        pass

    @staticmethod
    @abstractmethod
    def should_try_original_url():
        """Determine if next api call should use the original URL or not.

        Check API_URL constant to determine what is original URL.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_alternative_url():
        """Get stored URL."""
        pass
