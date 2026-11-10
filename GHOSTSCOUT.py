#!/usr/bin/env python3
# ============================================================
# GHOSTSCOUT v4.0
# LIVE CYBER TERMINAL + PASSIVE OSINT
# Kali Linux Edition
#
# Scope:
# - Local system monitoring
# - Local network information
# - Passive public domain metadata
# - Authorized domain analysis
# ============================================================

import os
import sys
import time
import math
import json
import socket
import random
import platform
import urllib.request
import urllib.error
import urllib.parse
import re

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


# ============================================================
# CONFIGURATION
# ============================================================

APP = "GHOSTSCOUT"
VERSION = "4.0"

console = Console()

GREEN = "bright_green"
CYAN = "bright_cyan"
WHITE = "bright_white"

START_TIME = time.time()

LOGS = []

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
    console.clear()


def now():
    return datetime.now().strftime("%H:%M:%S")


def add_log(message, level="INFO"):

    LOGS.append({
        "time": now(),
        "level": level,
        "message": message
    })

    if len(LOGS) > 40:
        LOGS.pop(0)


def format_bytes(value):

    for unit in ["B", "KB", "MB", "GB", "TB"]:

        if value < 1024:
            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{value:.1f} PB"


def uptime():

    seconds = int(time.time() - psutil.boot_time())

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    return f"{days}d {hours}h {minutes}m"


def pause():
    input("\nPress ENTER to continue...")


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def system_data():

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    swap = psutil.swap_memory()

    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": memory.percent,
        "disk": disk.percent,
        "swap": swap.percent,
        "ram_used": format_bytes(memory.used),
        "ram_total": format_bytes(memory.total),
        "disk_used": format_bytes(disk.used),
        "disk_total": format_bytes(disk.total),
        "uptime": uptime()
    }


# ============================================================
# LOCAL NETWORK INFORMATION
# ============================================================

def get_local_ip():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.connect(("192.0.2.1", 80))
        return sock.getsockname()[0]

    except OSError:
        return "Unavailable"

    finally:
        sock.close()


def network_data():

    counters = psutil.net_io_counters()

    interfaces = []

    for name, addresses in psutil.net_if_addrs().items():

        ipv4 = []
        ipv6 = []

        for address in addresses:

            if address.family == socket.AF_INET:
                ipv4.append(address.address)

            elif address.family == socket.AF_INET6:
                ipv6.append(address.address)

        interfaces.append({
            "name": name,
            "ipv4": ipv4,
            "ipv6": ipv6
        })

    return {
        "sent": counters.bytes_sent,
        "received": counters.bytes_recv,
        "interfaces": interfaces,
        "ip": get_local_ip(),
        "hostname": socket.gethostname()
    }


# ============================================================
# MATRIX RAIN
# ============================================================

def matrix_animation():

    chars = "0123456789ABCDEF"

    output = []

    for _ in range(10):

        line = Text()

        for _ in range(34):

            char = random.choice(chars)

            shade = random.choice([
                "green",
                "bright_green",
                "cyan",
                "bright_cyan"
            ])

            line.append(char, style=shade)

        output.append(line)

    return Group(*output)


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

            elif x == center or y == center:
                output.append("· ", style="green")

            else:
                output.append("  ")

        output.append("\n")

    return Align.center(output)


# ============================================================
# PROGRESS BAR
# ============================================================

def make_bar(value, width=16):

    value = max(0, min(100, value))

    filled = round(value / 100 * width)

    return (
        f"[bright_green]{'█' * filled}[/]"
        f"[grey23]{'░' * (width-filled)}[/]"
    )


# ============================================================
# SYSTEM PANEL
# ============================================================

def system_panel(data):

    table = Table(
        expand=True,
        box=None,
        show_header=False
    )

    table.add_column("Name", style=CYAN, width=8)
    table.add_column("Value", width=9)
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

def network_panel(data, tx_rate, rx_rate):

    table = Table(
        box=None,
        show_header=False,
        expand=True
    )

    table.add_column("Label", style=CYAN)
    table.add_column("Value", style=WHITE)

    table.add_row("Hostname", data["hostname"])
    table.add_row("Local IP", data["ip"])
    table.add_row("TX Rate", format_bytes(tx_rate) + "/s")
    table.add_row("RX Rate", format_bytes(rx_rate) + "/s")
    table.add_row("TX Total", format_bytes(data["sent"]))
    table.add_row("RX Total", format_bytes(data["received"]))

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
        "\n[ GHOSTSCOUT v4.0 ]\n",
        style="bold bright_green"
    )

    tagline = Text(
        "\nKALI LINUX EDITION\n\n"
        "EXPLORE. ANALYZE. SECURE.",
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
        ("2", "System Diagnostics", "System Status"),
        ("3", "Network Status", "Local Information"),
        ("4", "OSINT Intelligence", "Public Domain Data"),
        ("5", "Matrix Animation", "Visual Effects"),
        ("6", "Log Viewer", "Activity Logs"),
        ("7", "Information", "About"),
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
# LIVE LOGS
# ============================================================

def logs_panel():

    output = []

    for item in LOGS[-7:]:

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
# LIVE DASHBOARD
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
                    ">>> GHOSTSCOUT - LOCAL DEFENSIVE MONITORING <<<",
                    style="bold bright_green"
                )
            ),
            border_style=GREEN,
            box=box.DOUBLE
        )
    )

    return layout


def live_dashboard():

    add_log("Live dashboard started")

    previous = psutil.net_io_counters()
    previous_time = time.monotonic()
    last_log = time.monotonic()

    try:

        with Live(
            console=console,
            refresh_per_second=10,
            screen=True
        ) as live:

            while True:

                current = psutil.net_io_counters()
                current_time = time.monotonic()

                elapsed = max(
                    current_time - previous_time,
                    0.001
                )

                tx_rate = max(
                    0,
                    current.bytes_sent - previous.bytes_sent
                ) / elapsed

                rx_rate = max(
                    0,
                    current.bytes_recv - previous.bytes_recv
                ) / elapsed

                previous = current
                previous_time = current_time

                data = system_data()
                network = network_data()

                if current_time - last_log >= 5:

                    add_log("System metrics refreshed")
                    last_log = current_time

                live.update(
                    build_dashboard(
                        data,
                        network,
                        tx_rate,
                        rx_rate
                    )
                )

                time.sleep(0.1)

    except KeyboardInterrupt:
        add_log("Dashboard stopped")
        console.print("\n[bright_green]Dashboard stopped.[/]")


# ============================================================
# OSINT - DOMAIN VALIDATION
# ============================================================

def validate_domain(domain):

    domain = domain.strip().lower().rstrip(".")

    if len(domain) > 253:
        raise ValueError("Domain too long")

    try:
        domain = domain.encode("idna").decode("ascii")
    except UnicodeError:
        raise ValueError("Invalid domain format")

    pattern = (
        r"^(?=.{1,253}$)"
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,63}$"
    )

    if not re.fullmatch(pattern, domain):
        raise ValueError("Invalid domain format")

    return domain


# ============================================================
# OSINT - DNS LOOKUP
# ============================================================

def dns_lookup(domain):

    results = {
        "A": [],
        "AAAA": [],
        "MX": [],
        "NS": [],
        "TXT": []
    }

    try:

        addresses = socket.getaddrinfo(
            domain,
            None,
            type=socket.SOCK_STREAM
        )

        for item in addresses:

            ip = item[4][0]

            if ":" in ip:
                results["AAAA"].append(ip)
            else:
                results["A"].append(ip)

    except socket.gaierror:
        pass

    for record_type in ["MX", "NS", "TXT"]:

        url = (
            "https://dns.google/resolve?"
            + urllib.parse.urlencode({
                "name": domain,
                "type": record_type
            })
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "GHOSTSCOUT-OSINT/4.0"
            }
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=8
            ) as response:

                data = json.loads(
                    response.read().decode("utf-8")
                )

            for answer in data.get("Answer", []):

                value = answer.get("data", "")

                if value:
                    results[record_type].append(value)

        except (
            OSError,
            ValueError,
            urllib.error.URLError
        ):
            continue

    for key in results:

        results[key] = list(
            dict.fromkeys(results[key])
        )

    return results


# ============================================================
# OSINT - RDAP
# ============================================================

def rdap_lookup(domain):

    url = (
        "https://rdap.org/domain/"
        + urllib.parse.quote(domain, safe="")
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "GHOSTSCOUT-OSINT/4.0",
            "Accept": "application/rdap+json"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=12
    ) as response:

        data = json.loads(
            response.read().decode("utf-8")
        )

    result = {
        "domain": data.get("ldhName", domain),
        "handle": data.get("handle", "Unavailable"),
        "registrar": "Unavailable",
        "status": data.get("status", []),
        "events": [],
        "nameservers": []
    }

    for event in data.get("events", []):

        action = event.get("eventAction", "")

        if action in (
            "registration",
            "expiration",
            "last changed"
        ):

            result["events"].append({
                "action": action,
                "date": event.get("eventDate", "")
            })

    for nameserver in data.get("nameservers", []):

        name = nameserver.get("ldhName")

        if name:
            result["nameservers"].append(name)

    # Extract only public registrar name.
    # Registrant personal contact information is excluded.
    for entity in data.get("entities", []):

        if "registrar" not in entity.get("roles", []):
            continue

        vcard = entity.get("vcardArray", [])

        if len(vcard) > 1:

            for field in vcard[1]:

                if (
                    len(field) > 3
                    and field[0] == "fn"
                ):

                    result["registrar"] = str(field[3])
                    break

    return result


# ============================================================
# OSINT REPORT
# ============================================================

def run_osint():

    clear()

    console.print(
        Panel(
            Align.center(
                Text(
                    "GHOSTSCOUT OSINT\n"
                    "PASSIVE DOMAIN INTELLIGENCE",
                    style="bold bright_green"
                )
            ),
            border_style=GREEN,
            box=box.DOUBLE
        )
    )

    domain_input = console.input(
        "\n[bright_green]Target domain:[/] "
    ).strip()

    try:

        domain = validate_domain(domain_input)

    except ValueError as error:

        console.print(f"\n[red]ERROR: {error}[/]")
        pause()
        return

    console.print("\n[bright_green][+][/] Starting DNS lookup...")

    dns = dns_lookup(domain)

    console.print("[bright_green][+][/] Requesting RDAP metadata...")

    try:

        rdap = rdap_lookup(domain)

    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        ValueError,
        OSError
    ) as error:

        rdap = {
            "error": str(error)
        }

    report = {
        "tool": APP,
        "version": VERSION,
        "domain": domain,
        "generated_at": datetime.now().astimezone().isoformat(),
        "scope": "Passive public domain metadata",
        "dns": dns,
        "rdap": rdap
    }

    add_log(f"Passive OSINT completed for {domain}")

    console.print(
        Panel(
            f"[bright_green]DOMAIN:[/] {domain}\n"
            f"[bright_green]IP ADDRESS:[/] {', '.join(dns['A']) or 'Unavailable'}\n"
            f"[bright_green]IPV6:[/] {', '.join(dns['AAAA']) or 'Unavailable'}",
            title="DOMAIN INFORMATION",
            border_style=GREEN
        )
    )

    table = Table(
        title="DNS RECORDS",
        border_style=GREEN,
        box=box.ROUNDED
    )

    table.add_column("TYPE", style=CYAN)
    table.add_column("RESULT", style=WHITE)

    for record_type, values in dns.items():

        table.add_row(
            record_type,
            "\n".join(values) if values else "No record"
        )

    console.print(table)

    if "error" not in rdap:

        rdap_table = Table(
            title="RDAP METADATA",
            border_style=CYAN
        )

        rdap_table.add_column("FIELD", style=CYAN)
        rdap_table.add_column("VALUE", style=WHITE)

        rdap_table.add_row(
            "Registrar",
            rdap["registrar"]
        )

        rdap_table.add_row(
            "Handle",
            rdap["handle"]
        )

        rdap_table.add_row(
            "Status",
            ", ".join(rdap["status"]) or "Unavailable"
        )

        rdap_table.add_row(
            "Registration Events",
            "\n".join(
                f"{event['action']}: {event['date']}"
                for event in rdap["events"]
            ) or "Unavailable"
        )

        rdap_table.add_row(
            "Nameservers",
            "\n".join(rdap["nameservers"]) or "Unavailable"
        )

        console.print(rdap_table)

    else:

        console.print(
            f"[yellow]RDAP unavailable: {rdap['error']}[/]"
        )

    export = console.input(
        "\n[bright_cyan]Export JSON report? [y/N]: [/]"
    ).strip().lower()

    if export == "y":

        filename = (
            "ghostscout_osint_"
            + domain.replace(".", "_")
            + ".json"
        )

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                report,
                file,
                indent=4,
                ensure_ascii=False
            )

        console.print(
            f"\n[bright_green][OK][/] Saved: {filename}"
        )

        add_log(f"OSINT report exported: {filename}")

    pause()


# ============================================================
# SYSTEM DIAGNOSTICS
# ============================================================

def diagnostics():

    clear()

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

    pause()


# ============================================================
# NETWORK INFORMATION
# ============================================================

def show_network():

    clear()

    data = network_data()

    table = Table(
        title="LOCAL NETWORK INTERFACES",
        border_style=GREEN
    )

    table.add_column("INTERFACE", style=CYAN)
    table.add_column("IPV4", style=WHITE)
    table.add_column("IPV6", style=WHITE)

    for interface in data["interfaces"]:

        table.add_row(
            interface["name"],
            "\n".join(interface["ipv4"]) or "-",
            "\n".join(interface["ipv6"]) or "-"
        )

    console.print(
        Panel(
            f"""
HOSTNAME : {data['hostname']}
LOCAL IP : {data['ip']}

TX TOTAL : {format_bytes(data['sent'])}
RX TOTAL : {format_bytes(data['received'])}
            """,
            title="NETWORK INFORMATION",
            border_style=CYAN
        )
    )

    console.print(table)

    pause()


# ============================================================
# MATRIX SCREEN
# ============================================================

def matrix_screen():

    clear()

    try:

        with Live(
            matrix_animation(),
            console=console,
            refresh_per_second=12,
            screen=True
        ) as live:

            while True:

                live.update(matrix_animation())
                time.sleep(0.08)

    except KeyboardInterrupt:
        add_log("Matrix animation stopped")


# ============================================================
# LOG VIEWER
# ============================================================

def show_logs():

    clear()

    table = Table(
        title="GHOSTSCOUT ACTIVITY LOGS",
        border_style=GREEN
    )

    table.add_column("TIME", style=CYAN)
    table.add_column("LEVEL", style=GREEN)
    table.add_column("MESSAGE", style=WHITE)

    for item in LOGS:

        table.add_row(
            item["time"],
            item["level"],
            item["message"]
        )

    console.print(table)

    pause()


# ============================================================
# ABOUT
# ============================================================

def about():

    clear()

    console.print(
        Panel(
            """
GHOSTSCOUT v4.0

Advanced Cyber Terminal
Kali Linux Edition

MODULES:
- Live Matrix Rain
- Animated Radar
- CPU / RAM / Disk Monitoring
- Network Traffic Monitoring
- Local Interface Inventory
- Passive Domain OSINT
- DNS Intelligence
- RDAP Metadata
- JSON Report Export

Monitoring is limited to the local machine,
public domain metadata, and authorized analysis.
            """,
            title="ABOUT GHOSTSCOUT",
            border_style=GREEN
        )
    )

    pause()


# ============================================================
# MAIN MENU
# ============================================================

def main():

    clear()

    add_log("GHOSTSCOUT v4.0 initialized")
    add_log("Local monitoring modules ready")
    add_log("Passive OSINT module loaded")

    while True:

        clear()

        console.print(
            Panel(
                Align.center(
                    Text(
                        "G H O S T S C O U T\n"
                        "ADVANCED CYBER TERMINAL v4.0",
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

            diagnostics()

        elif choice == "3":

            show_network()

        elif choice == "4":

            run_osint()

        elif choice == "5":

            matrix_screen()

        elif choice == "6":

            show_logs()

        elif choice == "7":

            about()

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
            "\n[bold red]GHOSTSCOUT TERMINATED[/]"
        )

        sys.exit(0)

    except Exception as error:

        console.print(
            f"\n[bold red]ERROR: {error}[/]"
        )

        sys.exit(1)
