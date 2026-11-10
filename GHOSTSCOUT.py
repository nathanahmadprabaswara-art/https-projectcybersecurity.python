#!/usr/bin/env python3
# ============================================================
# GHOSTSCOUT v5.0
# Defensive System & Network Intelligence CLI
# Created by: Unknown
# Platform: Kali Linux / Linux
# ============================================================

import os
import sys
import json
import time
import socket
import ipaddress
import platform
import subprocess
import random
import shutil

from datetime import datetime
from urllib.parse import quote

import psutil
import requests

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()

APP_NAME = "GHOSTSCOUT"
VERSION = "5.0"
AUTHOR = "Unknown"

LOGS = []
INVENTORY = []


# ============================================================
# UTILITIES
# ============================================================

def clear():
    os.system("clear" if os.name != "nt" else "cls")


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_event(message):
    entry = {
        "time": timestamp(),
        "event": message
    }
    LOGS.append(entry)


def pause():
    Prompt.ask("\n[dim]Press ENTER to continue[/dim]")


def bytes_format(value):
    units = ["B", "KB", "MB", "GB", "TB"]

    for unit in units:
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{value:.2f} PB"


def header(title="SYSTEM"):
    console.print(
        Panel(
            f"[bold cyan]GHOSTSCOUT[/bold cyan] "
            f"[dim]// {title}[/dim]\n"
            f"[dim]DEFENSIVE INTELLIGENCE TERMINAL[/dim]",
            border_style="cyan",
            box=box.ROUNDED
        )
    )


# ============================================================
# MATRIX BOOT ANIMATION
# ============================================================

def matrix_boot():
    clear()

    chars = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ#$%&"

    console.print(
        Align.center(
            "[bold green]GHOSTSCOUT INITIALIZATION[/bold green]"
        )
    )

    for i in range(12):
        line = "".join(
            random.choice(chars)
            for _ in range(65)
        )

        console.print(
            f"[green]{line}[/green]"
        )

        time.sleep(0.04)

    with Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[cyan]{task.description}"),
        console=console
    ) as progress:

        task = progress.add_task(
            "Initializing defensive modules...",
            total=100
        )

        while not progress.finished:
            progress.update(
                task,
                advance=random.randint(5, 15)
            )
            time.sleep(0.12)

    console.print(
        "\n[bold green]SYSTEM READY[/bold green]"
    )

    time.sleep(0.8)


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def get_system_info():

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "processor": platform.processor() or "Unknown",
        "cpu": psutil.cpu_percent(interval=0.2),
        "ram": memory.percent,
        "ram_used": bytes_format(memory.used),
        "ram_total": bytes_format(memory.total),
        "disk": disk.percent,
        "uptime": time.time() - psutil.boot_time()
    }


def system_diagnostics():

    clear()
    header("SYSTEM DIAGNOSTICS")

    info = get_system_info()

    table = Table(
        title="SYSTEM INFORMATION",
        box=box.ROUNDED
    )

    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Hostname", info["hostname"])
    table.add_row("Operating System", info["platform"])
    table.add_row("Processor", info["processor"])
    table.add_row("CPU Usage", f'{info["cpu"]}%')
    table.add_row("RAM Usage", f'{info["ram"]}%')
    table.add_row(
        "RAM",
        f'{info["ram_used"]} / {info["ram_total"]}'
    )
    table.add_row("Disk Usage", f'{info["disk"]}%')
    table.add_row(
        "Uptime",
        f'{info["uptime"] / 3600:.2f} hours'
    )

    console.print(table)

    log_event("System diagnostics viewed")
    pause()


# ============================================================
# LOCAL NETWORK INFORMATION
# ============================================================

def network_information():

    clear()
    header("LOCAL NETWORK")

    interfaces = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    table = Table(
        title="NETWORK INTERFACES",
        box=box.ROUNDED
    )

    table.add_column("Interface", style="cyan")
    table.add_column("Address")
    table.add_column("Status")
    table.add_column("Speed")

    for name, addresses in interfaces.items():

        interface_status = stats.get(name)

        for address in addresses:

            if address.family not in (
                socket.AF_INET,
                socket.AF_INET6
            ):
                continue

            status = (
                "UP"
                if interface_status and interface_status.isup
                else "DOWN"
            )

            speed = (
                f"{interface_status.speed} Mbps"
                if interface_status
                else "Unknown"
            )

            table.add_row(
                name,
                address.address,
                status,
                speed
            )

    console.print(table)

    log_event("Local network information viewed")
    pause()


# ============================================================
# IP ADDRESS ANALYSIS
# ============================================================

def ip_analysis():

    clear()
    header("IP INTELLIGENCE")

    value = Prompt.ask("[cyan]Enter IP or CIDR[/cyan]")

    try:

        if "/" in value:

            network = ipaddress.ip_network(
                value,
                strict=False
            )

            table = Table(
                title="NETWORK ANALYSIS",
                box=box.ROUNDED
            )

            table.add_column("Property", style="cyan")
            table.add_column("Result")

            table.add_row(
                "Network",
                str(network.network_address)
            )

            table.add_row(
                "Netmask",
                str(network.netmask)
            )

            table.add_row(
                "Broadcast",
                str(network.broadcast_address)
            )

            table.add_row(
                "Prefix",
                str(network.prefixlen)
            )

            table.add_row(
                "IP Version",
                f"IPv{network.version}"
            )

            table.add_row(
                "Total Addresses",
                str(network.num_addresses)
            )

            console.print(table)

        else:

            ip = ipaddress.ip_address(value)

            table = Table(
                title="IP INTELLIGENCE",
                box=box.ROUNDED
            )

            table.add_column("Property", style="cyan")
            table.add_column("Result")

            table.add_row("Address", str(ip))
            table.add_row("Version", f"IPv{ip.version}")
            table.add_row("Private", str(ip.is_private))
            table.add_row("Global", str(ip.is_global))
            table.add_row("Loopback", str(ip.is_loopback))
            table.add_row("Multicast", str(ip.is_multicast))
            table.add_row("Reserved", str(ip.is_reserved))

            if ip.version == 4:

                network = ipaddress.ip_network(
                    f"{ip}/24",
                    strict=False
                )

                table.add_row(
                    "Example /24 Network",
                    str(network)
                )

                table.add_row(
                    "Example Broadcast",
                    str(network.broadcast_address)
                )

            console.print(table)

        log_event(f"IP analysis: {value}")

    except ValueError:

        console.print(
            "[red]Invalid IP address or CIDR.[/red]"
        )

    pause()


# ============================================================
# GATEWAY AND DNS
# ============================================================

def gateway_dns_analysis():

    clear()
    header("GATEWAY & DNS")

    gateway = "Not detected"
    dns_servers = []

    if platform.system() == "Linux":

        try:

            with open(
                "/proc/net/route",
                "r"
            ) as file:

                next(file)

                for line in file:

                    fields = line.split()

                    if fields[1] == "00000000":

                        gateway = socket.inet_ntoa(
                            bytes.fromhex(
                                fields[2]
                            )[::-1]
                        )

                        break

        except Exception:
            pass

        try:

            with open(
                "/etc/resolv.conf",
                "r"
            ) as file:

                for line in file:

                    if line.startswith("nameserver"):

                        dns_servers.append(
                            line.split()[1]
                        )

        except Exception:
            pass

    table = Table(
        title="NETWORK CONFIGURATION",
        box=box.ROUNDED
    )

    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row(
        "Default Gateway",
        gateway
    )

    table.add_row(
        "DNS Servers",
        ", ".join(dns_servers) if dns_servers else "Unknown"
    )

    console.print(table)

    pause()


# ============================================================
# TRAFFIC MONITOR
# ============================================================

def traffic_monitor():

    clear()
    header("TRAFFIC ANALYSIS")

    console.print(
        "[yellow]Sampling local traffic for 3 seconds...[/yellow]"
    )

    before = psutil.net_io_counters()

    start = time.time()
    time.sleep(3)

    after = psutil.net_io_counters()

    elapsed = time.time() - start

    received = after.bytes_recv - before.bytes_recv
    sent = after.bytes_sent - before.bytes_sent

    table = Table(
        title="NETWORK TRAFFIC",
        box=box.ROUNDED
    )

    table.add_column("Metric", style="cyan")
    table.add_column("Value")

    table.add_row(
        "Download",
        bytes_format(received)
    )

    table.add_row(
        "Upload",
        bytes_format(sent)
    )

    table.add_row(
        "Download Rate",
        f"{bytes_format(received / elapsed)}/s"
    )

    table.add_row(
        "Upload Rate",
        f"{bytes_format(sent / elapsed)}/s"
    )

    table.add_row(
        "Total Received",
        bytes_format(after.bytes_recv)
    )

    table.add_row(
        "Total Sent",
        bytes_format(after.bytes_sent)
    )

    console.print(table)

    pause()


# ============================================================
# LATENCY TEST
# ============================================================

def latency_test():

    clear()
    header("LATENCY TEST")

    target = Prompt.ask(
        "[cyan]Enter hostname or IP[/cyan]"
    )

    try:

        resolved = socket.gethostbyname(target)

        command = (
            ["ping", "-c", "4", "-W", "2", resolved]
            if platform.system() == "Linux"
            else ["ping", "-n", "4", resolved]
        )

        console.print(
            f"[cyan]Resolved address:[/cyan] {resolved}"
        )

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15
        )

        console.print(result.stdout or result.stderr)

        log_event(f"Latency test: {target}")

    except socket.gaierror:

        console.print(
            "[red]Hostname resolution failed.[/red]"
        )

    except subprocess.TimeoutExpired:

        console.print(
            "[red]Latency test timed out.[/red]"
        )

    except Exception as error:

        console.print(
            f"[red]Error: {error}[/red]"
        )

    pause()


# ============================================================
# PASSIVE DOMAIN OSINT
# ============================================================

def dns_query(domain, record_type):

    url = (
        "https://dns.google/resolve"
        f"?name={quote(domain)}"
        f"&type={record_type}"
    )

    try:

        response = requests.get(
            url,
            timeout=8,
            headers={"Accept": "application/dns-json"}
        )

        response.raise_for_status()

        data = response.json()

        return [
            item["data"]
            for item in data.get("Answer", [])
        ]

    except requests.RequestException:
        return []


def domain_osint():

    clear()
    header("PASSIVE DOMAIN OSINT")

    domain = Prompt.ask(
        "[cyan]Enter domain name[/cyan]"
    ).strip().lower()

    if (
        not domain
        or "/" in domain
        or " " in domain
    ):
        console.print("[red]Invalid domain input.[/red]")
        pause()
        return

    records = {}

    for record in ["A", "AAAA", "MX", "NS", "TXT"]:

        records[record] = dns_query(
            domain,
            record
        )

    table = Table(
        title=f"DNS INTELLIGENCE // {domain}",
        box=box.ROUNDED
    )

    table.add_column("Record", style="cyan")
    table.add_column("Results")

    for record, values in records.items():

        table.add_row(
            record,
            "\n".join(values) if values else "No records found"
        )

    console.print(table)

    log_event(f"Passive DNS lookup: {domain}")

    export = Prompt.ask(
        "Export DNS report? (y/n)",
        default="n"
    )

    if export.lower() == "y":

        save_report({
            "domain": domain,
            "dns_records": records
        })

    pause()


# ============================================================
# RDAP DOMAIN METADATA
# ============================================================

def rdap_lookup():

    clear()
    header("RDAP METADATA")

    domain = Prompt.ask(
        "[cyan]Enter domain[/cyan]"
    ).strip().lower()

    if (
        not domain
        or "/" in domain
        or " " in domain
    ):
        console.print("[red]Invalid domain.[/red]")
        pause()
        return

    try:

        response = requests.get(
            f"https://rdap.org/domain/{quote(domain)}",
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        table = Table(
            title="DOMAIN REGISTRATION METADATA",
            box=box.ROUNDED
        )

        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row(
            "Domain",
            data.get("ldhName", domain)
        )

        table.add_row(
            "Handle",
            str(data.get("handle", "Unknown"))
        )

        table.add_row(
            "Status",
            ", ".join(data.get("status", [])) or "Unknown"
        )

        nameservers = [
            ns.get("ldhName", "")
            for ns in data.get("nameservers", [])
        ]

        table.add_row(
            "Nameservers",
            ", ".join(nameservers) or "Unknown"
        )

        events = data.get("events", [])

        for event in events:

            table.add_row(
                event.get("eventAction", "Event"),
                event.get("eventDate", "Unknown")
            )

        console.print(table)

        log_event(f"RDAP lookup: {domain}")

    except requests.RequestException as error:

        console.print(
            f"[red]RDAP lookup failed: {error}[/red]"
        )

    pause()


# ============================================================
# MANUAL DEVICE INVENTORY
# ============================================================

def device_inventory():

    clear()
    header("DEVICE INVENTORY")

    table = Table(
        title="REGISTERED DEVICES",
        box=box.ROUNDED
    )

    table.add_column("ID", style="cyan")
    table.add_column("Device Name")
    table.add_column("IP Address")
    table.add_column("Notes")

    for index, device in enumerate(INVENTORY, 1):

        table.add_row(
            str(index),
            device["name"],
            device["ip"],
            device["notes"]
        )

    if not INVENTORY:

        console.print(
            "[yellow]No manually registered devices.[/yellow]"
        )

    else:

        console.print(table)

    choice = Prompt.ask(
        "Add a device? (y/n)",
        default="n"
    )

    if choice.lower() == "y":

        name = Prompt.ask("Device name")
        address = Prompt.ask("Device IP")

        try:
            ipaddress.ip_address(address)

            notes = Prompt.ask(
                "Notes",
                default="Authorized device"
            )

            INVENTORY.append({
                "name": name,
                "ip": address,
                "notes": notes
            })

            log_event(
                f"Device registered: {name}"
            )

            console.print(
                "[green]Device added successfully.[/green]"
            )

        except ValueError:

            console.print(
                "[red]Invalid IP address.[/red]"
            )

    pause()


# ============================================================
# LIVE DASHBOARD
# ============================================================

def dashboard():

    clear()

    psutil.cpu_percent(interval=None)

    try:

        with Live(
            refresh_per_second=2,
            console=console,
            screen=True
        ) as live:

            while True:

                info = get_system_info()

                net = psutil.net_io_counters()

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

                system_table = Table(
                    box=box.SIMPLE,
                    expand=True
                )

                system_table.add_column(
                    "SYSTEM",
                    style="cyan"
                )

                system_table.add_column("VALUE")

                system_table.add_row(
                    "CPU",
                    f'{info["cpu"]}%'
                )

                system_table.add_row(
                    "RAM",
                    f'{info["ram"]}%'
                )

                system_table.add_row(
                    "DISK",
                    f'{info["disk"]}%'
                )

                system_table.add_row(
                    "HOST",
                    info["hostname"]
                )

                system_table.add_row(
                    "UPTIME",
                    f'{info["uptime"] / 3600:.2f} hours'
                )

                network_table = Table(
                    box=box.SIMPLE,
                    expand=True
                )

                network_table.add_column(
                    "NETWORK",
                    style="cyan"
                )

                network_table.add_column("VALUE")

                network_table.add_row(
                    "RX",
                    bytes_format(net.bytes_recv)
                )

                network_table.add_row(
                    "TX",
                    bytes_format(net.bytes_sent)
                )

                network_table.add_row(
                    "PACKETS IN",
                    str(net.packets_recv)
                )

                network_table.add_row(
                    "PACKETS OUT",
                    str(net.packets_sent)
                )

                network_table.add_row(
                    "REGISTERED DEVICES",
                    str(len(INVENTORY))
                )

                layout["header"].update(
                    Panel(
                        "[bold cyan]GHOSTSCOUT // LIVE DASHBOARD[/bold cyan]",
                        border_style="cyan"
                    )
                )

                layout["system"].update(
                    Panel(
                        system_table,
                        title="SYSTEM STATUS",
                        border_style="green"
                    )
                )

                layout["network"].update(
                    Panel(
                        network_table,
                        title="NETWORK STATUS",
                        border_style="cyan"
                    )
                )

                layout["footer"].update(
                    Panel(
                        f"[green]LIVE[/green] "
                        f"[dim]{timestamp()} | CTRL+C TO EXIT[/dim]",
                        border_style="cyan"
                    )
                )

                live.update(layout)

                time.sleep(1)

    except KeyboardInterrupt:
        pass


# ============================================================
# ACTIVITY LOGS
# ============================================================

def activity_logs():

    clear()
    header("ACTIVITY LOGS")

    table = Table(
        title="SESSION EVENTS",
        box=box.ROUNDED
    )

    table.add_column("Timestamp", style="cyan")
    table.add_column("Activity")

    for entry in LOGS:

        table.add_row(
            entry["time"],
            entry["event"]
        )

    if not LOGS:

        console.print(
            "[yellow]No activity recorded.[/yellow]"
        )

    else:

        console.print(table)

    pause()


# ============================================================
# REPORT EXPORT
# ============================================================

def save_report(extra=None):

    report = {
        "application": APP_NAME,
        "version": VERSION,
        "generated_at": timestamp(),
        "system": get_system_info(),
        "network": {
            "interfaces": {
                name: [
                    {
                        "address": address.address,
                        "family": str(address.family)
                    }
                    for address in addresses
                ]
                for name, addresses in psutil.net_if_addrs().items()
            },
            "traffic": {
                "received": psutil.net_io_counters().bytes_recv,
                "sent": psutil.net_io_counters().bytes_sent
            }
        },
        "inventory": INVENTORY,
        "logs": LOGS,
        "additional_data": extra or {}
    }

    filename = (
        "GHOSTSCOUT_REPORT_"
        + datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".json"
    )

    try:

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
            f"\n[green]Report saved: {filename}[/green]"
        )

        log_event(f"Report exported: {filename}")

    except OSError as error:

        console.print(
            f"[red]Export failed: {error}[/red]"
        )


# ============================================================
# NETWORK MENU
# ============================================================

def network_menu():

    while True:

        clear()
        header("NETWORK ANALYSIS CENTER")

        console.print("""
[bold cyan] [1] [/bold cyan] IP Address Intelligence
[bold cyan] [2] [/bold cyan] Network Interfaces
[bold cyan] [3] [/bold cyan] Gateway & DNS
[bold cyan] [4] [/bold cyan] Traffic Analysis
[bold cyan] [5] [/bold cyan] Latency Test
[bold cyan] [0] [/bold cyan] Back
        """)

        choice = Prompt.ask("Select")

        if choice == "1":
            ip_analysis()

        elif choice == "2":
            network_information()

        elif choice == "3":
            gateway_dns_analysis()

        elif choice == "4":
            traffic_monitor()

        elif choice == "5":
            latency_test()

        elif choice == "0":
            break


# ============================================================
# OSINT MENU
# ============================================================

def osint_menu():

    while True:

        clear()
        header("PASSIVE OSINT CENTER")

        console.print("""
[bold cyan] [1] [/bold cyan] DNS Records
[bold cyan] [2] [/bold cyan] RDAP Metadata
[bold cyan] [0] [/bold cyan] Back
        """)

        choice = Prompt.ask("Select")

        if choice == "1":
            domain_osint()

        elif choice == "2":
            rdap_lookup()

        elif choice == "0":
            break


# ============================================================
# MAIN MENU
# ============================================================

def main_menu():

    while True:

        clear()

        console.print(
            Panel(
                Align.center(
                    "[bold cyan]G H O S T S C O U T[/bold cyan]\n"
                    "[dim]DEFENSIVE INTELLIGENCE FRAMEWORK[/dim]\n\n"
                    "[white]SYSTEM MONITORING | NETWORK ANALYSIS | OSINT[/white]"
                ),
                border_style="cyan",
                box=box.DOUBLE
            )
        )

        console.print("""
[bold cyan] [1] [/bold cyan] Live Dashboard
[bold cyan] [2] [/bold cyan] System Diagnostics
[bold cyan] [3] [/bold cyan] Network Information
[bold cyan] [4] [/bold cyan] IP & Network Analysis
[bold cyan] [5] [/bold cyan] Passive Domain OSINT
[bold cyan] [6] [/bold cyan] Device Inventory
[bold cyan] [7] [/bold cyan] Activity Logs
[bold cyan] [8] [/bold cyan] Export JSON Report
[bold cyan] [9] [/bold cyan] Matrix Animation
[bold cyan] [0] [/bold cyan] Exit
        """)

        choice = Prompt.ask(
            "[bold green]GHOSTSCOUT[/bold green]"
        )

        if choice == "1":
            dashboard()

        elif choice == "2":
            system_diagnostics()

        elif choice == "3":
            network_information()

        elif choice == "4":
            network_menu()

        elif choice == "5":
            osint_menu()

        elif choice == "6":
            device_inventory()

        elif choice == "7":
            activity_logs()

        elif choice == "8":

            clear()
            header("REPORT EXPORT")
            save_report()
            pause()

        elif choice == "9":
            matrix_boot()
            pause()

        elif choice == "0":

            console.print(
                "\n[bold cyan]GHOSTSCOUT SHUTDOWN[/bold cyan]"
            )

            log_event("Application shutdown")
            break

        else:

            console.print(
                "[red]Invalid menu option.[/red]"
            )

            time.sleep(1)


# ============================================================
# ENTRY POINT
# ============================================================

def main():

    try:

        matrix_boot()

        log_event("GHOSTSCOUT started")

        main_menu()

    except KeyboardInterrupt:

        console.print(
            "\n[yellow]Application interrupted.[/yellow]"
        )

    except Exception as error:

        console.print(
            f"\n[red]Fatal error: {error}[/red]"
        )


if __name__ == "__main__":
    main()
