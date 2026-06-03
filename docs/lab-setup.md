# Lab Setup

## VM Requirements

- Rocky Linux 9 minimal
- 2 vCPU minimum
- 4 GB RAM minimum, 8 GB recommended
- 1 OS disk
- 1 or more extra data disks

Example:

```text
/dev/sda  OS disk
/dev/sdb  data disk 1
/dev/sdc  data disk 2
```

## Initial Packages

```bash
sudo dnf install -y git python3 python3-pip ansible-core podman firewalld xfsprogs jq
```

## Install Source Into Appliance Layout

From the cloned repository:

```bash
sudo ./scripts/install-lab.sh
```

This creates:

```text
/opt/kronosdx/
/etc/kronosdx/
/var/lib/kronosdx/
/kdx-data/
```

To test the filesystem layout without touching the host root:

```bash
TARGET_ROOT=/tmp/kdx-rootfs ./scripts/install-lab.sh
```

## Full Lab Install

On a fresh Rocky Linux 9 lab VM:

```bash
sudo ./scripts/install-lab.sh --install-packages --start-services
```

This will:

- install required packages with `dnf`
- copy source into `/opt/kronosdx`
- create `/etc/kronosdx`, `/var/lib/kronosdx`, and `/kdx-data`
- generate the first-boot challenge key
- generate the agent token
- install systemd units
- build the wizard image as `localhost/kdx-wizard:latest`
- enable and start `kdx-agent` and `kdx-wizard`

After the services start, open:

```text
http://<vm-ip>:8443
```

Read the challenge key on the VM:

```bash
sudo cat /etc/kronosdx/challenge.key
```

Check version metadata:

```bash
cat /etc/kronosdx/version.yml
```

Open the local maintenance console:

```bash
sudo /opt/kronosdx/scripts/nos-console.sh
```

## RustFS Discovery Tests

Single-node Podman test:

```bash
sudo ./scripts/rustfs-single-node-test.sh
```

Useful overrides:

```bash
sudo RUSTFS_DATA_DIR=/kdx-data/disk01/rustfs ./scripts/rustfs-single-node-test.sh
```

Multi-node planning draft:

```bash
RUSTFS_NODES=node1,node2,node3,node4 RUSTFS_DISKS_PER_NODE=4 ./scripts/rustfs-multi-node-plan.sh
```

The multi-node script only prints the planned `RUSTFS_VOLUMES` style configuration. It does not modify the host.
