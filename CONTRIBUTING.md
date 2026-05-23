# Contributing

Contributions are welcome and appreciated. This role is maintained by
[Bob Tanner](https://github.com/basictheprogram).

---

## Upstream

This role is a fork of
[buluma/ansible-role-snmpd](https://github.com/buluma/ansible-role-snmpd).
Pull requests are **not** sent upstream — changes here are specific to this
fork's modernisation goals (ansible-core 2.20, ansible-lint 26.x, testinfra
verification).

---

## How to contribute

### 1. Open an issue

When you spot a bug or have a feature idea, [open an
issue](https://github.com/basictheprogram/ansible-role-snmpd/issues) first.
A clear description — what you expected, what happened, which platform — helps
a lot and avoids duplicated effort.

### 2. Fork and clone

```shell
git clone git@github.com:YOURNAMESPACE/ansible-role-snmpd.git
cd ansible-role-snmpd
```

### 3. Make your changes

Keep commits focused and the commit message descriptive.

### 4. Test your changes

Install the test dependencies:

```shell
pip install -r requirements.txt
```

Run a quick lint pass before every commit:

```shell
pre-commit run --all-files
```

Run Molecule against a specific platform (requires Docker):

```shell
image=ubuntu2404 molecule test
image=debian12   molecule test
image=rockylinux9 molecule test
```

Run the full test matrix:

```shell
molecule test
```

Molecule uses **testinfra / pytest** for verification. Tests live in
`molecule/default/tests/test_default.py`.

### 5. Open a pull request

[Open a pull request](https://github.com/basictheprogram/ansible-role-snmpd/pulls)
against `main`. Reference the related issue number in the PR description
(e.g. `Closes #42`). CI will run lint and the full Molecule matrix automatically.

---

## License

By contributing you agree that your changes will be licensed under the
[Apache-2.0](LICENSE) license that covers this project.
