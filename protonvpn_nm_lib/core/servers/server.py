from ...enums import ServerEnum
from abc import abstractmethod


class Server:
    """Server base class.

    Both logical and physical servers share three common
    properties and one commmon method. Thus, this class
    serves as a base class to be inherited by those
    two classes.
    """

    _server_id = ""
    _domain = ""
    _status = 0

    def __init__(self, server):
        self.server_id = server.get(ServerEnum.ID.value)
        self.domain = server.get(ServerEnum.DOMAIN.value)
        self.status = server.get(ServerEnum.STATUS.value)

    @abstractmethod
    def get_serialized_server(self):
        pass

    @property
    def server_id(self):
        return self._server_id

    @server_id.setter
    def server_id(self, new_id):
        self._server_id = new_id

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, new_domain):
        self._domain = new_domain

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, new_status):
        try:
            self._status = int(new_status)
        except TypeError:
            pass
