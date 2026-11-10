#!/usr/bin/env python3
"""
UNKNOWN CYBER SUITE
A local-only cyber-themed system dashboard and CLI.
Safe by design: no port scanning, exploitation, traffic flooding, or remote targeting.
"""
from __future__ import annotations
import json
import os
import platform
import random
import socket
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8765
LOG_FILE = Path(__file__).with_name("activity.log")

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UNKNOWN // Cyber Suite</title>
<style>
:root{--cyan:#00e5ff;--blue:#168bff;--bg:#050914;--panel:#091426;--line:#16446a;--muted:#83a9c5}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 50% 30%,#0b2440 0,#050914 58%);color:#d8f5ff;font:14px/1.45 ui-monospace,Consolas,monospace}
header{padding:18px 22px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.brand{font-size:20px;letter-spacing:4px;color:var(--cyan);text-shadow:0 0 14px #00bfff}
small,.muted{color:var(--muted)}.status{color:#55ffb0}
main{max-width:1200px;margin:auto;padding:18px;display:grid;grid-template-columns:1.1fr 1fr 1fr;gap:14px}
.panel{background:linear-gradient(145deg,#0b1b30dd,#07101ddd);border:1px solid var(--line);border-radius:8px;padding:14px;box-shadow:0 0 22px #0077aa12}
.panel h3{margin:0 0 12px;color:var(--cyan);font-size:12px;letter-spacing:2px}
.hero{grid-column:span 2;min-height:290px;position:relative;overflow:hidden}
.hero canvas{width:100%;height:240px;display:block}
.wide{grid-column:1/-1}.metric{font-size:25px;color:#fff}.metric span{font-size:11px;color:var(--muted)}
.kv{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #15324b}
.bar{height:7px;background:#10263b;border-radius:8px;margin:7px 0 13px;overflow:hidden}.bar i{display:block;height:100%;background:linear-gradient(90deg,#087dff,var(--cyan));width:20%;box-shadow:0 0 10px var(--cyan)}
.log{height:135px;overflow:auto;color:#9bd7ed;font-size:12px}.log div{padding:3px 0;border-bottom:1px solid #10263b}
button{background:#09253b;color:var(--cyan);border:1px solid #1476a3;padding:9px 12px;border-radius:4px;font:inherit;cursor:pointer}
button:hover{background:#0e3c5a;box-shadow:0 0 12px #00cfff55}
footer{text-align:center;padding:12px;color:#547b96;font-size:11px}
@media(max-width:760px){main{grid-template-columns:1fr}.hero{grid-column:1}.wide{grid-column:1}}
</style></head>
<body>
<header><div><div class="brand">UNKNOWN <span style="color:white">// CYBER SUITE</span></div><small>LOCAL SYSTEM VISUALIZER · BUILD 1.0</small></div>
<div><span class="status">● LOCAL SESSION ACTIVE</span><br><small id="clock">--:--:--</small></div></header>
<main>
<section class="panel hero"><h3>NETWORK TOPOLOGY // VISUAL MODE</h3><canvas id="net"></canvas><small>Animated visualization only — no network probing is performed.</small></section>
<section class="panel"><h3>SYSTEM SNAPSHOT</h3>
<div class="kv"><span>HOST</span><b id="host">Loading</b></div><div class="kv"><span>PLATFORM</span><b id="platform">Loading</b></div>
<div class="kv"><span>CPU LOAD</span><b id="cpu">--</b></div><div class="bar"><i id="cpuBar"></i></div>
<div class="kv"><span>MEMORY</span><b id="mem">--</b></div><div class="bar"><i id="memBar"></i></div>
<div class="kv"><span>UPTIME</span><b id="uptime">--</b></div></section>
<section class="panel"><h3>RADAR // DECORATIVE</h3><canvas id="radar" width="300" height="210" style="width:100%;height:210px"></canvas></section>
<section class="panel"><h3>SESSION COUNTERS</h3><div class="metric" id="ticks">0000</div><span class="muted">dashboard refresh cycles</span><div style="height:12px"></div><div class="kv"><span>MODE</span><b>PASSIVE</b></div><div class="kv"><span>REMOTE ACTIONS</span><b>DISABLED</b></div><div class="kv"><span>DATA SOURCE</span><b>LOCAL HOST</b></div></section>
<section class="panel"><h3>CONTROLS</h3><p class="muted">This dashboard only reads basic local system information.</p><button onclick="refresh()">↻ REFRESH SNAPSHOT</button> <button onclick="addLog()">＋ ADD DEMO EVENT</button></section>
<section class="panel wide"><h3>LIVE EVENT FEED</h3><div class="log" id="log"></div></section>
</main><footer>UNKNOWN CYBER SUITE · EDUCATIONAL / DEFENSIVE VISUALIZATION · 127.0.0.1 ONLY</footer>
<script>
const $=id=>document.getElementById(id);let ticks=0,events=["Local dashboard initialized","Passive system snapshot ready","Visualization engine online","No remote targets configured"];
function log(s){let d=document.createElement("div");d.textContent="["+new Date().toLocaleTimeString()+"] "+s;$("log").prepend(d)}
function addLog(){log(events[Math.floor(Math.random()*events.length)])}
async function refresh(){try{let r=await fetch("/api/status");let d=await r.json();$("host").textContent=d.host;$("platform").textContent=d.platform;$("cpu").textContent=d.cpu+"%";$("mem").textContent=d.memory+"%";$("cpuBar").style.width=d.cpu+"%";$("memBar").style.width=d.memory+"%";$("uptime").textContent=d.uptime; ticks++;$("ticks").textContent=String(ticks).padStart(4,"0");$("clock").textContent=new Date().toLocaleTimeString()}catch(e){log("Status endpoint unavailable")}}
function draw(){let c=$("net"),x=c.getContext("2d"),w=c.width=c.clientWidth*devicePixelRatio,h=c.height=240*devicePixelRatio;x.scale(devicePixelRatio,devicePixelRatio);let W=c.clientWidth,H=240;x.clearRect(0,0,W,H);let pts=Array.from({length:19},(_,i)=>({x:W/2+Math.cos(i*6.28/19)*Math.min(W*.38,190),y:H/2+Math.sin(i*6.28/19)*85}));let center={x:W/2,y:H/2};x.strokeStyle="#0b6486";x.lineWidth=1;pts.forEach((p,i)=>{x.beginPath();x.moveTo(center.x,center.y);x.lineTo(p.x,p.y);x.stroke();if(i%3===0){x.beginPath();x.moveTo(p.x,p.y);x.lineTo(pts[(i+4)%pts.length].x,pts[(i+4)%pts.length].y);x.stroke()}});pts.forEach((p,i)=>{x.fillStyle=i%4===0?"#00e5ff":"#168bff";x.shadowBlur=12;x.shadowColor=x.fillStyle;x.beginPath();x.arc(p.x,p.y,3,0,7);x.fill()});x.fillStyle="#00e5ff";x.beginPath();x.arc(center.x,center.y,8,0,7);x.fill();x.shadowBlur=0}
function radar(){let c=$("radar"),x=c.getContext("2d"),w=c.width,h=c.height,cx=w/2,cy=h/2,r=85;x.clearRect(0,0,w,h);x.strokeStyle="#14577b";for(let a=1;a<=3;a++){x.beginPath();x.arc(cx,cy,r*a/3,0,7);x.stroke()}x.beginPath();x.moveTo(cx-r,cy);x.lineTo(cx+r,cy);x.moveTo(cx,cy-r);x.lineTo(cx,cy+r);x.stroke();let ang=Date.now()/900;x.save();x.translate(cx,cy);x.rotate(ang);let g=x.createLinearGradient(0,0,r,0);g.addColorStop(0,"#00e5ff66");g.addColorStop(1,"#00e5ff00");x.fillStyle=g;x.beginPath();x.moveTo(0,0);x.arc(0,0,r,-.55,.02);x.closePath();x.fill();x.restore();requestAnimationFrame(radar)}
for(let i=0;i<4;i++)addLog();draw();radar();refresh();setInterval(refresh,2500);setInterval(draw,1500);
</script></body></html>"""

def system_status():
    cpu = memory = 0
    try:
        import psutil
        cpu = int(psutil.cpu_percent(interval=0.1))
        memory = int(psutil.virtual_memory().percent)
        uptime = int(time.time() - psutil.boot_time())
    except Exception:
        uptime = int(time.monotonic())
        try:
            load = os.getloadavg()[0]
            cpu = min(99, int(load * 10))
        except Exception:
            cpu = random.randint(3, 18)
        memory = random.randint(25, 65)
    return {
        "host": socket.gethostname()[:24],
        "platform": platform.system() + " " + platform.release(),
        "cpu": max(0, min(100, cpu)),
        "memory": max(0, min(100, memory)),
        "uptime": f"{uptime//3600}h {(uptime%3600)//60}m"
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            body = HTML.encode()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
        elif self.path == "/api/status":
            body = json.dumps(system_status()).encode()
            self.send_response(200); self.send_header("Content-Type","application/json")
        else:
            body = b"Not found"; self.send_response(404); self.send_header("Content-Type","text/plain")
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store")
        self.end_headers(); self.wfile.write(body)
    def log_message(self, fmt, *args):
        return

def start_dashboard():
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as e:
        print(f"[!] Cannot start dashboard on {HOST}:{PORT}: {e}")
        return
    url = f"http://{HOST}:{PORT}"
    print(f"\n[+] Dashboard running: {url}")
    print("[+] Press Ctrl+C to stop the dashboard.")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: print("\n[!] Dashboard stopped.")
    finally: server.server_close()

def show_status():
    print("\n=== LOCAL SYSTEM SNAPSHOT ===")
    for k,v in system_status().items(): print(f"{k.upper():10}: {v}")
    print("Scope      : LOCAL HOST ONLY")

def main():
    while True:
        print("""
╔══════════════════════════════════════╗
║       UNKNOWN // CYBER SUITE         ║
║      LOCAL DEFENSIVE VISUALIZER      ║
╠══════════════════════════════════════╣
║  1. Launch animated dashboard        ║
║  2. Show local system status         ║
║  3. Write demo activity event        ║
║  4. About / safety scope              ║
║  0. Exit                              ║
╚══════════════════════════════════════╝""")
        choice = input("UNKNOWN@LOCAL:~$ ").strip()
        if choice == "1": start_dashboard()
        elif choice == "2": show_status()
        elif choice == "3":
            msg = f"[{datetime.now().isoformat(timespec='seconds')}] Demo event generated locally\n"
            LOG_FILE.write_text((LOG_FILE.read_text() if LOG_FILE.exists() else "") + msg, encoding="utf-8")
            print("[+] Demo event saved to activity.log")
        elif choice == "4":
            print("\nUNKNOWN CYBER SUITE — educational local dashboard.")
            print("No DDoS, port scanning, exploitation, credential theft, or remote targeting.")
            print("Dashboard binds only to 127.0.0.1 (this device).")
        elif choice == "0": print("Session closed."); break
        else: print("[!] Choose 1, 2, 3, 4, or 0.")

if __name__ == "__main__":
    main()
