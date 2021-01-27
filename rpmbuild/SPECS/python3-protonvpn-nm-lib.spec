%define unmangled_name protonvpn-nm-lib
%define version 0.3.0
%define release 2

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
* Wed Jan 27 2021 Proton Technologies AG <opensource@proton.me> 0.3.0-2
- Update .spec file for public release
