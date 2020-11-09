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
