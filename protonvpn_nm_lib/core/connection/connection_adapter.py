from ...logger import logger
from ... import exceptions
from ...enums import NetworkManagerConnectionTypeEnum
from .nm_client import NMClient


class ConnectionAdapter:
    """ConnectionAdapter class.

    The intent with this class is to abstract the way connections are
    handled. As long as the client provides the same methods everything should
    work in case we change frameworks or backend.

    To introduce and alternative client backend, it client has to provide the
    following methods:
        client.add_connection()
        client.start_connection()
        client.stop_connection()
        client.remove_connection()
        client.get_protonvpn_connection()

    Also, the alternative custom backend should also have
    the following properties:
        client.virtual_device_name:
            The name of the virtual device name that will
            be used. This information is critical.
        client.certificate_filepath:
            The certificate filepath. Where will the the
            generated certificate be located at.
        client.protonvpn_user:
            A user object. The user object should at the least
            have the following properties:
                ovpn_username
                ovpn_password
        client.physical_server:
            The physical server. This physical servers is data
            that is collected by the Physical class, and should
            be implemented by the client. (check servers module)
    """
    def __init__(
        self,
        certificate_filepath=None,
        virtual_device_name=None,
        client=NMClient()
    ):
        self.client = client
        self.certificate_filepath = certificate_filepath
        self.virtual_device_name = virtual_device_name

    @property
    def virtual_device_name(self):
        return self.client.virtual_device_name

    @virtual_device_name.setter
    def virtual_device_name(self, new_virtual_device_name):
        self.client.virtual_device_name = new_virtual_device_name

    @property
    def certificate_filepath(self):
        return self.client.certificate_filepath

    @certificate_filepath.setter
    def certificate_filepath(self, new_certificate_filepath):
        self.client.certificate_filepath = new_certificate_filepath

    def vpn_add_connection(self, **kwargs):
        self.ensure_properties_are_set_before_add_connection()
        self.client.add_connection(**kwargs)

    def ensure_properties_are_set_before_add_connection(self):
        if self.certificate_filepath is None:
            raise ValueError(
                "Instance properties \"certificate_filepath\" has not "
                "been set. Please set the property before adding the "
                "connection."
            )

        if self.virtual_device_name is None:
            raise ValueError(
                "Instance properties \"virtual_device_name\" has not "
                "been set. Please set the property before adding the "
                "connection."
            )

    def vpn_connect(self):
        protonvpn_connection = self.get_non_active_protonvpn_connection()
        self.ensure_protovnpn_connection_exists(protonvpn_connection)
        self.client.start_connection(protonvpn_connection)

    def vpn_disconnect(self):
        protonvpn_connection = self.get_active_protonvpn_connection()
        self.ensure_protovnpn_connection_exists(protonvpn_connection)

        self.client.stop_connection(protonvpn_connection)

    def vpn_remove_connection(self):
        try:
            self.vpn_disconnect()
        except exceptions.ConnectionNotFound as e:
            raise exceptions.ConnectionNotFound(e)
        except: # noqa
            # It does not matter what type of exception is thrown here
            # after ConnectionNotFound, as long as the connection is disabled,
            # or the connection does not exist all is ok, as during
            # connection removal (below) an error will be trown
            # which can be then handled.
            pass

        protonvpn_connection = self.get_non_active_protonvpn_connection()

        self.ensure_protovnpn_connection_exists(protonvpn_connection)
        self.client.remove_connection(protonvpn_connection)

    def get_non_active_protonvpn_connection(self):
        return self._get_protonvpn_connection(
            NetworkManagerConnectionTypeEnum.ALL
        )

    def get_active_protonvpn_connection(self):
        return self._get_protonvpn_connection(
            NetworkManagerConnectionTypeEnum.ACTIVE
        )

    def _get_protonvpn_connection(self, network_manager_connection_type):
        """Get ProtonVPN connection.

        Args:
            connection_type (NetworkManagerConnectionTypeEnum):
                can either be:
                ALL - for all connections
                ACTIVE - only active connections

        Returns:
            protonvpn_connection
        """
        return self.client.get_protonvpn_connection(
            network_manager_connection_type
        )

    def ensure_protovnpn_connection_exists(self, protonvpn_connection):
        if not protonvpn_connection:
            logger.info(
                "ConnectionNotFound: Connection not found, "
                + "raising exception"
            )
            raise exceptions.ConnectionNotFound(
                "ProtonVPN connection was not found"
            )
