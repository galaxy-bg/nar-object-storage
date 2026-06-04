from html import escape

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.agent_client import AgentClient, AgentUnavailable

app = FastAPI(title="NAR Object Storage Wizard")


def page(content: str) -> str:
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
          {content}
        </main>
      </body>
    </html>
    """


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
          <button type="submit">Review Configuration</button>
        </form>
      </section>
    """)


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
    data_network_mode: str = Form("shared"),
    data_interface: str = Form(""),
    data_ip: str = Form(""),
    data_prefix: str = Form(""),
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
        """), status_code=400)

    admin_user = "nosadmin"
    disk_list = ", ".join(escape(disk) for disk in disks)
    data_network = "separate data uplink" if data_network_mode == "separate" else "management network"
    data_ip_summary = f"{escape(data_ip)}/{escape(data_prefix)}" if data_ip else "uses management IP"
    return page(f"""
      <section class="panel">
        <h2>Review</h2>
        <p><strong>Hostname:</strong> {escape(hostname)}</p>
        <p><strong>Node FQDN:</strong> {escape(node_fqdn) if node_fqdn else "not set"}</p>
        <p><strong>Admin user:</strong> {escape(admin_user)}</p>
        <p><strong>Management interface:</strong> {escape(management_interface)}</p>
        <p><strong>Management IP:</strong> {escape(management_ip)}/{escape(management_prefix)}</p>
        <p><strong>Gateway:</strong> {escape(gateway)}</p>
        <p><strong>Data network:</strong> {data_network}</p>
        <p><strong>Data interface:</strong> {escape(data_interface) if data_interface else "management network"}</p>
        <p><strong>Data IP:</strong> {data_ip_summary}</p>
        <p><strong>Cluster mode:</strong> {escape(cluster_mode)}</p>
        <p><strong>Cluster name:</strong> {escape(cluster_name) if cluster_name else "not set"}</p>
        <p><strong>Cluster domain:</strong> {escape(cluster_domain) if cluster_domain else "not set"}</p>
        <p><strong>Expected nodes:</strong> {escape(expected_nodes) if expected_nodes else "not set"}</p>
        <p><strong>Join endpoint:</strong> {escape(join_endpoint) if join_endpoint else "not set"}</p>
        <p><strong>Disks:</strong> {disk_list}</p>
        <p class="hint">Deploy is not wired to kdx-agent yet. This preview confirms wizard navigation.</p>
        <form method="get" action="/setup">
          <button type="submit">Back to Setup</button>
        </form>
      </section>
    """)


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
    """)
