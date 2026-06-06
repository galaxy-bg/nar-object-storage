# Maintenance Console

NAR Object Storage includes a local console maintenance concept for actions that should not be exposed through the normal first-boot wizard.

The initial helper is:

```bash
sudo /opt/kronosdx/scripts/nos-console.sh
```

Current menu:

- show version information
- show first-boot challenge key
- generate maintenance challenge response
- show factory reset commands
- show golden image preparation command
- root password reset placeholder

## Version File

The installer writes:

```text
/etc/kronosdx/version.yml
```

This file is intended for support and troubleshooting.

Example:

```yaml
product: NAR Object Storage
short_name: NOS
version: 0.1.0-milestone1
birth_moment: 2026-01-01T00:00:00Z
source_revision: unknown
install_layout: appliance
config_schema: 1
```

## Challenge Response

Maintenance challenge response uses:

```text
/etc/kronosdx/secrets/maintenance.key
```

The console generates a random challenge and an HMAC-SHA256 response. Later milestones can require that response before allowing sensitive actions such as factory reset or root password reset.

Factory reset and golden image preparation are local-console script workflows.
The menu prints the exact commands and confirmation phrases rather than running
destructive actions directly.
