import re

from .. import exceptions
from ..logger import logger


class ProtonVPNLogin:

    def __init__(
        self, connection, server_manager,
        user_manager, user_conf_manager
    ):
        # librart
        self.connection = connection

        # services
        self.server_manager = server_manager
        self.user_manager = user_manager
        self.user_conf_manager = user_conf_manager

    def _login(self, username, password):
        """Login user with the provided username and password.
        
        Args:
            protonvpn_username (string)
            protonvpn_password (string)
        """
        self.server_manager.killswitch_status = self.user_conf_manager.killswitch # noqa
        logger.info("Checking connectivity")
        # Public method providade by protonvpn_lib
        self.connection._ensure_connectivity()
        self._ensure_username_is_valid(username)
        self.__login_user(username, password)

    def _ensure_username_is_valid(self, username):
        """Ensure that the provided username is valid.

        This is done automatically during protonvpn._login(),
        but can be used at any time to check if the provided username
        follows the full Proton account.

        Expected:
            protonvpn@protonmail.com
            username@protonvpn.com
            username@customdns.com
        """
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
        """Proxymethod to login user with ProtonVPN credentials.

        Args:
            protonvpn_username (string)
            protonvpn_password (string)
        """
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
