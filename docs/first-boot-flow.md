# First Boot Flow

1. Operator opens the wizard on `http://<appliance-ip>:8443`.
2. Wizard asks for the challenge key.
3. Wizard collects:
   - hostname and node FQDN
   - `nosadmin` password
   - management interface, IP, gateway, DNS, NTP, optional VLAN
   - data network mode: use management network or use separate data uplink
   - cluster mode: create first node or join existing cluster
   - cluster intent: create first node or join existing control plane
   - create mode: cluster name, DNS domain, and expected node count
   - join mode: existing cluster endpoint and join token placeholder
   - disk selection from discovered disks
4. Wizard submits config to `kdx-agent`.
5. Agent writes `/etc/kronosdx/config.yml`.
6. Agent runs Ansible.
7. Ansible deploys host packages, storage mounts, firewall rules, and RustFS.

## RustFS Cluster Note

RustFS multi-node Linux deployment expects a planned set of nodes and volumes, such as a `RUSTFS_VOLUMES` expression that includes all participating nodes. The Kubernetes Helm chart models distributed mode through replicas and PVCs rather than a simple RustFS-specific node join token.

For that reason, the wizard treats create/join as appliance orchestration intent for now. The concrete Kubernetes/RustFS bootstrap workflow will be wired after the target deployment model is finalized.
