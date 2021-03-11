from .wrapper import keyring_wrapper
from .keyring_adapter import KeyringAdapter
from .keyring_ovpn import KeyringOVPN
from .keyring_proton import KeyringProton
from .keyring_session import KeyringSession

keyring_adapter = KeyringAdapter(keyring_wrapper)
keyring_ovpn = KeyringOVPN.init(keyring_adapter)
keyring_proton = KeyringProton.init(keyring_adapter)
keyring_session = KeyringSession.init(keyring_adapter)
