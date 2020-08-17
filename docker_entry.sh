#!/bin/bash
# start network manager and dbus system
sudo /etc/init.d/dbus start && \
sudo /etc/init.d/network-manager start
# start gnome-keyring daemon at bash shell init and launch interactive dbus session
echo 'eval "$(printf '\\n' | gnome-keyring-daemon --unlock)"'  >> ~/.bashrc
dbus-run-session -- bash
