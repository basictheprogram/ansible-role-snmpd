# ansible-role-snmpd

[![CI](https://github.com/basictheprogram/ansible-role-snmpd/actions/workflows/molecule.yml/badge.svg)](https://github.com/basictheprogram/ansible-role-snmpd/actions/workflows/molecule.yml)
[![License](https://img.shields.io/github/license/basictheprogram/ansible-role-snmpd)](LICENSE)
[![Ansible Galaxy](https://img.shields.io/badge/ansible--galaxy-realtime.snmpd-blue)](https://galaxy.ansible.com/realtime/snmpd)
[![ansible-core](https://img.shields.io/badge/ansible--core-%3E%3D%202.20-informational)](https://docs.ansible.com/ansible/latest/index.html)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![GitHub Issues](https://img.shields.io/github/issues/basictheprogram/ansible-role-snmpd)](https://github.com/basictheprogram/ansible-role-snmpd/issues)

Install and configure the SNMP daemon (`snmpd`) on Alpine, Debian/Ubuntu,
Red Hat/Rocky/Alma, Fedora, and SUSE systems.

## Fork notice

This role is a fork of
[buluma/ansible-role-snmpd](https://github.com/buluma/ansible-role-snmpd),
originally authored and published to Ansible Galaxy by
[buluma](https://github.com/buluma) under the
[Apache-2.0 license](https://github.com/buluma/ansible-role-snmpd/blob/master/LICENSE).
This work would not exist without that initial effort — thank you.

Changes from upstream: modernised for ansible-core 2.20, ansible-lint 26.x,
`ansible_facts` dict syntax, testinfra/pytest verification, preflight
fail-fast OS check, conf.d drop-in support, and trap sink configuration.
Pull requests are not sent upstream.

---

## Requirements

- ansible-core ≥ 2.20
- Python ≥ 3.11 (on the controller, for testinfra)
- pip packages in [`requirements.txt`](requirements.txt):
  `ansible-core`, `molecule`, `molecule-plugins[docker]`,
  `pytest-testinfra`, `paramiko`, `docker`, `pre-commit`

---

## Supported platforms

| Platform | Versions |
|----------|----------|
| Ubuntu   | jammy (22.04), noble (24.04), resolute (26.04) |
| Debian   | bookworm (12), trixie (13) |
| EL (Rocky / Alma / RHEL) | 8, 9 |
| Fedora   | current |
| Alpine   | current |

Minimum ansible-core: **2.20**

---

## Role variables

All variables have defaults in [`defaults/main.yml`](defaults/main.yml).

### Agent address

```yaml
# Bind address(es) for the SNMP agent. When undefined snmpd uses its own
# default (udp:161 on all interfaces). Set explicitly to control which
# interfaces and protocols are active.
# snmpd_agentaddress: "0.0.0.0,[::]"          # all IPv4 + IPv6
# snmpd_agentaddress: "udp:161,udp6:[::1]:161" # localhost only
```

### SNMP access control

These four structures map directly to `snmpd.conf` access-control directives.

```yaml
# com2sec — maps a security name to a source address and community string.
# Restrict source to the NMS subnet in production; never leave 'default'.
# Store the community string in Ansible Vault in production.
snmpd_security_names:
  - name: notConfigUser
    source: default
    community: public

# group — maps a security name to a security model.
snmpd_groups:
  - name: notConfigGroup
    security_model: v1          # v1 or v2c
    security_name: notConfigUser
  - name: NotConfigGroup
    security_model: v2c
    security_name: NotConfigUser

# view — defines which OID subtree is visible.
snmpd_views:
  - name: systemview
    type: included              # included or excluded
    subtree: ".1.3.6.1.2.1.1"
    # mask: "ff"               # optional bitmask

# access — grants a group read/write/notify rights on a view.
snmpd_accesses:
  - group: notConfigGroup
    context: ""
    security_model: any         # any, v1, v2c, or usm
    security_level: noauth
    prefix: exact
    read: systemview
    write: none
    notif: none
```

### System identity

```yaml
snmpd_syslocation: Unknown
snmpd_syscontact: Root <root@localhost>
snmpd_dontlogtcpwrappersconnects: "true"   # string "true" or "false"
```

### Drop-in directory (conf.d)

When `snmpd_use_conf_d` is `true` the role creates the conf.d directory,
writes the rendered config there, and replaces `/etc/snmp/snmpd.conf` with
an `includeDir`-only stub.

```yaml
snmpd_use_conf_d: false
snmpd_conf_d_path: /etc/snmp/snmpd.conf.d
snmpd_conf_d_file: ansible-snmpd.conf
```

### Simple read-only community (rocommunity)

Use `snmpd_rocommunities` when you only need basic SNMPv1/v2c read-only
access to the entire MIB tree and don't need the full
com2sec/group/view/access chain. The two approaches can coexist, but
typically you use one or the other.

```yaml
snmpd_security_names: []
snmpd_groups: []
snmpd_views: []
snmpd_accesses: []

snmpd_rocommunities:
  - community: "{{ vault_snmp_rocommunity }}"
    source: 192.168.100.0/24   # restrict to NMS subnet; omit to allow any source
```

### Trap destinations

```yaml
# snmpd_trap_sinks:
#   - host: 192.168.1.100
#     community: "{{ vault_snmp_rocommunity }}"  # optional; omit to use daemon default
```

### Optional monitors

```yaml
# Process monitors (proc directives)
snmpd_processes:
  - name: sshd
    minimum: 1
  - name: ntalkd
    maximum: 4
  - name: sendmail
    minimum: 1
    maximum: 10

# Script monitors (exec directives)
snmpd_scripts:
  - name: shelltest
    program: /bin/sh
    arguments: /tmp/shtest

# Disk space monitors — minimum is free space in KB (kilobytes).
# 10000 KB ≈ 10 MB  |  102400 KB ≈ 100 MB  |  1048576 KB ≈ 1 GB
snmpd_disks:
  - path: /
    minimum: 10000   # KB
  - path: /var
    minimum: 5000    # KB

# Load average thresholds
snmpd_load:
  one_minute_average: 12
  five_minute_average: 14
  fifteen_minute_average: 14
```

---

## Example playbook

```yaml
---
- name: Configure snmpd
  hosts: all
  become: true
  gather_facts: true

  vars:
    snmpd_agentaddress: "0.0.0.0,[::]"
    snmpd_syslocation: "Server Room A, Building 1"
    snmpd_syscontact: "ops@example.com"
    snmpd_security_names:
      - name: ro
        source: 192.168.1.0/24
        community: "{{ vault_snmp_rocommunity }}"
    snmpd_groups:
      - name: ro_group
        security_model: v1
        security_name: ro
      - name: ro_group
        security_model: v2c
        security_name: ro
    snmpd_views:
      - name: systemonly
        type: included
        subtree: ".1.3.6.1.2.1.1"
      - name: systemonly
        type: included
        subtree: ".1.3.6.1.2.1.25.1"
    snmpd_accesses:
      - group: ro_group
        context: ""
        security_model: any
        security_level: noauth
        prefix: exact
        read: systemonly
        write: none
        notif: none
    snmpd_trap_sinks:
      - host: 192.168.1.100
        community: "{{ vault_snmp_rocommunity }}"

  roles:
    - role: realtime.snmpd
```

A worked example for a data-center monitored VM is in
[`examples/host_vars/datacenter_vm.yml`](examples/host_vars/datacenter_vm.yml).

---

## Preflight checks

`tasks/preflight.yml` runs before any state-changing work:

1. **OS compatibility** — fails immediately if the target OS family is not in
   the supported list (`Alpine`, `Debian`, `RedHat`, `Suse`, `Fedora`).
2. **Variable validation** — asserts type and value constraints on every
   user-facing variable with a descriptive `fail_msg` for each.

---

## Testing

Install dependencies:

```bash
pip install -r requirements.txt
```

```bash
# Fast lint pass — run before every commit
pre-commit run --all-files

# Iterative molecule run (skips create/destroy)
molecule converge && molecule verify

# Full scenario (create → converge → verify → destroy)
molecule test
```

Override the test platform via environment variables (matches the CI matrix):

```bash
image=ubuntu2404  molecule test   # Ubuntu 24.04
image=ubuntu2204  molecule test   # Ubuntu 22.04
image=debian12    molecule test   # Debian 12
image=debian13    molecule test   # Debian 13
image=rockylinux9 molecule test   # Rocky Linux 9
image=fedora40    molecule test   # Fedora 40
```

### Verification

Verification uses **testinfra** (pytest). Tests are in
`molecule/default/tests/test_default.py` and cover:

- `snmpd` package is installed
- `/etc/snmp/snmpd.conf` exists, mode `0600`, owned by `root`
- No unrendered Jinja2 expressions in the config
- All expected directives present (`com2sec`, `group`, `view`, `access`,
  `syslocation`, `syscontact`)
- No trailing whitespace in rendered config
- `snmpd` service is running and enabled
- `snmpwalk` returns output for the system OID (end-to-end smoke test)

---

## Upstream credit

This role began as
[buluma/ansible-role-snmpd](https://github.com/buluma/ansible-role-snmpd),
created and published to Ansible Galaxy by [buluma](https://github.com/buluma).
The core SNMP access-control model, the `snmpd.conf.j2` template structure,
and the multi-platform package mapping all originate from that work.
Licensed [Apache-2.0](https://github.com/buluma/ansible-role-snmpd/blob/master/LICENSE).

---

## License

[Apache-2.0](LICENSE)

Original work: copyright [buluma](https://github.com/buluma)
Fork modifications: copyright Bob Tanner
