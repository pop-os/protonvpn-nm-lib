from .. import exceptions
from ..logger import logger
from ..services.proton_session_wrapper import ProtonSessionWrapper


class ProtonVPNSession:

    def __init__(self, user_manager):
        self.user_manager = user_manager

    def _get_session(self):
        """Get user session.

        Returns:
            ProtonSessionWrapper
        """
        try:
            return self.__get_existing_session()
        except exceptions.StoredSessionNotFound as e:
            raise exceptions.StoredSessionNotFound(e)
        except exceptions.IllegalSessionData as e:
            raise exceptions.IllegalSessionData(e)
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)

    def _check_session_exists(self):
        """Check if sessions exists.

        Returns:
            bool
        """
        try:
            return self.__get_existing_session(return_bool=True)
        except (exceptions.ProtonVPNException, Exception):
            return False

    def _ensure_session_is_valid(self, session):
        """Ensure that provided session is valid.

        Args:
            session (proton.api.Session): current user session
        """
        logger.info("Validating session")

        if not isinstance(session, ProtonSessionWrapper):
            err_msg = "Incorrect object type, "\
                "{} is expected "\
                "but got {} instead".format(
                    ProtonSessionWrapper, session
                )
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise TypeError(err_msg)

    def __get_existing_session(
        self, return_bool=False
    ):
        """Private method.

        Gets the session. Default behaviour is
        return the session. It can also return bool
        if return_bool=True, returning True if session exists,
        False otherwise.

        Args:
            return_bool (bool):
                (optional) should be true if
                boolean is value requested.
        """
        logger.info("Attempting to get existing session")
        session = None
        try:
            session = self.user_manager.load_session()
        except exceptions.JSONDataEmptyError:
            raise exceptions.IllegalSessionData(
                "The stored session might be corrupted. "
                + "Please, try to login again."
            )
        except (
            exceptions.JSONDataError,
            exceptions.JSONDataNoneError
        ):
            raise exceptions.StoredSessionNotFound(
                "There is no stored session. Please, login first."
            )
        except exceptions.AccessKeyringError as e:
            logger.exception(e)
            raise Exception(
                "Unable to load session. Could not access keyring."
            )
        except exceptions.KeyringError as e:
            logger.exception(e)
            raise Exception("Unknown keyring error occured: {}".format(e))
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(
                "Unknown error: {}".format(e)
            )
            raise Exception("Unknown error occured: {}.".format(e))

        logger.info("Session found.")

        if return_bool:
            return True if session else False

        return session
