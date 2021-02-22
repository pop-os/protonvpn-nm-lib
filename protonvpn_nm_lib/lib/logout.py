from ..logger import logger
from .. import exceptions


class ProtonVPNLogout:
    """Logout Class.
    User it for logout.

    Exposes method:
        _logout(
            session=None: ProtonSessionWrapper,
            _pass_check=None: Exception,
            _removed=None: String,
        )

    Description:
    _logout()
        Gets a user session, ensures that the session is valid,
        then attempts to logout via api (delete session from
        proton). If there is no internet connectivity then it will
        skip this step, and proceed to recursively delete all data
        that is stored on a users keychain.

    """
    def __init__(self, connection, session, disconnect, user_manager):
        # library
        self.connection = connection
        self.session = session
        self.disconnect = disconnect

        # services
        self.__user_manager = user_manager

    def _logout(self, session=None, _pass_check=None, _removed=None):
        logger.info("Attemping to logout...")

        if _pass_check is None and _removed is None:
            logger.info("First logout round")
            session = self.session._get_session()
            self.session._ensure_session_is_valid(session)
            try:
                session.logout()
            except exceptions.ProtonSessionWrapperError:
                logger.info("Unable to logout from API")
                pass

            try:
                self.disconnect._disconnect()
            except exceptions.ConnectionNotFound:
                pass

            _pass_check = []
            _removed = []

        try:
            self.__user_manager.logout(_pass_check, _removed)
        except exceptions.StoredProtonUsernameNotFound:
            logger.info("Recursive logout: StoredProtonUsernameNotFound")
            _pass_check.append(exceptions.StoredProtonUsernameNotFound)
            self.logout(session, _pass_check, _removed)
        except exceptions.StoredUserDataNotFound:
            logger.info("Recursive logout: StoredUserDataNotFound")
            _pass_check.append(exceptions.StoredUserDataNotFound)
            self.logout(session, _pass_check, _removed)
        except exceptions.StoredSessionNotFound:
            logger.info("Recursive logout: StoredSessionNotFound")
            _pass_check.append(exceptions.StoredSessionNotFound)
            self.logout(session, _pass_check, _removed)
        except exceptions.KeyringDataNotFound as e:
            logger.exception(e)
            raise Exception(e)
        except exceptions.AccessKeyringError as e:
            logger.exception(e)
            raise Exception(e)
        except exceptions.KeyringError as e:
            logger.exception(e)
            raise Exception(e)
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(
                "Unknown error: {}".format(e)
            )
            raise Exception("Unknown error occured: {}.".format(e))

        logger.info("Successful logout.")
