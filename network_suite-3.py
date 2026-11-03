#!/usr/bin/env python3
"""
UNKNOWN | NETWORK SUITE
Interactive Linux CLI for low-impact network diagnostics.
Developer: unknown

Features:
- Interactive menu
- DNS lookup for loopback/private/link-local destinations
- One TCP connectivity check per selected run
- JSON report export
- No traffic flooding, stress testing, or DDoS functionality
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "1.1.0"
BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║                  UNKNOWN | NETWORK SUITE                    ║
║                       PREMIUM CLI                           ║
╠══════════════════════════════════════════════════════════════╣
║  Developer : unknown                                         ║
║  Version   : 1.1.0                                           ║
║  Platform  : Linux / Python 3                                ║
║  Module    : Network Diagnostics                             ║
╚══════════════════════════════════════════════════════════════╝
"""


def resolve_and_validate(host: str) -> list[str]:
    """Resolve a host and permit only loopback/private/link-local IPs."""
    try:
        records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"DNS resolution failed: {exc}") from exc

    addresses = sorted({record[4][0].split("%", 1)[0] for record in records})
    if not addresses:
        raise ValueError("No IP addresses returned.")

    parsed = [ipaddress.ip_address(address) for address in addresses]
    rejected = [
        str(ip) for ip in parsed
        if not (ip.is_private or ip.is_loopback or ip.is_link_local)
    ]
    if rejected:
        raise ValueError(
            "Public/global destinations are blocked. "
            "Only loopback, private, or link-local addresses are accepted. "
            f"Blocked: {', '.join(rejected)}"
        )
    return addresses


def dns_lookup(host: str) -> dict[str, Any]:
    addresses = resolve_and_validate(host)
    return {
        "tool": "UNKNOWN | NETWORK SUITE",
        "version": VERSION,
        "developer": "unknown",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "operation": "dns_lookup",
        "target": host,
        "resolved_addresses": addresses,
    }


def tcp_check(address: str, port: int, timeout: float) -> dict[str, Any]:
    """Attempt one TCP connection and close it immediately."""
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    started = time.perf_counter()
    try:
        sock.connect((address, port))
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "address": address,
            "port": port,
            "reachable": True,
            "latency_ms": round(elapsed_ms, 2),
            "error": None,
        }
    except OSError as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "address": address,
            "port": port,
            "reachable": False,
            "latency_ms": round(elapsed_ms, 2),
            "error": str(exc),
        }
    finally:
        sock.close()


def build_report(host: str, port: int, timeout: float) -> dict[str, Any]:
    addresses = resolve_and_validate(host)
    checks = [tcp_check(address, port, timeout) for address in addresses]
    return {
        "tool": "UNKNOWN | NETWORK SUITE",
        "version": VERSION,
        "developer": "unknown",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "operation": "tcp_connectivity",
        "target": host,
        "port": port,
        "timeout_seconds": timeout,
        "resolved_addresses": addresses,
        "checks": checks,
        "summary": {
            "addresses_checked": len(checks),
            "reachable": sum(1 for item in checks if item["reachable"]),
            "unreachable": sum(1 for item in checks if not item["reachable"]),
        },
    }


def print_report(report: dict[str, Any]) -> None:
    print("\n[ DNS RESOLUTION ]")
    for address in report.get("resolved_addresses", []):
        print(f"  + {address}")

    if report.get("operation") == "tcp_connectivity":
        print("\n[ TCP CONNECTIVITY ]")
        for check in report["checks"]:
            status = "ONLINE" if check["reachable"] else "UNREACHABLE"
            print(
                f"  {check['address']}:{check['port']}  "
                f"{status:<11}  {check['latency_ms']:>8.2f} ms"
            )
            if check["error"]:
                print(f"    detail: {check['error']}")

        summary = report["summary"]
        print("\n[ SUMMARY ]")
        print(f"  Checked    : {summary['addresses_checked']}")
        print(f"  Reachable  : {summary['reachable']}")
        print(f"  Failed     : {summary['unreachable']}")


def save_json(report: dict[str, Any], destination: str) -> None:
    output = Path(destination).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n[OK] Report saved: {output.resolve()}")


def ask_host() -> str:
    host = input("  Host/IP (local or private): ").strip()
    if not host:
        raise ValueError("Host cannot be empty.")
    return host


def ask_port() -> int:
    raw = input("  TCP port (1-65535): ").strip()
    try:
        port = int(raw)
    except ValueError as exc:
        raise ValueError("Port must be a number.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535.")
    return port


def ask_timeout() -> float:
    raw = input("  Timeout seconds [2.0]: ").strip()
    timeout = 2.0 if not raw else float(raw)
    if not 0.2 <= timeout <= 10:
        raise ValueError("Timeout must be between 0.2 and 10 seconds.")
    return timeout


def interactive_menu() -> int:
    last_report: dict[str, Any] | None = None

    while True:
        print(BANNER)
        print("  [1] DNS lookup")
        print("  [2] TCP connectivity check")
        print("  [3] Export last report (JSON)")
        print("  [4] About")
        print("  [0] Exit")
        print("─" * 64)

        choice = input("  UNKNOWN > Select option: ").strip()

        try:
            if choice == "1":
                host = ask_host()
                last_report = dns_lookup(host)
                print_report(last_report)

            elif choice == "2":
                host = ask_host()
                port = ask_port()
                timeout = ask_timeout()
                last_report = build_report(host, port, timeout)
                print_report(last_report)

            elif choice == "3":
                if last_report is None:
                    print("\n[INFO] No report yet. Run DNS lookup or TCP check first.")
                else:
                    default_name = "reports/unknown-network-report.json"
                    destination = input(
                        f"  Output path [{default_name}]: "
                    ).strip() or default_name
                    save_json(last_report, destination)

            elif choice == "4":
                print(
                    "\nUNKNOWN | NETWORK SUITE"
                    f"\nVersion   : {VERSION}"
                    "\nDeveloper : unknown"
                    "\nPurpose   : Local/private network diagnostics"
                    "\nSafety    : Public destinations are blocked."
                    "\n           One TCP connection attempt per check."
                    "\n           No flooding or DDoS functions."
                )

            elif choice == "0":
                print("\nUNKNOWN | Session closed.")
                return 0

            else:
                print("\n[ERROR] Invalid menu option.")

        except (ValueError, OSError) as exc:
            print(f"\n[ERROR] {exc}")
        except (KeyboardInterrupt, EOFError):
            print("\n\nUNKNOWN | Session interrupted.")
            return 130

        input("\n  Press ENTER to return to menu...")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="unknown-net",
        description="Low-impact DNS and TCP connectivity diagnostics.",
        epilog="Example: python3 network_suite.py --host 127.0.0.1 --port 8000",
    )
    parser.add_argument("--host", help="Local/private host or IP")
    parser.add_argument("--port", type=int, help="TCP port (1-65535)")
    parser.add_argument("--timeout", type=float, default=2.0,
                        help="Connect timeout, 0.2-10 seconds")
    parser.add_argument("--json", dest="json_path",
                        help="Optional JSON report output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.host is None and args.port is None and args.json_path is None:
        return interactive_menu()

    if not args.host or args.port is None:
        print("[ERROR] --host and --port must be supplied together.", file=sys.stderr)
        return 2
    if not 1 <= args.port <= 65535:
        print("[ERROR] Port must be between 1 and 65535.", file=sys.stderr)
        return 2
    if not 0.2 <= args.timeout <= 10:
        print("[ERROR] Timeout must be between 0.2 and 10 seconds.", file=sys.stderr)
        return 2

    print(BANNER)
    try:
        report = build_report(args.host, args.port, args.timeout)
    except ValueError as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        return 2

    print_report(report)
    if args.json_path:
        save_json(report, args.json_path)

    print("\nUNKNOWN | NETWORK SUITE — diagnostic session complete.")
    return 0 if report["summary"]["reachable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
