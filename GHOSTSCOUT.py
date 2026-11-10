#!/usr/bin/env python3
# ============================================================
# GHOSTSCOUT v7.1
# Defensive System & Network Intelligence CLI
# Kali Linux / Linux
# ============================================================

import os
import sys
import json
import time
import socket
import shutil
import ipaddress
import platform
import subprocess
import tempfile
import base64
from pathlib import Path
from datetime import datetime

try:
    import psutil
    import requests
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich.layout import Layout
    from rich.align import Align
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("Install dependencies:")
    print("pip install rich psutil requests")
    sys.exit(1)

# Optional music support
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

APP_NAME = "GHOSTSCOUT"
VERSION = "7.1"

console = Console()

# ------------------------------------------------------------
# EMBEDDED AUDIO
# Paste the Base64-encoded MP3 data between the triple quotes.
# Leave empty to disable music.
# ------------------------------------------------------------

AUDIO_B64 = r"""
"""

_audio_temp = None


def play_music():
    global _audio_temp

    if not AUDIO_B64.strip() or not PYGAME_AVAILABLE:
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        if _audio_temp is None:
            audio_data = base64.b64decode(AUDIO_B64)
            handle = tempfile.NamedTemporaryFile(
                suffix=".mp3", delete=False
            )
            handle.write(audio_data)
            handle.close()
            _audio_temp = handle.name

        pygame.mixer.music.stop()
        pygame.mixer.music.load(_audio_temp)
        pygame.mixer.music.play()

    except Exception:
        pass


def stop_music():
    global _audio_temp

    if PYGAME_AVAILABLE:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass

    if _audio_temp:
        try:
            os.remove(_audio_temp)
        except OSError:
            pass


# ------------------------------------------------------------
# GENERAL UTILITIES
# ------------------------------------------------------------

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def pause():
    console.input("\n[dim]Press Enter to continue...[/dim]")


def log_event(message):
    entry = {
        "time": timestamp(),
        "event": message
    }

    try:
        with open("ghostscout_logs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def banner():
    clear()

    title = Text()
    title.append("GHOST", style="bold bright_green")
    title.append("SCOUT", style="bold white")
    title.append(f"  v{VERSION}", style="dim")

    console.print(
        Panel(
            Align.center(title),
            subtitle="[dim]SYSTEM & NETWORK INTELLIGENCE[/dim]",
            border_style="green",
            padding=(1, 2)
        )
    )


def matrix_intro():
    clear()
    console.print("[green]Initializing GHOSTSCOUT...[/green]\n")

    import random

    chars = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for _ in range(9):
        line = "".join(random.choice(chars) for _ in range(65))
        console.print(line, style="green", highlight=False)
        time.sleep(0.07)

    console.print("\n[bold green]SYSTEM READY[/bold green]")
    time.sleep(0.7)


def get_uptime():
    seconds = int(time.time() - psutil.boot_time())
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes}m"


# ------------------------------------------------------------
# SYSTEM INFORMATION
# ------------------------------------------------------------

def system_info():
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "uptime": get_uptime(),
        "cpu": psutil.cpu_percent(interval=0.2),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
    }


def diagnostics():
    banner()

    info = system_info()

    table = Table(
        title="SYSTEM DIAGNOSTICS",
        border_style="green"
    )

    table.add_column("Component", style="cyan")
    table.add_column("Information", style="white")

    for key, value in info.items():
        table.add_row(key.upper(), str(value))

    console.print(table)
    log_event("System diagnostics viewed")
    pause()


# ------------------------------------------------------------
# NETWORK INFORMATION
# ------------------------------------------------------------

def network_interfaces():
    table = Table(
        title="NETWORK INTERFACES",
        border_style="green"
    )

    table.add_column("Interface", style="cyan")
    table.add_column("Address")
    table.add_column("Family")

    for interface, addresses in psutil.net_if_addrs().items():
        for address in addresses:
            if address.family in (
                socket.AF_INET,
                socket.AF_INET6
            ):
                table.add_row(
                    interface,
                    address.address,
                    "IPv4" if address.family == socket.AF_INET
                    else "IPv6"
                )

    console.print(table)


def network_stats():
    stats = psutil.net_io_counters()

    table = Table(
        title="NETWORK TRAFFIC",
        border_style="green"
    )

    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Bytes sent", f"{stats.bytes_sent:,}")
    table.add_row("Bytes received", f"{stats.bytes_recv:,}")
    table.add_row("Packets sent", f"{stats.packets_sent:,}")
    table.add_row("Packets received", f"{stats.packets_recv:,}")

    console.print(table)


def analyze_ip():
    banner()
    console.print("[bold green]IP / CIDR ANALYSIS[/bold green]")

    value = console.input("\nEnter IP or CIDR: ").strip()

    try:
        if "/" in value:
            network = ipaddress.ip_network(value, strict=False)
            result = [
                ("Network", str(network.network_address)),
                ("Broadcast", str(network.broadcast_address)),
                ("Netmask", str(network.netmask)),
                ("Prefix", str(network.prefixlen)),
                ("Total addresses", str(network.num_addresses)),
                ("Version", f"IPv{network.version}")
            ]
        else:
            address = ipaddress.ip_address(value)
            result = [
                ("Address", str(address)),
                ("Version", f"IPv{address.version}"),
                ("Private", str(address.is_private)),
                ("Global", str(address.is_global)),
                ("Loopback", str(address.is_loopback)),
                ("Multicast", str(address.is_multicast))
            ]

        table = Table(title="ANALYSIS RESULT", border_style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        for key, val in result:
            table.add_row(key, val)

        console.print(table)
        log_event(f"IP analysis: {value}")

    except ValueError as error:
        console.print(f"[red]Invalid IP/CIDR: {error}[/red]")

    pause()


def network_analysis():
    banner()
    network_interfaces()
    network_stats()

    console.print("\n[bold green]1.[/bold green] Analyze IP/CIDR")
    console.print("[bold green]2.[/bold green] Ping diagnostic")
    console.print("[bold green]0.[/bold green] Back")

    choice = console.input("\nSelect: ").strip()

    if choice == "1":
        analyze_ip()

    elif choice == "2":
        host = console.input("Host or IP to test: ").strip()

        if not host or any(c.isspace() for c in host):
            console.print("[red]Invalid input.[/red]")
            pause()
            return

        try:
            console.print(f"\nTesting connectivity to {host}...")
            result = subprocess.run(
                ["ping", "-c", "4", "-W", "2", host],
                capture_output=True,
                text=True,
                timeout=12
            )

            console.print(result.stdout or result.stderr)
            log_event(f"Connectivity diagnostic: {host}")

        except (FileNotFoundError, subprocess.TimeoutExpired):
            console.print("[red]Ping unavailable or timed out.[/red]")

        pause()


# ------------------------------------------------------------
# PASSIVE OSINT
# Public DNS and RDAP metadata only.
# ------------------------------------------------------------

def dns_lookup(domain, record_type):
    url = "https://dns.google/resolve"

    response = requests.get(
        url,
        params={"name": domain, "type": record_type},
        timeout=8,
        headers={"User-Agent": "GHOSTSCOUT/7.1"}
    )

    response.raise_for_status()
    data = response.json()

    return [
        item.get("data", "")
        for item in data.get("Answer", [])
    ]


def passive_osint():
    banner()
    console.print("[bold green]PASSIVE DOMAIN INTELLIGENCE[/bold green]")
    console.print("[dim]Public DNS and registration metadata only.[/dim]")

    domain = console.input("\nDomain: ").strip().lower()

    if not domain or "/" in domain or " " in domain:
        console.print("[red]Invalid domain.[/red]")
        pause()
        return

    results = {}

    for record in ("A", "AAAA", "MX", "NS", "TXT"):
        try:
            results[record] = dns_lookup(domain, record)
        except requests.RequestException:
            results[record] = []

    try:
        response = requests.get(
            f"https://rdap.org/domain/{domain}",
            timeout=10,
            headers={"User-Agent": "GHOSTSCOUT/7.1"}
        )

        if response.ok:
            rdap = response.json()

            results["RDAP"] = {
                "ldhName": rdap.get("ldhName"),
                "status": rdap.get("status"),
                "events": rdap.get("events", [])
            }
        else:
            results["RDAP"] = {"status": "Unavailable"}

    except requests.RequestException:
        results["RDAP"] = {"status": "Unavailable"}

    table = Table(title=f"OSINT: {domain}", border_style="green")
    table.add_column("Record", style="cyan")
    table.add_column("Public data")

    for record, values in results.items():
        table.add_row(
            record,
            json.dumps(values, ensure_ascii=False)
        )

    console.print(table)

    log_event(f"Passive OSINT: {domain}")
    pause()


# ------------------------------------------------------------
# MANUAL DEVICE INVENTORY
# No automatic discovery or network scanning.
# ------------------------------------------------------------

DEVICE_FILE = Path("ghostscout_devices.json")


def load_devices():
    if not DEVICE_FILE.exists():
        return []

    try:
        return json.loads(DEVICE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def save_devices(devices):
    DEVICE_FILE.write_text(
        json.dumps(devices, indent=4),
        encoding="utf-8"
    )


def device_inventory():
    while True:
        banner()

        devices = load_devices()

        table = Table(
            title="MANUAL DEVICE INVENTORY",
            border_style="green"
        )

        table.add_column("Name", style="cyan")
        table.add_column("IP")
        table.add_column("Notes")

        for device in devices:
            table.add_row(
                device.get("name", ""),
                device.get("ip", ""),
                device.get("notes", "")
            )

        console.print(table)

        console.print("\n[green]1.[/green] Add device")
        console.print("[green]2.[/green] Remove device")
        console.print("[green]0.[/green] Back")

        choice = console.input("\nSelect: ").strip()

        if choice == "1":
            name = console.input("Device name: ").strip()
            address = console.input("IP address: ").strip()
            notes = console.input("Notes: ").strip()

            if not name:
                console.print("[red]Name is required.[/red]")
                pause()
                continue

            if address:
                try:
                    ipaddress.ip_address(address)
                except ValueError:
                    console.print("[red]Invalid IP address.[/red]")
                    pause()
                    continue

            devices.append({
                "name": name,
                "ip": address,
                "notes": notes,
                "added": timestamp()
            })

            save_devices(devices)
            log_event(f"Device added: {name}")

        elif choice == "2":
            if not devices:
                console.print("[yellow]Inventory is empty.[/yellow]")
                pause()
                continue

            for index, device in enumerate(devices, start=1):
                console.print(
                    f"{index}. {device.get('name', 'Unknown')}"
                )

            try:
                number = int(console.input("Device number: "))
                if 1 <= number <= len(devices):
                    removed = devices.pop(number - 1)
                    save_devices(devices)
                    log_event(
                        f"Device removed: {removed.get('name')}"
                    )
            except ValueError:
                console.print("[red]Invalid number.[/red]")

        elif choice == "0":
            return


# ------------------------------------------------------------
# LIVE DASHBOARD
# ------------------------------------------------------------

def dashboard():
    banner()
    console.print("[dim]Press Ctrl+C to return to menu.[/dim]\n")

    try:
        with Live(
            get_dashboard_layout(),
            console=console,
            refresh_per_second=1,
            screen=False
        ) as live:

            while True:
                live.update(get_dashboard_layout())
                time.sleep(1)

    except KeyboardInterrupt:
        pass

    log_event("Dashboard viewed")


def get_dashboard_layout():
    info = system_info()
    traffic = psutil.net_io_counters()

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )

    layout["body"].split_row(
        Layout(name="system"),
        Layout(name="network")
    )

    layout["header"].update(
        Panel(
            Align.center(
                "[bold green]GHOSTSCOUT // LIVE DASHBOARD[/bold green]"
            ),
            border_style="green"
        )
    )

    system_table = Table.grid(padding=(0, 2))
    system_table.add_column(style="cyan")
    system_table.add_column(style="white")

    system_table.add_row("Hostname", info["hostname"])
    system_table.add_row("Platform", platform.system())
    system_table.add_row("Uptime", info["uptime"])
    system_table.add_row("CPU", f"{info['cpu']}%")
    system_table.add_row("RAM", f"{info['ram']}%")
    system_table.add_row("Disk", f"{info['disk']}%")

    layout["system"].update(
        Panel(system_table, title="SYSTEM STATUS", border_style="green")
    )

    network_table = Table.grid(padding=(0, 2))
    network_table.add_column(style="cyan")
    network_table.add_column(style="white")

    network_table.add_row("Bytes sent", f"{traffic.bytes_sent:,}")
    network_table.add_row("Bytes received", f"{traffic.bytes_recv:,}")
    network_table.add_row("Packets sent", f"{traffic.packets_sent:,}")
    network_table.add_row("Packets received", f"{traffic.packets_recv:,}")
    network_table.add_row("Interfaces", str(len(psutil.net_if_addrs())))

    layout["network"].update(
        Panel(network_table, title="NETWORK STATUS", border_style="green")
    )

    layout["footer"].update(
        Panel(
            f"[green]ONLINE[/green]  |  {timestamp()}  |  "
            "[dim]Ctrl+C to exit dashboard[/dim]",
            border_style="green"
        )
    )

    return layout


# ------------------------------------------------------------
# ACTIVITY LOGS
# ------------------------------------------------------------

def view_logs():
    banner()

    path = Path("ghostscout_logs.jsonl")

    if not path.exists():
        console.print("[yellow]No activity logs yet.[/yellow]")
        pause()
        return

    table = Table(title="ACTIVITY LOGS", border_style="green")
    table.add_column("Time", style="cyan")
    table.add_column("Event")

    try:
        lines = path.read_text(encoding="utf-8").splitlines()

        for line in lines[-50:]:
            try:
                item = json.loads(line)
                table.add_row(
                    item.get("time", ""),
                    item.get("event", "")
                )
            except json.JSONDecodeError:
                continue

        console.print(table)

    except OSError as error:
        console.print(f"[red]{error}[/red]")

    pause()


# ------------------------------------------------------------
# REPORT EXPORT
# ------------------------------------------------------------

def export_report():
    banner()

    report = {
        "application": APP_NAME,
        "version": VERSION,
        "generated": timestamp(),
        "system": system_info(),
        "network_interfaces": {},
        "network_traffic": {},
        "manual_devices": load_devices()
    }

    for interface, addresses in psutil.net_if_addrs().items():
        report["network_interfaces"][interface] = [
            {
                "address": item.address,
                "family": str(item.family)
            }
            for item in addresses
        ]

    traffic = psutil.net_io_counters()

    report["network_traffic"] = {
        "bytes_sent": traffic.bytes_sent,
        "bytes_received": traffic.bytes_recv,
        "packets_sent": traffic.packets_sent,
        "packets_received": traffic.packets_recv
    }

    filename = (
        "ghostscout_report_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".json"
    )

    try:
        Path(filename).write_text(
            json.dumps(report, indent=4),
            encoding="utf-8"
        )

        console.print(f"[green]Report exported: {filename}[/green]")
        log_event(f"Report exported: {filename}")

    except OSError as error:
        console.print(f"[red]Export failed: {error}[/red]")

    pause()


# ------------------------------------------------------------
# MAIN MENU
# ------------------------------------------------------------

def main_menu():
    while True:
        banner()

        console.print(
            Panel(
                "[bold green]GHOSTSCOUT CONTROL CENTER[/bold green]\n"
                "[dim]Defensive system and network intelligence[/dim]",
                border_style="green"
            )
        )

        options = [
            ("1", "Live Dashboard"),
            ("2", "Network & IP Analysis"),
            ("3", "System Diagnostics"),
            ("4", "Passive Domain OSINT"),
            ("5", "Manual Device Inventory"),
            ("6", "Activity Logs"),
            ("7", "Export JSON Report"),
            ("8", "About GHOSTSCOUT"),
            ("0", "Exit")
        ]

        table = Table(
            show_header=False,
            border_style="green",
            expand=True
        )

        table.add_column("Option", style="bold green", width=10)
        table.add_column("Module", style="white")

        for number, label in options:
            table.add_row(number, label)

        console.print(table)

        choice = console.input("\n[bold green]GHOSTSCOUT > [/bold green]").strip()

        # Restart menu music after each selection.
        play_music()

        if choice == "1":
            dashboard()

        elif choice == "2":
            network_analysis()

        elif choice == "3":
            diagnostics()

        elif choice == "4":
            passive_osint()

        elif choice == "5":
            device_inventory()

        elif choice == "6":
            view_logs()

        elif choice == "7":
            export_report()

        elif choice == "8":
            banner()
            console.print(
                Panel(
                    "[bold green]GHOSTSCOUT v7.1[/bold green]\n\n"
                    "System diagnostics\n"
                    "Network interface monitoring\n"
                    "IP and CIDR analysis\n"
                    "Passive public DNS / RDAP lookup\n"
                    "Manual device inventory\n"
                    "JSON reporting\n\n"
                    "[dim]Use only on systems and networks "
                    "you own or are authorized to manage.[/dim]",
                    title="ABOUT",
                    border_style="green"
                )
            )
            pause()

        elif choice == "0":
            log_event("Application exited")
            break

        else:
            console.print("[red]Invalid menu option.[/red]")
            time.sleep(1)


# ------------------------------------------------------------
# STARTUP
# ------------------------------------------------------------

def main():
    try:
        matrix_intro()
        log_event("GHOSTSCOUT started")
        main_menu()

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")

    finally:
        stop_music()
        console.print("\n[bold green]GHOSTSCOUT OFFLINE[/bold green]")


if __name__ == "__main__":
    main()
