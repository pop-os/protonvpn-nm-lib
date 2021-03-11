from ...enums import KeyringEnum


class KeyringProton:
    """KeyringProton class.

    This class is an abstraction of KeyringAdapter. It should be
    used only to manage Proton username entry.
    """
    keyring_proton_user = KeyringEnum.DEFAULT_KEYRING_PROTON_USER.value
    _keyring_dict_key = "proton_username"

    def __init__(self, keyring_adapter):
        self.keyring_adapter = keyring_adapter
        self._protonvpn_username = None

    @property
    def protonvpn_username(self):
        return self._protonvpn_username

    @staticmethod
    def init(keyring_adapter):
        """Static method to initialize KeyringProton.

        Args:
            keyring_adapter (KeyringAdapter):
            can also be passed some other alternative
            implementation of a keyring.
        """
        keyring_proton = KeyringProton(keyring_adapter)
        keyring_proton.reload_properties()

        return keyring_proton

    def store(self, username):
        """Store ProtonVPN username.

        Instance properties are automatically updated once, so it is not
        needed to run self.reload_properties().

        Args:
            username (str)
        """
        self._protonvpn_username = username
        data = {self._keyring_dict_key: self._protonvpn_username}

        self.keyring_adapter.store_data(data, self.keyring_proton_user)

    def reload_properties(self):
        """Reload class proprties.

        This methods gets the stored data and updates the properties
        if its instance.
        """
        stored_user_data = self.keyring_adapter.get_stored_data(
            self.keyring_proton_user,
        )
        self._protonvpn_username = stored_user_data.get(
            self._keyring_dict_key, None
        )

    def delete(self):
        """Delete proton entry.

        Session is deleted via the keyring adapater.
        """
        self.keyring_adapter.delete_stored_data(self.keyring_proton_user)
        self._protonvpn_username = None
