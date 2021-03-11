from .keyring_backend import KeyringBackend
from .keyring_wrapper import KeyringWrapper

# Only static methods are to be used from KeyringBackend
# as it is passed uninstantiated
keyring_backend = KeyringBackend
keyring_wrapper = KeyringWrapper(keyring_backend)
