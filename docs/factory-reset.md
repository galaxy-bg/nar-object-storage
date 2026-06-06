# Factory Reset

NAR Object Storage has two local-console reset paths. These actions are intended
for appliance maintenance and lab re-provisioning, not for the normal first-boot
wizard flow.

## Config-Only Reset

```bash
sudo /opt/kronosdx/scripts/appliance-reset.sh --config-only
```

This resets the appliance to first-boot configuration mode without deleting
backend object data.

It removes:

- `/etc/kronosdx/config.yml`
- `/etc/kronosdx/firstboot.state`
- `/etc/kronosdx/challenge.key`
- `/var/lib/kronosdx/last-deploy.log`
- `/var/lib/kronosdx/storage-plan.yml`

It then regenerates the first-boot identity files through
`initialize-appliance-identity.sh` and restarts the wizard/agent services.

## Destroy-Data Reset

```bash
sudo /opt/kronosdx/scripts/appliance-reset.sh --destroy-data --confirm "RESET NAR OBJECT STORAGE"
```

This is destructive. It is meant for lab reuse or a deliberate appliance wipe.

It additionally:

- stops `rustfs.service`
- removes the `nar-object-storage`/legacy backend containers
- removes NAR Object Storage backend data directories under `/kdx-data/disk*/rustfs`
- removes backend credential files
- removes generated `/kdx-data/diskNN` fstab entries

The script requires an exact confirmation phrase before it will destroy data.

## Golden Image Preparation

```bash
sudo /opt/kronosdx/scripts/prepare-golden-image.sh --confirm "PREPARE NAR GOLDEN IMAGE"
```

Use this immediately before shutting down a VM and converting it to a template.

It keeps the installed appliance code, Python environment, systemd units, and
wizard container image, but removes node-specific identity and runtime state:

- appliance config and first-boot state
- challenge key and appliance secrets
- backend credentials and data
- deployment logs and storage plan
- backend/wizard containers
- SSH host keys
- machine-id
- shell history and journal logs

On the next boot, `kdx-identity.service` regenerates appliance identity files so
each clone starts with unique first-boot credentials.
