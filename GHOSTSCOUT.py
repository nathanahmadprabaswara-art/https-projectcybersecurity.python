#!/usr/bin/env python3
# ============================================================
# GHOSTSCOUT v2.1
# Security Operations Dashboard
# Python 3.10+
# Standard Library Only
# ============================================================

import os
import sys
import time
import json
import socket
import shutil
import random
import platform
import threading
import webbrowser

from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "GHOSTSCOUT"
VERSION = "2.1.0"

HOST = "127.0.0.1"
PORT = 8765

START_TIME = time.monotonic()

server = None
server_thread = None

GREEN = "\033[92m"
WHITE = "\033[97m"
GRAY = "\033[90m"
RED = "\033[91m"
RESET = "\033[0m"


# ============================================================
# TERMINAL UTILITIES
# ============================================================

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
          SECURITY OPERATIONS CONSOLE
""" + RESET)

    print(GRAY + f"       VERSION {VERSION} | LOCAL ENVIRONMENT" + RESET)
    print()


def boot():
    clear()
    banner()

    tasks = [
        "Initializing core interface",
        "Loading dashboard components",
        "Checking Python environment",
        "Preparing local services",
        "Initializing visual modules",
        "GHOSTSCOUT ready"
    ]

    for task in tasks:
        print(f"  {GREEN}[OK]{RESET} {task}")
        time.sleep(0.22)

    time.sleep(0.4)


def matrix_rain():
    clear()

    characters = "01ABCDEF0123456789"

    try:
        for _ in range(25):
            line = "".join(
                random.choice(characters)
                for _ in range(75)
            )

            print(GREEN + line + RESET)
            time.sleep(0.07)

    except KeyboardInterrupt:
        pass


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def system_info():
    disk = shutil.disk_usage(os.path.abspath(os.sep))

    return {
        "hostname": socket.gethostname(),
        "operating_system": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "disk_total": round(disk.total / (1024 ** 3), 2),
        "disk_used": round(disk.used / (1024 ** 3), 2),
        "disk_free": round(disk.free / (1024 ** 3), 2),
        "uptime": int(time.monotonic() - START_TIME),
        "timestamp": datetime.now().astimezone().isoformat()
    }


# ============================================================
# DASHBOARD HTML
# ============================================================

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>GHOSTSCOUT | Operations</title>

<style>

:root {
    --bg: #0b0f14;
    --panel: #111820;
    --panel2: #151e28;
    --border: #253342;
    --text: #e5edf5;
    --muted: #8292a4;
    --accent: #55c99a;
    --accent-soft: rgba(85,201,154,.12);
    --danger: #e47e7e;
    --warning: #d9b56c;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background: var(--bg);
    color: var(--text);
    font-family: Inter, "Segoe UI", Arial, sans-serif;
    min-height: 100vh;
}

button, input, select {
    font: inherit;
}

/* LAYOUT */

.layout {
    display: flex;
    min-height: 100vh;
}

/* SIDEBAR */

.sidebar {
    width: 235px;
    flex-shrink: 0;
    background: #0e141b;
    border-right: 1px solid var(--border);
    padding: 25px 17px;
}

.brand {
    font-size: 19px;
    font-weight: 800;
    letter-spacing: 3px;
    color: var(--accent);
    margin-bottom: 5px;
}

.brand-sub {
    color: var(--muted);
    font-size: 10px;
    letter-spacing: 1.5px;
}

.nav-title {
    margin: 38px 0 12px;
    padding-left: 10px;
    color: #667789;
    font-size: 10px;
    letter-spacing: 2px;
}

.nav-item {
    padding: 12px;
    margin: 5px 0;
    border-radius: 7px;
    color: #9aabba;
    font-size: 13px;
    cursor: pointer;
    transition: .2s;
}

.nav-item:hover,
.nav-item.active {
    background: var(--accent-soft);
    color: var(--accent);
}

.sidebar-bottom {
    margin-top: 45px;
    padding: 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 11px;
    color: var(--muted);
    line-height: 1.8;
}

/* MAIN */

.main {
    flex: 1;
    min-width: 0;
}

.topbar {
    height: 70px;
    padding: 0 30px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #0e141b;
}

.page-name {
    font-size: 14px;
    font-weight: 600;
}

.top-status {
    color: var(--accent);
    font-size: 12px;
}

.content {
    padding: 30px;
    max-width: 1500px;
    margin: auto;
}

.heading {
    margin-bottom: 25px;
}

.heading h1 {
    font-size: 25px;
    font-weight: 650;
    letter-spacing: -.5px;
}

.heading p {
    color: var(--muted);
    font-size: 13px;
    margin-top: 7px;
}

/* CARDS */

.grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
    margin-bottom: 20px;
}

.card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    min-width: 0;
    transition: border-color .2s;
}

.card:hover {
    border-color: #3a5a50;
}

.card-label {
    color: var(--muted);
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.card-value {
    margin-top: 14px;
    font-size: 23px;
    font-weight: 650;
    overflow-wrap: anywhere;
}

.card-note {
    color: var(--muted);
    font-size: 11px;
    margin-top: 8px;
}

.green {
    color: var(--accent);
}

.red {
    color: var(--danger);
}

/* SECTIONS */

.section {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 22px;
    margin-bottom: 20px;
}

.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 20px;
}

.section-header h2 {
    font-size: 14px;
    font-weight: 650;
}

.section-header span {
    font-size: 11px;
    color: var(--muted);
}

/* SYSTEM DETAILS */

.details {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 15px;
}

.detail {
    background: var(--panel2);
    border: 1px solid var(--border);
    padding: 14px;
    border-radius: 7px;
    min-width: 0;
}

.detail-label {
    color: var(--muted);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.detail-value {
    font-size: 13px;
    margin-top: 9px;
    overflow-wrap: anywhere;
}

/* DISK */

.progress {
    height: 7px;
    background: #25313c;
    border-radius: 20px;
    overflow: hidden;
    margin-top: 14px;
}

.progress-bar {
    height: 100%;
    background: var(--accent);
    width: 0%;
    transition: width .5s;
}

/* RADAR */

.radar-wrap {
    display: flex;
    justify-content: center;
    padding: 10px;
}

.radar {
    position: relative;
    width: 210px;
    height: 210px;
    border-radius: 50%;
    border: 1px solid #315447;
    background:
        linear-gradient(90deg, transparent 49.7%, #315447 50%, transparent 50.3%),
        linear-gradient(0deg, transparent 49.7%, #315447 50%, transparent 50.3%),
        repeating-radial-gradient(
            circle,
            transparent 0 32px,
            #315447 33px 34px
        );
    overflow: hidden;
}

.radar::after {
    content: "";
    position: absolute;
    width: 50%;
    height: 50%;
    left: 50%;
    top: 50%;
    transform-origin: top left;
    background: linear-gradient(135deg, #55c99a55, transparent 70%);
    animation: sweep 6s linear infinite;
}

@keyframes sweep {
    to {
        transform: rotate(360deg);
    }
}

.radar-dot {
    position: absolute;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--accent);
    z-index: 2;
}

/* INPUTS */

.controls {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 15px;
}

input, select {
    background: #0b1117;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 11px;
    outline: none;
    min-width: 0;
}

input:focus, select:focus {
    border-color: var(--accent);
}

.controls input {
    flex: 1;
}

.btn {
    background: #1b352b;
    color: var(--accent);
    border: 1px solid #315c48;
    padding: 10px 15px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    transition: .2s;
}

.btn:hover {
    background: #254a39;
}

.btn-danger {
    color: var(--danger);
    background: #321f22;
    border-color: #684047;
}

/* DEVICE INVENTORY */

.device-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}

.device {
    background: var(--panel2);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 14px;
    overflow-wrap: anywhere;
}

.device-name {
    font-size: 13px;
    font-weight: 650;
}

.device-address {
    color: var(--muted);
    font-size: 11px;
    margin-top: 7px;
}

.device-type {
    color: var(--accent);
    font-size: 10px;
    margin-top: 8px;
}

.device-status {
    margin-top: 10px;
    font-size: 10px;
    color: var(--accent);
}

.device-time {
    color: var(--muted);
    font-size: 10px;
    margin-top: 8px;
}

.device-actions {
    margin-top: 12px;
    display: flex;
    gap: 7px;
}

/* ACTIVITY */

.activity {
    max-height: 230px;
    overflow-y: auto;
}

.log-item {
    display: flex;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid #25334270;
    font-size: 12px;
}

.log-time {
    color: var(--muted);
    white-space: nowrap;
}

.log-message {
    color: #bdcbd7;
    overflow-wrap: anywhere;
}

/* FOOTER */

footer {
    padding: 20px 30px;
    border-top: 1px solid var(--border);
    color: #657587;
    font-size: 10px;
    letter-spacing: 1px;
    display: flex;
    justify-content: space-between;
    gap: 10px;
}

/* RESPONSIVE */

@media(max-width: 1050px) {
    .grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .details {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media(max-width: 700px) {
    .sidebar {
        display: none;
    }

    .content {
        padding: 17px;
    }

    .topbar {
        padding: 0 17px;
    }

    .grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
    }

    .card {
        padding: 14px;
    }

    .card-value {
        font-size: 18px;
    }

    .details,
    .device-list {
        grid-template-columns: 1fr;
    }

    footer {
        padding: 17px;
        flex-direction: column;
    }
}

</style>
</head>

<body>

<div class="layout">

<aside class="sidebar">

    <div class="brand">GHOSTSCOUT</div>
    <div class="brand-sub">OPERATIONS CONSOLE</div>

    <div class="nav-title">WORKSPACE</div>

    <div class="nav-item active" onclick="goTo('overview', this)">
        ◈ Overview
    </div>

    <div class="nav-item" onclick="goTo('system', this)">
        ▦ System details
    </div>

    <div class="nav-item" onclick="goTo('inventory', this)">
        ▣ Device inventory
    </div>

    <div class="nav-item" onclick="goTo('activity', this)">
        ◷ Activity logs
    </div>

    <div class="nav-title">ENVIRONMENT</div>

    <div class="sidebar-bottom">
        <div>APPLICATION STATUS</div>
        <div class="green">● OPERATIONAL</div>
        <div>MODE: LOCAL ONLY</div>
        <div>VERSION: 2.1.0</div>
    </div>

</aside>

<main class="main">

    <div class="topbar">
        <div class="page-name">Security Operations / Overview</div>
        <div class="top-status">● LOCAL SESSION</div>
    </div>

    <div class="content">

        <div class="heading" id="overview">
            <h1>Overview</h1>
            <p>System status, local environment and authorized inventory.</p>
        </div>

        <div class="grid">

            <div class="card">
                <div class="card-label">System status</div>
                <div class="card-value green">ONLINE</div>
                <div class="card-note">Application operational</div>
            </div>

            <div class="card">
                <div class="card-label">Application uptime</div>
                <div class="card-value" id="uptime">--</div>
                <div class="card-note">Since application startup</div>
            </div>

            <div class="card">
                <div class="card-label">Inventory devices</div>
                <div class="card-value" id="deviceCount">0</div>
                <div class="card-note">Manually registered</div>
            </div>

            <div class="card">
                <div class="card-label">Current time</div>
                <div class="card-value" id="clock">--:--</div>
                <div class="card-note" id="date">Loading date</div>
            </div>

        </div>

        <div class="section" id="system">

            <div class="section-header">
                <h2>System information</h2>
                <span id="systemStatus">Loading...</span>
            </div>

            <div class="details">

                <div class="detail">
                    <div class="detail-label">Hostname</div>
                    <div class="detail-value" id="hostname">--</div>
                </div>

                <div class="detail">
                    <div class="detail-label">Operating system</div>
                    <div class="detail-value" id="os">--</div>
                </div>

                <div class="detail">
                    <div class="detail-label">OS release</div>
                    <div class="detail-value" id="release">--</div>
                </div>

                <div class="detail">
                    <div class="detail-label">Architecture</div>
                    <div class="detail-value" id="architecture">--</div>
                </div>

                <div class="detail">
                    <div class="detail-label">Python version</div>
                    <div class="detail-value" id="python">--</div>
                </div>

                <div class="detail">
                    <div class="detail-label">Disk usage</div>
                    <div class="detail-value" id="disk">--</div>

                    <div class="progress">
                        <div class="progress-bar" id="diskBar"></div>
                    </div>
                </div>

            </div>

        </div>

        <div class="grid">

            <div class="card">
                <div class="card-label">Visual radar</div>

                <div class="radar-wrap">
                    <div class="radar" id="radar"></div>
                </div>

                <div class="card-note" style="text-align:center">
                    Decorative visualization only
                </div>
            </div>

            <div class="card">
                <div class="card-label">Environment mode</div>
                <div class="card-value green">LOCAL</div>
                <div class="card-note">
                    Dashboard bound to localhost.
                    No remote discovery.
                </div>
            </div>

        </div>

        <div class="section" id="inventory">

            <div class="section-header">
                <h2>Live-Time Device Inventory</h2>
                <span>MANUAL RECORDS</span>
            </div>

            <div class="card-note" style="margin-bottom:15px">
                Registered devices:
                <strong id="deviceCountDetail">0</strong>
                <br>
                <span id="inventoryUpdated">Last refreshed: --</span>
            </div>

            <div class="controls">

                <input id="deviceName"
                       placeholder="Device name">

                <input id="deviceAddress"
                       placeholder="IP address or note">

                <select id="deviceType">
                    <option value="Computer">Computer</option>
                    <option value="Mobile">Mobile</option>
                    <option value="Router">Router</option>
                    <option value="Other">Other</option>
                </select>

                <button class="btn" onclick="addDevice()">
                    + Add device
                </button>

            </div>

            <div class="controls">

                <input id="deviceSearch"
                       placeholder="Search inventory..."
                       oninput="renderDevices()">

                <button class="btn" onclick="exportInventory()">
                    Export JSON
                </button>

                <button class="btn"
                        onclick="document.getElementById('importFile').click()">
                    Import JSON
                </button>

                <input id="importFile"
                       type="file"
                       accept=".json,application/json"
                       hidden
                       onchange="importInventory(event)">

            </div>

            <div class="device-list" id="deviceList"></div>

            <div class="card-note">
                Live timer shows elapsed time since registration.
                Registered status does not indicate network connectivity.
            </div>

        </div>

        <div class="section" id="activity">

            <div class="section-header">
                <h2>Activity logs</h2>

                <button class="btn btn-danger"
                        onclick="clearLogs()">
                    Clear logs
                </button>
            </div>

            <div class="activity" id="activityLog"></div>

        </div>

    </div>

    <footer>
        <span>GHOSTSCOUT v2.1.0</span>
        <span>LOCAL SECURITY DASHBOARD</span>
    </footer>

</main>
</div>


<script>

// =====================================================
// UTILITIES
// =====================================================

const $ = id => document.getElementById(id);

function goTo(id, element) {
    $(id).scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.remove("active");
    });

    element.classList.add("active");
}


// =====================================================
// CLOCK
// =====================================================

function updateClock() {
    const now = new Date();

    $("clock").textContent =
        now.toLocaleTimeString();

    $("date").textContent =
        now.toLocaleDateString(undefined, {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric"
        });
}

updateClock();
setInterval(updateClock, 1000);


// =====================================================
// ACTIVITY LOGS
// =====================================================

let logs = [];

function addFeed(message) {
    logs.unshift({
        time: new Date().toLocaleTimeString(),
        message: message
    });

    logs = logs.slice(0, 100);

    renderLogs();
}

function renderLogs() {
    const container = $("activityLog");

    container.replaceChildren();

    logs.forEach(log => {
        const row = document.createElement("div");
        row.className = "log-item";

        const time = document.createElement("span");
        time.className = "log-time";
        time.textContent = log.time;

        const message = document.createElement("span");
        message.className = "log-message";
        message.textContent = log.message;

        row.append(time, message);
        container.appendChild(row);
    });
}

function clearLogs() {
    logs = [];
    renderLogs();
    addFeed("Activity logs cleared");
}


// =====================================================
// SYSTEM INFORMATION API
// =====================================================

async function refreshSystem() {
    try {
        const response = await fetch("/api/system");

        if (!response.ok) {
            throw new Error("System API unavailable");
        }

        const data = await response.json();

        $("hostname").textContent = data.hostname;
        $("os").textContent = data.operating_system;
        $("release").textContent = data.release;
        $("architecture").textContent = data.architecture;
        $("python").textContent = data.python_version;

        $("disk").textContent =
            data.disk_used + " GB used / " +
            data.disk_total + " GB total";

        const percentage = data.disk_total > 0
            ? (data.disk_used / data.disk_total) * 100
            : 0;

        $("diskBar").style.width =
            Math.min(100, percentage) + "%";

        $("uptime").textContent =
            formatUptime(data.uptime);

        $("systemStatus").textContent =
            "SYSTEM DATA UPDATED";

    } catch (error) {
        $("systemStatus").textContent =
            "SYSTEM DATA UNAVAILABLE";
    }
}

function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (days > 0) return days + "d " + hours + "h";
    if (hours > 0) return hours + "h " + minutes + "m";

    return minutes + "m " + secs + "s";
}

refreshSystem();
setInterval(refreshSystem, 10000);


// =====================================================
// DEVICE INVENTORY
// =====================================================

const STORAGE_KEY = "ghostscout_inventory";

let devices = [];

try {
    devices = JSON.parse(
        localStorage.getItem(STORAGE_KEY) || "[]"
    );

    if (!Array.isArray(devices)) {
        devices = [];
    }
} catch (error) {
    devices = [];
}

function saveDevices() {
    localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(devices)
    );

    updateDeviceCount();
}

function updateDeviceCount() {
    $("deviceCount").textContent = devices.length;
    $("deviceCountDetail").textContent = devices.length;
}

function addDevice() {
    const name = $("deviceName").value.trim();
    const address = $("deviceAddress").value.trim();
    const type = $("deviceType").value;

    if (!name || !address) {
        alert("Please complete the device name and address.");
        return;
    }

    const now = Date.now();

    devices.push({
        id: now + Math.random(),
        name: name,
        address: address,
        type: type,
        createdAt: now,
        updatedAt: now
    });

    saveDevices();
    renderDevices();

    $("deviceName").value = "";
    $("deviceAddress").value = "";

    addFeed("Device registered: " + name);
}

function removeDevice(id) {
    const device = devices.find(item => item.id === id);

    if (!device) return;

    if (!confirm("Remove " + device.name + "?")) {
        return;
    }

    devices = devices.filter(item => item.id !== id);

    saveDevices();
    renderDevices();

    addFeed("Device removed: " + device.name);
}

function elapsedTime(timestamp) {
    const seconds = Math.max(
        0,
        Math.floor((Date.now() - timestamp) / 1000)
    );

    if (seconds < 60) {
        return seconds + " seconds ago";
    }

    if (seconds < 3600) {
        return Math.floor(seconds / 60) + " minutes ago";
    }

    if (seconds < 86400) {
        return Math.floor(seconds / 3600) + " hours ago";
    }

    return Math.floor(seconds / 86400) + " days ago";
}

function renderDevices() {
    const container = $("deviceList");

    const query = $("deviceSearch").value.toLowerCase();

    container.replaceChildren();

    const filtered = devices.filter(device =>
        device.name.toLowerCase().includes(query) ||
        device.address.toLowerCase().includes(query) ||
        device.type.toLowerCase().includes(query)
    );

    if (filtered.length === 0) {
        const empty = document.createElement("div");
        empty.className = "card-note";
        empty.textContent = "No matching inventory records.";

        container.appendChild(empty);
    }

    filtered.forEach(device => {
        const card = document.createElement("div");
        card.className = "device";

        const name = document.createElement("div");
        name.className = "device-name";
        name.textContent = device.name;

        const address = document.createElement("div");
        address.className = "device-address";
        address.textContent = device.address;

        const type = document.createElement("div");
        type.className = "device-type";
        type.textContent = device.type;

        const status = document.createElement("div");
        status.className = "device-status";
        status.textContent = "● REGISTERED";

        const created = document.createElement("div");
        created.className = "device-time";
        created.textContent =
            "Registered: " +
            new Date(device.createdAt).toLocaleString();

        const updated = document.createElement("div");
        updated.className = "device-time";
        updated.dataset.timestamp = device.updatedAt;

        const actions = document.createElement("div");
        actions.className = "device-actions";

        const remove = document.createElement("button");
        remove.className = "btn btn-danger";
        remove.textContent = "Remove";
        remove.onclick = () => removeDevice(device.id);

        actions.appendChild(remove);

        card.append(
            name,
            address,
            type,
            status,
            created,
            updated,
            actions
        );

        container.appendChild(card);
    });

    updateDeviceCount();
    updateDeviceTimers();
    updateInventoryTime();
}


// =====================================================
// LIVE DEVICE TIMERS
// =====================================================

function updateDeviceTimers() {
    document.querySelectorAll("[data-timestamp]").forEach(element => {
        const timestamp = Number(element.dataset.timestamp);

        element.textContent =
            "Last updated: " +
            new Date(timestamp).toLocaleString() +
            " (" + elapsedTime(timestamp) + ")";
    });
}

function updateInventoryTime() {
    $("inventoryUpdated").textContent =
        "Last refreshed: " + new Date().toLocaleTimeString();
}

setInterval(() => {
    updateDeviceTimers();
    updateInventoryTime();
}, 1000);


// =====================================================
// IMPORT / EXPORT
// =====================================================

function exportInventory() {
    const content = JSON.stringify(devices, null, 2);

    const blob = new Blob(
        [content],
        { type: "application/json" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "ghostscout_inventory.json";
    link.click();

    URL.revokeObjectURL(url);

    addFeed("Inventory exported");
}

function importInventory(event) {
    const file = event.target.files[0];

    if (!file) return;

    const reader = new FileReader();

    reader.onload = function() {
        try {
            const imported = JSON.parse(reader.result);

            if (!Array.isArray(imported)) {
                throw new Error("Invalid inventory format");
            }

            const valid = imported.every(item =>
                item &&
                typeof item.name === "string" &&
                typeof item.address === "string" &&
                typeof item.type === "string"
            );

            if (!valid) {
                throw new Error("Invalid device records");
            }

            if (!confirm("Replace current inventory?")) {
                return;
            }

            devices = imported.map(item => ({
                id: Date.now() + Math.random(),
                name: item.name,
                address: item.address,
                type: item.type,
                createdAt: Number(item.createdAt) || Date.now(),
                updatedAt: Number(item.updatedAt) || Date.now()
            }));

            saveDevices();
            renderDevices();

            addFeed("Inventory imported successfully");

        } catch (error) {
            alert("Import failed: " + error.message);
        }

        event.target.value = "";
    };

    reader.readAsText(file);
}


// =====================================================
// DECORATIVE RADAR
// =====================================================

function createRadarPoints() {
    const radar = $("radar");

    radar.querySelectorAll(".radar-dot").forEach(dot => {
        dot.remove();
    });

    for (let i = 0; i < 5; i++) {
        const dot = document.createElement("div");

        dot.className = "radar-dot";
        dot.style.left = (15 + Math.random() * 70) + "%";
        dot.style.top = (15 + Math.random() * 70) + "%";

        radar.appendChild(dot);
    }
}

createRadarPoints();
setInterval(createRadarPoints, 4000);


// =====================================================
// INITIALIZATION
// =====================================================

renderDevices();

addFeed("GHOSTSCOUT dashboard initialized");
addFeed("Local environment enabled");

</script>

</body>
</html>
"""


# ============================================================
# HTTP DASHBOARD SERVER
# ============================================================

class DashboardHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/":
            content = HTML.encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(content))
            )
            self.end_headers()

            self.wfile.write(content)

        elif self.path == "/api/system":
            content = json.dumps(
                system_info()
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json"
            )
            self.send_header(
                "Content-Length",
                str(len(content))
            )
            self.send_header(
                "Cache-Control",
                "no-store"
            )
            self.end_headers()

            self.wfile.write(content)

        else:
            self.send_error(404)

    def log_message(self, format, *args):
        return


# ============================================================
# DASHBOARD CONTROL
# ============================================================

def launch_dashboard():

    global server
    global server_thread

    if server_thread and server_thread.is_alive():
        print(f"{GREEN}[INFO] Dashboard already running.{RESET}")
        webbrowser.open(f"http://{HOST}:{PORT}")
        return

    try:
        server = HTTPServer(
            (HOST, PORT),
            DashboardHandler
        )

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

    global server
    global server_thread

    if server:
        server.shutdown()
        server.server_close()

        server = None
        server_thread = None

        print(f"{GREEN}[OK] Dashboard stopped.{RESET}")

    else:
        print("[INFO] Dashboard is not running.")


# ============================================================
# ABOUT
# ============================================================

def about():

    clear()
    banner()

    print(WHITE + "GHOSTSCOUT v2.1.0")
    print("Security Operations Dashboard")
    print("Professional local interface")
    print("Live-time manual device inventory")
    print("System information and activity logs")
    print("JSON inventory import/export")
    print("Standard Python libraries only")
    print("No remote scanning or attack functionality")
    print(RESET)

    input("\nPress ENTER to continue...")


# ============================================================
# SYSTEM INFORMATION TERMINAL
# ============================================================

def show_system_info():

    clear()
    banner()

    info = system_info()

    for key, value in info.items():
        print(
            f"{GREEN}{key.upper():20}{RESET}: {value}"
        )

    input("\nPress ENTER to continue...")


# ============================================================
# MAIN MENU
# ============================================================

def menu():

    while True:

        clear()
        banner()

        print(f"{GREEN}[1]{RESET} System Information")
        print(f"{GREEN}[2]{RESET} Launch Dashboard")
        print(f"{GREEN}[3]{RESET} Matrix Animation")
        print(f"{GREEN}[4]{RESET} Stop Dashboard")
        print(f"{GREEN}[5]{RESET} About GHOSTSCOUT")
        print(f"{RED}[0]{RESET} Exit")

        choice = input(
            f"\n{GREEN}GHOSTSCOUT{RESET} > "
        ).strip()

        if choice == "1":

            show_system_info()

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

            print(
                f"\n{GREEN}GHOSTSCOUT TERMINATED.{RESET}"
            )

            sys.exit(0)

        else:

            print(f"{RED}Invalid option.{RESET}")
            time.sleep(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:
        boot()
        menu()

    except KeyboardInterrupt:

        stop_dashboard()

        print(
            f"\n{RED}Program interrupted.{RESET}"
        )

        sys.exit(0)
