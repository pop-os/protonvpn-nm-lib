from ..keyring.init import keyring_session, keyring_ovpn, keyring_proton
from .proton_session_wrapper import ProtonSessionWrapper
from .session import Session


# proton_session_wrapper is
# an uninstatiated ProtonSessionWrapper object
proton_session_wrapper = ProtonSessionWrapper
session = Session(
    proton_session_wrapper, keyring_session,
    keyring_ovpn, keyring_proton
)
