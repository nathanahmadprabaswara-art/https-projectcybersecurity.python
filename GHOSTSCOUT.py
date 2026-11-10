import os
import sys
import time
import random
import socket
import platform
import threading
import webbrowser
import shutil
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = "127.0.0.1"
PORT = 8765

server = None
server_thread = None

GREEN = "\033[92m"
DARK_GREEN = "\033[32m"
WHITE = "\033[97m"
RED = "\033[91m"
RESET = "\033[0m"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    print(GREEN + r"""
   ________  ______  ______  ______  ______
  / ____/ / / / __ \/ ____/ / ____/ / ____/
 / / __/ /_/ / / / / /     / /     / __/
 / /_/ / __  / /_/ / /___  / /___  / /___
 \____/_/ /_/_____/\____/  \____/ /_____/

             G H O S T S C O U T
          LOCAL SECURITY DASHBOARD
""" + RESET)


def boot():
    clear()
    banner()

    tasks = [
        "Initializing interface",
        "Loading terminal modules",
        "Checking Python environment",
        "Preparing local dashboard",
        "Loading visual components",
        "Starting GHOSTSCOUT"
    ]

    for task in tasks:
        print(f"{GREEN}[+]{RESET} {task}")
        time.sleep(0.35)

    print(f"\n{GREEN}[OK] SYSTEM READY{RESET}")
    time.sleep(0.7)


def system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def get_html():
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GHOSTSCOUT Dashboard</title>

<style>
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background:
        radial-gradient(circle at top, #10251b 0%, #050b08 45%, #020403 100%);
    color: #d8ffe5;
    font-family: Arial, sans-serif;
    min-height: 100vh;
}

header {
    padding: 25px;
    border-bottom: 1px solid #145c36;
    background: rgba(0, 0, 0, 0.45);
    box-shadow: 0 0 25px #00ff6620;
}

header h1 {
    color: #00ff72;
    letter-spacing: 5px;
    text-shadow: 0 0 15px #00ff72;
}

header p {
    color: #78b990;
    margin-top: 8px;
    font-size: 12px;
    letter-spacing: 2px;
}

.container {
    max-width: 1200px;
    margin: auto;
    padding: 25px;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.card {
    background: linear-gradient(145deg, #0c1c13, #07100b);
    border: 1px solid #145c36;
    border-radius: 12px;
    padding: 22px;
    min-height: 150px;
    box-shadow: 0 0 15px #00ff6610;
    transition: 0.3s;
}

.card:hover {
    border-color: #00ff72;
    box-shadow: 0 0 25px #00ff6630;
    transform: translateY(-3px);
}

.card h2 {
    color: #00ff72;
    font-size: 15px;
    letter-spacing: 2px;
    margin-bottom: 18px;
}

.value {
    color: #e0ffe9;
    font-size: 18px;
    font-weight: bold;
    overflow-wrap: anywhere;
}

.muted {
    color: #78a98a;
    font-size: 12px;
    margin-top: 8px;
}

.status {
    color: #00ff72;
    font-weight: bold;
}

.radar {
    width: 180px;
    height: 180px;
    border: 1px solid #00ff72;
    border-radius: 50%;
    margin: 10px auto;
    position: relative;
    overflow: hidden;
    background:
        linear-gradient(90deg, transparent 49.5%, #00ff7240 50%, transparent 50.5%),
        linear-gradient(0deg, transparent 49.5%, #00ff7240 50%, transparent 50.5%),
        repeating-radial-gradient(circle, transparent 0 25px, #00ff7230 26px 27px);
    box-shadow: 0 0 20px #00ff7230;
}

.radar::after {
    content: "";
    position: absolute;
    width: 50%;
    height: 50%;
    left: 50%;
    top: 50%;
    transform-origin: top left;
    background: linear-gradient(135deg, #00ff7270, transparent 70%);
    animation: scan 4s linear infinite;
}

@keyframes scan {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.radar-dot {
    position: absolute;
    width: 6px;
    height: 6px;
    background: #00ff72;
    border-radius: 50%;
    box-shadow: 0 0 10px #00ff72;
    z-index: 2;
}

input {
    width: 100%;
    padding: 11px;
    margin: 6px 0;
    color: #d8ffe5;
    background: #020805;
    border: 1px solid #145c36;
    border-radius: 6px;
    outline: none;
}

input:focus {
    border-color: #00ff72;
    box-shadow: 0 0 10px #00ff7230;
}

button {
    padding: 11px 15px;
    margin-top: 8px;
    width: 100%;
    border: 1px solid #00ff72;
    border-radius: 6px;
    background: #07351b;
    color: #00ff72;
    font-weight: bold;
    cursor: pointer;
    transition: 0.2s;
}

button:hover {
    background: #00ff72;
    color: #001b0a;
    box-shadow: 0 0 15px #00ff72;
}

.device {
    background: #06140b;
    border: 1px solid #145c36;
    border-radius: 7px;
    padding: 10px;
    margin-top: 8px;
    overflow-wrap: anywhere;
}

.device strong {
    color: #00ff72;
}

.feed-item {
    padding: 9px;
    border-bottom: 1px solid #145c3630;
    font-size: 12px;
    color: #a9d9b7;
}

footer {
    text-align: center;
    padding: 25px;
    color: #47785a;
    font-size: 11px;
    letter-spacing: 2px;
}

@media(max-width: 600px) {
    header h1 {
        font-size: 22px;
    }

    .container {
        padding: 15px;
    }
}
</style>
</head>

<body>

<header>
    <h1>GHOSTSCOUT</h1>
    <p>LOCAL SECURITY DASHBOARD // AUTHORIZED INVENTORY</p>
</header>

<div class="container">

    <div class="card">
        <h2>SYSTEM STATUS</h2>
        <div class="value status">● ONLINE</div>
        <div class="muted">Dashboard running locally</div>
        <div class="muted" id="clock">Loading...</div>
    </div>

    <div class="card">
        <h2>SECURITY MODE</h2>
        <div class="value">LOCAL ONLY</div>
        <div class="muted">No remote scanning or attacks</div>
    </div>

    <div class="card">
        <h2>LOCAL RADAR</h2>
        <div class="radar" id="radar"></div>
        <div class="muted" style="text-align:center">
            Decorative visualization only
        </div>
    </div>

    <div class="card">
        <h2>ACTIVITY FEED</h2>
        <div id="feed">
            <div class="feed-item">[SYSTEM] Dashboard initialized</div>
            <div class="feed-item">[SYSTEM] Local mode enabled</div>
        </div>
    </div>

    <div class="card">
        <h2>AUTHORIZED DEVICE INVENTORY</h2>

        <input id="deviceName"
               type="text"
               placeholder="Device name">

        <input id="deviceAddress"
               type="text"
               placeholder="IP address or note">

        <button onclick="addDevice()">
            + ADD DEVICE
        </button>

        <div id="deviceList"></div>

        <div class="muted">
            Manual inventory. No automatic network discovery.
        </div>
    </div>

    <div class="card">
        <h2>ABOUT GHOSTSCOUT</h2>
        <div class="value">GHOSTSCOUT v1.0</div>
        <div class="muted">
            Local dashboard and authorized device inventory.
        </div>
    </div>

</div>

<footer>
    GHOSTSCOUT // LOCAL ENVIRONMENT // 2026
</footer>

<script>
const feed = document.getElementById("feed");
const radar = document.getElementById("radar");

function updateClock() {
    document.getElementById("clock").textContent =
        new Date().toLocaleString();
}

setInterval(updateClock, 1000);
updateClock();

const messages = [
    "[SYSTEM] Interface operational",
    "[SYSTEM] Local dashboard active",
    "[INFO] Inventory module ready",
    "[INFO] Visual radar refreshed",
    "[SYSTEM] Waiting for user input"
];

function addFeed(message) {
    const item = document.createElement("div");
    item.className = "feed-item";
    item.textContent =
        new Date().toLocaleTimeString() + " " + message;

    feed.prepend(item);

    while (feed.children.length > 7) {
        feed.removeChild(feed.lastElementChild);
    }
}

setInterval(() => {
    const message =
        messages[Math.floor(Math.random() * messages.length)];

    addFeed(message);
}, 4000);


// Decorative radar points only
function createRadarPoints() {
    radar.querySelectorAll(".radar-dot").forEach(dot => dot.remove());

    for (let i = 0; i < 5; i++) {
        const dot = document.createElement("div");
        dot.className = "radar-dot";

        dot.style.left = (15 + Math.random() * 70) + "%";
        dot.style.top = (15 + Math.random() * 70) + "%";

        radar.appendChild(dot);
    }
}

createRadarPoints();
setInterval(createRadarPoints, 3000);


// Manual device inventory
function addDevice() {
    const nameInput = document.getElementById("deviceName");
    const addressInput = document.getElementById("deviceAddress");

    const name = nameInput.value.trim();
    const address = addressInput.value.trim();

    if (!name || !address) {
        alert("Please fill in both fields.");
        return;
    }

    const device = document.createElement("div");
    device.className = "device";

    const title = document.createElement("strong");
    title.textContent = name;

    const detail = document.createElement("div");
    detail.textContent = address;

    const removeButton = document.createElement("button");
    removeButton.textContent = "REMOVE";

    removeButton.onclick = function() {
        device.remove();
        addFeed("[INVENTORY] Device removed");
    };

    device.appendChild(title);
    device.appendChild(detail);
    device.appendChild(removeButton);

    document.getElementById("deviceList").appendChild(device);

    nameInput.value = "";
    addressInput.value = "";

    addFeed("[INVENTORY] Device added manually");
}
</script>

</body>
</html>"""


class DashboardHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        content = get_html().encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()

        self.wfile.write(content)

    def log_message(self, format, *args):
        return


def launch_dashboard():
    global server, server_thread

    if server_thread and server_thread.is_alive():
        print(f"{GREEN}[INFO] Dashboard already running.{RESET}")
        webbrowser.open(f"http://{HOST}:{PORT}")
        return

    try:
        server = HTTPServer((HOST, PORT), DashboardHandler)

        server_thread = threading.Thread(
            target=server.serve_forever,
            daemon=True
        )

        server_thread.start()

        url = f"http://{HOST}:{PORT}"

        print(f"{GREEN}[OK] Dashboard started: {url}{RESET}")
        webbrowser.open(url)

    except OSError as error:
        print(f"{RED}[ERROR] {error}{RESET}")


def stop_dashboard():
    global server, server_thread

    if server:
        server.shutdown()
        server.server_close()
        server = None
        server_thread = None
        print(f"{GREEN}[OK] Dashboard stopped.{RESET}")
    else:
        print("[INFO] Dashboard is not running.")


def about():
    clear()
    banner()

    print(WHITE + "GHOSTSCOUT v1.0")
    print("Created for local dashboard visualization.")
    print("Standard Python libraries only.")
    print("Radar is decorative; device inventory is manual.")
    print("No remote scanning or attack functionality.")
    print(RESET)

    input("\nPress ENTER to continue...")


def menu():
    while True:
        clear()
        banner()

        print(f"{GREEN}[1]{RESET} System Information")
        print(f"{GREEN}[2]{RESET} Launch Dashboard")
        print(f"{GREEN}[3]{RESET} Matrix Effect")
        print(f"{GREEN}[4]{RESET} Stop Dashboard")
        print(f"{GREEN}[5]{RESET} About")
        print(f"{RED}[0]{RESET} Exit")

        choice = input("\nGHOSTSCOUT > ").strip()

        if choice == "1":
            clear()
            banner()

            info = system_info()

            for key, value in info.items():
                print(f"{GREEN}{key.upper():15}{RESET}: {value}")

            input("\nPress ENTER to continue...")

        elif choice == "2":
            launch_dashboard()
            input("\nPress ENTER to continue...")

        elif choice == "3":
            matrix_rain()

        elif choice == "4":
            stop_dashboard()
            input("\nPress ENTER to continue...")

        elif choice == "5":
            about()

        elif choice == "0":
            stop_dashboard()
            print(f"\n{GREEN}GHOSTSCOUT TERMINATED.{RESET}")
            sys.exit(0)

        else:
            print(f"{RED}Invalid option.{RESET}")
            time.sleep(1)


def matrix_rain():
    clear()

    try:
        for _ in range(20):
            line = "".join(
                random.choice("01ABCDEF0123456789")
                for _ in range(70)
            )

            print(GREEN + line + RESET)
            time.sleep(0.08)

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    try:
        boot()
        menu()

    except KeyboardInterrupt:
        stop_dashboard()
        print(f"\n{RED}Program interrupted.{RESET}")
        sys.exit(0)
