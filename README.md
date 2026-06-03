# NAR Object Storage

Powered by KronosDX

Rocky Linux 9 based first-boot appliance framework for NAR Object Storage.

## Milestone 1 Scope

- First-boot wizard for appliance bootstrap
- Privileged host agent for controlled host operations
- Ansible deployment flow
- Podman-based RustFS backend bootstrap
- Lab-first VM workflow

## Bootstrap Flow

1. Operator opens the wizard on port `8443`.
2. Wizard validates the first-boot challenge key.
3. Operator enters appliance identity, management network, cluster mode, and disk selection.
4. Wizard sends the configuration to `kdx-agent`.
5. `kdx-agent` writes `/etc/kronosdx/config.yml`.
6. `kdx-agent` runs `/opt/kronosdx/ansible/site.yml`.
7. Ansible prepares the host, disks, firewall, Podman, and RustFS service.

## Repository Layout

See [docs/architecture.md](docs/architecture.md).

## Real Appliance Layout

The repository is source code. A deployed appliance uses:

```text
/opt/kronosdx/       application code and Ansible
/etc/kronosdx/       config, first-boot state, and secrets
/var/lib/kronosdx/   runtime state and logs
/kdx-data/           mounted storage disks
```

For lab staging:

```bash
TARGET_ROOT=/tmp/kdx-rootfs ./scripts/install-lab.sh
```

For a Rocky Linux lab VM:

```bash
sudo ./scripts/install-lab.sh
```

For a full lab bootstrap on Rocky Linux 9:

```bash
sudo ./scripts/install-lab.sh --install-packages --start-services
```
