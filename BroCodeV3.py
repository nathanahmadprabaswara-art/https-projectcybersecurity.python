import sys
import json
import sqlite3
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

class BroCodehaha123Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_response(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Engine", "BroCodehaha123-DB")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def init_database(self):
        conn = sqlite3.connect("osint_registry.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_string TEXT UNIQUE,
                full_name TEXT,
                leak_status TEXT,
                nodes_data TEXT
            )
        """)
        
        sample_nodes = [
            {"source": "Target_Identity", "relation": "MAPPED_TO", "target": "Digital_Footprint"},
            {"source": "Digital_Footprint", "relation": "LINKED_WITH", "target": "Network_Telemetry"},
            {"source": "Network_Telemetry", "relation": "RESOLVED_BY", "target": "BroCodehaha123_Core"}
        ]
        
        try:
            cursor.execute("""
                INSERT INTO targets (query_string, full_name, leak_status, nodes_data)
                VALUES (?, ?, ?, ?)
            """, (
                "Nathan,nathanahmadprabaswara@gmail.com,081232253524", 
                "Nathan Ahmad Prabaswara", 
                "CRITICAL_LEAK_FOUND", 
                json.dumps(sample_nodes)
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        finally:
            conn.close()

    def _query_local_database(self, query_param):
        conn = sqlite3.connect("osint_registry.db")
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, leak_status, nodes_data FROM targets WHERE query_string = ?", (query_param,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "engine": "BroCodehaha123 v3.0 [DB_CONNECTED]",
                "query_resolved": query_param,
                "status": "SUCCESS",
                "registry_dump": {
                    "identity": {
                        "matched_records": 1,
                        "probable_full_name": row[0],
                        "national_id_status": "INDEXED_VERIFIED"
                    },
                    "digital_footprint": {
                        "breached_databases": ["2022_DataLeak_Combo", "2024_Ecom_Dump", row[1]],
                        "social_networks": [
                            {"platform": "github", "status": "active"},
                            {"platform": "linkedin", "status": "stale"}
                        ]
                    },
                    "network_telemetry": {
                        "last_known_nodes": ["192.168.1.45", "127.0.0.1"],
                        "hostmask_resolutions": "ISP_RESOLVED_STATIC",
                        "graph_nodes": json.loads(row[2])
                    }
                }
            }
        else:
            return {
                "engine": "BroCodehaha123 v3.0 [DB_LIVE]",
                "query_resolved": query_param,
                "status": "RECORD_NOT_FOUND_IN_LOCAL_DB",
                "registry_dump": {
                    "identity": {"matched_records": 0, "probable_full_name": "Unknown Entity"},
                    "network_telemetry": {
                        "graph_nodes": [
                            {"source": f"ID_{query_param}", "relation": "UNRESOLVED_TARGET", "target": "Null_Node"}
                        ]
                    }
                }
            }

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BroCodehaha123 // OSINT CORE v3</title>
    <style>
        body {
            background-color: #050505;
            color: #00ff33;
            font-family: 'Courier New', Courier, monospace;
            margin: 0;
            padding: 20px;
            overflow-x: hidden;
        }
        .terminal-container {
            border: 1px solid #00ff33;
            background-color: #0a0a0a;
            box-shadow: 0 0 15px rgba(0, 255, 51, 0.2);
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
        }
        .header {
            border-bottom: 1px dashed #00ff33;
            padding-bottom: 10px;
            margin-bottom: 20px;
            text-shadow: 0 0 5px #00ff33;
        }
        .input-line {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .prompt {
            color: #00ff33;
            margin-right: 10px;
        }
        input[type="text"] {
            background: transparent;
            border: none;
            border-bottom: 1px solid #00ff33;
            color: #ffffff;
            font-family: 'Courier New', Courier, monospace;
            font-size: 16px;
            width: 70%;
            outline: none;
        }
        button {
            background: #00ff33;
            color: #050505;
            border: none;
            padding: 5px 15px;
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            cursor: pointer;
            margin-left: 10px;
            box-shadow: 0 0 5px #00ff33;
        }
        button:hover {
            background: #ffffff;
            box-shadow: 0 0 10px #ffffff;
        }
        .output-box {
            border: 1px solid #333;
            background-color: #020202;
            padding: 15px;
            min-height: 250px;
            white-space: pre-wrap;
            font-size: 14px;
            color: #00ff33;
        }
        .status-active {
            color: #ff0055;
            animation: blink 1s infinite;
        }
        @keyframes blink {
            50% { opacity: 0; }
        }
    </style>
</head>
<body>
    <div class="terminal-container">
        <div class="header">
            <pre>
 ____            ____          _      _           _           _ ___ _____ _____ 

| __ ) _ __ ___ / ___|___   __| | ___| |__   __ _| |__   __ _| |_  |___ /|___ / 
|  _ \| '__/ _ \ |   / _ \ / _` |/ _ \ '_ \ / _` | '_ \ / _` | | |   |_ \| |_ \ 
| |_) | | | (_) | |__| (_) | (_| |  __/ | | | (_| | | | | (_| | | |  ___) |___) |
|____/|_|  \___/ \____\___/ \__,_|\___|_| |_|\__,_|_| |_|\__,_|_|_| |____/|____/ 
            </pre>
            <div>SYSTEM STATUS: <span class="status-active">DATABASE_CONNECTED</span> | OPERATOR: Hack123</div>
        </div>
        
        <div class="input-line">
            <span class="prompt">BroCodehaha123_#> INPUT_TARGET:</span>
            <input type="text" id="targetInput" placeholder="Nama, Email, Username, atau Phone..." value="Nathan,nathanahmadprabaswara@gmail.com,081232253524">
            <button onclick="runQuery()">EXECUTE</button>
        </div>

        <div class="output-box" id="terminalOutput">[-] Awaiting target definition string...</div>
    </div>

    <script>
        function runQuery() {
            const target = document.getElementById('targetInput').value;
            const open_output = document.getElementById('terminalOutput');
            if (!target) {
                open_output.innerText = "[!] ERROR: Target string cannot be empty.";
                return;
            }
            
            open_output.innerText = "[*] Initializing BroCodehaha123 SQLite query core...\\n";
            open_output.innerText += "[*] Querying local relation tables for target data: " + target + "\\n";
            
            fetch('/api/lookup?q=' + encodeURIComponent(target))
                .then(res => res.json())
                .then(data => {
                    if (data.status === "SUCCESS" && data.registry_dump.network_telemetry.graph_nodes) {
                        let renderText = JSON.stringify(data, null, 4);
                        renderText += "\\n\\n[*] VISUALIZING GRAPH INTERACTION MAP (SQLITE_LIVE):\\n";
                        data.registry_dump.network_telemetry.graph_nodes.forEach(node => {
                            renderText += "    [ENTITAS] " + node.source + " ──(" + node.relation + ")──> " + node.target + "\\n";
                        });
                        open_output.innerText = renderText;
                    } else {
                        open_output.innerText = JSON.stringify(data, null, 4);
                    }
                })
                .catch(err => {
                    open_output.innerText = "[!] CRITICAL: Pipeline query error failed to fetch remote registry.";
                });
        }
    </script>
</body>
</html>"""
            self._send_response(200, "text/html", html_content)
            
        elif self.path.startswith("/api/lookup"):
            parsed_url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed_url.query)
            query_string = params.get("q", [""])[0]
            
            result_payload = self._query_local_database(query_string)
            self._send_response(200, "application/json", json.dumps(result_payload))
        else:
            self._send_response(404, "text/plain", "Not Found")

def main():
    port = 8080
    server_address = ('', port)
    
    initializer = BroCodehaha123Handler
    initializer.init_database(initializer)
    
    httpd = HTTPServer(server_address, BroCodehaha123Handler)
    print(f"[*] BroCodehaha123 SQLITE Engine deployed successfully via BroCodeV3.py.")
    print(f"[*] Local access link available at: http://localhost:{port}")
    try:
        httpd.serve_forever()
