#!/usr/bin/env python3
# ============================================================
# GHOSTSCOUT v3.0
# ADVANCED CYBER TERMINAL - KALI LINUX EDITION
# Local System & Network Monitoring
# ============================================================

import os
import sys
import time
import socket
import random
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
from rich.columns import Columns
from rich import box


# ============================================================
# CONFIGURATION
# ============================================================

APP = "GHOSTSCOUT"
VERSION = "3.0"

console = Console()

GREEN = "bright_green"
CYAN = "bright_cyan"
WHITE = "white"
MUTED = "grey70"
RED = "bright_red"

LOGS = []


# ============================================================
# TERMINAL UTILITIES
# ============================================================

def clear():
    console.clear()


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def add_log(message, level="INFO"):
    LOGS.append({
        "time": timestamp(),
        "level": level,
        "message": message
    })

    if len(LOGS) > 100:
        LOGS.pop(0)


def boot_sequence():

    clear()

    console.print(
        Panel(
            Align.center(
                Text(
                    "G H O S T S C O U T\n"
                    "ADVANCED CYBER TERMINAL v3.0",
                    style="bold bright_green"
                ),
                vertical="middle"
            ),
            border_style=GREEN,
            box=box.DOUBLE,
            padding=2
        )
    )

    tasks = [
        "Initializing GhostScout Kernel v3.0",
        "Loading terminal modules",
        "Preparing system diagnostics",
        "Detecting local network interfaces",
        "Initializing dashboard",
        "Welcome to GHOSTSCOUT"
    ]

    for task in tasks:

        console.print(
            f"[{GREEN}][+][/{GREEN}] {task} ... "
            f"[{GREEN}][OK][/{GREEN}]"
        )

        time.sleep(0.25)

    add_log("System initialized successfully")
    add_log("Local monitoring modules loaded")
    add_log("GHOSTSCOUT terminal online")


# ============================================================
# SYSTEM MONITORING
# ============================================================

def get_system_data():

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    swap = psutil.swap_memory()

    cpu = psutil.cpu_percent(interval=None)

    uptime = int(
        time.time() - psutil.boot_time()
    )

    return {
        "cpu": cpu,
        "ram": memory.percent,
        "disk": disk.percent,
        "swap": swap.percent,
        "uptime": uptime,
        "memory_used": memory.used,
        "memory_total": memory.total,
        "disk_used": disk.used,
        "disk_total": disk.total
    }


def format_bytes(value):

    units = ["B", "KB", "MB", "GB", "TB"]

    for unit in units:

        if value < 1024:
            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{value:.1f} PB"


def format_uptime(seconds):

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{days}d {hours}h {minutes}m {secs}s"


# ============================================================
# NETWORK INFORMATION
# ============================================================

def get_network_data():

    interfaces = []

    try:

        for name, addresses in psutil.net_if_addrs().items():

            ipv4 = []

            for address in addresses:

                if address.family == socket.AF_INET:

                    ipv4.append(address.address)

            interfaces.append({
                "name": name,
                "ipv4": ipv4
            })

    except Exception:
        pass

    hostname = socket.gethostname()

    try:

        local_ip = socket.gethostbyname(hostname)

    except socket.gaierror:

        local_ip = "Unavailable"

    stats = psutil.net_io_counters()

    return {
        "hostname": hostname,
        "local_ip": local_ip,
        "interfaces": interfaces,
        "bytes_sent": stats.bytes_sent,
        "bytes_recv": stats.bytes_recv
    }


# ============================================================
# PANEL: SYSTEM OVERVIEW
# ============================================================

def progress_bar(value, width=18):

    filled = int(width * value / 100)

    return (
        f"[{GREEN}]"
        + "█" * filled
        + "[/]"
        + "[grey23]"
        + "░" * (width - filled)
        + "[/]"
    )


def system_panel():

    data = get_system_data()

    table = Table(
        box=None,
        expand=True,
        show_header=False,
        padding=(0, 1)
    )

    table.add_column("Metric", style=CYAN, width=9)
    table.add_column("Value", width=9)
    table.add_column("Bar")

    metrics = [
        ("CPU", data["cpu"]),
        ("RAM", data["ram"]),
        ("DISK", data["disk"]),
        ("SWAP", data["swap"])
    ]

    for name, value in metrics:

        table.add_row(
            name,
            f"{value:.1f}%",
            progress_bar(value)
        )

    table.add_row(
        "UPTIME",
        format_uptime(data["uptime"]),
        ""
    )

    return Panel(
        table,
        title="[bold bright_green]SYSTEM OVERVIEW[/]",
        border_style=GREEN,
        box=box.DOUBLE
    )


# ============================================================
# PANEL: NETWORK STATUS
# ============================================================

def network_panel():

    data = get_network_data()

    table = Table(
        box=None,
        show_header=False,
        expand=True
    )

    table.add_column("Label", style=CYAN)
    table.add_column("Value", style=WHITE)

    table.add_row("Hostname", data["hostname"])
    table.add_row("Local IP", data["local_ip"])

    table.add_row(
        "TX",
        format_bytes(data["bytes_sent"])
    )

    table.add_row(
        "RX",
        format_bytes(data["bytes_recv"])
    )

    table.add_row(
        "Interfaces",
        str(len(data["interfaces"]))
    )

    return Panel(
        table,
        title="[bold bright_green]NETWORK STATUS[/]",
        border_style=GREEN,
        box=box.DOUBLE
    )


# ============================================================
# PANEL: INTERFACE INVENTORY
# ============================================================

def interface_panel():

    data = get_network_data()

    table = Table(
        expand=True,
        box=box.SIMPLE,
        border_style="green"
    )

    table.add_column("INTERFACE", style=CYAN)
    table.add_column("IP ADDRESS", style=WHITE)

    for interface in data["interfaces"]:

        addresses = (
            ", ".join(interface["ipv4"])
            if interface["ipv4"]
            else "No IPv4"
        )

        table.add_row(
            interface["name"],
            addresses
        )

    return Panel(
        table,
        title="[bold bright_green]LOCAL INTERFACES[/]",
        border_style=GREEN
    )


# ============================================================
# CENTRAL LOGO
# ============================================================

def logo_panel():

    logo = Text(
        "\n"
        "   ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗\n"
        "  ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝\n"
        "  ██║  ███╗███████║██║   ██║███████╗   ██║\n"
        "  ██║   ██║██╔══██║██║   ██║╚════██║   ██║\n"
        "  ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║\n"
        "   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝\n",
        style="bold bright_green"
    )

    subtitle = Text(
        "\nADVANCED CYBER TERMINAL\n",
        style="bold bright_cyan"
    )

    version = Text(
        "\n[  GHOSTSCOUT v3.0  ]\n",
        style="bold bright_green"
    )

    tagline = Text(
        "\nKALI LINUX EDITION\n\n"
        "Explore. Analyze. Secure.",
        style="bright_white"
    )

    return Panel(
        Align.center(
            Group(logo, subtitle, version, tagline),
            vertical="middle"
        ),
        border_style=CYAN,
        box=box.DOUBLE,
        padding=1
    )


# ============================================================
# PANEL: CLI MENU
# ============================================================

def menu_panel():

    menu = Table(
        box=None,
        show_header=False,
        expand=True
    )

    menu.add_column("KEY", style=GREEN, width=5)
    menu.add_column("MENU", style=WHITE)
    menu.add_column("DESCRIPTION", style=CYAN)

    options = [
        ("1", "Cyber Dashboard", "Live Monitor"),
        ("2", "System Diagnostics", "Check System"),
        ("3", "Network Status", "Local Interfaces"),
        ("4", "Device Inventory", "Manual Records"),
        ("5", "Log Viewer", "View Logs"),
        ("6", "Settings", "Configure"),
        ("7", "Information", "About GHOSTSCOUT"),
        ("0", "Exit", "Quit Terminal")
    ]

    for key, name, description in options:

        menu.add_row(
            f"[{key}]",
            name,
            f"— {description}"
        )

    return Panel(
        menu,
        title="[bold bright_green]GHOSTSCOUT MENU[/]",
        border_style=GREEN,
        box=box.DOUBLE
    )


# ============================================================
# PANEL: LIVE LOGS
# ============================================================

def logs_panel():

    output = []

    for item in LOGS[-7:]:

        line = (
            f"[grey70][{item['time']}][/]"
            f" [{GREEN}][{item['level']}][/] "
            f"{item['message']}"
        )

        output.append(line)

    if not output:
        output = ["[grey50]No activity recorded[/]"]

    return Panel(
        Group(*output),
        title="[bold bright_green]LIVE LOGS[/]",
        border_style=GREEN,
        box=box.DOUBLE
    )


# ============================================================
# FOOTER
# ============================================================

def footer_panel():

    return Panel(
        Align.center(
            Text(
                ">>> GHOSTSCOUT - LOCAL MONITORING <<<",
                style="bold bright_green"
            )
        ),
        border_style=GREEN,
        box=box.DOUBLE
    )


# ============================================================
# DASHBOARD LAYOUT
# ============================================================

def build_dashboard():

    layout = Layout()

    layout.split_column(
        Layout(name="top", ratio=5),
        Layout(name="bottom", ratio=2),
        Layout(name="footer", size=3)
    )

    layout["top"].split_row(
        Layout(name="left", ratio=3),
        Layout(name="center", ratio=4),
        Layout(name="right", ratio=3)
    )

    layout["left"].split_column(
        Layout(name="boot", ratio=1),
        Layout(name="menu", ratio=1)
    )

    layout["center"].update(logo_panel())

    layout["right"].split_column(
        Layout(name="system", ratio=1),
        Layout(name="network", ratio=1),
        Layout(name="interfaces", ratio=1)
    )

    layout["system"].update(system_panel())
    layout["network"].update(network_panel())
    layout["interfaces"].update(interface_panel())

    layout["boot"].update(
        Panel(
            Group(
                "[bright_green][+] Initializing GhostScout Kernel v3.0 ... [OK][/]",
                "[bright_green][+] Loading modules ... [OK][/]",
                "[bright_green][+] Checking local environment ... [OK][/]",
                "[bright_green][+] Preparing dashboard ... [OK][/]",
                "[bright_green][+] Welcome to GHOSTSCOUT[/]",
                "\n[bold red]root@ghostscout[/] [bright_green]~#[/] [bright_cyan]READY[/]"
            ),
            title="[bold bright_green]GHOSTSCOUT - BOOT SEQUENCE[/]",
            border_style=GREEN,
            box=box.DOUBLE
        )
    )

    layout["menu"].update(menu_panel())

    layout["bottom"].split_row(
        Layout(name="logs", ratio=3),
        Layout(name="quote", ratio=2)
    )

    layout["logs"].update(logs_panel())

    layout["quote"].update(
        Panel(
            Align.center(
                Text(
                    "\nIN THE SHADOWS,\n"
                    "WE FIND THE TRUTH.\n\n"
                    "- GHOSTSCOUT -",
                    style="bold bright_green"
                ),
                vertical="middle"
            ),
            border_style=GREEN,
            box=box.DOUBLE
        )
    )

    layout["footer"].update(footer_panel())

    return layout


# ============================================================
# INFORMATION PAGES
# ============================================================

def show_system():

    clear()

    data = get_system_data()

    console.print(
        Panel(
            f"""
[bright_green]CPU:[/]       {data['cpu']}%
[bright_green]RAM:[/]       {data['ram']}%
[bright_green]DISK:[/]      {data['disk']}%
[bright_green]SWAP:[/]      {data['swap']}%
[bright_green]UPTIME:[/]    {format_uptime(data['uptime'])}

[bright_green]OS:[/]        {platform.system()}
[bright_green]RELEASE:[/]   {platform.release()}
[bright_green]MACHINE:[/]   {platform.machine()}
[bright_green]PYTHON:[/]    {platform.python_version()}
            """,
            title="SYSTEM DIAGNOSTICS",
            border_style=GREEN
        )
    )

    input("\nPress ENTER to return...")


def show_network():

    clear()

    data = get_network_data()

    console.print(
        Panel(
            f"""
Hostname: {data['hostname']}
Local IP: {data['local_ip']}

TX: {format_bytes(data['bytes_sent'])}
RX: {format_bytes(data['bytes_recv'])}
            """,
            title="NETWORK INFORMATION",
            border_style=CYAN
        )
    )

    console.print(interface_panel())

    input("\nPress ENTER to return...")


def show_logs():

    clear()

    console.print(logs_panel())

    input("\nPress ENTER to return...")


def show_about():

    clear()

    console.print(
        Panel(
            """
[bold bright_green]GHOSTSCOUT v3.0[/]

Advanced Cyber Terminal
Kali Linux Edition

Features:
- Local system monitoring
- CPU / RAM / Disk / Swap
- Network interface information
- Local device inventory
- Activity logs
- Cyber terminal interface

Monitoring is limited to the local machine
and manually registered inventory.
            """,
            title="ABOUT",
            border_style=GREEN
        )
    )

    input("\nPress ENTER to return...")


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    add_log("Dashboard opened")

    clear()

    console.print(build_dashboard())

    console.print(
        "\n[bold red]root@ghostscout[/]"
        "[bright_green] ~#[/] ",
        end=""
    )

    console.print(
        "[bright_cyan]Dashboard rendered successfully[/]"
    )


# ============================================================
# MAIN MENU
# ============================================================

def main():

    boot_sequence()

    while True:

        dashboard()

        choice = console.input(
            "\n[bold red]root@ghostscout[/]"
            "[bright_green] ~#[/] "
            "[bold white]Select Menu: [/]"
        ).strip()

        if choice == "1":

            dashboard()

            input("\nPress ENTER to return...")

        elif choice == "2":

            show_system()

        elif choice == "3":

            show_network()

        elif choice == "4":

            clear()

            console.print(
                Panel(
                    "Device inventory is maintained in the dashboard "
                    "or as manually entered records.",
                    title="DEVICE INVENTORY",
                    border_style=GREEN
                )
            )

            input("\nPress ENTER to return...")

        elif choice == "5":

            show_logs()

        elif choice == "6":

            clear()

            console.print(
                Panel(
                    "GHOSTSCOUT v3.0\n"
                    "Mode: Local monitoring\n"
                    "Theme: Neon green / cyan\n"
                    "Interface: Rich terminal",
                    title="SETTINGS",
                    border_style=GREEN
                )
            )

            input("\nPress ENTER to return...")

        elif choice == "7":

            show_about()

        elif choice == "0":

            add_log("GHOSTSCOUT terminated")

            console.print(
                "\n[bold bright_green]GHOSTSCOUT OFFLINE[/]"
            )

            break

        else:

            console.print(
                "[bold red]Invalid menu option.[/]"
            )

            time.sleep(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        console.print(
            "\n[bold red]GHOSTSCOUT INTERRUPTED[/]"
        )

        sys.exit(0)

    except Exception as error:

        console.print(
            f"\n[bold red]ERROR:[/] {error}"
        )

        sys.exit(1)
