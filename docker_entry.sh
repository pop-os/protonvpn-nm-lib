#!/bin/bash
# start network manager and dbus system
sudo /etc/init.d/dbus start && \
sudo /etc/init.d/network-manager start

echo "---1"
# start gnome-keyring daemon at bash shell init and launch interactive dbus session
#echo 'eval "$(printf '\\n' | gnome-keyring-daemon --unlock)"'  >> ~/.bashrc
#echo 'eval "$(printf '\\n' | gnome-keyring-daemon -f )"'  >> $HOME/.profile
#dbus-run-session -- bash

#gnome-keyring-daemom --unlock;


echo "---2"
export $(dbus-launch)

echo "---3"
eval "$(dbus-launch --sh-syntax)"

mkdir -p ~/.cache
mkdir -p ~/.local/share/keyrings # where the automatic keyring is created

echo "---4"
# 1. Create the keyring manually with a dummy password in stdin
eval "$(printf '\n' | gnome-keyring-daemon --unlock)"

echo "---5"
# 2. Start the daemon, using the password to unlock the just-created keyring:
eval "$(printf '\n' | /usr/bin/gnome-keyring-daemon --start)"


if [ -f .env ]; then
  echo 'load .env';
  export $(cat .env | xargs)
fi

echo "---6"
sudo bash -c  "cat <<EOT > /etc/polkit-1/localauthority/50-local.d/org.freedesktop.NetworkManager.pkla
[nm-applet]
Identity=unix-user:user
Action=org.freedesktop.NetworkManager.*
ResultAny=yes
ResultInactive=no
ResultActive=yes
EOT"

#eval `dbus-launch --sh-syntax`
#eval `gnome-keyring-daemon --unlock`
#export $(gnome-keyring-daemon -s -d | xargs);
echo
echo
echo
echo
echo
env;
echo ""
#dbus-run-session -- $@;
#dbus-update-activation-environment --systemd DISPLAY
#dbus-run-session bash -c "GNOME_KEYRING_CONTROL=1 $*";
#$@;
python3 -m pytest
