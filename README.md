# ProtonVPN NM Library

Official ProtonVPN NetworkManager library for linux based systems.

### Dependencies:

| **Distro**                              | **Command**                                                                                                     |
|:----------------------------------------|:----------------------------------------------------------------------------------------------------------------|
|Fedora/CentOS/RHEL                       | `sudo dnf install -y NetworkManager NetworkManager-openvpn NetworkManager-openvpn-gnome openvpn python3-pyxdg python3-keyring python3-jinja2 python3-distro python3-psutil python3-gobject libsecret-devel dbus-x11 gnome-keyring` |
|Ubuntu/Linux Mint/Debian and derivatives | `sudo apt install -y network-manager network-manager-openvpn openvpn python3-xdg python3-keyring python3-jinja2 python3-distro gir1.2-nm-1.0 libsecret-tools dbus-x11 gnome-keyring network-manager-openvpn-gnome python3-proton-client` |
|OpenSUSE/SLES                            | To-do
|Arch Linux/Manjaro                       | `sudo pacman -S networkmanager networkmanager-openvpn openvpn python-pyxdg python-keyring python-jinja python-distro dbus-x11 gnome-keyring` |

### Virtual Environment Dependencies:
If you would like to run the the CLI from within a virtual environment (for either development purposes or other), then you can easily do that with the help of <a href="https://pipenv.readthedocs.io/en/latest/">pipenv</a>. Make sure to install pipenv and additional packages before.

| **Distro**                              | **Command**                                                                                                     |
|:----------------------------------------|:----------------------------------------------------------------------------------------------------------------|
|Fedora/CentOS/RHEL                       | `sudo dnf install pkgconf-pkg-config networkmanager networkmanager-openvpn openvpn cairo-devel cairo-gobject-devel libsecret-devel gobject-introspection-devel dbus-x11 gnome-keyring` |
|Ubuntu/Linux Mint/Debian and derivatives | `sudo apt install -y pkg-config network-manager network-manager-openvpn openvpn libcairo2-dev libgirepository1.0-dev gir1.2-nm-1.0 dbus-x11 libsecret-tools gnome-keyring` |
|OpenSUSE/SLES                            | To-do
|Arch Linux/Manjaro                       | `sudo pacman -S pkgconf networkmanager networkmanager-openvpn openvpn cairo base-devel gobject-introspection pkgconf dbus-x11 libsecret gnome-keyring gtk3` |

#### Install inside virtual environment:

  1. `cd protonvpn-nm-core`
  2. `pipenv install` (installs virtual environment and all necessary dependencies from Pipfile).
  3. `pipenv shell` (enter virtual environment).
  4. `pip install -e .` (to install).

<br>

# How to use:

### Login
``` protonvpn._login("protonvpn@protonmail.com", "ProtonPassword") ```

<br>

### Logout
``` protonvpn._logout() ```

<br>

### Connect
``` protonvpn._setup_connection(ConnectionTypeEnum.SERVERNAME, "PT#12", ProtocolEnum.TCP) ``` <br>
``` protonvpn._connect() ``` 

<br>

### Disconnect
``` protonvpn._disconnect() ```

| **API**                              | **Description**                                                                                                     |
|:------------------------------------------------|:----------------------------------------------------------------------------------------------------------------|
|`protonvpn._login(username, password)` | Login with your Proton credentials. |
| `protonvpn._ensure_username_is_valid(username)` | Ensure that the username is correctly formatted and is valid. |
| `protonvpn._logout()` | Logout user and delete current user session. |
| `protonvpn._setup_connection(connection_type, connection_type_extra_arg, protocol)` | Setup and configure VPN connection prior calling protonvpn._connect(). |
| `protonvpn._connect()` | Should be user either after protonvpn._setup_connection() orprotonvpn._setup_reconnection(). |
| `protonvpn._is_protocol_valid()` | Checks if provided protocol is a valid protocol. This is checked during protonvpn._setup_connection() and protonvpn._setup_reconnection(). Can be used whenever needed. |
| `protonvpn._get_active_connection_metadata()` | Get metadata of an active ProtonVPN connection. |
| `protonvpn._get_protonvpn_connection()` | Get ProtonVPN connection object. |
| `protonvpn._ensure_connectivity()` | Check for connectivity. 1) It checks if there is internet connection 2) It checks if API can be reached. This is checked during protonvpn._login(), protonvpn._setup_connection() and protonvpn._setup_reconnection(). Can be used whenever needed.|
| `protonvpn._disconnect()` | Disconnect from ProtonVPN. |
| `protonvpn._setup_reconnection()` | Setup and configure VPN connection to a previously connected server. Should be called before calling protonvpn._connect(). |
| `protonvpn._get_session()` | Get user session. This is fetched during protonvpn._login(), protonvpn._logout(), protonvpn._setup_connection() and protonvpn._setup_reconnection(). Can be used whenever needed. |
| `protonvpn._check_session_exists()` | Check if sessions exists. This is checked during protonvpn._login() and protonvpn._logout(), protonvpn._setup_connection() and protonvpn._setup_reconnection(). |
| `protonvpn._ensure_session_is_valid()` | Ensure that provided session is valid. This is checked during protonvpn._setup_connection() and protonvpn.setup_reconnection(). |
| `protonvpn._ensure_servername_is_valid()` | Ensures if the provided servername is valid. This is checked during protonvpn._setup_connection() and protonvpn._setup_reconnection(). Can be used whenever needed. |
| `protonvpn._get_country_name()` | Get country name of a given country code. |
| `protonvpn._ensure_country_exists(country_code)` | Ensures that a given country code exists. This is checked during protonvpn._setup_connection() and protonvpn._setup_reconnection(). Can be used whenever needed. |
| `protonvpn._get_filtered_server_list()` | Get filtered server list. This is checked during protonvpn._setup_connection() and protonvpn._setup_reconnection(). Can be used whenever needed. |
|`protonvpn._get_server_list()` | Get server list. This is checked during protonvpn._setup_connection() and protonvpn._setup_reconnection(). Can be used whenever needed. |
|`protonvpn._get_country_with_matching_servername(server_list)` | Generate dict with {country:[servername]}. |
|`protonvpn._get_server_information(servername)` | Get server information. |
|`protonvpn._refresh_servers()` | Refresh cached server list. This is fetched during protonvpn._setup_connection() and protonvpn._setup_reconnection(). Can be used whenever needed. |
|`protonvpn._get_active_connection_status(readeable_format=True)` | Get active connection status. |
|`protonvpn._convert_time_from_epoch(seconds_since_epoch)` | Convert time from epoch to 24h. |
|`protonvpn._get_user_settings_get_user_settings(readeable_format=True)` | Get user settings. |
|`protonvpn._get_netshield()` | Get user netshield setting. |
|`protonvpn._get_killswitch()` | Get user Kill Switch setting. |
|`protonvpn._get_protocol()` | Get user set default protocol. |
|`protonvpn._get_dns()` | Get user DNS setting. |
|`protonvpn._get_custom_dns()` | Get user custom DNS servers. |
|`protonvpn._get_user_tier()` | Get stored user tier. |
|`protonvpn._set_netshield(netshield_enum)` | Set netshield to specified option. |
|`protonvpn._set_killswitch(killswitch_enum)` | Set Kill Switch to specified option. |
|`protonvpn._set_protocol(protocol_enum)` | Set default protocol to specified option. |
|`protonvpn._set_automatic_dns()` | Set DNS to be managed automatically by ProtonVPN. |
|`protonvpn._set_custom_dns(dns_ip_list)` | Set DNS to be managed by custom servers. |
|`protonvpn._is_valid_dns_ipv4(dns_server_ip)` | Check if provided IP is valid. |
|`protonvpn._reset_to_default_configs()` | Reset user configuration to default values. |