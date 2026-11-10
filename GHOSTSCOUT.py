#!/usr/bin/env python3
# ==================================================
# GHOSTSCOUT V3.0
# ADVANCED CYBER TERMINAL
# KALI LINUX EDITION
# Created for local system monitoring
# ==================================================

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

# COLORS
G = "\033[92m"
C = "\033[96m"
R = "\033[91m"
Y = "\033[93m"
W = "\033[97m"
D = "\033[2m"
B = "\033[1m"
RESET = "\033[0m"

HOST = "127.0.0.1"
PORT = 8765

server = None
server_thread = None


# CLEAR TERMINAL
def clear():
    os.system("clear" if os.name == "posix" else "cls")


# MATRIX RAIN
def matrix_rain(duration=2):
    chars = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    width = shutil.get_terminal_size((80, 24)).columns

    end = time.time() + duration

    while time.time() < end:
        line = "".join(
            random.choice(chars + "   ")
            for _ in range(width)
        )
        print(G + line + RESET)
        time.sleep(0.06)

    clear()


# BANNER
def banner():
    print(G + B + r"""
   _____ _   _  ____  _____ _____ _____ _____
  / ____| | | |/ __ \ / ____/ ____|_   _|
 | |  __| |_| | |  | | (___| |      | |
 | | |_ |  _  | |  | |\___ \ |      | |
 | |__| | | | | |__| |____) | |_____| |_
  \_____|_| |_|\____/|_____/_____/|_____|

       G H O S T S C O U T
    ADVANCED CYBER TERMINAL
""" + RESET)

    print(C + "       KALI LINUX EDITION V3.0" + RESET)
    print()


# BOOT ANIMATION
def boot():
    clear()
    banner()

    messages = [
        "Initializing interface",
        "Loading terminal modules",
        "Checking Python runtime",
        "Preparing local dashboard",
        "Loading visual components",
        "GHOSTSCOUT READY"
    ]

    for msg in messages:
        print(G + "[  OK  ] " + RESET + msg)
        time.sleep(0.25)

    print()
    time.sleep(0.4)


# SYSTEM INFORMATION
def system_info():
    clear()

    print(G + B + "[ SYSTEM INTELLIGENCE ]" + RESET)

    print(C + "Hostname  : " + RESET + socket.gethostname())
    print(C + "Platform  : " + RESET + platform.platform())
    print(C + "Processor : " + RESET + platform.machine())
    print(C + "Python    : " + RESET + platform.python_version())
    print(C + "Time      : " + RESET + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    if sys.platform.startswith("linux"):
        print(C + "\n[ LOCAL NETWORK INTERFACES ]" + RESET)

        if shutil.which("ip"):
            os.system("ip -brief address")
        else:
            print("Command 'ip' unavailable.")

    input("\nPress ENTER to continue...")


# DASHBOARD HTML
HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>GHOSTSCOUT V3.0</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #020807;
    color: #00ff88;
    font-family: monospace;
}

header {
    padding: 25px;
    border-bottom: 1px solid #00ff88;
    background: #06140f;
}

h1 {
    font-size: 32px;
    letter-spacing: 6px;
    text-shadow: 0 0 15px #00ff88;
}

.subtitle {
    color: #65cfa1;
    letter-spacing: 3px;
}

.container {
    display: grid;
    grid-template-columns:
    repeat(auto-fit,minmax(230px,1fr));
    gap: 15px;
    padding: 20px;
}

.card {
    background: #07130f;
    border: 1px solid #087d50;
    padding: 20px;
    box-shadow: 0 0 15px #00ff8815;
}

.card h3 {
    color: #64ffb5;
}

.status {
    font-size: 25px;
    color: #65ffad;
    text-shadow: 0 0 10px #00ff88;
}

.radar {
    width: 170px;
    height: 170px;
    border: 1px solid #00ff88;
    border-radius: 50%;
    margin: auto;
    position: relative;
    overflow: hidden;

    background:
    repeating-radial-gradient(
    circle,
    transparent 0 25px,
    #087d50 26px 27px
    );
}

.radar::after {
    content: "";
    position: absolute;
    inset: 0;

    background:
    conic-gradient(
    transparent 70%,
    #00ff8866,
    transparent
    );

    animation: spin 3s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.terminal {
    min-height: 140px;
    line-height: 2;
    color: #8affbd;
    overflow-wrap: anywhere;
}

footer {
    padding: 20px;
    border-top: 1px solid #087d50;
    color: #65cfa1;
}

</style>
</head>

<body>

<header>
    <h1>GHOSTSCOUT</h1>

    <div class="subtitle">
        ADVANCED CYBER TERMINAL // V3.0
    </div>
</header>

<div class="container">

    <div class="card">
        <h3>SYSTEM STATUS</h3>
        <div class="status">ONLINE</div>
    </div>

    <div class="card">
        <h3>SECURITY MODE</h3>
        <div class="status">LOCAL ONLY</div>
    </div>

    <div class="card">
        <h3>LOCAL RADAR</h3>
        <div class="radar"></div>
        <p align="center">VISUAL DISPLAY</p>
    </div>

    <div class="card">
        <h3>ACTIVITY FEED</h3>
        <div class="terminal" id="feed">
            [OK] Interface initialized<br>
            [OK] Dashboard loaded<br>
            [SAFE] Local-only mode active
        </div>
    </div>

</div>

<footer>
    GHOSTSCOUT V3.0 |
    KALI LINUX EDITION |
    LOCAL DASHBOARD
</footer>

<script>

const messages = [
    "[OK] Local interface active",
    "[INFO] Dashboard refreshed",
    "[OK] Display service running",
    "[SAFE] Local-only mode enabled"
];

setInterval(() => {

    const feed = document.getElementById("feed");

    const line = document.createElement("div");

    line.textContent =
        messages[Math.floor(Math.random() * messages.length)];

    feed.appendChild(line);

    while (feed.children.length > 7) {
        feed.removeChild(feed.firstChild);
    }

}, 2500);

</script>

</body>
</html>
"""


# HTTP HANDLER
class DashboardHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return

        data = HTML.encode("utf-8")

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(data))
        )

        self.end_headers()

        self.wfile.write(data)

    def log_message(self, *args):
        pass


# START DASHBOARD
def launch_dashboard():

    global server, server_thread

    if server is None:

        try:
            server = HTTPServer(
                (HOST, PORT),
                DashboardHandler
            )

        except OSError as error:
            print(R + "[ERROR] " + str(error) + RESET)
            return

        server_thread = threading.Thread(
            target=server.serve_forever,
            daemon=True
        )

        server_thread.start()

    url = f"http://{HOST}:{PORT}"

    print(G + "\n[OK] DASHBOARD ONLINE" + RESET)
    print(C + url + RESET)

    webbrowser.open(url)

    input("\nPress ENTER to continue...")


# ABOUT
def about():

    clear()

    print(G + B + """
====================================
        GHOSTSCOUT V3.0
====================================
""" + RESET)

    print("Advanced Cyber Terminal")
    print("Kali Linux Edition")
    print("Local System Dashboard")
    print("Python Standard Library")

    print("\nNo remote attack functions.")
    print("Radar is a decorative visualization.")

    input("\nPress ENTER to continue...")


# MAIN MENU
def menu():

    while True:

        clear()
        banner()

        print(G + """
 [1] SYSTEM INFORMATION

 [2] LAUNCH DASHBOARD

 [3] MATRIX EFFECT

 [4] ABOUT GHOSTSCOUT

 [0] EXIT

""" + RESET)

        choice = input(
            G + "root@ghostscout:~# " + RESET
        ).strip()

        if choice == "1":

            system_info()

        elif choice == "2":

            launch_dashboard()

        elif choice == "3":

            matrix_rain(3)

        elif choice == "4":

            about()

        elif choice == "0":

            print(G + "\nGHOSTSCOUT SESSION CLOSED." + RESET)

            if server is not None:
                server.shutdown()
                server.server_close()

            break

        else:

            print(R + "Invalid option!" + RESET)
            time.sleep(1)


# ENTRY POINT
if __name__ == "__main__":

    try:
        boot()
        menu()

    except KeyboardInterrupt:
        print(G + "\nGHOSTSCOUT TERMINATED." + RESET)
