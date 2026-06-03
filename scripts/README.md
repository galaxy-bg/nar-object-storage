# Scripts

Installer and lab helper scripts live here.

## Appliance Helpers

- `install-appliance.sh`: copy the repository into the target appliance layout.
- `install-lab.sh`: compatibility wrapper for `install-appliance.sh`.
- `generate-challenge-key.sh`: generate a first-boot challenge key.
- `run-local-agent.sh`: run the local agent for development.
- `run-local-wizard.sh`: run the local wizard for development.
- `nos-console.sh`: local appliance console menu for version and maintenance challenge workflows.

## RustFS Discovery Helpers

- `rustfs-single-node-test.sh`: start a single-node RustFS Podman test container.
- `rustfs-multi-node-plan.sh`: print a multi-node volume/config planning draft.

These RustFS scripts are for requirement discovery. They are not final production deployment scripts.
