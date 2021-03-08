from .server import Server
from ...enums import PhysicalServerEnum, ServerEnum


class PhysicalServer(Server):
    """Physical Server class.

    This class represents the physical servers that are located
    in each logical server.
    Provides a method which returns a serealized physical server.
    """
    def __init__(self, physical_server):
        super().__init__(physical_server)

        self.entry_ip = physical_server.get(PhysicalServerEnum.ENTRY_IP.value)
        self.exit_ip = physical_server.get(PhysicalServerEnum.EXIT_IP.value)
        self.generation = physical_server.get(PhysicalServerEnum.GENERATION.value) # noqa
        self.service_down_reason = physical_server.get(
            PhysicalServerEnum.SERVICES_DOWN_REASON.value
        )
        self.label = physical_server.get(PhysicalServerEnum.LABEL.value)

    def get_serialized_server(self):
        """Get serealized physical servers.

        This should be used only when saving to an external file,
        as python objects are not writeable/accesible to external sources.

        Returns:
            dict
        """
        return {
            PhysicalServerEnum.ENTRY_IP.value: self.entry_ip,
            PhysicalServerEnum.EXIT_IP.value: self.exit_ip,
            ServerEnum.DOMAIN.value: self.domain,
            ServerEnum.ID.value: self.server_id,
            PhysicalServerEnum.GENERATION.value: self.generation,
            ServerEnum.STATUS.value: self.status,
            PhysicalServerEnum.SERVICES_DOWN_REASON.value: self.service_down_reason, # noqa
            PhysicalServerEnum.LABEL.value: self.label,
        }

    @property
    def entry_ip(self):
        return self._entry_ip

    @entry_ip.setter
    def entry_ip(self, new_entry_ip):
        self._entry_ip = new_entry_ip

    @property
    def exit_ip(self):
        return self._exit_ip

    @exit_ip.setter
    def exit_ip(self, new_exit_ip):
        self._exit_ip = new_exit_ip

    @property
    def generation(self):
        return self._generation

    @generation.setter
    def generation(self, new_generation):
        try:
            self._generation = int(new_generation)
        except TypeError:
            pass

    @property
    def service_down_reason(self):
        return self._service_down_reason

    @service_down_reason.setter
    def service_down_reason(self, new_service_down_reason):
        self._service_down_reason = new_service_down_reason

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, new_label):
        self._label = new_label
