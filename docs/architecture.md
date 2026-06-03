# Architecture

NAR Object Storage is a Rocky Linux 9 based first-boot appliance.

## Components

- `kdx-wizard`: containerized FastAPI first-boot UI on port `8443`
- `kdx-agent`: privileged host FastAPI service on `127.0.0.1:7070`
- `ansible`: host deployment automation
- `rustfs`: Podman-managed S3-compatible object storage backend

## Network Model

- Management traffic uses the selected management interface and IP.
- S3 data traffic can either share the management IP or use a separate data uplink.
- When data traffic shares management, no separate data IP is configured.
- When a separate data uplink is selected, S3 should bind to the data IP.

## Cluster Bootstrap Model

The first-boot wizard records whether the appliance should create the first node or join an existing control plane. RustFS-specific multi-node deployment will be generated later from the selected deployment model.

Current RustFS assumptions:

- Linux distributed mode needs a planned node and volume list.
- Kubernetes distributed mode is expected to be managed through Helm or manifests with replicas and PVCs.
- Join token handling is reserved for the Kubernetes/control-plane layer, not assumed to be a native RustFS join mechanism.

## Repository Layout

```text
ansible/   deployment playbooks and roles
agent/     privileged host service
wizard/    first-boot web UI
systemd/   service unit files
scripts/   install and lab helpers
docs/      project documentation
packaging/ appliance filesystem layout notes
```
