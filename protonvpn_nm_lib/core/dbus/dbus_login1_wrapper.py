from enum import Enum
from .dbus_wrapper import DbusWrapper
from ...logger import logger


class SystemBusLogin1ObjectPathEnum(Enum):
    USER_SELF = "/org/freedesktop/login1/user/self"


class SystemBusLogin1InterfaceEnum(Enum):
    LOGIN1_USER = "org.freedesktop.login1.User"
    SESSION = "org.freedesktop.login1.Session"


class Login1UnitWrapper:
    BUS_NAME = "org.freedesktop.login1"

    def __init__(self, bus):
        self.__dbus_wrapper = DbusWrapper(bus)

    def get_properties_current_user_session(self):
        return self.__dbus_wrapper.get_proxy_object_properties_interface(
            self._get_current_user_session_proxy_object()
        ).GetAll(SystemBusLogin1InterfaceEnum.SESSION.value)

    def connect_user_session_object_to_signal(self, signal_name, method):
        interface = self._get_current_session_interface()
        interface.connect_to_signal(signal_name, method)

    def _get_current_session_interface(self):
        return self.__dbus_wrapper.get_proxy_object_interface(
            self._get_current_user_session_proxy_object(),
            SystemBusLogin1InterfaceEnum.SESSION.value
        )

    def _get_current_user_session_proxy_object(self):
        all_params = self._get_properties_from_user_self()
        return self.__get_proxy_object(all_params["Sessions"][0][1])

    def get_user_interface_from_user_self_proxy_object(self):
        """Get org.freedesktop.login1.User interface.

        Returns:
            dbus.proxies.Interface: org.freedesktop.login1.User interface
        """
        return self.__dbus_wrapper.get_proxy_object_interface(
            self._get_user_self_proxy_object(),
            SystemBusLogin1InterfaceEnum.LOGIN1_USER.value
        )

    def _get_properties_from_user_self(self):
        prop_iface = self.__dbus_wrapper.get_proxy_object_properties_interface(
            self.get_user_interface_from_user_self_proxy_object()
        )
        return prop_iface.GetAll(SystemBusLogin1InterfaceEnum.LOGIN1_USER.value)

    def _get_user_self_proxy_object(self):
        """Get /org/freedesktop/login1/user/self proxy object.

        Returns:
            dbus.proxies.ProxyObject: network manager proxy object
        """
        return self.__get_proxy_object(SystemBusLogin1ObjectPathEnum.USER_SELF.value)

    def __get_proxy_object(self, path_to_object):
        return self.__dbus_wrapper.get_proxy_object(
            self.BUS_NAME,
            path_to_object
        )
