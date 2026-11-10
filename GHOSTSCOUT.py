#!/usr/bin/env python3
# ============================================================
# GHOSTSCOUT v3.0
# Advanced Cyber Terminal | Kali Linux Edition
# Defensive monitoring and local security diagnostics
# ============================================================

import os
import sys
import json
import time
import socket
import shutil
import random
import base64
import platform
import subprocess
import ipaddress
import tempfile
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
except ImportError:
    print("Install dependencies:")
    print("pip install rich psutil requests")
    sys.exit(1)

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

APP_NAME = "GHOSTSCOUT"
VERSION = "3.0"

console = Console()
BASE_DIR = Path(__file__).resolve().parent

LOG_FILE = BASE_DIR / "ghostscout_logs.jsonl"
DEVICE_FILE = BASE_DIR / "ghostscout_devices.json"
SETTINGS_FILE = BASE_DIR / "ghostscout_settings.json"

# Optional embedded MP3.
# Paste the Base64 audio data between the quotes.
AUDIO_B64 = r"""
"""

audio_temp = None

DEFAULT_SETTINGS = {
    "animation": True,
    "music": True
}


def load_settings():
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text())
            return {**DEFAULT_SETTINGS, **data}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


settings = load_settings()


# ------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def now():
    return datetime.now().strftime("%H:%M:%S")


def full_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def pause():
    console.input("\n[dim]Press Enter to continue...[/dim]")


def log_event(message, level="INFO"):
    entry = {
        "time": full_time(),
        "level": level,
        "event": message
    }

    try:
        with LOG_FILE.open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def panel_title(title):
    return Panel(
        Align.center(
            f"[bold bright_green]{title}[/bold bright_green]"
        ),
        border_style="bright_green"
    )


def get_uptime():
    seconds = int(time.time() - psutil.boot_time())
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"


def run_readonly_command(command, timeout=5):
    """Run a fixed, read-only local diagnostic command."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return result.stdout.strip() or result.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "Unavailable"


# ------------------------------------------------------------
# AUDIO
# ------------------------------------------------------------

def play_music():
    global audio_temp

    if not settings.get("music", True):
        return

    if not AUDIO_B64.strip() or not PYGAME_AVAILABLE:
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        if audio_temp is None:
            audio_bytes = base64.b64decode(AUDIO_B64)

            handle = tempfile.NamedTemporaryFile(
                suffix=".mp3",
                delete=False
            )
            handle.write(audio_bytes)
            handle.close()

            audio_temp = handle.name

        pygame.mixer.music.stop()
        pygame.mixer.music.load(audio_temp)
        pygame.mixer.music.play()

    except Exception:
        pass


def stop_music():
    global audio_temp

    if PYGAME_AVAILABLE:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass

    if audio_temp:
        try:
            os.remove(audio_temp)
        except OSError:
            pass


# ------------------------------------------------------------
# BOOT ANIMATION
# ------------------------------------------------------------

def matrix_intro():
    clear()

    messages = [
        "Initializing GhostScout Kernel...",
        "Loading system modules...",
        "Checking local network interfaces...",
        "Preparing diagnostic modules...",
        "Starting dashboard..."
    ]

    console.print("[bold green]GHOSTSCOUT - BOOT SEQUENCE[/bold green]\n")

    for message in messages:
        console.print(
            f"[green][+][/green] {message} [bold green][OK][/bold green]"
        )
        time.sleep(0.25 if settings.get("animation") else 0)

    if settings.get("animation"):
        console.print()

        chars = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for _ in range(5):
            line = "".join(random.choice(chars) for _ in range(60))
            console.print(line, style="green")
            time.sleep(0.06)

    console.print(
        "\n[bold bright_green]WELCOME TO GHOSTSCOUT[/bold bright_green]"
    )
    time.sleep(0.6)


# ------------------------------------------------------------
# SYSTEM OVERVIEW
# ------------------------------------------------------------

def system_information():
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "cpu": psutil.cpu_percent(interval=0.1),
        "ram": memory.percent,
        "disk": psutil.disk_usage("/").percent,
        "swap": swap.percent,
        "uptime": get_uptime()
    }


def system_diagnostics():
    clear()
    console.print(panel_title("SYSTEM DIAGNOSTICS"))

    info = system_information()

    table = Table(border_style="green")
    table.add_column("Component", style="cyan")
    table.add_column("Value", style="white")

    for key, value in info.items():
        table.add_row(key.upper(), str(value))

    console.print(table)

    processes = sorted(
        psutil.process_iter(["pid", "name", "username"]),
        key=lambda process: process.info.get("pid") or 0
    )

    process_table = Table(
        title="LOCAL PROCESSES",
        border_style="green"
    )
    process_table.add_column("PID")
    process_table.add_column("Process")
    process_table.add_column("User")

    for process in processes[:15]:
        data = process.info
        process_table.add_row(
            str(data.get("pid", "")),
            str(data.get("name", "Unknown")),
            str(data.get("username", "Unknown"))
        )

    console.print(process_table)
    log_event("System diagnostics viewed")
    pause()


# ------------------------------------------------------------
# NETWORK STATUS
# ------------------------------------------------------------

def network_interfaces():
    table = Table(
        title="NETWORK INTERFACES",
        border_style="green"
    )

    table.add_column("Interface", style="cyan")
    table.add_column("Address")
    table.add_column("Family")
    table.add_column("Status")

    interface_stats = psutil.net_if_stats()

    for interface, addresses in psutil.net_if_addrs().items():
        status = (
            "UP" if interface_stats.get(interface)
            and interface_stats[interface].isup
            else "DOWN"
        )

        for address in addresses:
            if address.family in (socket.AF_INET, socket.AF_INET6):
                family = (
                    "IPv4" if address.family == socket.AF_INET
                    else "IPv6"
                )

                table.add_row(
                    interface,
                    address.address,
                    family,
                    status
                )

    console.print(table)


def network_traffic():
    counters = psutil.net_io_counters()

    table = Table(
        title="NETWORK TRAFFIC",
        border_style="green"
    )

    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Bytes sent", f"{counters.bytes_sent:,}")
    table.add_row("Bytes received", f"{counters.bytes_recv:,}")
    table.add_row("Packets sent", f"{counters.packets_sent:,}")
    table.add_row("Packets received", f"{counters.packets_recv:,}")

    console.print(table)


# ------------------------------------------------------------
# NMAP LOCAL SECURITY AUDIT
# Restricted to localhost.
# ------------------------------------------------------------

def nmap_local_audit():
    clear()
    console.print(panel_title("NMAP LOCAL SECURITY AUDIT"))

    nmap_path = shutil.which("nmap")

    if not nmap_path:
        console.print("[yellow]Nmap is not installed.[/yellow]")
        console.print("Install: sudo apt install nmap")
        pause()
        return

    console.print("[cyan]Target:[/cyan] 127.0.0.1")
    console.print("[dim]Scope: localhost only; common TCP ports.[/dim]")
    console.print("[dim]No remote target input is accepted.[/dim]\n")

    command = [
        nmap_path,
        "-sT",
        "-F",
        "-n",
        "--reason",
        "127.0.0.1"
    ]

    try:
        with console.status(
            "[bold green]Checking localhost...[/bold green]"
        ):
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60,
                check=False
            )

        output = result.stdout.strip() or result.stderr.strip()

        console.print(
            Panel(
                output or "No output returned.",
                title="NMAP RESULT",
                border_style="green"
            )
        )

        log_event("Nmap localhost audit completed")

    except subprocess.TimeoutExpired:
        console.print("[red]Nmap audit timed out.[/red]")
        log_event("Nmap localhost audit timed out", "WARNING")

    except Exception as error:
        console.print(f"[red]Nmap error: {error}[/red]")
        log_event("Nmap error", "ERROR")

    pause()


def network_scanner():
    while True:
        clear()
        console.print(panel_title("NETWORK SCANNER"))

        network_interfaces()
        network_traffic()

        console.print("\n[green]1.[/green] Nmap localhost audit")
        console.print("[green]2.[/green] Refresh network status")
        console.print("[green]0.[/green] Back")

        choice = console.input(
            "\n[bold green]GHOSTSCOUT > [/bold green]"
        ).strip()

        if choice == "1":
            nmap_local_audit()
        elif choice == "2":
            continue
        elif choice == "0":
            return


# ------------------------------------------------------------
# SECURITY TOOLS
# Read-only local security checks.
# ------------------------------------------------------------

def security_tools():
    clear()
    console.print(panel_title("LOCAL SECURITY STATUS"))

    table = Table(border_style="green")
    table.add_column("Check", style="cyan")
    table.add_column("Result")

    ufw = run_readonly_command(["ufw", "status"])
    firewall = run_readonly_command(["firewall-cmd", "--state"])

    table.add_row("UFW", ufw[:500])
    table.add_row("Firewalld", firewall[:200])
    table.add_row(
        "Current user",
        os.environ.get("USER", "Unknown")
    )
    table.add_row(
        "Python version",
        platform.python_version()
    )

    console.print(table)

    console.print(
        "\n[dim]These checks report local status only. "
        "They do not change firewall settings.[/dim]"
    )

    log_event("Local security status checked")
    pause()


# ------------------------------------------------------------
# IP / CIDR INFORMATION
# ------------------------------------------------------------

def ip_analysis():
    clear()
    console.print(panel_title("IP / CIDR ANALYSIS"))

    value = console.input("Enter IP or CIDR: ").strip()

    try:
        if "/" in value:
            network = ipaddress.ip_network(value, strict=False)

            results = {
                "Network": network.network_address,
                "Broadcast": network.broadcast_address,
                "Netmask": network.netmask,
                "Prefix": network.prefixlen,
                "Total addresses": network.num_addresses,
                "Version": f"IPv{network.version}"
            }
        else:
            address = ipaddress.ip_address(value)

            results = {
                "Address": address,
                "Version": f"IPv{address.version}",
                "Private": address.is_private,
                "Global": address.is_global,
                "Loopback": address.is_loopback,
                "Multicast": address.is_multicast
            }

        table = Table(title="ANALYSIS RESULT", border_style="green")
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        for key, val in results.items():
            table.add_row(key, str(val))

        console.print(table)
        log_event(f"IP analysis: {value}")

    except ValueError:
        console.print("[red]Invalid IP address or CIDR.[/red]")

    pause()


# ------------------------------------------------------------
# PASSIVE OSINT
# Public DNS and RDAP metadata.
# ------------------------------------------------------------

def passive_osint():
    clear()
    console.print(panel_title("PASSIVE DOMAIN OSINT"))

    domain = console.input("Domain: ").strip().lower()

    if (
        not domain
        or "/" in domain
        or " " in domain
        or len(domain) > 253
    ):
        console.print("[red]Invalid domain.[/red]")
        pause()
        return

    results = {}

    for record in ("A", "AAAA", "MX", "NS", "TXT"):
        try:
            response = requests.get(
                "https://dns.google/resolve",
                params={"name": domain, "type": record},
                timeout=8,
                headers={"User-Agent": "GHOSTSCOUT/3.0"}
            )
            response.raise_for_status()

            results[record] = [
                item.get("data", "")
                for item in response.json().get("Answer", [])
            ]

        except requests.RequestException:
            results[record] = ["Unavailable"]

    try:
        response = requests.get(
            f"https://rdap.org/domain/{domain}",
            timeout=10,
            headers={"User-Agent": "GHOSTSCOUT/3.0"}
        )

        if response.ok:
            data = response.json()
            results["RDAP"] = {
                "domain": data.get("ldhName"),
                "status": data.get("status"),
                "events": data.get("events")
            }
        else:
            results["RDAP"] = "Unavailable"

    except requests.RequestException:
        results["RDAP"] = "Unavailable"

    table = Table(title=domain, border_style="green")
    table.add_column("Record", style="cyan")
    table.add_column("Public information")

    for key, value in results.items():
        table.add_row(
            key,
            json.dumps(value, ensure_ascii=False)
        )

    console.print(table)
    log_event(f"Passive OSINT: {domain}")
    pause()


def information_menu():
    while True:
        clear()
        console.print(panel_title("INFORMATION & RECON"))

        console.print("[green]1.[/green] IP / CIDR analysis")
        console.print("[green]2.[/green] Passive domain OSINT")
        console.print("[green]0.[/green] Back")

        choice = console.input("\nSelect: ").strip()

        if choice == "1":
            ip_analysis()
        elif choice == "2":
            passive_osint()
        elif choice == "0":
            return


# ------------------------------------------------------------
# MANUAL DEVICE INVENTORY
# ------------------------------------------------------------

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
        clear()
        console.print(panel_title("MANUAL DEVICE INVENTORY"))

        devices = load_devices()

        table = Table(border_style="green")
        table.add_column("#", style="green")
        table.add_column("Device", style="cyan")
        table.add_column("IP")
        table.add_column("Notes")

        for index, device in enumerate(devices, 1):
            table.add_row(
                str(index),
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
            address = console.input("IP address (optional): ").strip()
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
                "added": full_time()
            })

            save_devices(devices)
            log_event(f"Device added: {name}")

        elif choice == "2":
            if not devices:
                console.print("[yellow]Inventory is empty.[/yellow]")
                pause()
                continue

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
# LOG VIEWER
# ------------------------------------------------------------

def log_viewer():
    clear()
    console.print(panel_title("LIVE LOG VIEWER"))

    if not LOG_FILE.exists():
        console.print("[yellow]No logs available.[/yellow]")
        pause()
        return

    table = Table(border_style="green")
    table.add_column("Time", style="cyan")
    table.add_column("Level")
    table.add_column("Event")

    try:
        lines = LOG_FILE.read_text(
            encoding="utf-8"
        ).splitlines()

        for line in lines[-60:]:
            try:
                item = json.loads(line)
                table.add_row(
                    item.get("time", ""),
                    item.get("level", "INFO"),
                    item.get("event", "")
                )
            except json.JSONDecodeError:
                continue

        console.print(table)

    except OSError as error:
        console.print(f"[red]{error}[/red]")

    pause()


# ------------------------------------------------------------
# LIVE DASHBOARD
# ------------------------------------------------------------

def dashboard_layout():
    info = system_information()
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
                "[bold bright_green]GHOSTSCOUT // CYBER DASHBOARD[/bold bright_green]"
            ),
            border_style="green"
        )
    )

    system_table = Table.grid(padding=(0, 1))
    system_table.add_column(style="cyan")
    system_table.add_column(style="white")

    system_table.add_row("CPU", f"{info['cpu']}%")
    system_table.add_row("RAM", f"{info['ram']}%")
    system_table.add_row("DISK", f"{info['disk']}%")
    system_table.add_row("SWAP", f"{info['swap']}%")
    system_table.add_row("UPTIME", info["uptime"])
    system_table.add_row("HOST", info["hostname"])

    layout["system"].update(
        Panel(
            system_table,
            title="SYSTEM OVERVIEW",
            border_style="green"
        )
    )

    network_table = Table.grid(padding=(0, 1))
    network_table.add_column(style="cyan")
    network_table.add_column(style="white")

    network_table.add_row(
        "Bytes sent",
        f"{traffic.bytes_sent:,}"
    )
    network_table.add_row(
        "Bytes received",
        f"{traffic.bytes_recv:,}"
    )
    network_table.add_row(
        "Packets sent",
        f"{traffic.packets_sent:,}"
    )
    network_table.add_row(
        "Packets received",
        f"{traffic.packets_recv:,}"
    )
    network_table.add_row(
        "Interfaces",
        str(len(psutil.net_if_addrs()))
    )

    layout["network"].update(
        Panel(
            network_table,
            title="NETWORK STATUS",
            border_style="green"
        )
    )

    layout["footer"].update(
        Panel(
            f"[green]ONLINE[/green]  |  {now()}  |  "
            "[dim]Ctrl+C to return[/dim]",
            border_style="green"
        )
    )

    return layout


def cyber_dashboard():
    clear()
    console.print("[dim]Press Ctrl+C to return to menu.[/dim]")

    try:
        with Live(
            dashboard_layout(),
            console=console,
            refresh_per_second=1,
            screen=False
        ) as live:
            while True:
                live.update(dashboard_layout())
                time.sleep(1)

    except KeyboardInterrupt:
        pass

    log_event("Cyber dashboard viewed")


# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------

def settings_menu():
    global settings

    while True:
        clear()
        console.print(panel_title("GHOSTSCOUT SETTINGS"))

        console.print(
            f"1. Matrix animation: "
            f"{'ON' if settings['animation'] else 'OFF'}"
        )
        console.print(
            f"2. Music: "
            f"{'ON' if settings['music'] else 'OFF'}"
        )
        console.print("3. Save settings")
        console.print("0. Back")

        choice = console.input("\nSelect: ").strip()

        if choice == "1":
            settings["animation"] = not settings["animation"]

        elif choice == "2":
            settings["music"] = not settings["music"]

            if not settings["music"]:
                stop_music()

        elif choice == "3":
            SETTINGS_FILE.write_text(
                json.dumps(settings, indent=4),
                encoding="utf-8"
            )
            console.print("[green]Settings saved.[/green]")
            pause()

        elif choice == "0":
            return


# ------------------------------------------------------------
# EXPORT REPORT
# ------------------------------------------------------------

def export_report():
    clear()
    console.print(panel_title("EXPORT REPORT"))

    report = {
        "application": APP_NAME,
        "version": VERSION,
        "generated": full_time(),
        "system": system_information(),
        "interfaces": {},
        "traffic": {},
        "manual_devices": load_devices()
    }

    for interface, addresses in psutil.net_if_addrs().items():
        report["interfaces"][interface] = [
            {
                "address": address.address,
                "family": str(address.family)
            }
            for address in addresses
        ]

    traffic = psutil.net_io_counters()

    report["traffic"] = {
        "bytes_sent": traffic.bytes_sent,
        "bytes_received": traffic.bytes_recv,
        "packets_sent": traffic.packets_sent,
        "packets_received": traffic.packets_recv
    }

    filename = (
        BASE_DIR /
        f"ghostscout_report_{datetime.now():%Y%m%d_%H%M%S}.json"
    )

    try:
        filename.write_text(
            json.dumps(report, indent=4),
            encoding="utf-8"
        )

        console.print(f"[green]Exported: {filename.name}[/green]")
        log_event(f"Report exported: {filename.name}")

    except OSError as error:
        console.print(f"[red]Export failed: {error}[/red]")

    pause()


# ------------------------------------------------------------
# ABOUT
# ------------------------------------------------------------

def about():
    clear()

    console.print(
        Panel(
            "[bold bright_green]GHOSTSCOUT v3.0[/bold bright_green]\n\n"
            "ADVANCED CYBER TERMINAL\n"
            "KALI LINUX EDITION\n\n"
            "System monitoring\n"
            "Local network diagnostics\n"
            "Nmap localhost audit\n"
            "Passive DNS / RDAP OSINT\n"
            "Manual device inventory\n"
            "Security status checks\n"
            "JSON report export\n\n"
            "[dim]Use only on systems and networks "
            "you own or are authorized to manage.[/dim]",
            title="ABOUT GHOSTSCOUT",
            border_style="green"
        )
    )

    pause()


# ------------------------------------------------------------
# MAIN MENU
# ------------------------------------------------------------

def main_menu():
    while True:
        clear()

        console.print(
            Panel(
                "[bold bright_green]GHOSTSCOUT MENU[/bold bright_green]\n"
                "[dim]Advanced Cyber Terminal | Kali Linux Edition[/dim]",
                border_style="green"
            )
        )

        menu = [
            ("1", "Cyber Dashboard", "Live Monitor"),
            ("2", "Network Scanner", "Local Audit / Nmap"),
            ("3", "System Diagnostics", "Check System"),
            ("4", "Security Tools", "Local Security Status"),
            ("5", "Information", "IP / Passive OSINT"),
            ("6", "Log Viewer", "View Activity Logs"),
            ("7", "Settings", "Configure"),
            ("8", "About", "About GHOSTSCOUT"),
            ("0", "Exit", "Quit Terminal")
        ]

        table = Table(
            show_header=False,
            border_style="green",
            expand=True
        )

        table.add_column("ID", style="bold green", width=5)
        table.add_column("Module", style="white")
        table.add_column("Description", style="cyan")

        for number, title, description in menu:
            table.add_row(number, title, description)

        console.print(table)

        choice = console.input(
            "\n[bold red]root@ghostscout[/bold red]"
            "[bold green]:~# [/bold green]"
        ).strip()

        play_music()

        if choice == "1":
            cyber_dashboard()

        elif choice == "2":
            network_scanner()

        elif choice == "3":
            system_diagnostics()

        elif choice == "4":
            security_tools()

        elif choice == "5":
            information_menu()

        elif choice == "6":
            log_viewer()

        elif choice == "7":
            settings_menu()

        elif choice == "8":
            about()

        elif choice == "0":
            log_event("GHOSTSCOUT exited")
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
        console.print("\n[yellow]Interrupted by user.[/yellow]")

    finally:
        stop_music()
        console.print(
            "\n[bold bright_green]GHOSTSCOUT OFFLINE[/bold bright_green]"
        )


if __name__ == "__main__":
    main()
