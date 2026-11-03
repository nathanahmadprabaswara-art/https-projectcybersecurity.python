import sys
import json
import sqlite3
import time

class BroCodeOSINTCLIPro:
    def __init__(self):
        self.db_name = "osint_registry.db"
        self.operator = "Hack123"
        self.version = "v3.0-PRO"

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
        
        cursor.execute("SELECT COUNT(*) FROM targets")
        if cursor.fetchone()[0] == 0:
            sample_nodes = [
                {"source": "Target_Identity", "relation": "MAPPED_TO", "target": "Digital_Footprint"},
                {"source": "Digital_Footprint", "relation": "LINKED_WITH", "target": "Network_Telemetry"},
                {"source": "Network_Telemetry", "relation": "RESOLVED_BY", "target": "BroCodehaha123_Core"}
            ]
            cursor.execute("""
                INSERT INTO targets (query_string, full_name, leak_status, nodes_data)
                VALUES (?, ?, ?, ?)
            """, ("Nathan,nathanahmadprabaswara@gmail.com,081232253524", "Nathan Ahmad Prabaswara", "CRITICAL_LEAK_FOUND", json.dumps(sample_nodes)))
            conn.commit()
        conn.close()

    def show_banner(self):
        print("\033[92m" + "=" * 75)
        print(f"   ____             ____          _      _   _            _ _ _ ")
        print(f"  | __ ) _ __ ___  / ___|___   __| | ___| | | | __ _  ___| | | |")
        print(f"  |  _ \\| '__/ _ \\| |   / _ \\ / _` |/ _ \\ |_| |/ _` |/ __| | | |")
        print(f"  | |_) | | | (_) | |__| (_) | (_| |  __/  _  | (_| | (__|_|_|_|")
        print(f"  |____/|_|  \\___/ \\____\\___/ \\__,_|\\___|_| |_|\\__,_|\\___(_|_|_)")
        print(f"\n  ENGINE: BroCodehaha123 {self.version} | OPERATOR: {self.operator} | STATUS: ACTIVE")
        print("=" * 75 + "\033[0m")

    def simulate_loading(self, text):
        sys.stdout.write(f"[*] {text}")
        sys.stdout.flush()
        for _ in range(3):
            time.sleep(0.3)
            sys.stdout.write(".")
            sys.stdout.flush()
        print(" [DONE]")

    def add_target(self):
        print("\n\033[93m[+] MENU: TAMBAH DATA TARGET BARU\033[0m")
        query_string = input("Masukkan Parameter Unik (Nama,Email,NoHP): ").strip()
        if not query_string:
            print("\033[91m[!] Error: Parameter tidak boleh kosong!\033[0m")
            return
        
        full_name = input("Masukkan Nama Lengkap Target: ").strip()
        leak_status = input("Masukkan Status Kebocoran Data (Contoh: CRITICAL_LEAK): ").strip()
        
        target_clean = full_name.replace(" ", "_")
        param_list = query_string.split(",") if "," in query_string else [query_string]
        
        custom_nodes = [
            {"source": target_clean, "relation": "IDENTIFIED_BY", "target": str(param_list)},
            {"source": str(param_list), "relation": "HAS_TELEMETRY", "target": "Network_Node_Active"}
        ]
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO targets (query_string, full_name, leak_status, nodes_data)
                VALUES (?, ?, ?, ?)
            """, (query_string, full_name, leak_status, json.dumps(custom_nodes)))
            conn.commit()
            print(f"\033[92m[+] Sukses: Target '{full_name}' berhasil disimpan ke database.\033[0m")
        except sqlite3.IntegrityError:
            print("\033[91m[!] Error: Parameter target tersebut sudah ada di database.\033[0m")
        finally:
            conn.close()

    def view_all_targets(self):
        print("\n\033[93m[+] MENU: DAFTAR SEMUA TARGET DI DATABASE\033[0m")
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, query_string, full_name FROM targets")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("[-] Database kosong. Belum ada target terdaftar.")
            return
            
        for row in rows:
            print(f" ID: {row[0]} | Nama: {row[2]} | Query: {row[1]}")

    def execute_lookup(self, query_param=None):
        if not query_param:
            print("\n\033[93m[+] MENU: PENCARIAN & VISUALISASI REKORD TARGET\033[0m")
            query_param = input("Masukkan Parameter Target untuk di-scan: ").strip()
        
        self.simulate_loading("Menghubungkan ke SQLite Core Registry")
        self.simulate_loading("Mengekstraksi peta jaringan intelijen terbuka")
        print("-" * 75)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, leak_status, nodes_data FROM targets WHERE query_string LIKE ?", (f"%{query_param}%",))
        row = cursor.fetchone()
        conn.close()

        if row:
            full_name, leak_status, nodes_data = row
            nodes = json.loads(nodes_data)
            
            result = {
                "engine": f"BroCodehaha123 {self.version} [INTELLIGENCE_LIVE]",
                "query_resolved": query_param,
                "status": "SUCCESS",
                "registry_dump": {
                    "identity": {
                        "matched_records": 1,
                        "probable_full_name": full_name,
                        "data_integrity": "COMPROMISED"
                    },
                    "telemetry": {
                        "breach_signature": leak_status,
                        "infrastructure_node": "ISP_RESOLVED_STATIC"
                    }
                }
            }
            
            print("\033[96m" + json.dumps(result, indent=4) + "\033[0m")
            print("\n\033[92m[*] VISUALIZING GRAPH INTERACTION MAP (SQLITE_LIVE):\033[0m")
            for node in nodes:
                print(f"    \033[91m[ENTITAS]\033[0m {node['source']} \033[93m──({node['relation']})──>\033[0m {node['target']}")
        else:
            print(f"\n\033[91m[!] ALERT: Tanda tangan identitas target '{query_param}' tidak ditemukan.\033[0m")
        print("-" * 75)

    def interactive_menu(self):
        self.init_database()
        while True:
            self.show_banner()
            print("PILIH MODUL EKSEKUSI:")
            print(" [1] Jalankan Intel Lookup & Visualisasi Grafik Relasi")
            print(" [2] Tambah Rekord Target Baru ke Database")
            print(" [3] Tampilkan Semua Target Terdaftar")
            print(" [4] Keluar dari Sistem (Exit)")
            print("-" * 75)
            
            pilihan = input("BroCodehaha123_#> ").strip()
            
            if pilihan == "1":
                self.execute_lookup()
            elif pilihan == "2":
                self.add_target()
            elif pilihan == "3":
                self.view_all_targets()
            elif pilihan == "4":
                print("\n[*] Menutup repositori database eksekusi. Sistem dibersihkan.")
                break
            else:
                print("\n\033[91m[!] Opsi pilihan modul tidak valid!\033[0m")
            
            input("\nTekan [Enter] untuk kembali ke Menu Utama...")

def main():
    cli_engine = BroCodeOSINTCLIPro()
    cli_engine.interactive_menu()

if __name__ == "__main__":
    main()
