# ProtonVPN Network Manager Core

### The repo includes a CLI to test it's functionality manually.

### Automated testing is done with pytest, to run type `python -m pytest` and all tests will be run

### Dependencies (excluding the CLI):
 - #### [python-keyring](https://github.com/jaraco/keyring) (also):
   - gnome-keyring
   - SecretService
   - Kwallet
 - #### [python-proton-client](https://github.com/ProtonMail/proton-python-client) 
 - #### pytest
 - #### [jinja2](https://jinja.palletsprojects.com/en/2.11.x/)
 - #### [python-xdg](https://github.com/srstevenson/xdg)
 - #### dbus-ptyhon/python-dbus
 - #### [Python Gi/GObject](https://pygobject.readthedocs.io/en/latest/getting_started.html#ubuntu-logo-ubuntu-debian-logo-debian)
   - Network Manager (also):
     - NM-openvpn plugin
   - GLib
