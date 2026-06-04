from html import escape

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.agent_client import AgentClient, AgentUnavailable

app = FastAPI(title="NAR Object Storage Wizard")

STEPS = ("Challenge", "Setup", "Review", "Deploy", "Complete")


def page(content: str, step: str = "Challenge") -> str:
    steps = render_steps(step)
    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>NAR Object Storage</title>
        <style>
          body {{
            background: #eef5f1;
            color: #18242b;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 0;
          }}
          body::before {{
            background:
              radial-gradient(circle at 62% 20%, rgba(79, 177, 134, 0.28), transparent 28%),
              linear-gradient(135deg, #111a22 0%, #1d2b34 52%, #101820 100%);
            content: "";
            height: 248px;
            left: 0;
            position: fixed;
            right: 0;
            top: 0;
            z-index: -1;
          }}
          main {{
            margin: 0 auto;
            max-width: 960px;
            padding: 36px 24px 48px;
          }}
          .brand {{
            align-items: end;
            border-bottom: 1px solid rgba(128, 242, 215, 0.18);
            display: flex;
            justify-content: space-between;
            margin-bottom: 28px;
            padding-bottom: 20px;
          }}
          .brand h1 {{
            color: #ffffff;
            font-size: 34px;
            font-weight: 750;
            letter-spacing: 0;
            margin: 0 0 4px;
          }}
          .brand p {{
            color: #80f2d7;
            font-size: 14px;
            font-weight: 650;
            margin: 0;
          }}
          .panel {{
            background: white;
            border: 1px solid #d8e3de;
            border-radius: 8px;
            box-shadow: 0 16px 44px rgba(16, 24, 32, 0.14);
            padding: 24px;
          }}
          .panel h2 {{
            color: #17242d;
            margin: 0 0 6px;
          }}
          .panel-intro {{
            color: #62716b;
            margin: 0 0 22px;
          }}
          .grid {{
            display: grid;
            align-items: start;
            gap: 18px 16px;
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }}
          .full-span {{
            grid-column: 1 / -1;
          }}
          .section-title {{
            border-top: 1px solid #e3ece8;
            color: #26343d;
            font-size: 16px;
            font-weight: 750;
            grid-column: 1 / -1;
            margin: 8px 0 0;
            padding-top: 18px;
          }}
          label {{
            display: grid;
            gap: 6px;
            font-size: 14px;
            font-weight: 650;
          }}
          input, select {{
            background: #fbfdfc;
            border: 1px solid #c8d5cf;
            border-radius: 6px;
            font: inherit;
            padding: 10px 12px;
          }}
          input:focus, select:focus {{
            border-color: #4fb186;
            box-shadow: 0 0 0 3px rgba(79, 177, 134, 0.2);
            outline: none;
          }}
          input:disabled, select:disabled {{
            background: #f1f5f3;
            color: #7a8983;
          }}
          .password-control {{
            display: grid;
            gap: 6px;
          }}
          .password-row {{
            display: flex;
          }}
          .password-row input {{
            border-bottom-right-radius: 0;
            border-right: 0;
            border-top-right-radius: 0;
            min-width: 0;
            width: 100%;
          }}
          .password-row button {{
            background: #edf5f1;
            border: 1px solid #c8d5cf;
            border-bottom-left-radius: 0;
            border-bottom-right-radius: 6px;
            border-top-left-radius: 0;
            border-top-right-radius: 6px;
            color: #26343d;
            margin: 0;
            min-width: 72px;
            padding: 0 12px;
          }}
          .password-row button:hover {{
            background: #dcece4;
          }}
          .password-message {{
            color: #8f1f17;
            display: none;
            font-size: 12px;
            font-weight: 650;
          }}
          .password-message.visible {{
            display: block;
          }}
          select[multiple] {{
            min-height: 118px;
          }}
          .check-row {{
            align-items: center;
            display: flex;
            gap: 10px;
            min-height: 42px;
          }}
          .check-row input {{
            height: 18px;
            width: 18px;
          }}
          .choice-grid {{
            display: grid;
            gap: 12px;
            grid-column: 1 / -1;
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }}
          .choice-card {{
            background: #fbfdfc;
            border: 1px solid #c8d5cf;
            border-radius: 8px;
            display: grid;
            gap: 8px;
            padding: 14px;
          }}
          .choice-card:focus-within {{
            border-color: #4fb186;
            box-shadow: 0 0 0 3px rgba(79, 177, 134, 0.16);
          }}
          .choice-card input {{
            height: 16px;
            margin: 0;
            width: 16px;
          }}
          .choice-title {{
            align-items: center;
            display: flex;
            gap: 8px;
            font-weight: 750;
          }}
          .choice-card .field-help {{
            margin-left: 24px;
          }}
          button {{
            background: #4fb186;
            border: 0;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            font: inherit;
            font-weight: 700;
            margin-top: 18px;
            padding: 11px 16px;
          }}
          button:hover {{
            background: #439c75;
          }}
          .button-row {{
            align-items: center;
            display: flex;
            gap: 12px;
            margin-top: 18px;
          }}
          .button-row form {{
            margin: 0;
          }}
          .secondary-button {{
            background: #edf5f1;
            color: #26343d;
          }}
          .secondary-button:hover {{
            background: #dcece4;
          }}
          pre {{
            background: #111a22;
            border-radius: 6px;
            color: #d9fff6;
            font-size: 13px;
            line-height: 1.45;
            overflow: auto;
            padding: 14px;
            white-space: pre-wrap;
          }}
          .error {{
            background: #fff1f0;
            border: 1px solid #ffc9c3;
            border-radius: 6px;
            color: #8f1f17;
            margin-bottom: 16px;
            padding: 10px 12px;
          }}
          .hint {{
            color: #62716b;
            font-size: 14px;
            margin-top: 10px;
          }}
          .field-help {{
            color: #687771;
            font-size: 12px;
            font-weight: 450;
            line-height: 1.4;
          }}
          .steps {{
            display: grid;
            gap: 8px;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            margin: -8px 0 22px;
          }}
          .step {{
            border-top: 3px solid rgba(128, 242, 215, 0.24);
            color: #d1e8e1;
            font-size: 13px;
            font-weight: 700;
            padding-top: 8px;
          }}
          .step.done {{
            border-color: #80f2d7;
            color: #80f2d7;
          }}
          .step.current {{
            border-color: #ffffff;
            color: #ffffff;
          }}
          @media (max-width: 720px) {{
            .grid {{
              grid-template-columns: 1fr;
            }}
            .brand {{
              align-items: start;
              display: grid;
              gap: 10px;
            }}
            .choice-grid {{
              grid-template-columns: 1fr;
            }}
            .steps {{
              grid-template-columns: 1fr;
            }}
          }}
        </style>
        <script>
          function syncDataNetworkFields() {{
            const mode = document.querySelector('input[name="data_network_mode"]:checked')?.value || "shared";
            const separate = mode === "separate";
            document.querySelectorAll("[data-network-field]").forEach((field) => {{
              field.disabled = !separate;
              if (!separate) {{
                field.value = "";
              }}
            }});
          }}
          function syncClusterFields() {{
            const mode = document.querySelector('input[name="cluster_mode"]:checked')?.value || "create";
            const create = mode === "create";
            document.querySelectorAll("[data-cluster-create]").forEach((field) => {{
              field.disabled = !create;
              if (!create) {{
                field.value = "";
              }}
            }});
            document.querySelectorAll("[data-cluster-join]").forEach((field) => {{
              field.disabled = create;
              if (create) {{
                field.value = "";
              }}
            }});
          }}
          function togglePasswordVisibility() {{
            const fields = document.querySelectorAll("[data-password-field]");
            const firstField = fields[0];
            if (!firstField) {{
              return;
            }}
            const show = firstField.type === "password";
            fields.forEach((field) => {{
              field.type = show ? "text" : "password";
            }});
            document.querySelectorAll("[data-password-toggle]").forEach((button) => {{
              button.textContent = show ? "Hide" : "Show";
            }});
          }}
          function validateAdminPassword() {{
            const password = document.querySelector('[name="admin_password"]');
            const confirm = document.querySelector('[name="admin_password_confirm"]');
            const message = document.querySelector("[data-password-message]");
            if (!password || !confirm || !message) {{
              return true;
            }}
            const mismatch = confirm.value.length > 0 && password.value !== confirm.value;
            confirm.setCustomValidity(mismatch ? "Passwords do not match." : "");
            message.classList.toggle("visible", mismatch);
            return !mismatch;
          }}
          window.addEventListener("DOMContentLoaded", () => {{
            document.querySelectorAll('input[name="data_network_mode"]').forEach((input) => {{
              input.addEventListener("change", syncDataNetworkFields);
            }});
            document.querySelectorAll('input[name="cluster_mode"]').forEach((input) => {{
              input.addEventListener("change", syncClusterFields);
            }});
            document.querySelectorAll("[data-password-field]").forEach((input) => {{
              input.addEventListener("input", validateAdminPassword);
            }});
            document.querySelectorAll("[data-password-toggle]").forEach((button) => {{
              button.addEventListener("click", togglePasswordVisibility);
            }});
            document.querySelectorAll("form").forEach((form) => {{
              form.addEventListener("submit", (event) => {{
                if (!validateAdminPassword()) {{
                  event.preventDefault();
                }}
              }});
            }});
            syncDataNetworkFields();
            syncClusterFields();
            validateAdminPassword();
          }});
        </script>
      </head>
      <body>
        <main>
          <div class="brand">
            <div>
              <h1>NAR Object Storage</h1>
              <p>Powered by KronosDX</p>
            </div>
          </div>
          {steps}
          {content}
        </main>
      </body>
    </html>
    """


def render_steps(current_step: str) -> str:
    current_index = STEPS.index(current_step) if current_step in STEPS else 0
    items = []
    for index, label in enumerate(STEPS):
        state = "current" if index == current_index else "done" if index < current_index else ""
        class_name = f"step {state}".strip()
        items.append(f'<div class="{class_name}">{index + 1}. {label}</div>')
    return f'<nav class="steps" aria-label="Setup progress">{"".join(items)}</nav>'


def interface_options(interfaces: list[dict], selected: str | None = None) -> str:
    if not interfaces:
        return '<option value="" disabled selected>No host interfaces discovered</option>'

    options = []
    for index, interface in enumerate(interfaces):
        name = str(interface.get("name", ""))
        if not name:
            continue
        state = str(interface.get("state", "UNKNOWN"))
        ipv4 = ", ".join(str(address) for address in interface.get("ipv4", [])) or "no IPv4"
        label = f"{name} - {state.lower()} - {ipv4}"
        is_selected = selected == name or (selected is None and index == 0)
        selected_attr = " selected" if is_selected else ""
        options.append(f'<option value="{escape(name)}"{selected_attr}>{escape(label)}</option>')

    return "\n".join(options) or '<option value="" disabled selected>No host interfaces discovered</option>'


def disk_options(disks: list[dict]) -> str:
    if not disks:
        return '<option value="" disabled>No unused data disks discovered</option>'

    options = []
    for disk in disks:
        path = str(disk.get("path", ""))
        if not path:
            continue
        size = human_size(int(disk.get("size") or 0))
        model = str(disk.get("model") or "unknown model")
        label = f"{path} - {size} - {model}"
        options.append(f'<option value="{escape(path)}">{escape(label)}</option>')

    return "\n".join(options) or '<option value="" disabled>No unused data disks discovered</option>'


def human_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if size < 1024 or unit == "PiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size_bytes} B"


def discovery() -> tuple[list[dict], list[dict], str]:
    try:
        client = AgentClient()
        return client.network_interfaces(), client.disks(), ""
    except AgentUnavailable as exc:
        return [], [], f"kdx-agent discovery is unavailable: {escape(str(exc))}"


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def optional_int(value) -> int | None:
    if value is None:
        return None
    value = str(value).strip()
    return int(value) if value else None


def hidden_inputs(payload: dict) -> str:
    fields = []
    for key, value in payload.items():
        if isinstance(value, list):
            for item in value:
                fields.append(f'<input type="hidden" name="{escape(key)}" value="{escape(str(item))}">')
        elif value is not None:
            fields.append(f'<input type="hidden" name="{escape(key)}" value="{escape(str(value))}">')
    return "\n".join(fields)


def deploy_payload(
    hostname: str,
    node_fqdn: str,
    admin_user: str,
    management_interface: str,
    management_ip: str,
    management_prefix: str,
    gateway: str,
    dns: str,
    ntp: str,
    management_vlan_id: str,
    data_network_mode: str,
    data_interface: str,
    data_ip: str,
    data_prefix: str,
    data_vlan_id: str,
    cluster_mode: str,
    cluster_name: str,
    cluster_domain: str,
    expected_nodes: str,
    join_endpoint: str,
    disks: list[str],
) -> dict:
    return {
        "hostname": hostname,
        "node_fqdn": node_fqdn,
        "admin_user": admin_user or "nosadmin",
        "management_interface": management_interface,
        "management_ip": management_ip,
        "management_prefix": optional_int(management_prefix),
        "gateway": gateway,
        "dns": split_csv(dns),
        "ntp": split_csv(ntp),
        "management_vlan_id": optional_int(management_vlan_id),
        "data_network_mode": data_network_mode,
        "data_interface": data_interface,
        "data_ip": data_ip,
        "data_prefix": optional_int(data_prefix),
        "data_vlan_id": optional_int(data_vlan_id),
        "cluster_mode": cluster_mode,
        "cluster_name": cluster_name,
        "cluster_domain": cluster_domain,
        "expected_nodes": optional_int(expected_nodes),
        "join_endpoint": join_endpoint,
        "disks": disks,
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return challenge_page()


@app.post("/challenge")
def verify_challenge(challenge_key: str = Form(...)):
    try:
        valid = AgentClient().verify_challenge(challenge_key)
    except AgentUnavailable as exc:
        return HTMLResponse(challenge_page(f"kdx-agent is unavailable: {escape(str(exc))}"), status_code=503)

    if not valid:
        return HTMLResponse(challenge_page("Invalid challenge key."), status_code=401)
    return RedirectResponse("/setup", status_code=303)


@app.get("/setup", response_class=HTMLResponse)
def setup() -> str:
    interfaces, disks, discovery_error = discovery()
    management_options = interface_options(interfaces)
    data_options = interface_options(interfaces, selected="")
    storage_options = disk_options(disks)
    discovery_error_html = f'<div class="error">{discovery_error}</div>' if discovery_error else ""

    return page(f"""
      <section class="panel">
        {discovery_error_html}
        <h2>Appliance Bootstrap</h2>
        <p class="panel-intro">Configure the first node identity, networks, cluster identity, and storage disks.</p>
        <form method="post" action="/review">
          <div class="grid">
            <div class="section-title">Identity</div>
            <label>Hostname
              <input name="hostname" required>
              <span class="field-help">Example: nar-node-01</span>
            </label>
            <label>Node FQDN
              <input name="node_fqdn">
              <span class="field-help">Example: nar-node-01.storage.kronosdx.local</span>
            </label>
            <label>Admin user
              <input name="admin_user_display" value="nosadmin" disabled>
              <input name="admin_user" value="nosadmin" type="hidden">
              <span class="field-help">Fixed appliance administrator account.</span>
            </label>
            <div class="password-control">
              <label for="admin_password">Admin password</label>
              <div class="password-row">
                <input id="admin_password" name="admin_password" type="password" required data-password-field>
                <button type="button" data-password-toggle>Show</button>
              </div>
            </div>
            <div class="password-control">
              <label for="admin_password_confirm">Confirm admin password</label>
              <div class="password-row">
                <input id="admin_password_confirm" name="admin_password_confirm" type="password" required data-password-field>
                <button type="button" data-password-toggle>Show</button>
              </div>
              <span class="password-message" data-password-message>Passwords do not match.</span>
            </div>

            <div class="section-title">Management Network</div>
            <label>Management interface
              <select name="management_interface" required>
                {management_options}
              </select>
              <span class="field-help">Discovered from the host through kdx-agent.</span>
            </label>
            <label>Management IP
              <input name="management_ip" required>
              <span class="field-help">Example: 192.168.20.101</span>
            </label>
            <label>Management prefix
              <input name="management_prefix" required>
              <span class="field-help">Example: 24</span>
            </label>
            <label>Gateway
              <input name="gateway" required>
              <span class="field-help">Example: 192.168.20.1</span>
            </label>
            <label>DNS servers
              <input name="dns">
              <span class="field-help">Example: 192.168.20.10, 8.8.8.8</span>
            </label>
            <label>NTP servers
              <input name="ntp">
              <span class="field-help">Example: time.storage.kronosdx.local, 192.168.20.20</span>
            </label>
            <label>Management VLAN ID
              <input name="management_vlan_id">
              <span class="field-help">Leave empty when no VLAN tagging is needed.</span>
            </label>

            <div class="section-title">Data Network</div>
            <div class="choice-grid">
              <label class="choice-card">
                <span class="choice-title">
                  <input name="data_network_mode" type="radio" value="shared" checked>
                  Use management network
                </span>
                <span class="field-help">S3 API uses the management IP. No extra data IP is requested.</span>
              </label>
              <label class="choice-card">
                <span class="choice-title">
                  <input name="data_network_mode" type="radio" value="separate">
                  Use separate data uplink
                </span>
                <span class="field-help">S3 API uses a dedicated data interface and IP.</span>
              </label>
            </div>
            <label>Data interface
              <select name="data_interface" data-network-field>
                {data_options}
              </select>
              <span class="field-help">Used for S3 traffic when a separate data uplink exists.</span>
            </label>
            <label>Data IP
              <input name="data_ip" data-network-field>
              <span class="field-help">Example: 10.10.50.101</span>
            </label>
            <label>Data prefix
              <input name="data_prefix" data-network-field>
              <span class="field-help">Example: 24</span>
            </label>
            <label>Data VLAN ID
              <input name="data_vlan_id" data-network-field>
              <span class="field-help">Leave empty when no VLAN tagging is needed.</span>
            </label>
            <div></div>

            <div class="section-title">Cluster</div>
            <div class="choice-grid">
              <label class="choice-card">
                <span class="choice-title">
                  <input name="cluster_mode" type="radio" value="create" checked>
                  Create first node
                </span>
                <span class="field-help">Prepare this appliance as the seed node. RustFS/Kubernetes bootstrap details will be generated later.</span>
              </label>
              <label class="choice-card">
                <span class="choice-title">
                  <input name="cluster_mode" type="radio" value="join">
                  Join existing cluster
                </span>
                <span class="field-help">Use this only after the control-plane join flow is defined for Kubernetes.</span>
              </label>
            </div>
            <label>Cluster name
              <input name="cluster_name" data-cluster-create>
              <span class="field-help">Example: nar-cluster-01</span>
            </label>
            <label>Cluster DNS domain
              <input name="cluster_domain" data-cluster-create>
              <span class="field-help">Example: storage.kronosdx.local</span>
            </label>
            <label>Expected node count
              <select name="expected_nodes" data-cluster-create>
                <option value="1">1 node - standalone evaluation</option>
                <option value="4" selected>4 nodes - distributed baseline</option>
                <option value="8">8 nodes</option>
                <option value="16">16 nodes</option>
              </select>
              <span class="field-help">RustFS distributed guidance starts from 4 servers for safe multi-node mode.</span>
            </label>
            <label>Existing cluster endpoint
              <input name="join_endpoint" data-cluster-join>
              <span class="field-help">Example: https://s3.nar-cluster-01.storage.kronosdx.local</span>
            </label>
            <label>Join token
              <input name="join_token" type="password" data-cluster-join>
              <span class="field-help">Placeholder for Kubernetes/control-plane join flow; not RustFS-specific yet.</span>
            </label>
            <div></div>

            <div class="section-title">Storage</div>
            <label class="full-span">Disk selection
              <select name="disks" multiple required>
                {storage_options}
              </select>
              <span class="field-help">Hold Command or Ctrl to select multiple disks. Values come from lsblk through kdx-agent.</span>
            </label>
          </div>
          <button type="submit">Next: Review</button>
        </form>
      </section>
    """, step="Setup")


@app.post("/review", response_class=HTMLResponse)
def review(
    hostname: str = Form(...),
    node_fqdn: str = Form(""),
    admin_user: str = Form("nosadmin"),
    admin_password: str = Form(...),
    admin_password_confirm: str = Form(...),
    management_interface: str = Form(...),
    management_ip: str = Form(...),
    management_prefix: str = Form(...),
    gateway: str = Form(...),
    dns: str = Form(""),
    ntp: str = Form(""),
    management_vlan_id: str = Form(""),
    data_network_mode: str = Form("shared"),
    data_interface: str = Form(""),
    data_ip: str = Form(""),
    data_prefix: str = Form(""),
    data_vlan_id: str = Form(""),
    cluster_mode: str = Form(...),
    cluster_name: str = Form(""),
    cluster_domain: str = Form(""),
    expected_nodes: str = Form(""),
    join_endpoint: str = Form(""),
    disks: list[str] = Form(...),
) -> str:
    if admin_password != admin_password_confirm:
        return HTMLResponse(page("""
          <section class="panel">
            <h2>Password mismatch</h2>
            <p class="panel-intro">The admin password and confirmation do not match.</p>
            <form method="get" action="/setup">
              <button type="submit">Back to Setup</button>
            </form>
          </section>
        """, step="Setup"), status_code=400)

    admin_user = "nosadmin"
    try:
        payload = deploy_payload(
            hostname=hostname,
            node_fqdn=node_fqdn,
            admin_user=admin_user,
            management_interface=management_interface,
            management_ip=management_ip,
            management_prefix=management_prefix,
            gateway=gateway,
            dns=dns,
            ntp=ntp,
            management_vlan_id=management_vlan_id,
            data_network_mode=data_network_mode,
            data_interface=data_interface,
            data_ip=data_ip,
            data_prefix=data_prefix,
            data_vlan_id=data_vlan_id,
            cluster_mode=cluster_mode,
            cluster_name=cluster_name,
            cluster_domain=cluster_domain,
            expected_nodes=expected_nodes,
            join_endpoint=join_endpoint,
            disks=disks,
        )
    except (TypeError, ValueError) as exc:
        return HTMLResponse(page(f"""
          <section class="panel">
            <div class="error">Invalid setup value: {escape(str(exc))}</div>
            <form method="get" action="/setup">
              <button type="submit">Back to Setup</button>
            </form>
          </section>
        """, step="Setup"), status_code=400)
    disk_list = ", ".join(escape(disk) for disk in disks)
    data_network = "separate data uplink" if data_network_mode == "separate" else "management network"
    data_ip_summary = f"{escape(data_ip)}/{escape(data_prefix)}" if data_ip else "uses management IP"
    dns_summary = escape(dns) if dns else "not set"
    ntp_summary = escape(ntp) if ntp else "not set"
    hidden = hidden_inputs(payload)
    return page(f"""
      <section class="panel">
        <h2>Review</h2>
        <p><strong>Hostname:</strong> {escape(hostname)}</p>
        <p><strong>Node FQDN:</strong> {escape(node_fqdn) if node_fqdn else "not set"}</p>
        <p><strong>Admin user:</strong> {escape(admin_user)}</p>
        <p><strong>Management interface:</strong> {escape(management_interface)}</p>
        <p><strong>Management IP:</strong> {escape(management_ip)}/{escape(management_prefix)}</p>
        <p><strong>Gateway:</strong> {escape(gateway)}</p>
        <p><strong>DNS:</strong> {dns_summary}</p>
        <p><strong>NTP:</strong> {ntp_summary}</p>
        <p><strong>Data network:</strong> {data_network}</p>
        <p><strong>Data interface:</strong> {escape(data_interface) if data_interface else "management network"}</p>
        <p><strong>Data IP:</strong> {data_ip_summary}</p>
        <p><strong>Cluster mode:</strong> {escape(cluster_mode)}</p>
        <p><strong>Cluster name:</strong> {escape(cluster_name) if cluster_name else "not set"}</p>
        <p><strong>Cluster domain:</strong> {escape(cluster_domain) if cluster_domain else "not set"}</p>
        <p><strong>Expected nodes:</strong> {escape(expected_nodes) if expected_nodes else "not set"}</p>
        <p><strong>Join endpoint:</strong> {escape(join_endpoint) if join_endpoint else "not set"}</p>
        <p><strong>Disks:</strong> {disk_list}</p>
        <div class="button-row">
          <form method="post" action="/deploy">
            {hidden}
            <button type="submit">Deploy Appliance</button>
          </form>
          <form method="get" action="/setup">
            <button class="secondary-button" type="submit">Back to Setup</button>
          </form>
        </div>
      </section>
    """, step="Review")


@app.post("/deploy", response_class=HTMLResponse)
def deploy(
    hostname: str = Form(...),
    node_fqdn: str = Form(""),
    admin_user: str = Form("nosadmin"),
    management_interface: str = Form(...),
    management_ip: str = Form(...),
    management_prefix: str = Form(...),
    gateway: str = Form(...),
    dns: list[str] = Form([]),
    ntp: list[str] = Form([]),
    management_vlan_id: str = Form(""),
    data_network_mode: str = Form("shared"),
    data_interface: str = Form(""),
    data_ip: str = Form(""),
    data_prefix: str = Form(""),
    data_vlan_id: str = Form(""),
    cluster_mode: str = Form(...),
    cluster_name: str = Form(""),
    cluster_domain: str = Form(""),
    expected_nodes: str = Form(""),
    join_endpoint: str = Form(""),
    disks: list[str] = Form(...),
) -> str:
    payload = {
        "hostname": hostname,
        "node_fqdn": node_fqdn,
        "admin_user": admin_user or "nosadmin",
        "management_interface": management_interface,
        "management_ip": management_ip,
        "management_prefix": optional_int(management_prefix),
        "gateway": gateway,
        "dns": dns,
        "ntp": ntp,
        "management_vlan_id": optional_int(management_vlan_id),
        "data_network_mode": data_network_mode,
        "data_interface": data_interface,
        "data_ip": data_ip,
        "data_prefix": optional_int(data_prefix),
        "data_vlan_id": optional_int(data_vlan_id),
        "cluster_mode": cluster_mode,
        "cluster_name": cluster_name,
        "cluster_domain": cluster_domain,
        "expected_nodes": optional_int(expected_nodes),
        "join_endpoint": join_endpoint,
        "disks": disks,
    }

    try:
        result = AgentClient().deploy(payload)
    except AgentUnavailable as exc:
        return HTMLResponse(page(f"""
          <section class="panel">
            <div class="error">Deploy failed because kdx-agent is unavailable: {escape(str(exc))}</div>
            <form method="get" action="/setup">
              <button type="submit">Back to Setup</button>
            </form>
          </section>
        """, step="Deploy"), status_code=503)

    status = "Deployment Complete" if result.get("ok") else "Deployment Failed"
    status_code = 200 if result.get("ok") else 500
    output = "\n".join(
        part for part in [str(result.get("stdout", "")), str(result.get("stderr", ""))] if part.strip()
    )
    output_html = escape(output.strip() or "No Ansible output captured.")
    complete_step = "Complete" if result.get("ok") else "Deploy"
    action_label = "Edit Setup" if result.get("ok") else "Back to Setup"
    return HTMLResponse(page(f"""
      <section class="panel">
        <h2>{status}</h2>
        <p><strong>Config:</strong> {escape(str(result.get("config_path", "unknown")))}</p>
        <p><strong>Log:</strong> {escape(str(result.get("log_path", "unknown")))}</p>
        <p><strong>Return code:</strong> {escape(str(result.get("returncode", "unknown")))}</p>
        <pre>{output_html}</pre>
        <form method="get" action="/setup">
          <button type="submit">{action_label}</button>
        </form>
      </section>
    """, step=complete_step), status_code=status_code)


def challenge_page(error: str | None = None) -> str:
    error_html = f'<div class="error">{error}</div>' if error else ""
    return page(f"""
      <section class="panel">
        {error_html}
        <form method="post" action="/challenge">
          <label>Challenge key
            <input name="challenge_key" type="password" autocomplete="one-time-code" required autofocus>
          </label>
          <button type="submit">Continue</button>
          <p class="hint">Use the key from /etc/kronosdx/challenge.key on the appliance.</p>
        </form>
      </section>
    """, step="Challenge")
