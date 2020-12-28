%define unmangled_name protonvpn-nm-lib
%define version 0.3.0
%define release 1

Summary: Official ProtonVPN NetworkManager library
Name: python3-protonvpn-nm-lib
Version: %{version}
Release: %{release}
Source0: %{unmangled_name}-%{version}.tar.gz
License: MIT
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{unmangled_name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Proton Technologies AG <opensource@proton.me>
Url: https://github.com/ProtonMail/proton-python-client
Requires: gnome-keyring
Requires: libsecret
Requires: dbus-x11
Requires: openvpn
Requires: NetworkManager
Requires: NetworkManager-openvpn
Requires: gtk3
Requires: python3-proton-client
Requires: python3-keyring
Requires: python3-distro
Requires: python3-jinja2
Requires: python3-pyxdg

%{?python_disable_dependency_generator}

%description
Package installs official ProtonVPN NetworkManager library.


%prep
%setup -n %{unmangled_name}-%{version} -n %{unmangled_name}-%{version}

%build
python3 setup.py build

%install
python3 setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
