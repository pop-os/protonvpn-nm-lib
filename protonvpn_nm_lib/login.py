from .logger import logger
from . import exceptions


class Login:
    def _login(self, username, password):
        """Proxymethod to login user with ProtonVPN credentials."""
        self.server_manager.killswitch_status = self.user_conf_manager.killswitch # noqa
        logger.info("Checking connectivity")
        self.check_connectivity()
        self.__login_user(username, password)

    def __login_user(self, protonvpn_username, protonvpn_password):
        logger.info("Attempting to login...")
        try:
            self.user_manager.login(protonvpn_username, protonvpn_password)
        except (TypeError, ValueError) as e:
            logger.info(e)
            raise Exception("Unable to authenticate: {}".format(e))
        except (exceptions.API8002Error, exceptions.API85032Error) as e:
            logger.info(e)
            raise Exception("{}".format(e))
        except exceptions.APITimeoutError as e:
            logger.info(e)
            raise Exception("Connection timeout, unable to reach API.")
        except (exceptions.UnhandledAPIError, exceptions.APIError) as e:
            logger.info(e)
            raise Exception("Unhandled API error occured: {}".format(e))
        except exceptions.ProtonSessionWrapperError as e:
            logger.info(e)
            logger.exception(
                "ProtonSessionWrapperError: {}".format(e)
            )
            raise Exception("Unknown API error occured: {}".format(e))
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(
                "Unknown error: {}".format(e)
            )
            raise Exception("Unknown error occured: {}".format(e))

        logger.info("Successful login.")
