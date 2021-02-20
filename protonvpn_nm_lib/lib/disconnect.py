import dbus

from .. import exceptions
from ..logger import logger


class ProtonVPNDisconnect:

    def __init__(
        self, connection_manager,
        user_conf_manager, ipv6_lp_manager,
        reconector_manager, ks_manager
    ):
        self.connection_manager = connection_manager
        self.user_conf_manager = user_conf_manager
        self.ipv6_lp_manager = ipv6_lp_manager
        self.reconector_manager = reconector_manager
        self.ks_manager = ks_manager

    def _disconnect(self):
        logger.info("Attempting to disconnecting from ProtonVPN")

        try:
            self.connection_manager.remove_connection(
                self.user_conf_manager,
                self.ks_manager,
                self.ipv6_lp_manager,
                self.reconector_manager
            )
        except exceptions.ConnectionNotFound as e:
            raise Exception("Unable to disconnect: {}".format(e))
        except (
            exceptions.RemoveConnectionFinishError,
            exceptions.StopConnectionFinishError
        ) as e:
            raise Exception("Unable to disconnect: {}".format(e))
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
