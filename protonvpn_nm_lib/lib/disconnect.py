import dbus

from .. import exceptions
from ..logger import logger


class ProtonVPNDisconnect:
    """Disconnect Class.
    Use it to disconnect from VPN.

    Exposes method:
        _disconnect()

    Description:
    _disconnect()
        First it attempts from the VPN connection. After
        successfully disconencting from VPN, it will proceed
        to remove the connection from NetworkManager.
    """
    def __init__(
        self, connection_manager,
        user_conf_manager, ipv6_lp_manager,
        reconector_manager, ks_manager
    ):
        self.__connection_manager = connection_manager
        self.__user_conf_manager = user_conf_manager
        self.__ipv6_lp_manager = ipv6_lp_manager
        self.__reconector_manager = reconector_manager
        self.__ks_manager = ks_manager

    def _disconnect(self):
        logger.info("Attempting to disconnecting from ProtonVPN")

        try:
            self.__connection_manager.remove_connection(
                self.__user_conf_manager,
                self.__ks_manager,
                self.__ipv6_lp_manager,
                self.__reconector_manager
            )
        except exceptions.ConnectionNotFound as e:
            raise exceptions.ConnectionNotFound(
                "Unable to disconnect: {}".format(e)
            )
        except (
            exceptions.RemoveConnectionFinishError,
            exceptions.StopConnectionFinishError
        ) as e:
            raise exceptions.ConnectionNotFound(
                "Unable to disconnect: {}".format(e)
            )
        except (
            exceptions.ProtonVPNException,
            dbus.exceptions.DBusException,
            Exception
        ) as e:
            logger.exception(
                "Unknown error: {}".format(e)
            )
            raise Exception("Unknown error occured: {}".format(e))

        logger.info("Disconnected from VPN")
