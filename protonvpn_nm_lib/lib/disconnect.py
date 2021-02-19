from ..logger import logger
from .. import exceptions
import dbus


class Disconnect:
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
