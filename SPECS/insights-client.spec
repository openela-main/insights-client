%define _binaries_in_noarch_packages_terminate_build 0

Name:                   insights-client
Summary:                Uploads Insights information to Red Hat on a periodic basis
Version:                3.1.7
Release:                12.1%{?dist}
Source0:                https://github.com/RedHatInsights/insights-client/releases/download/v%{version}/insights-client-%{version}.tar.gz
Source1:                https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg
Source2:                https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg.asc
Epoch:                  0
License:                GPLv2+
URL:                    https://console.redhat.com/insights
Group:                  Applications/System
Vendor:                 Red Hat, Inc.

#
# patches_ignore=DROP-IN-RPM
# patches_base=3.1.7
Patch0001: 0001-fix-remove-PathExists-condition-from-unit.patch

Provides: redhat-access-insights = %{version}-%{release}%{?dist}

Obsoletes: redhat-access-insights <= 1.0.13-2
Obsoletes: redhat-access-proactive <= 1.0.13-2

BuildArch: noarch

Requires: tar
Requires: gpg
Requires: pciutils

%global __python3 /usr/libexec/platform-python
%{?__python3:Requires: %{__python3}}
%{?systemd_requires}
Requires: python3-requests >= 2.6
Requires: python3-PyYAML
Requires: python3-magic
Requires: python3-six
Requires: python3dist(setuptools)
Requires: coreutils
BuildRequires: wget
BuildRequires: binutils
BuildRequires: python3-devel
BuildRequires: platform-python-devel
BuildRequires: systemd
BuildRequires: pam
Requires(post): policycoreutils-python-utils


%description
Sends insightful information to Red Hat for automated analysis

%prep
%autosetup -p1


%build
%{configure} PYTHON=%{__python3}
%{__make}


%install
%{make_install}
%{__install} -D -m 644 %{_builddir}/%{name}-%{version}/data/insights-client.motd %{buildroot}/%{_sysconfdir}/insights-client/insights-client.motd
%{__install} -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/insights-client/rpm.egg
%{__install} -D -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/insights-client/rpm.egg.asc

# Create different insights directories in /var
mkdir -p %{buildroot}%{_localstatedir}/log/insights-client/
mkdir -p %{buildroot}%{_localstatedir}/lib/insights/
mkdir -p %{buildroot}%{_localstatedir}/cache/insights/
mkdir -p %{buildroot}%{_localstatedir}/cache/insights-client/

%post
%systemd_post %{name}.timer
%systemd_post %{name}-boot.service
if [ -d %{_sysconfdir}/motd.d ]; then
    if [ ! -e %{_sysconfdir}/motd.d/insights-client -a ! -L %{_sysconfdir}/motd.d/insights-client ]; then
        if [ -e %{_localstatedir}/lib/insights/newest.egg ]; then
            ln -sn /dev/null %{_sysconfdir}/motd.d/insights-client
        else
            ln -sn %{_sysconfdir}/insights-client/insights-client.motd %{_sysconfdir}/motd.d/insights-client
        fi
    fi
fi

if [ -x /usr/sbin/selinuxenabled ] && /usr/sbin/selinuxenabled; then
    /usr/sbin/semanage permissive --add insights_client_t || true
fi

%preun
%systemd_preun %{name}.timer
%systemd_preun %{name}.service
%systemd_preun %{name}-boot.service

%postun
%systemd_postun %{name}.timer
%systemd_postun %{name}.service
%systemd_postun %{name}-boot.service

if [ $1 -eq 0 ]; then
    if [ -x /usr/sbin/selinuxenabled ] && /usr/sbin/selinuxenabled; then
        /usr/sbin/semanage permissive --delete insights_client_t || true
    fi
fi

# Clean up files created by insights-client that are unowned by the RPM
if [ $1 -eq 0 ]; then
    rm -f %{_sysconfdir}/cron.daily/insights-client
    rm -f %{_sysconfdir}/ansible/facts.d/insights.fact
    rm -f %{_sysconfdir}/ansible/facts.d/insights_machine_id.fact
    rm -f %{_sysconfdir}/motd.d/insights-client
    rm -rf %{_localstatedir}/lib/insights
    rm -rf %{_localstatedir}/log/insights-client
    rm -f %{_sysconfdir}/insights-client/.*.etag
fi


%clean
rm -rf %{buildroot}


%files
%config(noreplace) %{_sysconfdir}/insights-client/*.conf
%{_sysconfdir}/insights-client/insights-client.motd
%{_sysconfdir}/insights-client/.fallback.json*
%{_sysconfdir}/insights-client/.exp.sed
%{_sysconfdir}/insights-client/rpm.egg*
%{_bindir}/*
%{_unitdir}/*
%attr(444,root,root) %{_sysconfdir}/insights-client/*.pem
%attr(444,root,root) %{_sysconfdir}/insights-client/redhattools.pub.gpg
%{python3_sitelib}/insights_client/
%{_defaultdocdir}/%{name}
%{_presetdir}/*.preset
%attr(700,root,root) %dir %{_localstatedir}/log/insights-client/
%attr(700,root,root) %dir %{_localstatedir}/cache/insights-client/
%attr(750,root,root) %dir %{_localstatedir}/cache/insights/
%attr(750,root,root) %dir %{_localstatedir}/lib/insights/

%doc
%defattr(-, root, root)
%{_mandir}/man8/*.8.gz
%{_mandir}/man5/*.5.gz


%changelog
* Fri May 26 2023 Pino Toscano <ptoscano@redhat.com> - 0:3.1.7-12.1
- Conditionally run semanage only when SELinux is enabled (RHBZ#2210269)

* Thu Nov 10 2022 Alba Hita Catala <ahitacat@redhat.com> 0:3.1.7-12
- Set SELinux policy to permissive for rhcd_t module (RHBZ#2141443)

* Wed Nov 09 2022 Link Dupont <link@redhat.com> 0:3.1.7-11
- Include insights-core.egg as RPM source (RHBZ#2141087)

* Thu Oct 20 2022 Link Dupont <link@redhat.com> 0:3.1.7-10
- Ensure __python3 macro is globally set to platform-python (RHBZ#2075150)

* Mon Sep 12 2022 Gael Chamoulaud <gchamoul@redhat.com> 3.1.7-9
- Add /var/cache/insights-client/ directory in files directives (RHBZ#2126105)

* Fri Apr 08 2022 Gael Chamoulaud <gchamoul@redhat.com> 0:3.1.7-8
- Add several insights /var directories in files directives

* Mon Mar 14 2022 Gael Chamoulaud (Strider) <gchamoul@redhat.com> 0:3.1.7-7
- Update patches

* Mon Mar 14 2022 Gaël Chamoulaud <gchamoul@redhat.com> - 3.1.7-6
- Update patches
- Add DROP-IN-RPM patches_ignore rule for rdopkg

* Wed Feb 16 2022 Gaël Chamoulaud <gchamoul@redhat.com> - 3.1.7-5
- Restore insights-client-boot.service preun/postun (RHBZ#2024836)

* Wed Feb 02 2022 Gaël Chamoulaud <gchamoul@redhat.com> - 3.1.7-4
- Renaming "cloud.redhat.com" to "console.redhat.com" (RHBZ#2013799)

* Mon Jan 31 2022 Link Dupont <link@redhat.com> - 3.1.7-3
- Patch to fix an issue where insights-client continuously launches (RHBZ#2022191)

* Fri Jan 28 2022 Link Dupont <link@redhat.com> - 3.1.7-2
- Remove scriptlets referencing nonexistent files (RHBZ#2024836)

* Wed Oct 20 2021 Link Dupont <link@redhat.com> - 3.1.7-1
- New upstream release (Resolves RHBZ#2013799)
- Disable client metrics collection
- Create fallback.json dynamically at build time

* Tue Aug 24 2021 Link Dupont <link@redhat.com> - 3.1.6-1
- New upstream version

* Mon Aug  2 2021 Jeremy Crafts <jcrafts@redhat.com> - 3.1.5-1
- New upstream version

* Thu May 27 2021 Jeremy Crafts <jcrafts@redhat.com> - 3.1.4-2
- Replace platform-python-setuptools dependency with python3dist(setuptools)

* Mon May 17 2021 Jeremy Crafts <jcrafts@redhat.com> - 3.1.4-1
- New upstream version

* Tue Apr 20 2021 Jeremy Crafts <jcrafts@redhat.com> - 3.1.2-1
- New upstream version

* Thu Nov 19 2020 Link Dupont <link@redhat.com> - 3.1.1-1
- New upstream release (RHBZ#1899590)

* Thu Aug 20 2020 Link Dupont <link@redhat.com> - 3.1.0-3
- Backport patch to disable sleeping a systemd unit (RHBZ#1870656)

* Tue Aug 11 2020 Link Dupont <link@redhat.com> - 3.1.0-2
- Disable automatic registration of insights-client (RHBZ#1868116)

* Thu Jul 23 2020 Link Dupont <link@redhat.com> - 3.1.0-1
- First release with core collection as the default collection medium
- Manpage and configuration updates for core collection parameters (RHCLOUD-4266)

* Fri Jul 17 2020 Link Dupont <link@redhat.com> - 3.0.15-1
- Insights is automatically registered when a host is subscribed to RHSM (RHCLOUD-6538)
- Disable results checking by default (RHCLOUD-6204)

* Thu Jun 11 2020 Link Dupont <link@redhat.com> - 3.0.14-2
- Backport patch that fixes shellcheck warnings (RHCLOUD-6204)

* Wed Apr 29 2020 Link Dupont <link@redhat.com> - 3.0.14-1
- Removed printing to stdout in cron script (RHBZ#1828778)
- Add deprecation message when running legacy redhat-access-insights (RHCLOUD-5409)
- Update systemd timer to use timers.target (RHBZ#1798373)
- Fix an issue updating motd.d on relevant systems (RHCLOUD-6144)
- Update shipped core to version 3.0.161 (RHCLOUD-4457)
- Enable automatic checking for advisor results (RHCLOUD-4558)
- Ensure dependency on coreutils for timeout (RHCLOUD-5131)
- Build system converted to autotools (RHCLOUD-4333)

* Tue Feb 11 2020 Link Dupont <link@redhat.com> - 3.0.13-1
- Resolves: RHBZ#1753991

* Fri Dec 20 2019 Jeremy Crafts <jcrafts@redhat.com> - 3.0.12-0
- Update core egg (3.0.139-1)

* Wed Dec 11 2019 Jeremy Crafts <jcrafts@redhat.com> - 3.0.10-0
- Update core egg (3.0.137-1)
- Remove insights-client-run entrypoint
- Enable timer persistence
- Fix directory permissions
- Timer/service documentation for overriding parameters
- Resolves: BZ1772027

* Thu Sep 26 2019 Jeremy Crafts <jcrafts@redhat.com> - 3.0.8-2
- Resolves: BZ1753991

* Fri Aug 30 2019 Jeremy Crafts <jcrafts@redhat.com> - 3.0.8-0
- Modify MOTD logic and installation

* Thu Aug 29 2019 Jeremy Crafts <jcrafts@redhat.com> - 3.0.7-0
- Update core egg with bugfixes (3.0.121-1)
- Remove unused PyOpenSSL dependency
- Remove ACLs from previous installations
- Update service URL
- Add MOTD information
- Resolves: BZ1740286

* Tue Dec 11 2018 Jeremy Crafts <jcrafts@redhat.com> - 3.0.5-4
- Update core egg with bugfixes
- Resolves: BZ1656973

* Thu Nov 15 2018 Lumír Balhar <lbalhar@redhat.com> - 3.0.5-3
- Require platform-python-setuptools instead of python3-setuptools
- Resolves: rhbz#1650111

* Thu Sep 20 2018 Tomas Orsava <torsava@redhat.com> - 3.0.5-2
- Require the Python interpreter directly instead of using the package name
- Related: rhbz#1619153

* Wed Aug 8 2018 Jeremy Crafts <jcrafts@redhat.com> - 3.0.5-1
- Python 3 compatibility fixes
- Remove libcgroup dependency
- Resolves: BZ1510990
 
* Tue Aug 7 2018 Jeremy Crafts <jcrafts@redhat.com> - 3.0.5-0
- RHEL 8 build with bugfixes

* Tue Jun 5 2018 Jeremy Crafts <jcrafts@redhat.com> - 3.0.4-0
- Initial RHEL 8 build

* Wed Mar 14 2018 Richard Brantley <rbrantle@redhat.com> - 3.0.3-8
- Resolves: rhbz#1555041

* Fri Feb 16 2018 Kyle Lape <klape@redhat.com> - 3.0.3-6
- Persist systemd timer config between reboots

* Wed Feb 7 2018 Kyle Lape <klape@redhat.com> - 3.0.3-2
- Correct the version strings in Obsoletes and Provides in RPM spec

* Thu Jan 18 2018 Kyle Lape <klape@redhat.com> - 3.0.3-1
- RHEL 7 RPM now uses systemd service and timer instead of cron
- Addition of IO and CPU cgroup constraints
- Fixed memory cgroup constraint

* Wed Oct 18 2017 Richard Brantley <rbrantle@redhat.com> - 3.0.2-2
- Resolves BZ1498650, BZ1500008, BZ1501545, BZ1501552, BZ1501556, BZ1501561, BZ1501565, BZ1501566
- Fixes version migration logic
- Fixes symlink issues to old binary
- Fixes short ID analysis for images and containers
- Fixes Docker library detection
- Fixes image and container detection
- Fixes registration execution flow
- Fixes --version flag to print to stdout and include additional versioning information
- Includes Insights Core 3.0.3-1

* Wed Oct 4 2017 Richard Brantley <rbrantle@redhat.com> - 3.0.1-5
- Resolves BZ1498581
- Fixes sys.path issues
- Includes Insights Core 3.0.2-6

* Wed Sep 27 2017 Richard Brantley <rbrantle@redhat.com> - 3.0.0-4
- Initial build
