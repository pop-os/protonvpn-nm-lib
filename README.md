# ProtonVPN Network Manager Core

### Dependencies:

| **Distro**                              | **Command**                                                                                                     |
|:----------------------------------------|:----------------------------------------------------------------------------------------------------------------|
|Ubuntu/Linux Mint/Debian and derivatives | `sudo apt install -y python3 network-manager network-manager-openvpn pkg-config openvpn python3-pip python3-xdg python3-keyring python3-jinja2 python3-dialog python3-pytest libcairo2-dev libgirepository1.0-dev gir1.2-nm-1.0 dbus-x11 libsecret-tools gnome-keyring` |

| **Python3**                            | **Command**                             |
|:---------------------------------------|:----------------------------------------|
| Additional Python3 dependencies        | `pip3 install proton-client keyring xdg`|

### Requires:
- keyring >= 2.16

### Tested on:
 - Ubuntu:
   - 16.04: does not work (tls-pinning will fail due to keyring)
   - 18.04: works but daemon reconnector does not behave properly because pkaction==0.105 (daemon reconnector works only with pkaction==0.106)
 - Manjaro >= 20: works
 - Debian 9: does not work (tls-pinning will fail due to keyring)
 - Debian 10: not tested