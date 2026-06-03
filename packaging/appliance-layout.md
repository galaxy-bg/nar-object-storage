# Appliance Layout

Target installed layout:

```text
/opt/kronosdx/
/etc/kronosdx/
/var/lib/kronosdx/
/kdx-data/
```

## Ownership Model

```text
/opt/kronosdx              root:root 0755
/etc/kronosdx              root:root 0700
/etc/kronosdx/secrets      root:root 0700
/var/lib/kronosdx          root:root 0755
/var/lib/kronosdx/agent    root:root 0750
/var/lib/kronosdx/wizard   root:root 0750
/var/lib/kronosdx/logs     root:root 0750
/kdx-data                  root:root 0755
```

## Source-to-Target Mapping

```text
ansible/   -> /opt/kronosdx/ansible/
agent/     -> /opt/kronosdx/agent/
wizard/    -> /opt/kronosdx/wizard/
scripts/   -> /opt/kronosdx/scripts/
systemd/   -> /opt/kronosdx/systemd/
```
