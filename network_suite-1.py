#!/usr/bin/env python3
"""
UNKNOWN | NETWORK SUITE
Premium-style, low-impact network diagnostics CLI.
Developer: unknown

This tool performs DNS resolution and one TCP connection check per run.
It intentionally does not generate traffic floods, concurrent load, or DDoS traffic.
Only loopback/private/link-local destinations are accepted.
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


BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║                  UNKNOWN | NETWORK SUITE                    ║
║                         PREMIUM CLI                         ║
╠══════════════════════════════════════════════════════════════╣
║  Developer : unknown                                         ║
║  Module    : Network Diagnostics                             ║
║  Engine    : Python standard library                         ║
╚══════════════════════════════════════════════════════════════╝
"""


def resolve_and_validate(host: str) -> list[str]:
    """Resolve host and reject public/global IP destinations."""
    try:
        records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"DNS resolution failed: {exc}") from exc

    addresses = sorted({record[4][0] for record in records})
    if not addresses:
        raise ValueError("No IP addresses returned.")

    parsed = [ipaddress.ip_address(address) for address in addresses]
    rejected = [str(ip) for ip in parsed if not (
        ip.is_private or ip.is_loopback or ip.is_link_local
    )]
    if rejected:
        raise ValueError(
            "Destination resolves to a public/global IP. "
            "For safety, this CLI only checks loopback, private, or "
            f"link-local destinations. Rejected: {', '.join(rejected)}"
        )
    return addresses


def tcp_check(address: str, port: int, timeout: float) -> dict[str, Any]:
    """Attempt exactly one TCP connection and close it immediately."""
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
        "version": "1.0.0",
        "developer": "unknown",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
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
    for address in report["resolved_addresses"]:
        print(f"  + {address}")

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="unknown-net",
        description="Low-impact DNS and TCP connectivity diagnostics.",
        epilog="Example: python network_suite.py --host 127.0.0.1 --port 8000",
    )
    parser.add_argument("--host", required=True, help="Local/private host or IP")
    parser.add_argument("--port", required=True, type=int, help="TCP port (1-65535)")
    parser.add_argument("--timeout", type=float, default=2.0, help="Connect timeout, 0.2-10 seconds")
    parser.add_argument("--json", dest="json_path", help="Optional JSON report output path")
    return parser.parse_args()


def main() -> int:
    print(BANNER)
    args = parse_args()

    if not 1 <= args.port <= 65535:
        print("[ERROR] Port must be between 1 and 65535.", file=sys.stderr)
        return 2
    if not 0.2 <= args.timeout <= 10:
        print("[ERROR] Timeout must be between 0.2 and 10 seconds.", file=sys.stderr)
        return 2

    try:
        report = build_report(args.host, args.port, args.timeout)
    except ValueError as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        return 2

    print_report(report)

    if args.json_path:
        output = Path(args.json_path)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\n[OK] JSON report saved: {output.resolve()}")

    print("\nUNKNOWN | NETWORK SUITE — diagnostic session complete.")
    return 0 if report["summary"]["reachable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
