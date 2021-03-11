from ... import exceptions
from ...logger import logger


class KeyringAdapter:
    """KeyringAdapter class.

    This class is used to store, load and delete data related
    to a user session. Its uses a keyring wrapper to do all
    those actions.

    If you desire to use an alternate keyring system,
    then provide a class to KeyringAdapter which
    implements the following methods:
        get_entry(key_entry)
        add_entry(key_entry, data)
        delete_entry(key_entry)

    Where @key_entry is a string, that:
     - if saved to file, it will act as a dict key, where
        the data should be stored;
     - if saved to a keyring system, it will be saved to this
        specific keyring entry name.
    """
    def __init__(self, keyring_wrapper):
        self.keyring_wrapper = keyring_wrapper
        # current_DE = str(os.getenv("XDG_CURRENT_DESKTOP"))
        # logger.info("Current DE: \"{}\"".format(current_DE))

    def store_data(self, data, key_entry):
        """Store data to specified key entry.

        Args:
            data (dict): data to be stored
            key_entry (string)
        """
        logger.info("Storing {}".format(key_entry))
        self.ensure_data_is_dict_format(data)
        if data is None or len(data) < 1:
            logger.error(
                "IllegalData: Expected dict. "
                + "Raising exception."
            )
            raise exceptions.IllegalData(
                "Unexpected object type {} (expected dict)".format(
                    data
                )
            )

        self.keyring_wrapper.add_entry(key_entry, data)

    def get_stored_data(self, key_entry):
        """Get stored data from specified key entry.

        Args:
            key_entry (string)
        Returns:
            json: json encoded data
        """

        try:
            stored_data = self.keyring_wrapper.get_entry(key_entry)
        except (Exception, exceptions.JSONError) as e:
            logger.exception(e)
            return {}

        # self.ensure_data_is_dict_format(stored_data)
        return stored_data

    def delete_stored_data(self, key_entry):
        """Delete stored data specified key entry.

        Args:
            key_entry (string)
        """
        logger.info("Deleting stored {}".format(key_entry))
        self.keyring_wrapper.delete_entry(key_entry)

    def ensure_data_is_dict_format(self, data):
        if not isinstance(data, dict):
            msg = "Provided data {} is not a valid type (expect {})".format(
                data, dict
            )

            logger.error(msg)
            raise TypeError(msg)
