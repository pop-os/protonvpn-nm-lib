from ..logger import logger
from .. import exceptions


class ProtonVPNLogout:

    def __init__(self, connection, session, user_manager):
        # library
        self.connection = connection
        self.session = session

        # services
        self.user_manager = user_manager

    def _logout(self, session=None, _pass_check=None, _removed=None):
        logger.info("Attemping to logout...")

        if _pass_check is None and _removed is None:
            logger.info("First logout round")
            # Public method providade by protonvpn_lib
            session = self.session._get_session()
            # Public method providade by protonvpn_lib
            self.session._ensure_session_is_valid(session)
            try:
                session.logout()
            except exceptions.ProtonSessionWrapperError:
                logger.info("Unable to logout from API")
                pass
            # Public method providade by protonvpn_lib
            self.connection._remove_protonvpn_connection()
            _pass_check = []
            _removed = []

        try:
            self.user_manager.logout(_pass_check, _removed)
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
