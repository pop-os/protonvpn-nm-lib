# ProtonVPN Network Manager Core

### Dependencies:

| **Distro**                              | **Command**                                                                                                     |
|:----------------------------------------|:----------------------------------------------------------------------------------------------------------------|
|Fedora/CentOS/RHEL                       | `sudo dnf install -y networkmanager networkmanager-openvpn openvpn python3-pip python3-pyxdg python3-keyring python3-jinja2 python3-dialog python3-distro python3-psutil python3-gobject libsecret-devel dbus-x11 gnome-keyring` |
|Ubuntu/Linux Mint/Debian and derivatives | `sudo apt install -y network-manager network-manager-openvpn network-manager-openvpn-gnome openvpn python3-pip python3-xdg python3-keyring python3-jinja2 python3-dialog python3-distro gir1.2-nm-1.0 libsecret-tools dbus-x11 gnome-keyring` |
|OpenSUSE/SLES                            | To-do
|Arch Linux/Manjaro                       | `sudo pacman -S networkmanager networkmanager-openvpn openvpn python-pip python-pyxdg python-keyring python-gobject python-jinja-2 python-pythondialog python-distro libsecret dbus-x11 gnome-keyring` |

### Virtual Environment Dependencies:
If you would like to run the the CLI from within a virtual environment (for either development purposes or other), then you can easily do that with the help of <a href="https://pipenv.readthedocs.io/en/latest/">pipenv</a>. Make sure to install pipenv and additional packages before.

| **Distro**                              | **Command**                                                                                                     |
|:----------------------------------------|:----------------------------------------------------------------------------------------------------------------|
|Fedora/CentOS/RHEL                       | `sudo dnf install pkgconf-pkg-config networkmanager networkmanager-openvpn openvpn cairo-devel cairo-gobject-devel libsecret-devel gobject-introspection-devel dbus-x11 gnome-keyring` |
|Ubuntu/Linux Mint/Debian and derivatives | `sudo apt install -y pkg-config network-manager network-manager-openvpn openvpn libcairo2-dev libgirepository1.0-dev gir1.2-nm-1.0 dbus-x11 libsecret-tools gnome-keyring` |
|OpenSUSE/SLES                            | To-do
|Arch Linux/Manjaro                       | `sudo pacman -S pkgconf networkmanager networkmanager-openvpn openvpn cairo base-devel gobject-introspection pkgconf dbus-x11 libsecret gnome-keyring gtk3` |

Steps to manually install inside virtual environment:

  1. `cd protonvpn-nm-core`
  2. `pipenv install` (installs virtual environment and all necessary dependencies from Pipfile).
  3. `pipenv shell` (enter virtual environment).
  4. `pip install -e .` (to install).


## Before install, part 1:

  1. Create a group called "protonvpn": `sudo groupadd protonvpn`
  2. Add user to group "protonvpn": `sudo usermod -a -G protonvpn <USER>`
  3. Follow "Daemon(.service) Configuration" instructions and replace `<GROUP_NAME>` with "protonvpn" and `<USER>` for your actual user
  4. Follow "PolicyKit Configuration" instructions and replace `<GROUP_NAME>` with "protonvpn" and `<USER>` for your actual user

## Before install, part 2:

### Confgure daemon(.service) **- daemon unavailable, skip to Configure PolKit instead**

 1. Create `protonvpn_reconnect.service` inside `/etc/systemd/system/` with the following content (still experimental):


    [Unit]
    Description=ProtonVPN Reconnector
    After=network-online.target
    Wants=network-online.target **systemd-networkd-wait-online.service

    [Service]
    User=<USERNAME>
    Group=protonvpn
    ExecStart=/usr/bin/python3 <PATH/TO/dbus_daemon_reconnector.py>
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target

 2. `systemctl daemon-reload`

**Note: depending on your system, `systemd-networkd-wait-online.service` might not be needed:** https://wiki.archlinux.org/index.php/NetworkManager#Enable_NetworkManager_Wait_Online 

### Configure PolKit

To check version, type `pkaction --version`

#### Versions >= 0.106
The policy should reside inside `/etc/polkit-1/rules.d/` (as per https://wiki.archlinux.org/index.php/Polkit#Authorization_rules)

The first file (`50-manage-NetworkManager.rules`) should contain following information:

    polkit.addRule(function(action, subject) {
          if ((action.id == "org.freedesktop.NetworkManager.settings.modify.own" || action.id == "org.freedesktop.NetworkManager.network-control") &&
              subject.isInGroup("protonvpn")) {
                return polkit.Result.YES;
          }
    });

**Daemon unavailable, skip this step**
The second file (`57-manage-protonvpn-daemon.rules`) should contain following information:

    polkit.addRule(function(action, subject) {
          if (action.id == "org.freedesktop.systemd1.manage-units" &&
              action.lookup("unit") == "protonvpn_reconnect.service" &&
              subject.isInGroup("protonvpn")) {
                return polkit.Result.YES;
          }
    });

#### Versions <= 0.105

The policy should reside inside `/etc/polkit-1/localauthority/50-local.d/`:

  `/etc/polkit-1/localauthority/50-local.d/org.freedesktop.NetworkManager.pkla`

The file should contain following information:

    [nm-applet]
    Identity=unix-group:protonvpn
    Action=org.freedesktop.NetworkManager.settings.modify.own
    ResultAny=yes
    ResultInactive=no
    ResultActive=yes

Known issues:

  - The .service  is still being invoked with PolKit. Meaning that whenever the service is to be started/stopped via the client, the user is still prompted for sudo password. Some PolKit configurations are still needed to avoid this. Ultimately, adding the .service to visudo should (but appearently does not), resolve the issue.
  - In addition to org.freedesktop.NetworkManager.settings.modify.own, one could also have Action=org.freedesktop.systemd1.manage-units. This would fix the previous issue, but it would create a huge security flaw, as all systemd processes could be controlled by the <GROUP>/<USERNAME> without any root privilege escalation.

## Install

 1. `cd protonvpn-nm-core`
 2. `pip3 install .`

## Uninstall

 - `pip3 uninstall protonvpn-cli-experimental`

## How to use

| **Command**                       | **Description**                                       |
|:----------------------------------|:------------------------------------------------------|
|`protonvpn-exp login`                  | Login with ProtonVPN credentials.                     |
|`protonvpn-exp logout`                 | Logout from ProtonVPN.                                |
|`protonvpn-exp connect, c`             | Display dialog window in terminal.                    |
|`protonvpn-exp c [servername]`         | Connect to a specified server.                        |
|`protonvpn-exp c -r`                   | Connect to a random server.                           |
|`protonvpn-exp c -f`                   | Connect to the fastest server.                        |
|`protonvpn-exp c --p2p`                | Connect to the fastest P2P server.                    |
|`protonvpn-exp c --cc [countrycode]`   | Connect to the fastest server in a specified country. |
|`protonvpn-exp c --sc`                 | Connect to the fastest Secure Core server.            |
|`protonvpn-exp disconnect, d`          | Disconnect the current session.                       |
|`protonvpn-exp --version`              | Display version.                                      |
|`protonvpn-exp --help`                 | Show help message.                                    |

