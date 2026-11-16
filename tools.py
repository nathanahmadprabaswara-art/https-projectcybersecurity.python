"""BroCode tools. Each tool is a generator that yields output lines.
Hanya gunakan pada target yang kamu miliki / punya izin tertulis."""
import socket, ssl, re, json, math, shutil, subprocess, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 BroCode/1.0"}
TOP_PORTS = [21,22,23,25,53,80,110,111,135,139,143,443,445,465,587,993,995,
             1433,1521,2049,3306,3389,5432,5900,6379,8000,8080,8443,9200,27017]
SERVICES = {21:"ftp",22:"ssh",23:"telnet",25:"smtp",53:"dns",80:"http",110:"pop3",
    111:"rpc",135:"msrpc",139:"netbios",143:"imap",443:"https",445:"smb",465:"smtps",
    587:"submission",993:"imaps",995:"pop3s",1433:"mssql",1521:"oracle",2049:"nfs",
    3306:"mysql",3389:"rdp",5432:"postgres",5900:"vnc",6379:"redis",8000:"http-alt",
    8080:"http-proxy",8443:"https-alt",9200:"elasticsearch",27017:"mongodb"}

def _http(url, timeout=8, method="GET"):
    req = urllib.request.Request(url, headers=UA, method=method)
    return urllib.request.urlopen(req, timeout=timeout)

def _host(t):
    t = t.strip()
    if "://" in t: t = urllib.parse.urlparse(t).hostname or t
    return t.split("/")[0].split(":")[0]

def _resolve(t):
    return socket.gethostbyname(_host(t))

# ---------------- NMAP ----------------
def nmap_scan(target, mode="quick"):
    """Pakai nmap asli jika terpasang, kalau tidak pakai scanner TCP bawaan."""
    host = _host(target)
    if shutil.which("nmap"):
        args = {"quick": ["-T4","-F"], "service": ["-sV","-T4","-F"],
                "full": ["-T4","-p-"], "os": ["-O","-sV","-T4","-F"]}.get(mode, ["-T4","-F"])
        yield f"[nmap] nmap {' '.join(args)} {host}"
        p = subprocess.Popen(["nmap", *args, host], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True)
        for line in p.stdout: yield line.rstrip()
        return
    yield "[!] nmap tidak terpasang -> memakai TCP connect scanner bawaan"
    yield from port_scan(host)

def port_scan(target, ports=None, timeout=0.8):
    host = _host(target)
    try: ip = _resolve(host)
    except Exception as e: yield f"[x] DNS gagal: {e}"; return
    ports = ports or TOP_PORTS
    yield f"Scanning {host} ({ip}) - {len(ports)} port"
    def probe(p):
        try:
            with socket.create_connection((ip, p), timeout=timeout) as s:
                s.settimeout(0.6); banner = ""
                try:
                    if p in (80,8000,8080): s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
                    banner = s.recv(80).decode(errors="ignore").strip().splitlines()[0][:50]
                except Exception: pass
                return p, banner
        except Exception: return None
    found = 0
    with ThreadPoolExecutor(60) as ex:
        for r in ex.map(probe, ports):
            if r:
                found += 1
                yield f"  {r[0]:<6}open   {SERVICES.get(r[0],'?'):<14}{r[1]}"
    yield f"Selesai: {found} port terbuka"

def host_discovery(cidr_or_ip):
    import ipaddress
    try: net = ipaddress.ip_network(cidr_or_ip, strict=False)
    except Exception as e: yield f"[x] {e}"; return
    hosts = [str(h) for h in net.hosts()][:256]
    yield f"Discovery {net} ({len(hosts)} host)"
    def alive(ip):
        for p in (80,443,22,445):
            try:
                socket.create_connection((ip,p),timeout=0.5).close(); return ip,p
            except ConnectionRefusedError: return ip,p
            except Exception: pass
    with ThreadPoolExecutor(100) as ex:
        for r in ex.map(alive, hosts):
            if r: yield f"  UP  {r[0]}  (via tcp/{r[1]})"
    yield "Selesai"

# ---------------- OSINT ----------------
def dns_lookup(target):
    host = _host(target)
    try:
        name, alias, ips = socket.gethostbyname_ex(host)
        yield f"Host   : {name}"
        for i in ips:
            try: rev = socket.gethostbyaddr(i)[0]
            except Exception: rev = "-"
            yield f"A      : {i}   (rDNS: {rev})"
        for a in alias: yield f"CNAME  : {a}"
        try:
            for r in socket.getaddrinfo(host, None, socket.AF_INET6):
                yield f"AAAA   : {r[4][0]}"; break
        except Exception: pass
    except Exception as e: yield f"[x] {e}"

def whois(target):
    q = _host(target)
    server = "whois.iana.org"
    for _ in range(3):
        try:
            with socket.create_connection((server, 43), timeout=8) as s:
                s.sendall((q + "\r\n").encode()); data = b""
                while True:
                    c = s.recv(4096)
                    if not c: break
                    data += c
        except Exception as e: yield f"[x] {e}"; return
        txt = data.decode(errors="ignore")
        m = re.search(r"(?im)^(?:refer|whois):\s*(\S+)", txt)
        if m and m.group(1) != server: server = m.group(1); continue
        break
    keep = re.compile(r"(?i)^(domain name|registrar|creation|created|updated|expir|name server|"
                      r"status|org|netname|country|inetnum|cidr|descr|abuse|registrant org)")
    n = 0
    for l in txt.splitlines():
        if keep.match(l.strip()): yield "  " + l.strip()[:90]; n += 1
        if n > 40: break
    if not n: yield "  (tidak ada data ringkas)"

def ip_geo(target):
    try: ip = _resolve(target)
    except Exception as e: yield f"[x] {e}"; return
    try:
        d = json.load(_http(f"http://ip-api.com/json/{ip}?fields=66846719"))
        for k in ("query","country","regionName","city","isp","org","as","timezone","lat","lon","proxy","hosting"):
            if k in d: yield f"  {k:<11}: {d[k]}"
    except Exception as e: yield f"[x] geolokasi gagal: {e}"

def http_headers(url):
    if "://" not in url: url = "https://" + url
    try: r = _http(url)
    except urllib.error.HTTPError as r: pass
    except Exception as e: yield f"[x] {e}"; return
    yield f"HTTP {r.status}  {r.geturl()}"
    h = {k.lower(): v for k, v in r.headers.items()}
    for k in ("server","x-powered-by","content-type","set-cookie"):
        if k in h: yield f"  {k}: {h[k][:70]}"
    yield "Security headers:"
    for k in ("strict-transport-security","content-security-policy","x-frame-options",
              "x-content-type-options","referrer-policy","permissions-policy"):
        yield f"  [{'OK' if k in h else '--'}] {k}"

def ssl_info(target):
    host = _host(target)
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=8) as s:
            with ctx.wrap_socket(s, server_hostname=host) as ss:
                c = ss.getpeercert(); yield f"TLS    : {ss.version()}  {ss.cipher()[0]}"
        sub = dict(x[0] for x in c["subject"]); iss = dict(x[0] for x in c["issuer"])
        yield f"Subject: {sub.get('commonName')}"
        yield f"Issuer : {iss.get('organizationName')}"
        yield f"Valid  : {c['notBefore']}  ->  {c['notAfter']}"
        san = [v for k, v in c.get("subjectAltName", [])][:8]
        yield f"SAN    : {', '.join(san)}"
    except Exception as e: yield f"[x] {e}"

def subdomain_enum(target):
    d = _host(target)
    words = "www mail ftp dev test staging api admin portal vpn blog shop cdn app m ns1 ns2 smtp imap webmail git jenkins grafana docs status beta intranet db".split()
    yield f"Brute-force {len(words)} subdomain untuk {d}"
    def r(w):
        try: return w, socket.gethostbyname(f"{w}.{d}")
        except Exception: return None
    with ThreadPoolExecutor(30) as ex:
        for x in ex.map(r, words):
            if x: yield f"  {x[0]+'.'+d:<34}{x[1]}"
    yield "Selesai"

def phishing_check(url):
    if "://" not in url: url = "http://" + url
    u = urllib.parse.urlparse(url); h = (u.hostname or "").lower(); score = 0; notes = []
    def add(n, p): 
        nonlocal score; score += p; notes.append(f"  [+{p}] {n}")
    if re.fullmatch(r"[\d.]+", h): add("host berupa alamat IP", 25)
    if "@" in u.netloc: add("karakter '@' di URL", 25)
    if h.startswith("xn--") or ".xn--" in h: add("punycode (homograph)", 25)
    if u.scheme != "https": add("tidak memakai HTTPS", 10)
    if len(url) > 75: add("URL sangat panjang", 10)
    if h.count(".") >= 4: add("terlalu banyak subdomain", 15)
    if h.count("-") >= 3: add("banyak tanda hubung", 10)
    if re.search(r"\.(zip|top|xyz|click|tk|ml|ga|cf|gq|work|country)$", h): add("TLD berisiko", 15)
    kw = [k for k in ("login","verify","secure","account","update","bank","paypal","wallet","signin","password","confirm") if k in url.lower()]
    if kw: add("kata kunci: " + ",".join(kw), 5 * min(len(kw), 4))
    if h:
        p = {c: h.count(c) / len(h) for c in set(h)}
        if -sum(v * math.log2(v) for v in p.values()) > 3.8: add("domain tampak acak (entropi tinggi)", 10)
    for l in notes: yield l
    lvl = "TINGGI" if score >= 50 else "SEDANG" if score >= 25 else "RENDAH"
    yield f"Skor risiko: {min(score,100)}/100  ->  {lvl}"
    yield "(heuristik saja, verifikasi juga via VirusTotal / urlscan.io)"

def username_osint(name):
    sites = {"GitHub":"https://github.com/{}","GitLab":"https://gitlab.com/{}","Reddit":"https://www.reddit.com/user/{}",
             "Twitter/X":"https://x.com/{}","Instagram":"https://www.instagram.com/{}","TikTok":"https://www.tiktok.com/@{}",
             "Medium":"https://medium.com/@{}","Dev.to":"https://dev.to/{}","Keybase":"https://keybase.io/{}"}
    yield f"Mencari username '{name}' di {len(sites)} situs (hasil 200 = kemungkinan ada)"
    def chk(kv):
        try: return kv[0], _http(kv[1].format(name), 6).status, kv[1].format(name)
        except urllib.error.HTTPError as e: return kv[0], e.code, kv[1].format(name)
        except Exception: return kv[0], 0, ""
    with ThreadPoolExecutor(9) as ex:
        for n, c, u in ex.map(chk, sites.items()):
            yield f"  [{'FOUND' if c==200 else ' -- ' if c else 'ERR '}] {n:<10} {u if c==200 else ''}"

def traceroute(target):
    host = _host(target); exe = shutil.which("traceroute") or shutil.which("tracepath")
    if not exe: yield "[!] traceroute/tracepath tidak tersedia"; return
    p = subprocess.Popen([exe, "-n", host], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for l in p.stdout: yield l.rstrip()

TOOLS = [  # (hotkey, name, func, argumen, contoh)
 ("1","NMAP SCAN",nmap_scan,"host","scanme.nmap.org"),
 ("2","PORT SCAN",port_scan,"host","127.0.0.1"),
 ("3","HOST DISCOVERY",host_discovery,"cidr","192.168.1.0/24"),
 ("4","DNS LOOKUP",dns_lookup,"domain","example.com"),
 ("5","WHOIS",whois,"domain/ip","example.com"),
 ("6","IP GEOLOCATE",ip_geo,"ip/domain","8.8.8.8"),
 ("7","HTTP HEADERS",http_headers,"url","example.com"),
 ("8","SSL CERT",ssl_info,"domain","example.com"),
 ("9","SUBDOMAINS",subdomain_enum,"domain","example.com"),
 ("a","PHISHING URL",phishing_check,"url","http://paypa1-login.xyz/verify"),
 ("b","USERNAME OSINT",username_osint,"username","torvalds"),
 ("c","TRACEROUTE",traceroute,"host","1.1.1.1"),
]
