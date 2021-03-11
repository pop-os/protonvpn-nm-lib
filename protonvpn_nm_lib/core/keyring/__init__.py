from .wrapper import keyring_wrapper
from .keyring_adapter import KeyringAdapter
from .keyring_ovpn import KeyringOVPN # noqa
from .keyring_proton import KeyringProton # noqa
from .keyring_session import KeyringSession # noqa

keyring_adapter = KeyringAdapter(keyring_wrapper)
