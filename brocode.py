#!/usr/bin/env python3
"""
BroCode v2 - Toolkit OSINT pasif untuk riset keamanan & verifikasi hoaks.
Dibuat oleh Nathan.

Mode interaktif : python brocode.py
Mode perintah   : python brocode.py <perintah> [opsi]

  url    <url>...       Verifikasi risiko phishing URL
  ip     <ip>...        Analisis IP & jaringan
  domain <domain>...    Recon pasif domain (RDAP, DNS, SPF/DKIM/DMARC, subdomain, header keamanan)
  email  <file|->       Analisis header email (deteksi spoofing / phishing)
  hoax   "<klaim>"      Verifikasi klaim (Google Fact Check API + ciri-ciri hoaks)
  image  <file>...      Metadata & jejak keaslian gambar (EXIF, hash, tautan reverse search)
  batch  <file>         Analisis banyak target sekaligus
  menu                  Mode interaktif

Opsi umum: --json | -o laporan.html|csv|json | --no-banner

API key opsional (environment variable):
  VT_API_KEY          VirusTotal (url, ip)
  ABUSEIPDB_API_KEY   AbuseIPDB (ip)
  GOOGLE_API_KEY      Google Fact Check Tools API (hoax)
  BROCODE_TIMEOUT     batas waktu koneksi dalam detik (default 8)

Dependensi : pip install requests rich
Opsional   : pip install pillow   (untuk metadata EXIF gambar)

Etika: hanya memakai sumber data publik dan permintaan ringan (tanpa port scan).
Gunakan untuk aset milik sendiri / yang Anda berwenang memeriksanya, jangan untuk
menargetkan individu. Skor adalah indikator, bukan bukti - verifikasi manual.
"""

import argparse
import base64
import contextlib
import csv
import difflib
import hashlib
import html
import ipaddress
import json
import os
import re
import socket
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.parser import Parser
from email.utils import parseaddr
from urllib.parse import quote, urljoin, urlparse

try:
    import requests
    from rich import box
    from rich.columns import Columns
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree
except ImportError:
    sys.exit("Dependensi belum terpasang. Jalankan: pip install requests rich")

try:
    from PIL import ExifTags, Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

VERSION = "2.0"
UA = "Mozilla/5.0 (compatible; BroCode/2.0; security-research)"
try:
    TIMEOUT = float(os.environ.get("BROCODE_TIMEOUT", "8"))
except ValueError:
    TIMEOUT = 8.0

console = Console()

# ------------------------------------------------------------------ data

TWO_LEVEL_SUFFIXES = {
    "co.id", "go.id", "ac.id", "or.id", "web.id", "sch.id", "my.id", "net.id",
    "co.uk", "org.uk", "com.au", "co.jp", "com.sg", "com.my", "co.in",
}

SUSPICIOUS_TLDS = {
    "zip", "mov", "top", "xyz", "icu", "click", "link", "tk", "ml", "ga", "cf",
    "gq", "cyou", "sbs", "cfd", "rest", "support", "country", "work", "buzz",
}

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rb.gy",
    "s.id", "ow.ly", "shorturl.at", "bit.do", "t.ly", "rebrand.ly",
}

KEYWORDS = [
    "login", "signin", "verify", "verifikasi", "update", "secure", "account",
    "akun", "password", "otp", "konfirmasi", "hadiah", "undian", "klaim",
    "blokir", "suspend", "bantuan", "refund", "wallet", "pin",
]

# Brand -> domain resmi (registered domain). Tambahkan brand perusahaan Anda di sini.
BRANDS = {
    "bca": {"bca.co.id", "klikbca.com"},
    "mandiri": {"bankmandiri.co.id", "livin.bankmandiri.co.id"},
    "bri": {"bri.co.id"},
    "bni": {"bni.co.id"},
    "tokopedia": {"tokopedia.com"},
    "shopee": {"shopee.co.id", "shopee.com"},
    "gojek": {"gojek.com"},
    "dana": {"dana.id"},
    "ovo": {"ovo.id"},
    "linkaja": {"linkaja.id"},
    "telkomsel": {"telkomsel.com"},
    "bpjs": {"bpjs-kesehatan.go.id", "bpjsketenagakerjaan.go.id"},
    "google": {"google.com", "google.co.id"},
    "microsoft": {"microsoft.com", "live.com", "office.com"},
    "paypal": {"paypal.com"},
    "apple": {"apple.com", "icloud.com"},
    "facebook": {"facebook.com"},
    "instagram": {"instagram.com"},
    "whatsapp": {"whatsapp.com"},
    "amazon": {"amazon.com"},
    "netflix": {"netflix.com"},
}

CLOUD_HINTS = [
    "amazon", "aws", "google", "microsoft", "azure", "digitalocean", "ovh",
    "hetzner", "linode", "vultr", "cloudflare", "alibaba", "oracle", "contabo",
]

SEC_HEADERS = [
    ("strict-transport-security", "HSTS", "sedang"),
    ("content-security-policy", "CSP", "sedang"),
    ("x-content-type-options", "X-Content-Type-Options", "rendah"),
    ("x-frame-options", "X-Frame-Options", "rendah"),
    ("referrer-policy", "Referrer-Policy", "rendah"),
    ("permissions-policy", "Permissions-Policy", "rendah"),
]

DKIM_SELECTORS = ["default", "google", "selector1", "selector2", "k1", "mail"]
DOH_TYPES = {"A": 1, "NS": 2, "MX": 15, "TXT": 16, "AAAA": 28, "CAA": 257}
PENALTY = {"tinggi": 20, "sedang": 10, "rendah": 4, "info": 0}
SEV_STYLE = {"tinggi": "bold red", "sedang": "yellow", "rendah": "cyan", "info": "dim"}
SEV_ORDER = {"tinggi": 0, "sedang": 1, "rendah": 2, "info": 3}

URGENT_WORDS = ["segera", "urgent", "verifikasi", "diblokir", "blokir", "hadiah", "suspend",
                "action required", "limited", "konfirmasi", "kedaluwarsa", "expired", "final notice"]

HOAX_PATTERNS = [
    (r"\b(viral|sebarkan|bagikan|broadcast|forward|tolong share|share ke|sebar)\b", 10,
     "Ajakan menyebarkan pesan (pola umum hoaks berantai)"),
    (r"\b(100\s*%|dijamin|terbukti|pasti benar)\b", 8, "Klaim mutlak tanpa bukti"),
    (r"\b(menurut sumber|katanya|konon|info dari|dari grup|dari teman|dikabarkan)\b", 10,
     "Sumber tidak jelas / rujukan lisan"),
    (r"\b(urgent|segera|darurat|waspada|awas|hati-hati|jangan sampai)\b", 8,
     "Bahasa mendesak atau menakut-nakuti"),
    (r"\b(gratis|hadiah|undian|bagi-bagi|bansos|subsidi|saldo)\b", 10,
     "Iming-iming hadiah/bantuan (sering dipakai penipuan)"),
    (r"\b(dokter|peneliti|ilmuwan|pakar|profesor)\b", 4,
     "Mengutip otoritas tanpa menyebut nama/institusi yang bisa dicek"),
]

FACT_CHECK_SITES = [
    ("TurnBackHOAX (Mafindo)", "https://turnbackhoax.id"),
    ("CekFakta.com", "https://cekfakta.com"),
    ("Google Fact Check Explorer", "https://toolbox.google.com/factcheck/explorer"),
]

IMAGE_SEARCH_SITES = [
    ("Google Lens", "https://lens.google.com/"),
    ("TinEye", "https://tineye.com/"),
    ("Yandex Images", "https://yandex.com/images/"),
]

AI_TOOLS = ["midjourney", "stable diffusion", "dall-e", "dalle", "firefly", "dreamstudio",
            "comfyui", "automatic1111", "novelai"]
EDIT_TOOLS = ["photoshop", "gimp", "canva", "lightroom", "snapseed", "picsart", "facetune",
              "pixlr", "paint.net"]

BANNER_ART = [
    r"    .-----.         .-----.",
    r"    |     |         |     |",
    r"  .'       '._____.'       '.",
    r"  |  .---.  |#####|  .---.  |",
    r"  | /  +  \ |#####| /  +  \ |",
    r"  | \_____/ |#####| \_____/ |",
    r"  '-._____.-'     '-._____.-'",
]

BANNER_WORD = [
    r" ___            ___          _     ",
    r"| _ ) _ _ ___  / __|___  __| |___ ",
    r"| _ \| '_/ _ \| (__/ _ \/ _` / -_)",
    r"|___/|_| \___/ \___\___/\__,_\___|",
]


# --------------------------------------------------------------- utilitas

def T(value, style=""):
    """Teks rich yang aman (tidak mem-parse markup dari data eksternal)."""
    return Text("" if value is None else str(value), style=style)


def now_utc():
    return datetime.now(timezone.utc)


def parse_dt(s):
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def resolve(host):
    try:
        return {ai[4][0] for ai in socket.getaddrinfo(host, None)}
    except (socket.gaierror, UnicodeError, OSError):
        return set()


def is_public_host(host):
    """True jika host resolve ke IP publik saja (cegah akses ke jaringan internal)."""
    ips = resolve(host)
    if not ips:
        return False
    try:
        return all(ipaddress.ip_address(i.split("%")[0]).is_global for i in ips)
    except ValueError:
        return False


def registered_domain(host):
    parts = host.lower().strip(".").split(".")
    n = 3 if len(parts) >= 3 and ".".join(parts[-2:]) in TWO_LEVEL_SUFFIXES else 2
    if len(parts) < n:
        return host.lower(), parts[0], 0
    return ".".join(parts[-n:]), parts[-n], len(parts) - n


def clean_domain(raw):
    raw = raw.strip().lower()
    if "://" in raw:
        raw = urlparse(raw).hostname or raw
    raw = raw.split("/")[0].split(":")[0].strip(".")
    return raw


def normalize_label(s):
    """Normalisasi homoglyph sederhana: 0->o, 1->l, 3->e, 5->s, rn->m."""
    s = s.lower().replace("rn", "m")
    return s.translate(str.maketrans("0135", "oles"))


def http_get_json(url, headers=None, params=None, timeout=None):
    try:
        r = requests.get(url, headers=headers, params=params, timeout=timeout or TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except (requests.RequestException, ValueError):
        pass
    return None


def verdict_for(score):
    if score >= 60:
        return "KEMUNGKINAN BESAR PHISHING"
    if score >= 30:
        return "MENCURIGAKAN"
    return "RISIKO RENDAH (bukan jaminan aman)"


def score_color(score):
    return "red" if score >= 60 else "yellow" if score >= 30 else "green"


def new_result(kind, raw):
    r = {"kind": kind, "input": raw, "score": 0, "verdict": "", "findings": [], "info": {}}

    def add(points, text, severity=None):
        r["score"] += points
        item = {"points": points, "text": text}
        if severity:
            item["severity"] = severity
        r["findings"].append(item)

    return r, add


# ------------------------------------------------------------ analisis URL

def brand_lookalike(host):
    reg, label, _ = registered_domain(host)
    norm = normalize_label(label)
    host_l = host.lower()
    for brand, official in BRANDS.items():
        if reg in official:
            return None
        if brand in norm.split("-") or (len(brand) >= 5 and brand in norm):
            return f"memuat nama brand '{brand}' tetapi bukan domain resmi"
        if brand in host_l.split(".")[:-2] or any(brand == p for p in host_l.split(".")[:-1]):
            return f"subdomain menyerupai brand '{brand}' pada domain tidak resmi ({reg})"
        ratio = difflib.SequenceMatcher(None, norm, brand).ratio()
        if len(brand) >= 4 and 0.8 <= ratio < 1.0:
            return f"mirip brand '{brand}' (typosquatting, kemiripan {ratio:.0%})"
        if norm == brand:
            return f"meniru brand '{brand}' dengan karakter pengganti"
    return None


def follow(url, max_hops=10):
    """Ikuti redirect secara manual, hanya ke host publik. Tidak mengunduh body."""
    chain, headers, status = [], None, None
    s = requests.Session()
    s.headers["User-Agent"] = UA
    cur = url
    for _ in range(max_hops):
        host = urlparse(cur).hostname
        if not host:
            chain.append({"url": cur, "status": "URL tidak valid"})
            break
        if not is_public_host(host):
            chain.append({"url": cur, "status": "dilewati (DNS gagal / IP non-publik)"})
            break
        try:
            r = s.get(cur, allow_redirects=False, timeout=TIMEOUT, stream=True)
        except requests.exceptions.SSLError:
            chain.append({"url": cur, "status": "error SSL"})
            break
        except requests.RequestException as e:
            chain.append({"url": cur, "status": f"error: {type(e).__name__}"})
            break
        chain.append({"url": cur, "status": r.status_code})
        headers = {k.lower(): v for k, v in r.headers.items()}
        status = r.status_code
        loc = r.headers.get("Location")
        redirected = r.is_redirect and loc
        r.close()
        if not redirected:
            break
        cur = urljoin(cur, loc)
    return {"chain": chain, "headers": headers, "status": status}


def vcard_field(entity, field):
    for item in (entity.get("vcardArray") or [None, []])[1]:
        if item and item[0] == field:
            return item[3]
    return None


def rdap_domain(domain):
    data = http_get_json(f"https://rdap.org/domain/{domain}",
                         headers={"Accept": "application/rdap+json"})
    if not data:
        return None
    out = {"registrar": None, "created": None, "expires": None, "updated": None,
           "status": data.get("status", []),
           "nameservers": [n.get("ldhName", "").lower() for n in data.get("nameservers", [])]}
    for ev in data.get("events", []):
        act, date = ev.get("eventAction"), ev.get("eventDate")
        if act == "registration":
            out["created"] = date
        elif act == "expiration":
            out["expires"] = date
        elif act == "last changed":
            out["updated"] = date
    for ent in data.get("entities", []):
        if "registrar" in ent.get("roles", []):
            out["registrar"] = vcard_field(ent, "fn")
    c, e = parse_dt(out["created"]), parse_dt(out["expires"])
    out["age_days"] = (now_utc() - c).days if c else None
    out["days_to_expiry"] = (e - now_utc()).days if e else None
    return out


def domain_age_days(domain):
    info = rdap_domain(domain)
    return info["age_days"] if info else None


def tls_info(host, port=443):
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ss:
                cert = ss.getpeercert()
    except ssl.SSLCertVerificationError as e:
        return {"valid": False, "error": e.verify_message}
    except (OSError, ssl.SSLError) as e:
        return {"valid": None, "error": str(e)}
    nb = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notBefore"]), timezone.utc)
    na = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), timezone.utc)
    issuer = dict(x[0] for x in cert.get("issuer", ())).get("organizationName", "?")
    return {
        "valid": True,
        "issuer": issuer,
        "not_before": nb.date().isoformat(),
        "not_after": na.date().isoformat(),
        "age_days": (now_utc() - nb).days,
        "days_left": (na - now_utc()).days,
    }


def vt_lookup(kind, ident):
    key = os.environ.get("VT_API_KEY")
    if not key:
        return None
    data = http_get_json(f"https://www.virustotal.com/api/v3/{kind}/{ident}",
                         headers={"x-apikey": key})
    if not data:
        return {"note": "tidak ada data / belum pernah dipindai di VirusTotal"}
    return data.get("data", {}).get("attributes", {})


def analyze_url(raw, fetch=True):
    result, add = new_result("url", raw)
    url = raw if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw) else "http://" + raw
    p = urlparse(url)
    host = (p.hostname or "").lower()
    if not host:
        result["error"] = "URL tidak valid"
        return result

    result["info"]["host"] = host
    reg, label, sub_count = registered_domain(host)
    result["info"]["registered_domain"] = reg

    if p.scheme == "http":
        add(10, "Tidak memakai HTTPS")
    if "@" in p.netloc:
        add(25, "URL memuat '@' (teknik menyamarkan tujuan sebenarnya)")
    try:
        ipaddress.ip_address(host)
        add(25, "Host berupa alamat IP, bukan nama domain")
    except ValueError:
        pass
    if "xn--" in host:
        add(20, "Domain memakai punycode/IDN (risiko homograph attack)")
    if len(url) > 100:
        add(5, f"URL sangat panjang ({len(url)} karakter)")
    if sub_count >= 3:
        add(10, f"Banyak subdomain ({sub_count} level)")
    if host.count("-") >= 3:
        add(8, "Banyak tanda hubung pada domain")
    tld = host.rsplit(".", 1)[-1]
    if tld in SUSPICIOUS_TLDS:
        add(12, f"TLD '.{tld}' sering disalahgunakan")
    if reg in SHORTENERS:
        add(8, "Layanan pemendek URL (tujuan asli disembunyikan)")
    hits = [k for k in KEYWORDS if k in (host + p.path + p.query).lower()]
    if hits:
        add(min(16, 4 * len(hits)), "Kata kunci umum phishing: " + ", ".join(hits[:6]))
    bl = brand_lookalike(host)
    if bl:
        add(30, "Peniruan brand: " + bl)

    if fetch:
        chain = follow(url)["chain"]
        result["info"]["redirect_chain"] = chain
        if len(chain) > 3:
            add(8, f"Rantai redirect panjang ({len(chain)} hop)")
        final_host = urlparse(chain[-1]["url"]).hostname if chain else None
        if final_host and registered_domain(final_host)[0] != reg:
            result["info"]["final_domain"] = registered_domain(final_host)[0]
            if reg not in SHORTENERS:
                add(6, f"Redirect berpindah ke domain lain: {registered_domain(final_host)[0]}")
            fb = brand_lookalike(final_host)
            if fb:
                add(30, "Tujuan akhir meniru brand: " + fb)

    age = domain_age_days(reg)
    if age is None:
        result["info"]["domain_age_days"] = "tidak tersedia (RDAP untuk TLD ini mungkin tidak didukung)"
    else:
        result["info"]["domain_age_days"] = age
        if age < 30:
            add(30, f"Domain baru dibuat ({age} hari lalu)")
        elif age < 180:
            add(15, f"Domain relatif baru ({age} hari)")

    if fetch and is_public_host(host):
        tls = tls_info(host)
        result["info"]["tls"] = tls
        if tls.get("valid") is False:
            add(20, f"Sertifikat TLS tidak valid: {tls.get('error')}")
        elif tls.get("valid") and tls["age_days"] < 14:
            add(5, f"Sertifikat TLS baru diterbitkan ({tls['age_days']} hari lalu)")

    uid = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    vt = vt_lookup("urls", uid)
    if vt is not None:
        stats = vt.get("last_analysis_stats")
        result["info"]["virustotal"] = stats or vt
        if stats:
            mal = stats.get("malicious", 0)
            if mal >= 3:
                add(40, f"VirusTotal: {mal} engine menandai berbahaya")
            elif mal >= 1:
                add(20, f"VirusTotal: {mal} engine menandai berbahaya")

    result["verdict"] = verdict_for(result["score"])
    return result


# ------------------------------------------------------------- analisis IP

def cymru_asn(ip):
    """Team Cymru IP-to-ASN lewat whois (port 43). Pasif, hanya query data publik."""
    try:
        with socket.create_connection(("whois.cymru.com", 43), timeout=TIMEOUT) as s:
            s.sendall(f"begin\nverbose\n{ip}\nend\n".encode())
            buf = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
    except OSError:
        return None
    for line in buf.decode(errors="replace").splitlines():
        if "|" in line and not line.strip().upper().startswith("AS "):
            f = [x.strip() for x in line.split("|")]
            if len(f) >= 7:
                return {"asn": f[0], "prefix": f[2], "country": f[3],
                        "registry": f[4], "allocated": f[5], "as_name": f[6]}
    return None


def rdap_ip(ip):
    data = http_get_json(f"https://rdap.org/ip/{ip}",
                         headers={"Accept": "application/rdap+json"})
    if not data:
        return None
    out = {"name": data.get("name"), "handle": data.get("handle"),
           "country": data.get("country"), "type": data.get("type"),
           "range": f"{data.get('startAddress')} - {data.get('endAddress')}"}
    for ent in data.get("entities", []):
        roles = ent.get("roles", [])
        if "abuse" in roles:
            out["abuse_contact"] = vcard_field(ent, "email")
        if "registrant" in roles:
            out["registrant"] = vcard_field(ent, "fn")
    return out


def analyze_ip(raw):
    result, add = new_result("ip", raw)
    try:
        ip = ipaddress.ip_address(raw.strip())
    except ValueError:
        result["error"] = "Alamat IP tidak valid"
        return result

    result["info"]["version"] = ip.version
    if not ip.is_global:
        result["info"]["scope"] = ("privat/reserved/loopback/link-local - "
                                   "bukan IP publik, pencarian eksternal dilewati")
        result["verdict"] = "BUKAN IP PUBLIK"
        return result

    try:
        result["info"]["reverse_dns"] = socket.gethostbyaddr(str(ip))[0]
    except (socket.herror, socket.gaierror, OSError):
        result["info"]["reverse_dns"] = None

    asn = cymru_asn(str(ip))
    if asn:
        result["info"]["asn"] = asn
    rdap = rdap_ip(str(ip))
    if rdap:
        result["info"]["rdap"] = rdap

    blob = " ".join(str(x) for x in [result["info"].get("reverse_dns"),
                                      (asn or {}).get("as_name"),
                                      (rdap or {}).get("name")]).lower()
    cloud = [c for c in CLOUD_HINTS if c in blob]
    if cloud:
        add(0, "Terindikasi hosting/cloud: " + ", ".join(cloud)
            + " (IP bersama; belum tentu berbahaya)")

    key = os.environ.get("ABUSEIPDB_API_KEY")
    if key:
        d = http_get_json("https://api.abuseipdb.com/api/v2/check",
                          headers={"Key": key, "Accept": "application/json"},
                          params={"ipAddress": str(ip), "maxAgeInDays": 90})
        if d:
            d = d.get("data", {})
            result["info"]["abuseipdb"] = {
                "confidence_score": d.get("abuseConfidenceScore"),
                "total_reports": d.get("totalReports"),
                "usage_type": d.get("usageType"),
                "isp": d.get("isp"),
            }
            conf = d.get("abuseConfidenceScore") or 0
            if conf >= 50:
                add(40, f"AbuseIPDB: skor kepercayaan penyalahgunaan {conf}%")
            elif conf >= 25:
                add(20, f"AbuseIPDB: skor kepercayaan penyalahgunaan {conf}%")

    vt = vt_lookup("ip_addresses", str(ip))
    if vt is not None:
        stats = vt.get("last_analysis_stats")
        result["info"]["virustotal"] = stats or vt
        if stats and stats.get("malicious", 0) >= 1:
            add(30, f"VirusTotal: {stats['malicious']} engine menandai IP ini berbahaya")

    s = result["score"]
    result["verdict"] = ("REPUTASI BURUK" if s >= 60 else "PERLU DIPERHATIKAN" if s >= 30
                         else "TIDAK ADA INDIKASI BURUK (dari sumber yang dicek)")
    return result


# ----------------------------------------------------------- recon domain

def doh_query(name, rtype):
    """DNS-over-HTTPS (Cloudflare, cadangan Google). None = gagal, [] = tidak ada record."""
    want = DOH_TYPES[rtype]
    for endpoint in ("https://cloudflare-dns.com/dns-query", "https://dns.google/resolve"):
        data = http_get_json(endpoint, headers={"Accept": "application/dns-json"},
                             params={"name": name, "type": rtype})
        if data is None:
            continue
        out = []
        for a in data.get("Answer", []) or []:
            if a.get("type") != want:
                continue
            d = str(a.get("data", ""))
            if rtype == "TXT":
                d = re.sub(r'"\s+"', "", d).strip('"')
            out.append(d)
        return out
    return None


def crtsh_subdomains(domain):
    """Subdomain pasif dari Certificate Transparency (crt.sh)."""
    try:
        r = requests.get("https://crt.sh/", params={"q": f"%.{domain}", "output": "json"},
                         headers={"User-Agent": UA}, timeout=max(TIMEOUT, 20))
        if r.status_code != 200:
            return None
        names = set()
        for row in r.json():
            for n in str(row.get("name_value", "")).splitlines():
                n = n.strip().lower().lstrip("*.")
                if n.endswith("." + domain):
                    names.add(n)
        return sorted(names)
    except (requests.RequestException, ValueError):
        return None


def eval_spf(txts):
    spf = [t for t in (txts or []) if t.lower().startswith("v=spf1")]
    if not spf:
        return {"present": False}
    rec = spf[0]
    m = re.search(r"([+\-~?])all\b", rec)
    lookups = 0
    for term in rec.split()[1:]:
        t = term.lstrip("+-~?").lower()
        if (t.startswith(("include:", "exists:", "redirect=", "ptr")) or t in ("a", "mx")
                or t.startswith(("a:", "a/", "mx:", "mx/"))):
            lookups += 1
    return {"present": True, "record": rec, "all": m.group(1) if m else None,
            "multiple": len(spf) > 1, "lookups": lookups}


def eval_dmarc(txts):
    rec = [t for t in (txts or []) if t.lower().startswith("v=dmarc1")]
    if not rec:
        return {"present": False}
    tags = {}
    for part in rec[0].split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            tags[k.strip().lower()] = v.strip()
    return {"present": True, "record": rec[0], "policy": tags.get("p", "").lower(),
            "pct": tags.get("pct"), "rua": tags.get("rua")}


def domain_grade(penalty):
    for limit, g in ((8, "A"), (20, "B"), (40, "C"), (70, "D")):
        if penalty <= limit:
            return g
    return "F"


def analyze_domain(raw):
    domain = clean_domain(raw)
    result = {"kind": "domain", "input": raw, "domain": domain, "score": 0, "verdict": "",
              "findings": [], "info": {}}
    if not domain or "." not in domain:
        result["error"] = "Nama domain tidak valid"
        return result
    reg = registered_domain(domain)[0]
    public = is_public_host(domain)

    def add(sev, text):
        pts = PENALTY[sev]
        result["score"] += pts
        result["findings"].append({"severity": sev, "points": pts, "text": text})

    with ThreadPoolExecutor(max_workers=8) as ex:
        f_rdap = ex.submit(rdap_domain, reg)
        f_sub = ex.submit(crtsh_subdomains, domain)
        f_web = ex.submit(follow, f"https://{domain}", 6) if public else None
        f_tls = ex.submit(tls_info, domain) if public else None
        f_dns = {t: ex.submit(doh_query, domain, t) for t in DOH_TYPES}
        f_dmarc = ex.submit(doh_query, f"_dmarc.{domain}", "TXT")
        f_dkim = {s: ex.submit(doh_query, f"{s}._domainkey.{domain}", "TXT")
                  for s in DKIM_SELECTORS}
        rdap = f_rdap.result()
        subs = f_sub.result()
        web = f_web.result() if f_web else None
        tls = f_tls.result() if f_tls else None
        dns = {t: f.result() for t, f in f_dns.items()}
        dmarc_txt = f_dmarc.result()
        dkim_found = [s for s, f in f_dkim.items()
                      if any("p=" in x or "v=dkim1" in x.lower() for x in (f.result() or []))]

    if all(v is None for v in dns.values()):
        result["error"] = "Semua query DNS gagal (periksa koneksi internet / firewall / nama domain)"
        return result
    spf = eval_spf(dns.get("TXT"))
    dmarc = eval_dmarc(dmarc_txt)
    spf["unknown"] = dns.get("TXT") is None
    dmarc["unknown"] = dmarc_txt is None
    has_mx = bool(dns.get("MX"))
    result["info"] = {
        "registered_domain": reg, "resolves_public": public, "rdap": rdap, "dns": dns,
        "email_security": {"has_mx": has_mx, "spf": spf, "dmarc": dmarc, "dkim_selectors": dkim_found},
        "web": web, "tls": tls, "subdomains": subs,
    }

    # --- temuan ---
    if not public:
        add("info", "Domain tidak resolve ke IP publik; pemeriksaan web & TLS dilewati")
    mail_sev = "tinggi" if has_mx else "rendah"
    suffix = "" if has_mx else " (domain tidak punya MX)"
    if spf["unknown"]:
        add("info", "Query TXT gagal; pemeriksaan SPF dilewati")
    elif not spf["present"]:
        add(mail_sev, "SPF tidak ditemukan: domain mudah dipalsukan untuk email" + suffix)
    else:
        q = spf["all"]
        if q == "+":
            add("tinggi", "SPF memakai '+all': mengizinkan siapa saja mengirim atas nama domain")
        elif q == "?":
            add("sedang", "SPF berakhir '?all' (netral): tidak ada penegakan")
        elif q == "~":
            add("rendah", "SPF '~all' (softfail): pertimbangkan '-all' bila semua pengirim sudah terdaftar")
        elif q is None:
            add("sedang", "SPF tidak punya mekanisme 'all' di akhir")
        if spf["multiple"]:
            add("sedang", "Lebih dari satu record SPF (menyebabkan permerror)")
        if spf["lookups"] > 10:
            add("sedang", f"SPF memakai ~{spf['lookups']} DNS lookup (batas 10)")
    if dmarc["unknown"]:
        add("info", "Query DMARC gagal; pemeriksaan DMARC dilewati")
    elif not dmarc["present"]:
        add(mail_sev, "DMARC tidak ditemukan" + suffix)
    elif dmarc["policy"] == "none":
        add("sedang", "Kebijakan DMARC 'p=none': hanya memantau, belum menolak email palsu")
    elif dmarc["policy"] == "quarantine":
        add("rendah", "Kebijakan DMARC 'p=quarantine': pertimbangkan 'p=reject'")
    if has_mx and not dkim_found:
        add("info", "Selector DKIM umum tidak ditemukan (belum tentu tidak ada; selector bisa kustom)")
    if dns.get("CAA") == []:
        add("rendah", "Tidak ada record CAA (pembatasan penerbit sertifikat)")

    if rdap:
        d = rdap.get("days_to_expiry")
        if d is not None and d < 0:
            add("tinggi", "Domain sudah kedaluwarsa")
        elif d is not None and d < 30:
            add("sedang", f"Domain kedaluwarsa dalam {d} hari")
    elif public:
        add("info", "Data RDAP tidak tersedia untuk TLD ini")

    if public:
        if tls:
            if tls.get("valid") is False:
                add("tinggi", f"Sertifikat TLS tidak valid: {tls.get('error')}")
            elif tls.get("valid"):
                dl = tls.get("days_left", 999)
                if dl < 0:
                    add("tinggi", "Sertifikat TLS sudah kedaluwarsa")
                elif dl < 14:
                    add("tinggi", f"Sertifikat TLS kedaluwarsa dalam {dl} hari")
                elif dl < 30:
                    add("sedang", f"Sertifikat TLS kedaluwarsa dalam {dl} hari")
            else:
                add("info", f"Tidak bisa memeriksa TLS: {tls.get('error')}")
        hdrs = (web or {}).get("headers")
        if not hdrs:
            add("info", "Situs tidak dapat diambil lewat HTTPS")
        else:
            last = web["chain"][-1]["url"] if web["chain"] else ""
            if last.startswith("http://"):
                add("tinggi", "Situs berakhir di HTTP tanpa enkripsi")
            for key, label, sev in SEC_HEADERS:
                if key not in hdrs:
                    add(sev, f"Header keamanan {label} tidak ada")
            srv = hdrs.get("server", "")
            if re.search(r"\d+\.\d+", srv):
                add("rendah", f"Header Server membocorkan versi: {srv}")
            if "x-powered-by" in hdrs:
                add("rendah", f"Header X-Powered-By membocorkan teknologi: {hdrs['x-powered-by']}")

    result["findings"].sort(key=lambda f: SEV_ORDER[f["severity"]])
    result["grade"] = domain_grade(result["score"])
    result["verdict"] = f"Postur keamanan: Grade {result['grade']}"
    return result


# ----------------------------------------------------------- header email

def parse_received(h):
    h = " ".join(h.split())
    by = re.search(r"\bby\s+(\S+)", h, re.I)
    frm = re.search(r"\bfrom\s+(\S+)", h, re.I)
    ips = []
    for m in re.finditer(r"(?<![\w.])((?:\d{1,3}\.){3}\d{1,3})(?![\w.])", h):
        try:
            ipaddress.ip_address(m.group(1))
            ips.append(m.group(1))
        except ValueError:
            pass
    for m in re.finditer(r"\[(?:IPv6:)?([0-9a-fA-F:]{3,})\]", h):
        try:
            ipaddress.ip_address(m.group(1))
            ips.append(m.group(1))
        except ValueError:
            pass
    date = h.rsplit(";", 1)[1].strip() if ";" in h else ""
    return {"from": frm.group(1) if frm else "", "by": by.group(1).rstrip(";,") if by else "",
            "ips": ips, "date": date}


def addr_domain(value):
    _, addr = parseaddr(value or "")
    return addr.split("@")[-1].lower().strip(">") if "@" in addr else ""


def analyze_email(raw_headers, label="header email"):
    result, add = new_result("email", label)
    msg = Parser().parsestr(raw_headers, headersonly=True)
    if not msg.keys():
        result["error"] = "Tidak ada header email yang terbaca"
        return result

    def h(name):
        v = msg.get(name)
        return " ".join(str(v).split()) if v is not None else ""

    from_h, reply_h, ret_h = h("From"), h("Reply-To"), h("Return-Path")
    name, addr = parseaddr(from_h)
    from_dom, reply_dom, ret_dom = addr_domain(from_h), addr_domain(reply_h), addr_domain(ret_h)
    msgid_dom = addr_domain(h("Message-ID"))

    hops_raw = list(reversed(msg.get_all("Received", []) or []))
    hops = [parse_received(x) for x in hops_raw]
    origin_ip = None
    for hop in hops:
        for ip in hop["ips"]:
            try:
                if ipaddress.ip_address(ip).is_global:
                    origin_ip = ip
                    break
            except ValueError:
                pass
        if origin_ip:
            break

    auth = " ".join(" ".join(str(v).split()) for v in msg.get_all("Authentication-Results", []) or []).lower()

    def auth_res(mech):
        m = re.search(rf"\b{mech}=(\w+)", auth)
        return m.group(1) if m else None

    spf, dkim, dmarc = auth_res("spf"), auth_res("dkim"), auth_res("dmarc")
    if not spf and msg.get("Received-SPF"):
        spf = str(msg.get("Received-SPF")).split()[0].lower()

    result["info"] = {
        "from": from_h, "reply_to": reply_h, "return_path": ret_h, "subject": h("Subject"),
        "date": h("Date"), "message_id": h("Message-ID"), "hops": hops, "origin_ip": origin_ip,
        "auth": {"spf": spf, "dkim": dkim, "dmarc": dmarc},
    }

    # --- pemeriksaan ---
    if spf in ("fail",):
        add(20, "SPF gagal: server pengirim tidak diizinkan oleh domain pengirim")
    elif spf == "softfail":
        add(10, "SPF softfail: server pengirim mencurigakan")
    elif spf is None or spf in ("none", "neutral", "permerror", "temperror"):
        add(8, "Hasil SPF tidak tersedia / tidak meyakinkan")
    if dkim == "fail":
        add(20, "Tanda tangan DKIM tidak valid (isi/pengirim mungkin dimanipulasi)")
    elif dkim is None or dkim in ("none", "neutral", "permerror", "temperror"):
        add(8, "Hasil DKIM tidak tersedia / tidak meyakinkan")
    if dmarc == "fail":
        add(25, "DMARC gagal: email tidak selaras dengan domain pengirim (indikasi spoofing)")
    elif dmarc is None:
        add(8, "Hasil DMARC tidak tersedia")
    if not auth and not msg.get("Received-SPF"):
        add(5, "Tidak ada header autentikasi; pastikan header diambil dari kotak masuk penerima")

    if from_dom and ret_dom and registered_domain(from_dom)[0] != registered_domain(ret_dom)[0]:
        add(8, f"Return-Path ({ret_dom}) berbeda domain dengan From ({from_dom})")
    if from_dom and reply_dom and registered_domain(from_dom)[0] != registered_domain(reply_dom)[0]:
        add(15, f"Reply-To ({reply_dom}) berbeda domain dengan From ({from_dom}): balasan dialihkan")
    if from_dom and msgid_dom and registered_domain(from_dom)[0] != registered_domain(msgid_dom)[0]:
        add(5, f"Domain Message-ID ({msgid_dom}) berbeda dengan From")

    m = re.search(r"[\w.+-]+@([\w-]+(?:\.[\w-]+)+)", name or "")
    if m and from_dom and registered_domain(m.group(1).lower())[0] != registered_domain(from_dom)[0]:
        add(25, f"Nama tampilan memuat alamat '{m.group(0)}' yang berbeda dari alamat asli {addr}")
    if from_dom:
        fb = brand_lookalike(from_dom)
        if fb:
            add(30, "Domain pengirim meniru brand: " + fb)
        reg = registered_domain(from_dom)[0]
        for brand, official in BRANDS.items():
            if re.search(rf"\b{brand}\b", (name or "").lower()) and reg not in official:
                add(20, f"Nama pengirim mengaku '{brand}' tetapi domain {reg} bukan domain resminya")
                break
    subj = h("Subject").lower()
    urg = [w for w in URGENT_WORDS if w in subj]
    if urg:
        add(8, "Subjek bernada mendesak: " + ", ".join(urg[:4]))
    if not h("Date"):
        add(5, "Header Date tidak ada")

    result["verdict"] = verdict_for(result["score"])
    return result


# ------------------------------------------------------- verifikasi hoaks

def factcheck_search(query, lang="id"):
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("FACTCHECK_API_KEY")
    if not key:
        return [], "no_key"
    params = {"query": query[:250], "pageSize": 10, "key": key}
    if lang:
        params["languageCode"] = lang
    data = http_get_json("https://factchecktools.googleapis.com/v1alpha1/claims:search", params=params)
    if data is None:
        return [], "error"
    claims = data.get("claims", [])
    if not claims and lang:
        params.pop("languageCode")
        data = http_get_json("https://factchecktools.googleapis.com/v1alpha1/claims:search", params=params)
        claims = (data or {}).get("claims", [])
    out = []
    for c in claims:
        out.append({
            "text": c.get("text", ""), "claimant": c.get("claimant", ""),
            "date": c.get("claimDate", ""),
            "reviews": [{"publisher": (r.get("publisher") or {}).get("name", ""),
                         "title": r.get("title", ""), "url": r.get("url", ""),
                         "rating": r.get("textualRating", ""), "date": r.get("reviewDate", "")}
                        for r in c.get("claimReview", [])],
        })
    return out, "ok"


def analyze_claim(text, lang="id"):
    text = " ".join(text.split())
    result, add = new_result("hoax", text)
    if not text:
        result["error"] = "Klaim kosong"
        return result
    for pat, pts, msg in HOAX_PATTERNS:
        if re.search(pat, text, re.I):
            add(pts, msg)
    letters = [c for c in text if c.isalpha()]
    if len(letters) >= 30 and sum(c.isupper() for c in letters) / len(letters) > 0.4:
        add(8, "Banyak huruf kapital (gaya sensasional)")
    if re.search(r"[!?]{3,}", text):
        add(5, "Tanda seru/tanya berlebihan")
    if not re.search(r"https?://|www\.", text):
        add(5, "Tidak mencantumkan tautan/sumber primer")

    claims, status = factcheck_search(text, lang)
    result["info"]["factcheck_status"] = status
    result["info"]["claims"] = claims
    result["info"]["manual_links"] = FACT_CHECK_SITES
    bad = re.compile(r"hoa[xk]s?|salah|false|palsu|menyesatkan|misleading|tidak benar|fabricated|disinformasi", re.I)
    flagged = False
    for c in claims:
        for rv in c["reviews"]:
            if bad.search(rv["rating"] or "") and not flagged:
                add(40, f"Pemeriksa fakta ({rv['publisher']}) menandai klaim serupa: {rv['rating']}")
                flagged = True
    s = result["score"]
    result["verdict"] = ("BANYAK CIRI HOAKS" if s >= 50 else "ADA CIRI HOAKS" if s >= 25
                         else "CIRI HOAKS SEDIKIT (bukan bukti klaim itu benar)")
    return result


# ------------------------------------------------------------ analisis gambar

def _exif_val(v):
    if isinstance(v, bytes):
        return v.decode("utf-8", "ignore").strip("\x00 ")
    if isinstance(v, (int, float, str)):
        return v
    try:
        return float(v)
    except (TypeError, ValueError):
        return str(v)


def _dms(vals, ref):
    try:
        d, m, s = [float(x) for x in vals]
        dec = d + m / 60 + s / 3600
        return -dec if ref in ("S", "W") else dec
    except (TypeError, ValueError):
        return None


def analyze_image(path):
    result, add = new_result("image", path)
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        result["error"] = "File tidak ditemukan"
        return result
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
            md5.update(chunk)
    info = result["info"]
    info.update({"size_bytes": os.path.getsize(path), "sha256": sha.hexdigest(), "md5": md5.hexdigest(),
                 "exif": {}, "gps": None, "search_links": IMAGE_SEARCH_SITES})
    if not PIL_OK:
        add(0, "Pillow belum terpasang (pip install pillow); hanya hash yang dihitung")
        result["verdict"] = "METADATA TIDAK DIBACA"
        return result
    try:
        img = Image.open(path)
    except Exception as e:  # file bukan gambar / rusak
        result["error"] = f"Tidak bisa membuka gambar: {type(e).__name__}"
        return result
    info.update({"format": img.format, "dimensions": f"{img.width} x {img.height}", "mode": img.mode})

    exif = img.getexif()
    tags = {ExifTags.TAGS.get(k, str(k)): _exif_val(v) for k, v in exif.items()}
    try:
        for k, v in exif.get_ifd(0x8769).items():
            tags[ExifTags.TAGS.get(k, str(k))] = _exif_val(v)
    except Exception:
        pass
    keep = ["Make", "Model", "Software", "DateTime", "DateTimeOriginal", "DateTimeDigitized",
            "LensModel", "Orientation"]
    info["exif"] = {k: tags[k] for k in keep if k in tags}
    try:
        gps = exif.get_ifd(0x8825)
        if gps and 2 in gps and 4 in gps:
            lat, lon = _dms(gps[2], gps.get(1)), _dms(gps[4], gps.get(3))
            if lat is not None and lon is not None:
                info["gps"] = {"lat": round(lat, 6), "lon": round(lon, 6)}
    except Exception:
        pass

    meta_text = " ".join(str(v) for v in list(info["exif"].values()) + list(img.info.keys())
                         + [img.info.get("Software", ""), img.info.get("parameters", "")]).lower()
    if not tags:
        add(0, "Tidak ada metadata EXIF: umum pada gambar dari media sosial/WhatsApp "
               "(metadata dihapus) atau gambar sudah diproses ulang")
    if any(t in meta_text for t in AI_TOOLS) or "parameters" in img.info or "prompt" in img.info:
        add(30, "Metadata menyebut alat pembuat gambar AI / parameter generasi gambar")
    ed = [t for t in EDIT_TOOLS if t in meta_text]
    if ed:
        add(10, f"Metadata menyebut perangkat lunak edit: {', '.join(ed)} (tidak otomatis berarti manipulasi)")
    dt, dto = info["exif"].get("DateTime"), info["exif"].get("DateTimeOriginal")
    if dt and dto and dt != dto:
        add(8, f"Waktu modifikasi ({dt}) berbeda dari waktu pengambilan ({dto})")
    if info["gps"]:
        add(0, f"Metadata memuat koordinat GPS ({info['gps']['lat']}, {info['gps']['lon']}). "
               "Bisa membantu verifikasi lokasi, tetapi dapat dipalsukan atau tidak mutakhir")
    if tags and not info["exif"].get("Make") and not info["exif"].get("Model"):
        add(0, "Ada EXIF tetapi tanpa merek/model kamera")
    s = result["score"]
    result["verdict"] = ("ADA INDIKASI GAMBAR DIOLAH/AI" if s >= 30 else "PERLU DICEK LEBIH LANJUT" if s >= 8
                         else "TIDAK ADA INDIKASI DARI METADATA (bukan bukti keaslian)")
    return result


# ------------------------------------------------------------ batch & laporan

def classify_target(line):
    line = line.strip()
    low = line.lower()
    for pfx, kind in (("domain:", "domain"), ("url:", "url"), ("ip:", "ip"), ("image:", "image")):
        if low.startswith(pfx):
            return kind, line[len(pfx):].strip()
    try:
        ipaddress.ip_address(line)
        return "ip", line
    except ValueError:
        return "url", line


def run_one(kind, target, fetch=True):
    if kind == "url":
        return analyze_url(target, fetch=fetch)
    if kind == "ip":
        return analyze_ip(target)
    if kind == "domain":
        return analyze_domain(target)
    if kind == "image":
        return analyze_image(target)
    raise ValueError(kind)


def run_batch(path, fetch=True, workers=4, progress=True):
    with open(path, encoding="utf-8", errors="replace") as f:
        items = [classify_target(ln) for ln in f if ln.strip() and not ln.strip().startswith("#")]
    results = [None] * len(items)
    ctx = (Progress(SpinnerColumn(style="red"), TextColumn("[bold]Batch"), BarColumn(bar_width=None, complete_style="red"),
                    TextColumn("{task.completed}/{task.total}"), console=console)
           if progress else contextlib.nullcontext())
    with ctx as prog:
        task = prog.add_task("batch", total=len(items)) if progress else None
        with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            futs = {ex.submit(run_one, k, t, fetch): i for i, (k, t) in enumerate(items)}
            for fut in as_completed(futs):
                i = futs[fut]
                try:
                    results[i] = fut.result()
                except Exception as e:  # satu target gagal tidak menghentikan batch
                    results[i] = {"kind": items[i][0], "input": items[i][1], "score": 0,
                                  "verdict": "GAGAL", "findings": [], "info": {},
                                  "error": f"{type(e).__name__}: {e}"}
                if progress:
                    prog.advance(task)
    return results


KIND_LABEL = {"url": "URL", "ip": "IP", "domain": "Domain", "email": "Email",
              "hoax": "Klaim", "image": "Gambar"}


def finding_texts(r):
    out = []
    for f in r.get("findings", []):
        sev = f.get("severity")
        out.append(f"[{sev}] {f['text']}" if sev else f["text"])
    if r.get("error"):
        out.insert(0, f"ERROR: {r['error']}")
    return out


HTML_TEMPLATE = """<!doctype html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Laporan BroCode</title>
<style>
:root{--bg:#0d0e11;--card:#16181d;--line:#262a31;--fg:#f4f1ec;--dim:#a9a7a2;--red:#e5252a;--amber:#e8a317;--green:#2fb36d}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 64px}
header{display:flex;align-items:center;gap:20px;margin-bottom:28px}
header svg{flex:none}
h1{margin:0;font-size:36px;letter-spacing:-1px}
h1 span{color:var(--red)}
.sub{color:var(--dim);font-size:14px}
.stats{display:flex;gap:12px;flex-wrap:wrap;margin:0 0 24px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 18px;min-width:130px}
.stat b{display:block;font-size:26px}
.hi{color:var(--red)}.mid{color:var(--amber)}.lo{color:var(--green)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:10px 14px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:13px;text-transform:uppercase;letter-spacing:.5px}
td.t{word-break:break-all}
.bar{height:8px;background:var(--line);border-radius:4px;width:120px;overflow:hidden}
.bar i{display:block;height:100%}
.bg-hi{background:var(--red)}.bg-mid{background:var(--amber)}.bg-lo{background:var(--green)}
details summary{cursor:pointer;color:var(--dim)}
ul{margin:8px 0 0 18px;padding:0}
footer{margin-top:32px;color:var(--dim);font-size:13px}
</style></head><body><div class="wrap">
<header>
<svg width="84" height="70" viewBox="0 0 240 200" role="img" aria-label="Logo BroCode">
<rect x="34" y="14" width="52" height="46" rx="12" fill="#9E1218"/><rect x="154" y="14" width="52" height="46" rx="12" fill="#9E1218"/>
<rect x="96" y="82" width="48" height="34" rx="8" fill="#9E1218"/>
<rect x="18" y="50" width="84" height="136" rx="30" fill="#E5252A"/><rect x="138" y="50" width="84" height="136" rx="30" fill="#E5252A"/>
<circle cx="60" cy="138" r="30" fill="#0D0E11" stroke="#9E1218" stroke-width="5"/><circle cx="180" cy="138" r="30" fill="#0D0E11" stroke="#9E1218" stroke-width="5"/>
</svg>
<div><h1>Bro<span>Code</span></h1><div class="sub">Laporan OSINT &middot; @@DATE@@ &middot; Dibuat oleh Nathan</div></div>
</header>
<div class="stats">@@STATS@@</div>
<table><thead><tr><th>Jenis</th><th>Target</th><th>Skor</th><th>Verdict</th><th>Temuan</th></tr></thead>
<tbody>@@ROWS@@</tbody></table>
<footer>Skor adalah indikator berbasis heuristik dan sumber data publik, bukan bukti. Verifikasi manual sebelum bertindak.</footer>
</div></body></html>
"""


def build_html(results):
    esc = html.escape
    counts = {"hi": 0, "mid": 0, "lo": 0}
    rows = []
    for r in results:
        score = int(r.get("score", 0) or 0)
        cls = "hi" if score >= 60 else "mid" if score >= 30 else "lo"
        counts[cls] += 1
        items = finding_texts(r)
        details = ("<details><summary>%d temuan</summary><ul>%s</ul></details>"
                   % (len(items), "".join(f"<li>{esc(x)}</li>" for x in items))) if items else "-"
        rows.append(
            "<tr><td>%s</td><td class='t'>%s</td>"
            "<td><div class='bar'><i class='bg-%s' style='width:%d%%'></i></div>%d</td>"
            "<td class='%s'><b>%s</b></td><td>%s</td></tr>"
            % (esc(KIND_LABEL.get(r.get("kind"), "?")), esc(str(r.get("input", ""))), cls,
               min(score, 100), score, cls, esc(r.get("verdict", "")), details))
    stats = ("<div class='stat'><b>%d</b>Total target</div>"
             "<div class='stat'><b class='hi'>%d</b>Risiko tinggi</div>"
             "<div class='stat'><b class='mid'>%d</b>Mencurigakan</div>"
             "<div class='stat'><b class='lo'>%d</b>Risiko rendah</div>"
             % (len(results), counts["hi"], counts["mid"], counts["lo"]))
    return (HTML_TEMPLATE.replace("@@DATE@@", now_utc().strftime("%Y-%m-%d %H:%M UTC"))
            .replace("@@STATS@@", stats).replace("@@ROWS@@", "".join(rows)))


def export_report(results, path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    elif ext == ".csv":
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["jenis", "target", "skor", "verdict", "temuan"])
            for r in results:
                w.writerow([KIND_LABEL.get(r.get("kind"), "?"), r.get("input", ""), r.get("score", 0),
                            r.get("verdict", ""), " | ".join(finding_texts(r))])
    elif ext in (".html", ".htm"):
        with open(path, "w", encoding="utf-8") as f:
            f.write(build_html(results))
    else:
        raise ValueError("Ekstensi laporan harus .html, .csv, atau .json")
    return path


# ------------------------------------------------------------ tampilan (rich)

def score_bar(score, width=24):
    color = score_color(score)
    filled = min(width, round(min(score, 100) / 100 * width))
    t = Text()
    t.append("█" * filled, style=color)
    t.append("░" * (width - filled), style="grey37")
    t.append(f" {score}", style=f"bold {color}")
    return t


def banner_renderable():
    art = T("\n".join(BANNER_ART), "bold red")
    info = Group(
        T("\n".join(BANNER_WORD), "bold red"),
        T("OSINT Toolkit - URL, IP, domain, email & hoaks", "dim"),
        Text.assemble("Dibuat oleh ", ("Nathan", "bold white")),
    )
    grid = Table.grid(padding=(0, 3))
    grid.add_row(art, info)
    return Panel(grid, border_style="red", box=box.ROUNDED, padding=(1, 2),
                 subtitle=f"[dim]v{VERSION} - pasif & legal[/dim]")


def kv_table(rows, title=None):
    t = Table(box=box.SIMPLE_HEAD, show_header=False, title=title, title_style="bold",
              title_justify="left", expand=False, pad_edge=False)
    t.add_column(style="dim", no_wrap=True)
    t.add_column(overflow="fold")
    for k, v in rows:
        t.add_row(T(k), v if isinstance(v, (Text, Table, Tree, Group)) else T(v))
    return t


def findings_table(findings, with_sev=False):
    t = Table(box=box.SIMPLE_HEAD, expand=True, pad_edge=False)
    t.add_column("Tingkat" if with_sev else "Poin", no_wrap=True)
    t.add_column("Temuan", overflow="fold")
    for f in findings:
        if with_sev:
            t.add_row(T(f["severity"].upper(), SEV_STYLE[f["severity"]]), T(f["text"]))
        else:
            t.add_row(T(f"+{f['points']}", "bold" if f["points"] else "dim"), T(f["text"]))
    if not findings:
        t.add_row(T("-", "dim"), T("Tidak ada indikator mencurigakan terdeteksi", "dim"))
    return t


def head_grid(rows):
    g = Table.grid(padding=(0, 2))
    for k, v in rows:
        g.add_row(T(k, "dim"), v if isinstance(v, Text) else T(v, "bold"))
    return g


def render_url(r):
    color = score_color(r["score"])
    info = r["info"]
    parts = [head_grid([("Target", r["input"]), ("Domain", info["registered_domain"]),
                        ("Skor risiko", score_bar(r["score"])),
                        ("Verdict", T(r["verdict"], f"bold {color}"))]),
             findings_table(r["findings"])]
    rows = [("Usia domain", info.get("domain_age_days"))]
    tls = info.get("tls")
    if tls:
        rows.append(("TLS", f"{tls['issuer']} ({tls['not_before']} s/d {tls['not_after']})"
                     if tls.get("valid") else f"bermasalah - {tls.get('error')}"))
    if "virustotal" in info:
        rows.append(("VirusTotal", str(info["virustotal"])))
    parts.append(kv_table(rows))
    if info.get("redirect_chain"):
        tree = Tree(T("Redirect chain", "bold"))
        for h in info["redirect_chain"]:
            tree.add(T(f"[{h['status']}] {h['url']}"))
        parts.append(tree)
    return Panel(Group(*parts), title="Analisis URL", border_style=color, box=box.ROUNDED, padding=(1, 2))


def render_ip(r):
    color = score_color(r["score"])
    parts = [head_grid([("IP", r["input"]), ("Verdict", T(r["verdict"], f"bold {color}"))])]
    if r["score"] or r["findings"]:
        parts[0].add_row(T("Skor risiko", "dim"), score_bar(r["score"]))
    rows = []
    for k, v in r["info"].items():
        if isinstance(v, dict):
            rows.append((k.upper(), T("")))
            rows.extend((f"  {kk}", str(vv)) for kk, vv in v.items())
        else:
            rows.append((k, str(v)))
    parts.append(kv_table(rows))
    if r["findings"]:
        parts.append(findings_table(r["findings"]))
    return Panel(Group(*parts), title="Analisis IP & Jaringan", border_style=color,
                 box=box.ROUNDED, padding=(1, 2))


def render_domain(r):
    info, grade = r["info"], r["grade"]
    gcolor = {"A": "green", "B": "green", "C": "yellow", "D": "red", "F": "red"}[grade]
    blocks = [head_grid([("Domain", r["domain"]), ("Grade", T(f" {grade} ", f"bold white on {gcolor}")),
                         ("Poin masalah", str(r["score"]))])]
    rd = info.get("rdap")
    if rd:
        blocks.append(kv_table([
            ("Registrar", rd.get("registrar") or "-"), ("Dibuat", rd.get("created") or "-"),
            ("Usia", f"{rd['age_days']} hari" if rd.get("age_days") is not None else "-"),
            ("Kedaluwarsa", f"{rd.get('expires') or '-'} ({rd['days_to_expiry']} hari lagi)"
             if rd.get("days_to_expiry") is not None else "-"),
            ("Nameserver", ", ".join(rd.get("nameservers", [])) or "-"),
            ("Status", ", ".join(rd.get("status", [])) or "-")], title="Registrasi (RDAP)"))
    dns_rows = []
    for t in DOH_TYPES:
        v = info["dns"].get(t)
        dns_rows.append((t, "(query gagal)" if v is None else "\n".join(v) if v else "-"))
    blocks.append(kv_table(dns_rows, title="Record DNS"))

    es = info["email_security"]
    spf, dm = es["spf"], es["dmarc"]
    ok, bad, warn = "green", "red", "yellow"

    def stat(text, color):
        return T(text, color)

    spf_t = stat("query gagal", "dim") if spf.get("unknown") else stat("tidak ada", bad) if not spf["present"] else stat(
        f"ada ({spf['all'] or '?'}all) - {spf['lookups']} lookup", ok if spf["all"] == "-" else warn)
    dm_t = stat("query gagal", "dim") if dm.get("unknown") else stat("tidak ada", bad) if not dm["present"] else stat(
        f"p={dm['policy'] or '?'}", ok if dm["policy"] == "reject" else warn)
    dk_t = stat(", ".join(es["dkim_selectors"]), ok) if es["dkim_selectors"] else stat("tidak terdeteksi (selector umum)", "dim")
    blocks.append(kv_table([("MX", "ada" if es["has_mx"] else "tidak ada"), ("SPF", spf_t),
                            ("DMARC", dm_t), ("DKIM", dk_t)], title="Keamanan Email"))

    web = info.get("web") or {}
    hdrs = web.get("headers")
    if hdrs:
        ht = Table(box=box.SIMPLE_HEAD, pad_edge=False, title="Header Keamanan Web", title_justify="left",
                   title_style="bold")
        ht.add_column("Header")
        ht.add_column("Status", no_wrap=True)
        ht.add_column("Nilai", overflow="ellipsis", max_width=48)
        for key, label, sev in SEC_HEADERS:
            present = key in hdrs
            ht.add_row(T(label), T("✔ ada", "green") if present else T("✘ tidak ada", SEV_STYLE[sev]),
                       T(hdrs.get(key, "")[:48], "dim"))
        blocks.append(ht)
    tls = info.get("tls")
    if tls:
        blocks.append(kv_table([("TLS", f"{tls['issuer']} - berlaku s/d {tls['not_after']} ({tls['days_left']} hari)"
                                 if tls.get("valid") else f"bermasalah - {tls.get('error')}")]))
    subs = info.get("subdomains")
    if subs:
        shown = subs[:45]
        blocks.append(Panel(Columns([T(s) for s in shown], equal=False, expand=False),
                            title=f"Subdomain dari Certificate Transparency ({len(subs)})",
                            title_align="left", box=box.SIMPLE))
    elif subs == []:
        blocks.append(T("Subdomain (crt.sh): tidak ditemukan", "dim"))
    else:
        blocks.append(T("Subdomain (crt.sh): layanan tidak merespons", "dim"))
    blocks.append(findings_table(r["findings"], with_sev=True))
    return Panel(Group(*blocks), title="Recon Domain", border_style=gcolor, box=box.ROUNDED, padding=(1, 2))


def render_email(r):
    color = score_color(r["score"])
    info = r["info"]
    head = head_grid([("Dari", info["from"]), ("Reply-To", info["reply_to"] or "-"),
                      ("Return-Path", info["return_path"] or "-"), ("Subjek", info["subject"] or "-"),
                      ("Tanggal", info["date"] or "-"), ("Skor risiko", score_bar(r["score"])),
                      ("Verdict", T(r["verdict"], f"bold {color}"))])

    def auth_cell(v):
        if v is None:
            return T("tidak ada", "dim")
        return T(v, "green" if v == "pass" else "red" if v in ("fail", "softfail") else "yellow")

    au = info["auth"]
    auth = Table.grid(padding=(0, 3))
    auth.add_row(T("SPF", "dim"), auth_cell(au["spf"]), T("DKIM", "dim"), auth_cell(au["dkim"]),
                 T("DMARC", "dim"), auth_cell(au["dmarc"]))
    hops = Table(box=box.SIMPLE_HEAD, title="Jalur pengiriman (dari asal ke penerima)",
                 title_justify="left", title_style="bold", pad_edge=False)
    for c in ("#", "From", "By", "IP", "Waktu"):
        hops.add_column(c, overflow="fold")
    for i, h in enumerate(info["hops"], 1):
        hops.add_row(str(i), T(h["from"]), T(h["by"]), T(", ".join(h["ips"]) or "-"), T(h["date"], "dim"))
    parts = [head, Text(""), auth, hops, findings_table(r["findings"])]
    if info["origin_ip"]:
        parts.append(T(f"IP asal (publik pertama di jalur): {info['origin_ip']} - "
                       f"cek dengan: brocode ip {info['origin_ip']}", "cyan"))
    return Panel(Group(*parts), title="Analisis Header Email", border_style=color,
                 box=box.ROUNDED, padding=(1, 2))


def render_hoax(r):
    color = score_color(r["score"])
    info = r["info"]
    parts = [head_grid([("Klaim", r["input"][:300]), ("Skor ciri hoaks", score_bar(r["score"])),
                        ("Verdict", T(r["verdict"], f"bold {color}"))]),
             findings_table(r["findings"])]
    st = info.get("factcheck_status")
    if st == "no_key":
        parts.append(T("Google Fact Check API belum aktif: set GOOGLE_API_KEY (gratis di Google Cloud) "
                       "untuk pencarian otomatis.", "yellow"))
    elif st == "error":
        parts.append(T("Pencarian Fact Check gagal (cek API key / koneksi).", "yellow"))
    elif not info["claims"]:
        parts.append(T("Tidak ditemukan pemeriksaan fakta untuk klaim ini di Fact Check Tools. "
                       "Bukan berarti klaim benar - coba cari manual.", "dim"))
    else:
        ct = Table(box=box.SIMPLE_HEAD, title="Hasil pemeriksa fakta", title_justify="left",
                   title_style="bold", pad_edge=False)
        for c in ("Pemeriksa", "Peringkat", "Judul / tautan"):
            ct.add_column(c, overflow="fold")
        for c in info["claims"][:8]:
            for rv in c["reviews"][:2]:
                ct.add_row(T(rv["publisher"]), T(rv["rating"], "bold"), T(f"{rv['title']}\n{rv['url']}", "dim"))
        parts.append(ct)
    links = Table.grid(padding=(0, 2))
    for name, url in info["manual_links"]:
        links.add_row(T(name, "dim"), T(url, "cyan"))
    parts.append(T("Cek manual:", "bold"))
    parts.append(links)
    return Panel(Group(*parts), title="Verifikasi Klaim / Hoaks", border_style=color,
                 box=box.ROUNDED, padding=(1, 2))


def render_image(r):
    color = score_color(r["score"])
    info = r["info"]
    rows = [("File", r["input"]), ("Ukuran", f"{info['size_bytes']:,} bytes"), ("SHA-256", info["sha256"]),
            ("MD5", info["md5"])]
    if info.get("format"):
        rows += [("Format", f"{info['format']} {info['dimensions']} ({info['mode']})")]
    parts = [head_grid([("Verdict", T(r["verdict"], f"bold {color}")), ("Skor", score_bar(r["score"]))]),
             kv_table(rows)]
    if info["exif"]:
        parts.append(kv_table([(k, str(v)) for k, v in info["exif"].items()], title="Metadata EXIF"))
    parts.append(findings_table(r["findings"]))
    links = Table.grid(padding=(0, 2))
    for name, url in info["search_links"]:
        links.add_row(T(name, "dim"), T(url, "cyan"))
    parts.append(T("Reverse image search (unggah manual untuk melacak sumber asli):", "bold"))
    parts.append(links)
    return Panel(Group(*parts), title="Analisis Gambar", border_style=color, box=box.ROUNDED, padding=(1, 2))


RENDERERS = {"url": render_url, "ip": render_ip, "domain": render_domain, "email": render_email,
             "hoax": render_hoax, "image": render_image}


def render_result(r):
    if r.get("error"):
        return Panel(Group(T(r["input"], "bold"), T(r["error"], "red")),
                     title=KIND_LABEL.get(r.get("kind"), "Hasil"), border_style="red", box=box.ROUNDED)
    return RENDERERS[r["kind"]](r)


def render_batch_summary(results):
    t = Table(box=box.ROUNDED, border_style="red", title="Ringkasan Batch", title_style="bold")
    for c in ("#", "Jenis", "Target", "Skor", "Verdict"):
        t.add_column(c, overflow="fold")
    order = sorted(range(len(results)), key=lambda i: -(results[i].get("score") or 0))
    for i in order:
        r = results[i]
        sc = int(r.get("score") or 0)
        t.add_row(str(i + 1), T(KIND_LABEL.get(r.get("kind"), "?")), T(r.get("input", "")),
                  score_bar(sc, 12), T(r.get("verdict") or r.get("error", ""), f"bold {score_color(sc)}"))
    return t


# ------------------------------------------------------------- mode interaktif

def read_multiline(prompt):
    console.print(T(prompt, "dim"))
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def read_text_file(path):
    with open(os.path.expanduser(path), encoding="utf-8", errors="replace") as f:
        return f.read()


def status_ctx(msg, quiet=False):
    return contextlib.nullcontext() if quiet else console.status(f"[bold red]{msg}", spinner="dots")


def offer_export(results):
    if Confirm.ask("Simpan hasil ke laporan?", default=False, console=console):
        path = Prompt.ask("Nama file (.html / .csv / .json)", default="laporan-brocode.html", console=console)
        try:
            console.print(T(f"Laporan disimpan: {export_report(results, path)}", "green"))
        except (ValueError, OSError) as e:
            console.print(T(f"Gagal menyimpan: {e}", "red"))


def show_status():
    t = Table(box=box.SIMPLE_HEAD, title="Status & Pengaturan", title_style="bold")
    t.add_column("Komponen")
    t.add_column("Status")
    t.add_column("Fungsi", style="dim")
    for env, fn in (("VT_API_KEY", "VirusTotal (url, ip)"), ("ABUSEIPDB_API_KEY", "AbuseIPDB (ip)"),
                    ("GOOGLE_API_KEY", "Fact Check Tools (hoax)")):
        on = bool(os.environ.get(env))
        t.add_row(T(env), T("aktif" if on else "belum di-set", "green" if on else "yellow"), T(fn))
    t.add_row(T("Pillow"), T("terpasang" if PIL_OK else "belum terpasang", "green" if PIL_OK else "yellow"),
              T("Metadata EXIF gambar"))
    t.add_row(T("BROCODE_TIMEOUT"), T(f"{TIMEOUT:g} detik"), T("Batas waktu koneksi"))
    console.print(t)
    console.print(T("Set API key lewat environment variable, mis. (Linux/macOS) export VT_API_KEY=xxxx, "
                    "atau (Windows) setx VT_API_KEY xxxx.", "dim"))


MENU = [
    ("1", "Verifikasi URL phishing"),
    ("2", "Analisis IP & jaringan"),
    ("3", "Recon domain pasif (DNS, SPF/DMARC, subdomain, header)"),
    ("4", "Analisis header email (spoofing / phishing)"),
    ("5", "Verifikasi klaim / hoaks"),
    ("6", "Metadata & keaslian gambar"),
    ("7", "Batch dari file + laporan"),
    ("8", "Status & pengaturan API key"),
    ("0", "Keluar"),
]


def menu():
    console.print(banner_renderable())
    while True:
        t = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
        t.add_column(style="bold red", no_wrap=True)
        t.add_column()
        for k, v in MENU:
            t.add_row(k, v)
        console.print(t)
        choice = Prompt.ask("[bold red]Pilih menu[/bold red]", choices=[k for k, _ in MENU],
                            default="1", console=console)
        results = []
        try:
            if choice == "0":
                console.print(T("Sampai jumpa!", "dim"))
                return 0
            if choice == "1":
                for u in Prompt.ask("URL (pisahkan dengan spasi)", console=console).split():
                    with status_ctx(f"Menganalisis {u} ..."):
                        results.append(analyze_url(u))
            elif choice == "2":
                for ip in Prompt.ask("Alamat IP (pisahkan dengan spasi)", console=console).split():
                    with status_ctx(f"Menganalisis {ip} ..."):
                        results.append(analyze_ip(ip))
            elif choice == "3":
                console.print(T("Gunakan hanya untuk domain milik sendiri / yang Anda berwenang periksa.", "dim"))
                for d in Prompt.ask("Domain (pisahkan dengan spasi)", console=console).split():
                    with status_ctx(f"Recon {d} ..."):
                        results.append(analyze_domain(d))
            elif choice == "4":
                path = Prompt.ask("Path file header/.eml (kosongkan untuk menempel)", default="", console=console)
                if path:
                    raw, label = read_text_file(path), path
                else:
                    raw = read_multiline("Tempel header email, lalu ketik END pada baris baru:")
                    label = "header email (ditempel)"
                results.append(analyze_email(raw, label))
            elif choice == "5":
                claim = Prompt.ask("Tempel klaim / pesan yang ingin dicek", console=console)
                with status_ctx("Memeriksa klaim ..."):
                    results.append(analyze_claim(claim))
            elif choice == "6":
                for p in Prompt.ask("Path gambar (pisahkan dengan spasi)", console=console).split():
                    results.append(analyze_image(p))
            elif choice == "7":
                path = Prompt.ask("Path file daftar target (satu per baris)", console=console)
                results = run_batch(path)
            elif choice == "8":
                show_status()
                continue
        except (OSError, KeyboardInterrupt) as e:
            console.print(T(f"Dibatalkan / gagal: {e}", "red"))
            continue
        if choice == "7" and results:
            console.print(render_batch_summary(results))
            if Confirm.ask("Tampilkan detail tiap target?", default=False, console=console):
                for r in results:
                    console.print(render_result(r))
        else:
            for r in results:
                console.print(render_result(r))
        if results:
            offer_export(results)
        console.print()


# -------------------------------------------------------------------- CLI

def build_parser():
    ap = argparse.ArgumentParser(prog="brocode", description="BroCode - toolkit OSINT pasif oleh Nathan")
    ap.add_argument("--no-banner", action="store_true", help="sembunyikan banner")
    ap.add_argument("--version", action="version", version=f"BroCode {VERSION}")
    sub = ap.add_subparsers(dest="cmd")

    def common(p):
        p.add_argument("--json", action="store_true", help="keluaran JSON")
        p.add_argument("-o", "--out", metavar="FILE", help="simpan laporan (.html/.csv/.json)")

    pu = sub.add_parser("url", help="verifikasi URL phishing")
    pu.add_argument("targets", nargs="+")
    pu.add_argument("--no-fetch", action="store_true", help="analisis statis (tanpa mengikuti redirect/TLS)")
    common(pu)
    pi = sub.add_parser("ip", help="analisis IP & jaringan")
    pi.add_argument("targets", nargs="+")
    common(pi)
    pd = sub.add_parser("domain", help="recon pasif domain")
    pd.add_argument("targets", nargs="+")
    common(pd)
    pe = sub.add_parser("email", help="analisis header email")
    pe.add_argument("file", nargs="?", default="-", help="file header/.eml, atau - untuk stdin")
    common(pe)
    ph = sub.add_parser("hoax", help="verifikasi klaim / hoaks")
    ph.add_argument("claim", nargs="+")
    ph.add_argument("--lang", default="id", help="kode bahasa Fact Check (default id)")
    common(ph)
    pm = sub.add_parser("image", help="metadata & keaslian gambar")
    pm.add_argument("files", nargs="+")
    common(pm)
    pb = sub.add_parser("batch", help="analisis banyak target dari file")
    pb.add_argument("file")
    pb.add_argument("--no-fetch", action="store_true")
    pb.add_argument("--workers", type=int, default=4)
    common(pb)
    sub.add_parser("menu", help="mode interaktif")
    return ap


def main():
    ap = build_parser()
    args = ap.parse_args()
    if args.cmd in (None, "menu"):
        return menu()

    quiet = args.json
    if not args.no_banner:
        (Console(stderr=True) if quiet else console).print(banner_renderable())

    results = []
    try:
        if args.cmd == "url":
            for t in args.targets:
                with status_ctx(f"Menganalisis {t} ...", quiet):
                    results.append(analyze_url(t, fetch=not args.no_fetch))
        elif args.cmd == "ip":
            for t in args.targets:
                with status_ctx(f"Menganalisis {t} ...", quiet):
                    results.append(analyze_ip(t))
        elif args.cmd == "domain":
            for t in args.targets:
                with status_ctx(f"Recon {t} ...", quiet):
                    results.append(analyze_domain(t))
        elif args.cmd == "email":
            raw = sys.stdin.read() if args.file == "-" else read_text_file(args.file)
            results.append(analyze_email(raw, "stdin" if args.file == "-" else args.file))
        elif args.cmd == "hoax":
            with status_ctx("Memeriksa klaim ...", quiet):
                results.append(analyze_claim(" ".join(args.claim), args.lang))
        elif args.cmd == "image":
            results = [analyze_image(f) for f in args.files]
        elif args.cmd == "batch":
            results = run_batch(args.file, fetch=not args.no_fetch, workers=args.workers, progress=not quiet)
    except OSError as e:
        console.print(T(f"Error: {e}", "red"))
        return 1
    except KeyboardInterrupt:
        console.print(T("Dibatalkan.", "yellow"))
        return 130

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    elif args.cmd == "batch":
        console.print(render_batch_summary(results))
    else:
        for r in results:
            console.print(render_result(r))
    if args.out:
        try:
            console.print(T(f"Laporan disimpan: {export_report(results, args.out)}", "green"))
        except (ValueError, OSError) as e:
            console.print(T(f"Gagal menyimpan laporan: {e}", "red"))
            return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
