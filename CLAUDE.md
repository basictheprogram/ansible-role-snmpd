# Claude Code project notes — ansible-role-snmpd

This is an Ansible role that installs and configures the SNMP daemon
(`snmpd`) on Alpine, Debian/Ubuntu, Red Hat/CentOS/Rocky, Fedora, and
SUSE systems.

Forked from [buluma/ansible-role-snmpd](https://github.com/buluma/ansible-role-snmpd).
Maintained by Bob Tanner <tanner@comap.org>.

---

## Behavioral guidelines

These four rules govern how to work in this repo. They bias toward
caution over speed — for trivial one-liner changes, use judgment.

### 1. Think before writing tasks

**Don't assume. Surface tradeoffs. Ask when uncertain.**

Before adding or changing anything:

* State assumptions explicitly. If a variable could live in `defaults/`,
  `vars/`, or a per-distro file, say which and why before choosing.
* If multiple approaches exist (e.g. `ansible.builtin.lineinfile` vs
  the Jinja2 template approach), present the tradeoff — don't pick
  silently. This role uses templates exclusively; lineinfile is
  explicitly not used for snmpd config.
* If the request is ambiguous (which task file? which template block?),
  name the ambiguity and ask. Don't guess and implement.
* If a simpler approach solves the problem, say so and push back.

### 2. Simplicity first

**Minimum tasks, variables, and template logic that solve the problem.**

* No new default variables beyond what the task being added requires.
* No Jinja2 abstraction for logic used in only one template.
* No `when:` conditions for scenarios that have no test coverage.
* No "future-proofing" of the public interface that wasn't asked for.
* If a template block is 30 lines and could be 10, rewrite it.

Ask: would a senior Ansible engineer call this overcomplicated? If yes,
simplify.

### 3. Surgical changes

**Touch only what the request requires. Clean up only your own mess.**

When editing existing tasks, templates, or defaults:

* Don't reformat adjacent YAML, fix unrelated comments, or clean up
  upstream code that wasn't broken by your change.
* Match the existing style — indentation, quoting, bullet character —
  even if you'd do it differently from scratch.
* If you notice unrelated dead code or stale variables, mention it;
  don't delete it without being asked.

When your change creates orphans:

* Remove `vars`, `when` conditions, or template blocks that YOUR change
  made unreachable.
* Don't remove pre-existing orphans unless explicitly asked.

Every changed line should trace directly to the request.

### 4. Goal-driven execution

**Define the success criteria before starting. Verify before declaring done.**

Transform requests into verifiable outcomes:

* "Add a new distro" → `meta/main.yml` updated, `vars/main.yml`
  extended if needed, `molecule converge` passes,
  `pre-commit run --all-files` clean.
* "Add a new snmpd config variable" → rendered template matches expected
  snmpd.conf syntax, `molecule verify` passes.
* "Fix an idempotency bug" → second `molecule converge` reports zero
  changed tasks.

For multi-step changes, state a brief plan before starting:

    1. Edit template  → verify: rendered snmpd.conf is valid
    2. Add task       → verify: molecule converge green
    3. Add test       → verify: molecule verify green
    4. Lint           → verify: pre-commit run --all-files clean

---

## Role architecture

The role is self-contained — no runtime role dependencies.

    defaults/main.yml          User-facing variables (lowest precedence).
                               All SNMP access structures, system info,
                               and optional feature lists live here.
    vars/main.yml              OS-family variable mapping. Resolves
                               snmpd_packages (package name differs by OS)
                               and snmpd_service at runtime.
    tasks/assert.yml           Input validation — run once, delegated to
                               localhost. Validates every user-facing
                               variable before any change is made.
    tasks/main.yml             Orchestrates: assert → install package →
                               configure snmpd.conf → start/enable service
    handlers/main.yml          Restarts snmpd when config changes.
    templates/snmpd.conf.j2    Renders /etc/snmp/snmpd.conf from role vars.
    molecule/default/          Molecule test scenario (converge, prepare,
                               verify).

### Variable loading order

1. `defaults/main.yml` — all user-facing defaults (lowest precedence).
2. `vars/main.yml` — resolves `snmpd_packages` and `snmpd_service`
   using `ansible_os_family` lookup. This overrides defaults.
3. Inventory / playbook variables override anything from steps 1–2.

### Config management — templates only

All snmpd configuration is managed via `templates/snmpd.conf.j2`.
`ansible.builtin.lineinfile` is not used. Do not introduce lineinfile
tasks; they produce non-idempotent, hard-to-audit config.

---

## Conventions

* **FQCN**: all module calls use fully-qualified collection names
  (`ansible.builtin.template`, `ansible.builtin.package`,
  `ansible.builtin.service`, `ansible.builtin.assert`). The
  `.ansible-lint` config enforces this via `fqcn-builtins`.
* **`become: true`**: set explicitly on privileged tasks, not at
  play level.
* **Lint**: `.ansible-lint`, `.yamllint`, `.pre-commit-config.yaml`
  define the rules. Run `pre-commit run --all-files` before declaring
  any work done.
* **Community strings**: `snmpd_security_names[].community` is the
  SNMPv1/v2c community string — effectively a shared password for SNMP
  access. Store it in Ansible Vault in production. No `no_log` is
  currently applied; consider adding it if community strings appear
  in task output.
* **Idempotency**: every task must be safe to re-run. Template tasks
  are inherently idempotent; package tasks use `state: present`.

## Supported platforms

| Platform | Versions |
|----------|----------|
| Alpine   | all |
| EL (Rocky, Alma, RHEL) | all |
| Debian   | all |
| Fedora   | all |
| Ubuntu   | all |

Minimum ansible-core: **2.12**

Package name by OS family: `snmpd` (Debian default), `net-snmp`
(Alpine, RedHat, Suse). Service name: `snmpd` on all platforms.

When adding a new platform:

1. Add the distro to `meta/main.yml` platforms.
2. Extend `vars/main.yml` with a new OS family key if the package or
   service name differs.
3. Update `README.md` platform table.
4. Add or update the molecule platform in
   `molecule/default/molecule.yml`.

## Testing locally

* `pre-commit run --all-files` — fast lint/format pass. Run before
  every commit.
* `molecule converge` then `molecule verify` — fast iteration during
  template/task work; skips the destroy/create cycle.
* `molecule test` — full role exercise. Run before declaring a change
  done.

### Molecule scenario

Located at `molecule/default/`. Uses:

* `prepare.yml` — refreshes the package cache (apt/dnf/apk) so converge installations succeed; no external role dependency.
* `converge.yml` — applies `realtime.snmpd`.
* `verify.yml` — verifies snmpd installation and configuration state.

---

## Role-specific notes

### Role overview

Installs and configures the SNMP daemon (`snmpd`) on Alpine,
Debian/Ubuntu, Red Hat/CentOS/Rocky, Fedora, and SUSE. Manages the
full snmpd.conf lifecycle via a Jinja2 template covering security names,
groups, views, access controls, system location/contact, process
monitoring, disk monitoring, and load thresholds.

### Source of truth

No `DESIGN.md` exists in this role yet. This `CLAUDE.md` and the
existing code are the current source of truth. Add a `DESIGN.md` before
making any significant structural changes — see Implementation order
below.

### Secrets

`snmpd_security_names[].community` is the SNMPv1/v2c community string
— treat it as a secret in production:

* Store in Ansible Vault, not in plain inventory.
* Do not pass it as a task argument in a way that appears in Ansible
  output (the template task writes it to disk; that is acceptable).

No variables in `defaults/main.yml` or `vars/main.yml` match the
patterns `_key`, `_token`, `_password`, or `_secret`.

### Commit scopes

Role-specific subsystem scopes: `package`, `config`, `service`,
`assert`, `defaults`, `vars`, `meta`, `molecule`.

### Settled decisions

<!-- TODO: fill in settled decisions -->

### Open questions

<!-- TODO: fill in open questions -->

### Implementation order

The role is functionally complete. Remaining work items — one focused
session and one commit each:

1. **Add `DESIGN.md`** — document the snmpd config model, settled
   decisions (template-only, no lineinfile, vars/main.yml OS mapping),
   and open questions (SNMPv3 support, community string `no_log`).
2. **Review `README.md`** — update author/maintainer section to reflect
   the fork; verify variable documentation is complete.
3. **Evaluate `no_log`** — determine whether the configure task should
   set `no_log: true` given that community strings may appear in
   changed-task output. Add if needed.
4. **Review `molecule/default/verify.yml`** — confirm assertions
   validate snmpd.conf content (not just service state) and that a
   test community string exercises the full template.
5. **SNMPv3 user support (optional)** — current template handles only
   v1/v2c community-based access. If v3 (USM) is needed, add
   `snmpd_users` to `defaults/main.yml` and extend
   `templates/snmpd.conf.j2`.
6. **Verify pre-commit hooks pass** — hooks were updated by the
   template sync (2026-05-23); run `pre-commit run --all-files` to
   confirm all new hooks are satisfied.

### Consumer side notes

This role is consumed from playbooks as `realtime.snmpd` (Ansible Galaxy
namespace). When asked about consumer-side changes, ask which inventory
repo to operate on — it is not in this directory tree.

Minimal playbook:

```yaml
- name: configure snmpd
  hosts: all
  become: true
  gather_facts: true
  roles:
    - role: realtime.snmpd
```

This role has no Galaxy role dependencies — `molecule/default/prepare.yml`
primes the package cache using built-in modules only.

Key variables to set per host or group:

```yaml
snmpd_syslocation: "Server Room A, Building 1"
snmpd_syscontact: "ops@example.org"
snmpd_security_names:
  - name: myNet
    source: 192.168.1.0/24
    community: "{{ vault_snmp_rocommunity }}"
```

---

## Commit message guide

You are an expert DevOps engineer and professional git commit message
writer. When generating a commit message, follow these steps exactly.

### Step 1 — Retrieve changes

Run:

    git diff --cached

Analyze the full staged diff. This is the **single source of truth**
for what will be committed.

### Step 2 — Understand the change

Determine:

* The **primary purpose** of the change
* The **type of change** (feature, bug fix, refactor, etc.)
* The **most relevant scope** within the role
* Whether the change introduces a **breaking change** for role consumers

Pay special attention to:

* Changes to `defaults/main.yml` — any renamed or removed variable is a
  breaking change for consumers who set it in inventory
* Changes to `templates/snmpd.conf.j2` — rendered output must remain
  valid snmpd.conf syntax; test with snmpd -C -c /etc/snmp/snmpd.conf
* Changes to `vars/main.yml` — affects OS family package and service
  name resolution
* Changes to `tasks/assert.yml` — validation changes affect which
  variable combinations are accepted
* Changes to `meta/main.yml` — Galaxy metadata, min Ansible version,
  or supported platform list

### Step 3 — Select commit type

Use Conventional Commits:

* `feat` — new task, variable, template capability, or platform support
* `fix` — bug fix or idempotency correction
* `docs` — README, CLAUDE.md, DESIGN.md, inline comments
* `style` — YAML formatting, whitespace, ansible-lint cleanup
* `refactor` — restructure tasks/templates without behavior change
* `perf` — performance improvement (e.g., reduced task runs)
* `test` — molecule scenarios, verify playbook, lint config
* `chore` — galaxy metadata, dependencies, tooling
* `ci` — CI workflows, pre-commit hooks

### Step 4 — Determine scope

Common scopes: `package`, `config`, `service`, `assert`, `defaults`,
`vars`, `meta`, `molecule`.

Only include a scope when it adds clarity. Prefer the functional scope
for feature-driven changes (`feat(config): ...`) and the structural
scope for housekeeping (`chore(meta): ...`).

### Step 5 — Write the commit message

Format exactly as:

    <type>[optional scope]: <short summary (<=50 chars)>

    <body wrapped at 72 characters>

    [optional footer(s)]

**Subject line rules:**

* Use **imperative mood** ("Add", "Fix", "Update", "Remove")
* Maximum **50 characters**
* Describe the **result**, not the implementation

**Body rules** (required for non-trivial changes):

Explain **why the change was made**, focusing on:

* What deployment scenario or upstream behavior motivated it
* What downstream role consumers need to know to upgrade safely
* Any ansible-core or platform version constraints involved

**Bullet rules:**

* Use `*` (asterisk) for all bullets — never `-` or `•`
* Nested bullets indented with two spaces
* No Markdown formatting of any kind

### Breaking changes

A change is breaking when it:

* Renames or removes a default variable
* Changes a default value in a way that alters snmpd behavior
* Changes the `snmpd_security_names` or `snmpd_accesses` item schema
* Drops support for an Ansible version or platform
* Renames a handler

If the diff introduces a breaking change:

* Add `!` after the type/scope in the subject
* Include a footer: `BREAKING CHANGE: <description>`

Examples:

    feat(config): add SNMPv3 user configuration support
    fix(assert): correct syslocation type check (string not iterable)
    chore(meta): bump min_ansible_version to 2.20
    test(molecule): add verify assertions for snmpd.conf content
    docs: add DESIGN.md with settled decisions and open questions

    feat(defaults)!: rename snmpd_community to snmpd_security_names

    BREAKING CHANGE: snmpd_community is now snmpd_security_names; update
    inventory vars before upgrading.

### Step 6 — Output rules

Return **only the commit message** — no explanation, no analysis,
no diff, no markdown formatting, no code fences. The output will be
pasted directly into a git commit editor.
