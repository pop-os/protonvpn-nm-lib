%define unmangled_name protonvpn-nm-lib
%define version 0.5.2
%define release 1

Prefix: %{_prefix}

Name: python3-protonvpn-nm-lib
Version: %{version}
Release: %{release}
Summary: Official ProtonVPN NetworkManager library

Group: ProtonVPN
License: GPLv3
Url: https://github.com/ProtonVPN/
Vendor: Proton Technologies AG <opensource@proton.me>
Source0: %{unmangled_name}-%{version}.tar.gz
BuildArch: noarch
BuildRoot: %{_tmppath}/%{unmangled_name}-%{version}-%{release}-buildroot

BuildRequires: python3-devel
BuildRequires: python3-setuptools
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
Requires: python3-dbus

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
%{python3_sitelib}/protonvpn_nm_lib/
%{python3_sitelib}/protonvpn_nm_lib-%{version}*.egg-info/
%defattr(-,root,root)

%changelog
* Thu Apr 15 2021 Proton Technologies AG <opensource@proton.me> 0.5.2-1
- Cache servers and client configurations upon login

* Tue Feb 30 2021 Proton Technologies AG <opensource@proton.me> 0.5.1-5
- Improve reconnection logic when computer goes to sleep or there is no internet connectivity
- Improve logging
- Impove Kill Switch --on option after reboot
- Improve error handling
- Disconnect after logout
- Return server object after successfully reconnecting
- Add secure core settings for GUI purpose
- Rename Kill Switch always-on to permanent
- Add option to connect to fastest server and fastest server in country based on secure core setting

* Thu Feb 25 2021 Proton Technologies AG <opensource@proton.me> 0.5.0-2
- Refactor library
- Create public API
- Improved library overall stability 
- Implement subprocess wrapper

* Thu Feb 25 2021 Proton Technologies AG <opensource@proton.me> 0.4.2-1
- Correctly apply server domain for TLS authentication

* Wed Feb 24 2021 Proton Technologies AG <opensource@proton.me> 0.4.1-1
- Fix bug when connecting to P2P, Secure-Core and TOR due to incorrect subject name for TLS authentication


* Mon Feb 01 2021 Proton Technologies AG <opensource@proton.me> 0.4.0-2
- Improved Kill Switch logic
- Improved reconnection logic after suspend/hibernate
- Add IP server label suffix to username

* Wed Jan 27 2021 Proton Technologies AG <opensource@proton.me> 0.3.0-2
- Update .spec file for public release
