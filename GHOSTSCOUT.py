#!/usr/bin/env python3
# ============================================================
# GHOSTSCOUT v3.1
# LIVE CYBER TERMINAL - KALI LINUX
# Local defensive monitoring only
# ============================================================

import os
import sys
import time
import math
import random
import socket
import platform
import shutil
from datetime import datetime

import psutil

from rich.console import Console, Group
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich import box

console = Console()

GREEN = "bright_green"
CYAN = "bright_cyan"
WHITE = "bright_white"
DIM = "grey50"

VERSION = "3.1"
START_TIME = time.time()

LOGS = []
MATRIX_WIDTH = 34
MATRIX_HEIGHT = 12

RADAR_SIZE = 17
RADAR_ANGLE = 0

BLIPS = [
    (3, 5),
    (10, 3),
    (12, 11),
    (5, 13),
    (8, 7)
]


# ============================================================
# UTILITIES
# ============================================================

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def now():
    return datetime.now().strftime("%H:%M:%S")


def add_log(message, level="INFO"):

    LOGS.append({
        "time": now(),
        "level": level,
        "message": message
    })

    if len(LOGS) > 30:
        LOGS.pop(0)


def format_bytes(value):

    for unit in ["B", "KB", "MB", "GB", "TB"]:

        if value < 1024:
            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{value:.1f} PB"


def uptime():

    seconds = int(time.time() - START_TIME)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds %= 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"


# ============================================================
# LIVE SYSTEM DATA
# ============================================================

def system_data():

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    swap = psutil.swap_memory()

    return {
        "cpu": psutil.cpu_percent(),
        "ram": memory.percent,
        "disk": disk.percent,
        "swap": swap.percent,
        "ram_used": format_bytes(memory.used),
        "ram_total": format_bytes(memory.total),
        "disk_used": format_bytes(disk.used),
        "disk_total": format_bytes(disk.total),
        "uptime": uptime()
    }


def network_data():

    counters = psutil.net_io_counters()

    return {
        "sent": counters.bytes_sent,
        "received": counters.bytes_recv
    }


def get_local_ip():

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        sock.connect(("192.0.2.1", 80))

        ip = sock.getsockname()[0]

        sock.close()

        return ip

    except OSError:
        return "Unavailable"


# ============================================================
# MATRIX RAIN ANIMATION
# ============================================================

def matrix_animation():

    chars = "0123456789ABCDEF"

    lines = []

    for _ in range(MATRIX_HEIGHT):

        line = Text()

        for _ in range(MATRIX_WIDTH):

            char = random.choice(chars)

            shade = random.choice([
                "green",
                "bright_green",
                "cyan",
                "bright_cyan"
            ])

            line.append(char, style=shade)

        lines.append(line)

    return Group(*lines)


# ============================================================
# RADAR ANIMATION
# ============================================================

def radar_animation():

    global RADAR_ANGLE

    RADAR_ANGLE = (RADAR_ANGLE + 8) % 360

    center = RADAR_SIZE // 2

    output = Text()

    for y in range(RADAR_SIZE):

        for x in range(RADAR_SIZE):

            dx = x - center
            dy = y - center

            distance = math.sqrt(dx * dx + dy * dy)

            if distance > center:
                output.append("  ")
                continue

            angle = (
                math.degrees(math.atan2(-dy, dx)) + 360
            ) % 360

            difference = abs(
                (angle - RADAR_ANGLE + 180) % 360 - 180
            )

            if (x, y) in BLIPS:
                output.append("● ", style="bold bright_cyan")

            elif distance < 1.2:
                output.append("◆ ", style="bright_green")

            elif difference < 12:
                output.append("▓ ", style="bright_green")

            elif abs(distance - 4) < .4:
                output.append("· ", style="green")

            elif abs(distance - 7) < .4:
                output.append("· ", style="green")

            elif abs(distance - 8) < .4:
                output.append("· ", style="green")

            elif x == center or y == center:
                output.append("· ", style="green")

            else:
                output.append("  ")

        output.append("\n")

    return Align.center(output)


# ============================================================
# SYSTEM OVERVIEW PANEL
# ============================================================

def make_bar(value, width=17):

    value = max(0, min(100, value))

    filled = round(value / 100 * width)

    return (
        f"[bright_green]{'█' * filled}[/]"
        f"[grey23]{'░' * (width-filled)}[/]"
    )


def system_panel(data):

    table = Table(
        expand=True,
        box=None,
        show_header=False
    )

    table.add_column("Name", style=CYAN, width=7)
    table.add_column("Value", width=8)
    table.add_column("Bar")

    for name in ["cpu", "ram", "disk", "swap"]:

        value = data[name]

        table.add_row(
            name.upper(),
            f"{value:.1f}%",
            make_bar(value)
        )

    table.add_row(
        "UPTIME",
        data["uptime"],
        ""
    )

    table.add_row(
        "MEMORY",
        data["ram_used"],
        ""
    )

    return Panel(
        table,
        title="[bold bright_green]SYSTEM OVERVIEW[/]",
        border_style=GREEN,
        box=box.DOUBLE
    )


# ============================================================
# NETWORK PANEL
# ============================================================

def network_panel(network, tx_rate, rx_rate):

    table = Table(
        box=None,
        show_header=False,
        expand=True
    )

    table.add_column("Label", style=CYAN)
    table.add_column("Value", style=WHITE)

    table.add_row(
        "Hostname",
        socket.gethostname()
    )

    table.add_row(
        "Interface",
        "Local interfaces"
    )

    table.add_row(
        "IP Address",
        get_local_ip()
    )

    table.add_row(
        "TX Rate",
        format_bytes(tx_rate) + "/s"
    )

    table.add_row(
        "RX Rate",
        format_bytes(rx_rate) + "/s"
    )

    table.add_row(
        "TX Total",
        format_bytes(network["sent"])
    )

    table.add_row(
        "RX Total",
        format_bytes(network["received"])
    )

    return Panel(
        table,
        title="[bold bright_green]NETWORK STATUS[/]",
        border_style=GREEN,
        box=box.DOUBLE
    )


# ============================================================
# CENTRAL LOGO
# ============================================================

def logo_panel():

    logo = Text(
        "\n"
        " ██████╗ ██╗  ██╗ ██████╗ ███████╗\n"
        "██╔════╝ ██║  ██║██╔═══██╗██╔════╝\n"
        "██║  ███╗███████║██║   ██║███████╗\n"
        "██║   ██║██╔══██║██║   ██║╚════██║\n"
        "╚██████╔╝██║  ██║╚██████╔╝███████║\n"
        " ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝\n",
        style="bold bright_green"
    )

    subtitle = Text(
        "\nADVANCED CYBER TERMINAL\n",
        style="bold bright_cyan"
    )

    version = Text(
        "\n[ GHOSTSCOUT v3.1 ]\n",
        style="bold bright_green"
    )

    tagline = Text(
        "\nKALI LINUX EDITION\n\n"
        "EXPLORE. ANALYZE. SECURE.\n",
        style="bright_white"
    )

    return Panel(
        Align.center(
            Group(logo, subtitle, version, tagline),
            vertical="middle"
        ),
        border_style=CYAN,
        box=box.DOUBLE
    )


# ============================================================
# LIVE LOGS
# ============================================================

def logs_panel():

    output = []

    for item in LOGS[-8:]:

        output.append(
            f"[grey70][{item['time']}][/]"
            f" [{GREEN}][{item['level']}][/]"
            f" {item['message']}"
        )

    if not output:
        output = ["[grey50]Waiting for events...[/]"]

    return Panel(
        Group(*output),
        title="[bold bright_green]LIVE LOGS[/]",
        border_style=GREEN,
        box=box.DOUBLE
    )


# ============================================================
# MENU PANEL
# ============================================================

def menu_panel():

    table = Table(
        expand=True,
        box=None,
        show_header=False
    )

    table.add_column("Key", style=GREEN, width=5)
    table.add_column("Menu", style=WHITE)
    table.add_column("Description", style=CYAN)

    options = [
        ("1", "Cyber Dashboard", "Live Monitor"),
        ("2", "System Diagnostics", "Check System"),
        ("3", "Network Status", "Local Information"),
        ("4", "Matrix Animation", "Visual Effect"),
        ("5", "Log Viewer", "View Logs"),
        ("6", "Information", "About"),
        ("0", "Exit", "Quit Terminal")
    ]

    for key, name, description in options:

        table.add_row(
            f"[{key}]",
            name,
            "— " + description
        )

    return Panel(
        table,
        title="[bold bright_green]GHOSTSCOUT MENU[/]",
        border_style=GREEN,
        box=box.DOUBLE
    )


# ============================================================
# DASHBOARD LAYOUT
# ============================================================

def build_dashboard(data, network, tx_rate, rx_rate):

    layout = Layout()

    layout.split_column(
        Layout(name="main", ratio=5),
        Layout(name="logs", ratio=1),
        Layout(name="footer", size=3)
    )

    layout["main"].split_row(
        Layout(name="left", ratio=3),
        Layout(name="center", ratio=4),
        Layout(name="right", ratio=3)
    )

    layout["left"].split_column(
        Layout(name="matrix", ratio=1),
        Layout(name="menu", ratio=1)
    )

    layout["matrix"].update(
        Panel(
            matrix_animation(),
            title="[bold bright_green]MATRIX BOOT STREAM[/]",
            border_style=GREEN,
            box=box.DOUBLE
        )
    )

    layout["menu"].update(menu_panel())

    layout["center"].update(logo_panel())

    layout["right"].split_column(
        Layout(name="system", ratio=1),
        Layout(name="network", ratio=1),
        Layout(name="radar", ratio=1)
    )

    layout["system"].update(system_panel(data))

    layout["network"].update(
        network_panel(network, tx_rate, rx_rate)
    )

    layout["radar"].update(
        Panel(
            radar_animation(),
            title="[bold bright_green]LIVE RADAR[/]",
            border_style=GREEN,
            box=box.DOUBLE
        )
    )

    layout["logs"].update(logs_panel())

    layout["footer"].update(
        Panel(
            Align.center(
                Text(
                    ">>> GHOSTSCOUT - HACK THE LIMITS <<<",
                    style="bold bright_green"
                )
            ),
            border_style=GREEN,
            box=box.DOUBLE
        )
    )

    return layout


# ============================================================
# LIVE DASHBOARD
# ============================================================

def live_dashboard():

    add_log("Live dashboard started")

    previous = psutil.net_io_counters()

    last_log = time.time()

    try:

        with Live(
            console=console,
            refresh_per_second=10,
            screen=True,
            transient=False
        ) as live:

            while True:

                current = psutil.net_io_counters()

                tx_rate = max(
                    0,
                    current.bytes_sent - previous.bytes_sent
                )

                rx_rate = max(
                    0,
                    current.bytes_recv - previous.bytes_recv
                )

                previous = current

                data = system_data()

                network = {
                    "sent": current.bytes_sent,
                    "received": current.bytes_recv
                }

                if time.time() - last_log > 5:

                    add_log(
                        "System monitoring refreshed"
                    )

                    last_log = time.time()

                dashboard = build_dashboard(
                    data,
                    network,
                    tx_rate,
                    rx_rate
                )

                live.update(dashboard)

                time.sleep(0.1)

    except KeyboardInterrupt:

        add_log("Live dashboard stopped")

        console.print(
            "\n[bold bright_green]Dashboard stopped.[/]"
        )


# ============================================================
# OTHER MENUS
# ============================================================

def diagnostics():

    data = system_data()

    console.print(
        Panel(
            f"""
CPU       : {data['cpu']}%
RAM       : {data['ram']}%
DISK      : {data['disk']}%
SWAP      : {data['swap']}%
RAM USED  : {data['ram_used']}
DISK USED : {data['disk_used']}
UPTIME    : {data['uptime']}
OS        : {platform.system()}
RELEASE   : {platform.release()}
MACHINE   : {platform.machine()}
PYTHON    : {platform.python_version()}
            """,
            title="SYSTEM DIAGNOSTICS",
            border_style=GREEN
        )
    )

    input("\nPress ENTER...")


def show_network():

    network = network_data()

    console.print(
        Panel(
            f"""
HOSTNAME : {socket.gethostname()}
LOCAL IP : {get_local_ip()}

TX TOTAL : {format_bytes(network['sent'])}
RX TOTAL : {format_bytes(network['received'])}
            """,
            title="NETWORK INFORMATION",
            border_style=CYAN
        )
    )

    input("\nPress ENTER...")


def show_logs():

    for item in LOGS:

        console.print(
            f"[grey70][{item['time']}][/]"
            f" [{GREEN}][{item['level']}][/]"
            f" {item['message']}"
        )

    input("\nPress ENTER...")


def about():

    console.print(
        Panel(
            """
GHOSTSCOUT v3.1

Kali Linux Cyber Terminal

LIVE FEATURES:
- Matrix Rain
- Animated Radar
- Live System Metrics
- Network Traffic Rates
- Animated Terminal Dashboard
- Live Activity Logs

LOCAL DEFENSIVE MONITORING ONLY.
            """,
            title="ABOUT GHOSTSCOUT",
            border_style=GREEN
        )
    )

    input("\nPress ENTER...")


# ============================================================
# MAIN
# ============================================================

def main():

    clear()

    add_log("GHOSTSCOUT kernel initialized")
    add_log("Local monitoring ready")

    while True:

        clear()

        console.print(
            Panel(
                Align.center(
                    Text(
                        "GHOSTSCOUT v3.1\n"
                        "ADVANCED CYBER TERMINAL",
                        style="bold bright_green"
                    )
                ),
                border_style=GREEN,
                box=box.DOUBLE
            )
        )

        console.print(menu_panel())

        choice = console.input(
            "\n[bold red]root@ghostscout[/]"
            "[bright_green] ~#[/] "
            "[white]Select Menu: [/]"
        ).strip()

        if choice == "1":
            live_dashboard()

        elif choice == "2":
            clear()
            diagnostics()

        elif choice == "3":
            clear()
            show_network()

        elif choice == "4":

            clear()

            try:
                while True:
                    console.print(matrix_animation())
                    time.sleep(0.08)
                    clear()

            except KeyboardInterrupt:
                pass

        elif choice == "5":
            clear()
            show_logs()

        elif choice == "6":
            clear()
            about()

        elif choice == "0":

            console.print(
                "\n[bold bright_green]GHOSTSCOUT OFFLINE[/]"
            )

            break

        else:

            console.print(
                "[bold red]Invalid menu option.[/]"
            )

            time.sleep(1)


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        console.print(
            "\n[bold red]GHOSTSCOUT TERMINATED[/]"
        )

    except Exception as error:
        console.print(
            f"\n[bold red]ERROR: {error}[/]"
        )

        sys.exit(1)
