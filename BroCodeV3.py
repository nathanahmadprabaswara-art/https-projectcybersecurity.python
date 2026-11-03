import sys
import json
import sqlite3

class BroCodeOSINTCLI:
    def __init__(self):
        self.db_name = "osint_registry.db"
        self.operator = "Hack123"
        self.version = "v3.0"

    def init_database(self):
        conn = sqlite3.connect(self.db_name)
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

    def execute_lookup(self, query_param):
        print("=" * 70)
        print(f" BroCodehaha123 // OSINT CORE CLI {self.version}")
        print(f" SYSTEM STATUS : ACTIVE | OPERATOR : {self.operator}")
        print("=" * 70)
        print(f"[*] Initializing SQLite query core...")
        print(f"[*] Querying relation tables for target data: {query_param}\n")

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, leak_status, nodes_data FROM targets WHERE query_string = ?", (query_param,))
        row = cursor.fetchone()
        conn.close()

        if row:
            full_name, leak_status, nodes_data = row
            nodes = json.loads(nodes_data)
            
            result = {
                "engine": f"BroCodehaha123 {self.version} [DB_CONNECTED]",
                "query_resolved": query_param,
                "status": "SUCCESS",
                "registry_dump": {
                    "identity": {
                        "matched_records": 1,
                        "probable_full_name": full_name,
                        "national_id_status": "INDEXED_VERIFIED"
                    },
                    "digital_footprint": {
                        "breached_databases": ["2022_DataLeak_Combo", "2024_Ecom_Dump", leak_status],
                        "social_networks": [
                            {"platform": "github", "status": "active"},
                            {"platform": "linkedin", "status": "stale"}
                        ]
                    },
                    "network_telemetry": {
                        "last_known_nodes": ["192.168.1.45", "127.0.0.1"],
                        "hostmask_resolutions": "ISP_RESOLVED_STATIC"
                    }
                }
            }
            
            print(json.dumps(result, indent=4))
            print("\n[*] VISUALIZING GRAPH INTERACTION MAP (SQLITE_LIVE):")
            for node in nodes:
                print(f"    [ENTITAS] {node['source']} ──({node['relation']})──> {node['target']}")
        else:
            result = {
                "engine": f"BroCodehaha123 {self.version} [DB_LIVE]",
                "query_resolved": query_param,
                "status": "RECORD_NOT_FOUND_IN_LOCAL_DB",
                "registry_dump": {
                    "identity": {"matched_records": 0, "probable_full_name": "Unknown Entity"}
                }
            }
            print(json.dumps(result, indent=4))
            print(f"\n[!] ALERT: Target identity signature not found in current local database.")
            print(f"    [ENTITAS] ID_{query_param} ──(UNRESOLVED_TARGET)──> Null_Node")
            
        print("=" * 70)

def print_usage():
    print("""
BroCodehaha123 CLI Engine Usage:
  python BroCodeV3.py -t "<target_string>"

Example:
  python BroCodeV3.py -t "Nathan,nathanahmadprabaswara@gmail.com,081232253524"
""")

def main():
    args = sys.argv[1:]
    if not args or "-h" in args or "--help" in args:
        print_usage()
        sys.exit(0)

    target = None
    if args[0] == "-t" and len(args) > 1:
        target = args[1]

    if not target:
        print("[!] ERROR: Target parameter required. Use -t flag.")
        print_usage()
        sys.exit(1)

    cli_engine = BroCodeOSINTCLI()
    cli_engine.init_database()
    cli_engine.execute_lookup(target)

if __name__ == "__main__":
    main()

