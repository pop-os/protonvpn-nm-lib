from abc import ABC, abstractmethod


class AbstractInterfaceManager(ABC):
    @abstractmethod
    def manage(self):
        pass

    @abstractmethod
    def run_subprocess(self):
        pass

    @abstractmethod
    def update_connection_status(self):
        pass
