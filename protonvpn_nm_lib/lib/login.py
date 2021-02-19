from ..logger import logger
from .. import exceptions
import re


class Login:
    def _login(self, username, password):
        """Proxymethod to login user with ProtonVPN credentials."""
        self.server_manager.killswitch_status = self.user_conf_manager.killswitch # noqa
        logger.info("Checking connectivity")
        # Public method providade by protonvpn_lib
        self._check_connectivity()
        self.__validate_username(username)
        self.__login_user(username, password)

    def __validate_username(self, username):
        re_username = re.compile(
            r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        )
        if not re_username.search(username):
            raise exceptions.InvalidUsernameFormat(
                "The provided username \"{}\" is invalid."
                "\nPlease provide your full Proton account username, ie: "
                "username@protonmail.com".format(
                    username
                )
            )

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
