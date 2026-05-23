# Security Policy

This role installs and configures the SNMP daemon. It does not introduce
network services of its own beyond what snmpd itself provides. The most
common security concern is the community string — store it in Ansible Vault
in production.

## Supported Versions

These versions of [ansible-core](https://pypi.org/project/ansible-core/) are
supported:

| Version    | Supported          |
| ---------- | ------------------ |
| 2.20       | :white_check_mark: |
| < 2.20     | :x:                |

## Reporting a Vulnerability

Please [open an issue](https://github.com/basictheprogram/ansible-role-snmpd/issues)
describing the vulnerability. Include as much detail as you can — affected
platforms, steps to reproduce, and potential impact. You can expect an
acknowledgement within a few days and a status update as the investigation
progresses.
