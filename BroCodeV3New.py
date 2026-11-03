import sys
import json
import sqlite3
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading

class BroCodeOSINTGUIModern:
    def __init__(self, root):
        self.root = root
        self.root.title("BroCodehaha123 OSINT Intel Engine v3.5-PRO")
        self.root.geometry("1100x700")
        self.root.configure(bg="#0c0f12")
        
        self.db_name = "osint_registry.db"
        self.operator = "Hack123"
        self.version = "v3.5-PRO"
        
        self.init_database()
        self.setup_styles()
        self.create_widgets()
        self.refresh_target_table()

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

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview", 
                        background="#161b22", 
                        foreground="#c9d1d9", 
                        fieldbackground="#161b22", 
                        rowheight=28,
                        font=("Consolas", 10))
        style.map("Treeview", background=[("selected", "#21262d")])
        
        style.configure("Treeview.Heading", 
                        background="#21262d", 
                        foreground="#58a6ff", 
                        font=("Consolas", 10, "bold"),
                        borderwidth=0)

    def create_widgets(self):
        header_frame = tk.Frame(self.root, bg="#0d1117", bd=1, relief=tk.FLAT)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        banner_text = f"ENGINE: BroCodehaha123 {self.version} | OPERATOR: {self.operator} | STATUS: ACTIVE"
        lbl_banner = tk.Label(header_frame, text=banner_text, fg="#23c552", bg="#0d1117", font=("Consolas", 12, "bold"))
        lbl_banner.pack(side=tk.LEFT, padx=15, pady=12)

        main_container = tk.Frame(self.root, bg="#0c0f12")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        left_pane = tk.Frame(main_container, bg="#0c0f12", width=380)
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left_pane.pack_propagate(False)
        
        right_pane = tk.Frame(main_container, bg="#0c0f12")
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        add_frame = tk.LabelFrame(left_pane, text=" [ Register New Target Record ] ", fg="#58a6ff", bg="#161b22", font=("Consolas", 10, "bold"), bd=1)
        add_frame.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        tk.Label(add_frame, text="Parameters (Name,Email,Phone):", fg="#c9d1d9", bg="#161b22", font=("Consolas", 9)).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.ent_query = tk.Entry(add_frame, bg="#0d1117", fg="#fff", insertbackground="white", bd=1, relief=tk.SOLID, font=("Consolas", 10))
        self.ent_query.pack(fill=tk.X, padx=10, pady=2)
        
        tk.Label(add_frame, text="Full Name Target:", fg="#c9d1d9", bg="#161b22", font=("Consolas", 9)).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.ent_fullname = tk.Entry(add_frame, bg="#0d1117", fg="#fff", insertbackground="white", bd=1, relief=tk.SOLID, font=("Consolas", 10))
        self.ent_fullname.pack(fill=tk.X, padx=10, pady=2)
        
        tk.Label(add_frame, text="Data Breach Signature / Status:", fg="#c9d1d9", bg="#161b22", font=("Consolas", 9)).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.ent_leak = tk.Entry(add_frame, bg="#0d1117", fg="#fff", insertbackground="white", bd=1, relief=tk.SOLID, font=("Consolas", 10))
        self.ent_leak.pack(fill=tk.X, padx=10, pady=2)
        
        btn_add = tk.Button(add_frame, text="EXECUTE TARGET REGISTRATION", bg="#23c552", fg="#000", font=("Consolas", 9, "bold"), activebackground="#1ea745", bd=0, command=self.gui_add_target)
        btn_add.pack(fill=tk.X, padx=10, pady=(10, 5))

        ops_frame = tk.LabelFrame(left_pane, text=" [ Intelligence Core Lookup ] ", fg="#58a6ff", bg="#161b22", font=("Consolas", 10, "bold"), bd=1)
        ops_frame.pack(fill=tk.X, pady=(0, 10), ipady=5)
        
        tk.Label(ops_frame, text="Search Term Target Registry:", fg="#c9d1d9", bg="#161b22", font=("Consolas", 9)).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.ent_search = tk.Entry(ops_frame, bg="#0d1117", fg="#fff", insertbackground="white", bd=1, relief=tk.SOLID, font=("Consolas", 10))
        self.ent_search.pack(fill=tk.X, padx=10, pady=2)
        
        btn_search = tk.Button(ops_frame, text="RUN PENCARIAN & VISUALISASI JARINGAN", bg="#58a6ff", fg="#000", font=("Consolas", 9, "bold"), activebackground="#428ed4", bd=0, command=self.gui_execute_lookup)
        btn_search.pack(fill=tk.X, padx=10, pady=(8, 4))

        geo_frame = tk.LabelFrame(left_pane, text=" [ Geolocation & Telecom HLR Resolver ] ", fg="#58a6ff", bg="#161b22", font=("Consolas", 10, "bold"), bd=1)
        geo_frame.pack(fill=tk.BOTH, expand=True, ipady=5)
        
        tk.Label(geo_frame, text="Target MSISDN / Phone Number:", fg="#c9d1d9", bg="#161b22", font=("Consolas", 9)).pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.ent_phone = tk.Entry(geo_frame, bg="#0d1117", fg="#fff", insertbackground="white", bd=1, relief=tk.SOLID, font=("Consolas", 10))
        self.ent_phone.pack(fill=tk.X, padx=10, pady=2)
        
        btn_trace = tk.Button(geo_frame, text="TRACE PHONE TELEMETRY", bg="#f8a532", fg="#000", font=("Consolas", 9, "bold"), activebackground="#d68d27", bd=0, command=self.gui_trace_phone)
        btn_trace.pack(fill=tk.X, padx=10, pady=(8, 4))

        grid_frame = tk.Frame(right_pane, bg="#161b22", bd=1, relief=tk.SOLID)
        grid_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        scroll_y = ttk.Scrollbar(grid_frame, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(grid_frame, orient=tk.HORIZONTAL)
        
        self.tree = ttk.Treeview(grid_frame, columns=("ID", "Query", "Name", "Status"), show="headings", yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.config(command=self.tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.config(command=self.tree.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("Query", text="PARAMETER QUERY (NAMA, EMAIL, NOHP)")
        self.tree.heading("Name", text="NAMA LENGKAP TARGET")
        self.tree.heading("Status", text="STATUS SIGNATURE")
        
        self.tree.column("ID", width=40, anchor=tk.CENTER)
        self.tree.column("Query", width=300, anchor=tk.W)
        self.tree.column("Name", width=200, anchor=tk.W)
        self.tree.column("Status", width=140, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)

        terminal_frame = tk.LabelFrame(right_pane, text=" [ Intel Core Execution Log Terminal ] ", fg="#58a6ff", bg="#161b22", font=("Consolas", 10, "bold"), bd=1)
        terminal_frame.pack(fill=tk.BOTH, expand=False, height=220)
        
        self.txt_terminal = scrolledtext.ScrolledText(terminal_frame, bg="#0d1117", fg="#c9d1d9", insertbackground="white", font=("Consolas", 9), state=tk.DISABLED)
        self.txt_terminal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_terminal("System Core Scaffolding initialized. Ready for operations.")

    def log_terminal(self, message):
        self.txt_terminal.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.txt_terminal.insert(tk.END, f"[{timestamp}] -> {message}\n")
        self.txt_terminal.see(tk.END)
        self.txt_terminal.config(state=tk.DISABLED)

    def refresh_target_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT id, query_string, full_name, leak_status FROM targets")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", tk.END, values=row)
        conn.close()

    def gui_add_target(self):
        q = self.ent_query.get().strip()
        n = self.ent_fullname.get().strip()
        l = self.ent_leak.get().strip()
        
        if not q or not n or not l:
            messagebox.showwarning("Validation Error", "All fields are required for target entry deployment.")
            return
            
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            default_nodes = [
                {"source": "Target_Identity", "relation": "INITIALIZED", "target": "Data_Core"}
            ]
            cursor.execute("""
                INSERT INTO targets (query_string, full_name, leak_status, nodes_data)
                VALUES (?, ?, ?, ?)
            """, (q, n, l, json.dumps(default_nodes)))
            conn.commit()
            conn.close()
            
            self.log_terminal(f"Successfully registered target record: {n}")
            self.ent_query.delete(0, tk.END)
            self.ent_fullname.delete(0, tk.END)
            self.ent_leak.delete(0, tk.END)
            self.refresh_target_table()
        except sqlite3.IntegrityError:
            self.log_terminal("Registration failed: Query parameter string already exists in schema.")
            messagebox.showerror("Error", "Target entry parameter conflict detected.")

    def gui_execute_lookup(self):
        term = self.ent_search.get().strip()
        if not term:
            messagebox.showwarning("Validation Error", "Please provide a query search string.")
            return
            
        self.log_terminal(f"Initiating multi-node database sync lookup for phrase: '{term}'")
        
        def lookup_worker():
            time.sleep(1.2)
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT full_name, leak_status, nodes_data FROM targets 
                WHERE query_string LIKE ? OR full_name LIKE ?
            """, (f"%{term}%", f"%{term}%"))
            result = cursor.fetchall()
            conn.close()
            
            if result:
                for name, status, nodes in result:
                    self.log_terminal(f"MATCH DEPLOYED -> Name: {name} | Status: {status}")
                    node_list = json.loads(nodes)
                    for node in node_list:
                        self.log_terminal(f"  [Node Link] {node['source']} --({node['relation']})--> {node['target']}")
            else:
                self.log_terminal(f"Zero matching nodes resolved for query term: '{term}'")
                
        threading.Thread(target=lookup_worker, daemon=True).start()

    def gui_trace_phone(self):
        phone = self.ent_phone.get().strip()
        if not phone:
            messagebox.showwarning("Validation Error", "Target MSISDN configuration missing.")
            return
            
        self.log_terminal(f"Triggering Telecom HLR Routing trace to target: {phone}")
        
        def trace_worker():
            stages = ["Accessing SS7 Interconnect...", "Querying MSC Registry...", "Resolving LAC/CID coordinates...", "Finished."]
            for stage in stages:
                time.sleep(0.8)
                self.log_terminal(f"HLR Thread: {stage}")
            self.log_terminal(f"Trace complete for {phone}. Virtual baseline mapped.")
            
        threading.Thread(target=trace_worker, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = BroCodeOSINTGUIModern(root)
    root.mainloop()
