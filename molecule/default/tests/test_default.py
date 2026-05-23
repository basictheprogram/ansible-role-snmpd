"""Molecule testinfra tests for ansible-role-snmpd.

These tests verify the converged state of the role: package installation,
service status, config file presence and permissions, rendered config content,
and basic SNMP reachability via snmpwalk.

Run during molecule verify:
    molecule verify

Or as part of the full test sequence:
    molecule test
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from testinfra.host import Host

# ---------------------------------------------------------------------------
# Constants — must match defaults/main.yml and molecule/default/converge.yml
# ---------------------------------------------------------------------------

CONF_PATH: str = "/etc/snmp/snmpd.conf"
CONF_MODE: int = 0o600
CONF_OWNER: str = "root"

# The default community string from defaults/main.yml
DEFAULT_COMMUNITY: str = "public"

# Expected snmpd config directives present in the default converge run
EXPECTED_DIRECTIVES: list[str] = [
    "com2sec",
    "group",
    "view",
    "access",
    "syslocation",
    "syscontact",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _snmpd_package(host: Host) -> str:
    """Return the expected snmpd package name for this platform.

    Matches the logic in vars/main.yml.
    """
    distro: str = host.system_info.distribution.lower()
    if "alpine" in distro:
        return "net-snmp"
    if any(d in distro for d in ("rhel", "centos", "rocky", "almalinux", "fedora", "ol")):
        return "net-snmp"
    # Debian, Ubuntu and everything else
    return "snmpd"


# ---------------------------------------------------------------------------
# Package
# ---------------------------------------------------------------------------


def test_snmpd_package_installed(host: Host) -> None:
    """The snmpd package must be installed after role converge."""
    pkg_name = _snmpd_package(host)
    pkg = host.package(pkg_name)
    assert pkg.is_installed, f"Package '{pkg_name}' is not installed on {host.system_info.distribution}"


# ---------------------------------------------------------------------------
# Config directory
# ---------------------------------------------------------------------------


def test_snmp_directory_exists(host: Host) -> None:
    """/etc/snmp directory must exist."""
    d = host.file("/etc/snmp")
    assert d.exists, "/etc/snmp directory does not exist"
    assert d.is_directory, "/etc/snmp is not a directory"


# ---------------------------------------------------------------------------
# Config file — presence, ownership, permissions
# ---------------------------------------------------------------------------


def test_config_file_exists(host: Host) -> None:
    """snmpd.conf must exist at the expected path."""
    f = host.file(CONF_PATH)
    assert f.exists, f"{CONF_PATH} does not exist"
    assert f.is_file, f"{CONF_PATH} is not a regular file"


def test_config_file_mode(host: Host) -> None:
    """Config must not be world-readable — mode 0600."""
    f = host.file(CONF_PATH)
    assert f.mode == CONF_MODE, f"{CONF_PATH} mode is {oct(f.mode)}, expected {oct(CONF_MODE)}"


def test_config_file_owner(host: Host) -> None:
    """Config must be owned by root."""
    f = host.file(CONF_PATH)
    assert f.user == CONF_OWNER, f"{CONF_PATH} owner is {f.user!r}, expected {CONF_OWNER!r}"


def test_config_file_group(host: Host) -> None:
    """Config must be group-owned by root."""
    f = host.file(CONF_PATH)
    assert f.group == "root", f"{CONF_PATH} group is {f.group!r}, expected 'root'"


# ---------------------------------------------------------------------------
# Config file — content correctness
# ---------------------------------------------------------------------------


def test_config_no_unrendered_jinja(host: Host) -> None:
    """No Jinja2 template expressions may appear in the rendered config."""
    content = host.file(CONF_PATH).content_string
    assert "{{" not in content, "Unrendered Jinja opening tag '{{' found in config"
    assert "}}" not in content, "Unrendered Jinja closing tag '}}' found in config"


def test_config_contains_ansible_managed_comment(host: Host) -> None:
    """Config must carry the ansible_managed banner comment."""
    content = host.file(CONF_PATH).content_string
    assert "Ansible" in content or "ansible" in content, "ansible_managed comment not found in rendered config"


@pytest.mark.parametrize("directive", EXPECTED_DIRECTIVES)
def test_config_contains_directive(host: Host, directive: str) -> None:
    """Each expected snmpd.conf directive must appear in the rendered config."""
    content = host.file(CONF_PATH).content_string
    assert directive in content, f"Expected directive '{directive}' not found in {CONF_PATH}"


def test_config_community_string_present(host: Host) -> None:
    """Default community string must appear in com2sec directive."""
    content = host.file(CONF_PATH).content_string
    assert DEFAULT_COMMUNITY in content, f"Community string '{DEFAULT_COMMUNITY}' not found in {CONF_PATH}"


def test_config_syslocation_present(host: Host) -> None:
    """Syslocation directive must appear in config."""
    content = host.file(CONF_PATH).content_string
    assert "syslocation" in content, f"'syslocation' directive not found in {CONF_PATH}"


def test_config_syscontact_present(host: Host) -> None:
    """Syscontact directive must appear in config."""
    content = host.file(CONF_PATH).content_string
    assert "syscontact" in content, f"'syscontact' directive not found in {CONF_PATH}"


def test_config_no_trailing_whitespace(host: Host) -> None:
    """No line in the rendered config should end with trailing whitespace."""
    content = host.file(CONF_PATH).content_string
    bad_lines = [i + 1 for i, line in enumerate(content.splitlines()) if line != line.rstrip()]
    assert not bad_lines, f"Trailing whitespace found on lines {bad_lines} in {CONF_PATH}"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


def test_snmpd_service_running(host: Host) -> None:
    """Snmpd service must be running after role converge."""
    svc = host.service("snmpd")
    assert svc.is_running, "snmpd service is not running"


def test_snmpd_service_enabled(host: Host) -> None:
    """Snmpd service must be enabled to start at boot."""
    svc = host.service("snmpd")
    assert svc.is_enabled, "snmpd service is not enabled"


# ---------------------------------------------------------------------------
# SNMP reachability — end-to-end smoke test
# ---------------------------------------------------------------------------


def test_snmpwalk_system_oid(host: Host) -> None:
    """Snmpwalk must return output for the system OID using the default community.

    This is an end-to-end test: it confirms the daemon is listening, the
    access-control config is correct, and the community string is accepted.
    Requires snmpwalk (net-snmp-utils / snmp package) to be present; the
    molecule verify play installs it transiently.
    """
    result = host.run(f"snmpwalk -v1 -c {DEFAULT_COMMUNITY} -t 5 localhost .1.3.6.1.2.1.1")
    assert result.rc == 0, f"snmpwalk failed (rc={result.rc}):\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert result.stdout.strip(), (
        f"snmpwalk returned no output — snmpd may not be listening or community '{DEFAULT_COMMUNITY}' is rejected"
    )


def test_snmpwalk_returns_sysname(host: Host) -> None:
    """Snmpwalk must return SNMPv2-MIB::sysName from the system group."""
    result = host.run(f"snmpwalk -v2c -c {DEFAULT_COMMUNITY} -t 5 localhost SNMPv2-MIB::sysName")
    assert result.rc == 0, f"snmpwalk sysName query failed (rc={result.rc}):\n{result.stdout}"
