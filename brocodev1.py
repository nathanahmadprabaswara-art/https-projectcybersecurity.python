#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BroCodeV1 - OSINT & Cybersecurity Toolkit (CLI)

Hanya untuk riset, edukasi, dan pengujian yang sah / berizin.
Dependensi: hanya pustaka standar Python 3.8+.
Opsional (hasil lebih akurat untuk nomor HP):  pip install phonenumbers
"""
import sys, os, re, json, base64, hashlib, ipaddress, socket, webbrowser, codecs
import urllib.parse as up
from datetime import datetime, timezone
from email.parser import HeaderParser

try:
    import phonenumbers
    from phonenumbers import carrier as pn_carrier, geocoder as pn_geo, timezone as pn_tz
    HAS_PN = True
except Exception:
    HAS_PN = False

USE_COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
def c(code, s): return f"\033[{code}m{s}\033[0m" if USE_COLOR else s
G  = lambda s: c("92", s)   # hijau
D  = lambda s: c("2;32", s) # hijau redup
Y  = lambda s: c("93", s)   # kuning
R  = lambda s: c("91", s)   # merah
B  = lambda s: c("1;92", s) # tebal

BANNER = r"""
  ____            ____          _       __     ___
 | __ ) _ __ ___ / ___|___   __| | ___  \ \   / / |
 |  _ \| '__/ _ \ |   / _ \ / _` |/ _ \  \ \ / /| |
 | |_) | | | (_) | |__| (_) | (_| |  __/   \ V / | |
 |____/|_|  \___/ \____\___/ \__,_|\___|    \_/  |_|
"""

def banner():
    print(G(BANNER))
    print(D("  OSINT & cybersecurity toolkit  |  hanya untuk penggunaan sah & berizin"))
    print(D("  Mode nomor HP: " + ("phonenumbers (lengkap)" if HAS_PN else "bawaan (terbatas, pip install phonenumbers)")))
    print()

# ---------- helper I/O ----------
def ask(prompt):
    try:
        return input(G("brocode") + D("> ") + prompt + " ").strip()
    except (EOFError, KeyboardInterrupt):
        print(); return ""

def ask_block(prompt):
    print(G("brocode") + D("> ") + prompt + D(" (akhiri dengan baris kosong)"))
    lines = []
    try:
        while True:
            l = input()
            if not l.strip(): break
            lines.append(l)
    except (EOFError, KeyboardInterrupt):
        pass
    return "\n".join(lines)

def head(t): print("\n" + B(f"== {t} ==") + "\n")
def kv(k, v): print(f"  {D(k.ljust(16))} {v}")
def clean_domain(s): return re.sub(r"^https?://", "", s.strip(), flags=re.I).split("/")[0]

def show_links(items):
    """items: list of (nama, url, ket). Cetak dan tawarkan untuk dibuka di browser."""
    for i, (n, u, d) in enumerate(items, 1):
        print(f"  {G(str(i).rjust(2))}. {n.ljust(20)} {D(d)}")
        print(f"      {D(u)}")
    sel = ask("Buka di browser? (nomor / a=semua / Enter=lewati)")
    if sel.lower() == "a":
        for _, u, _ in items: webbrowser.open_new_tab(u)
    elif sel.isdigit() and 1 <= int(sel) <= len(items):
        webbrowser.open_new_tab(items[int(sel) - 1][1])

# ---------- 1. IOC Extractor ----------
IOC_RE = {
    "IPv4":   r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b",
    "URL":    r"\b(?:hxxps?|https?)://[^\s\"'<>]+",
    "Email":  r"\b[\w.+-]+(?:@|\[at\])[\w-]+(?:\.|\[\.\])[\w.-]+\b",
    "Domain": r"\b(?:[a-z0-9-]+(?:\.|\[\.\]))+(?:com|net|org|io|id|co|info|biz|xyz|ru|cn|top|dev|app|gov|edu|me|cc|tk|site|online)\b",
    "SHA256": r"\b[a-fA-F0-9]{64}\b",
    "SHA1":   r"\b[a-fA-F0-9]{40}\b",
    "MD5":    r"\b[a-fA-F0-9]{32}\b",
    "CVE":    r"\bCVE-\d{4}-\d{4,7}\b",
}
def refang(s): return re.sub(r"^hxxp", "http", s.replace("[.]", ".").replace("[at]", "@"), flags=re.I)

def m_ioc():
    head("IOC Extractor")
    text = ask_block("Tempel teks/log/laporan:")
    found = False
    for k, rx in IOC_RE.items():
        res = sorted({refang(x) for x in re.findall(rx, text, flags=re.I)})
        if res:
            found = True
            print(B(f"# {k} ({len(res)})"))
            for r in res: print("  " + r)
    if not found: print(Y("Tidak ada IOC ditemukan."))

# ---------- 2. Domain Recon ----------
def m_domain():
    head("Domain / URL Pivot")
    d = clean_domain(ask("Domain (contoh: example.com):"))
    if not d: return
    try:
        ips = sorted({a[4][0] for a in socket.getaddrinfo(d, None)})
        kv("Resolve DNS", ", ".join(ips))
        try: kv("Reverse DNS", socket.gethostbyaddr(ips[0])[0])
        except Exception: pass
    except Exception:
        print(Y("  Resolve DNS gagal (offline atau domain tidak ada)."))
    e = up.quote(d)
    show_links([
        ("WHOIS", f"https://who.is/whois/{e}", "registrar & tanggal"),
        ("crt.sh", f"https://crt.sh/?q={e}", "sertifikat & subdomain"),
        ("VirusTotal", f"https://www.virustotal.com/gui/domain/{e}", "reputasi"),
        ("urlscan.io", f"https://urlscan.io/search/#domain:{e}", "riwayat scan"),
        ("Wayback Machine", f"https://web.archive.org/web/*/{e}", "arsip situs"),
        ("Shodan", f"https://www.shodan.io/search?query=hostname:{e}", "host terkait"),
        ("Censys", f"https://search.censys.io/search?q={e}", "sertifikat & layanan"),
        ("SecurityTrails", f"https://securitytrails.com/domain/{e}/dns", "DNS historis"),
        ("BuiltWith", f"https://builtwith.com/{e}", "teknologi"),
    ])

# ---------- 3. IP & CIDR ----------
def m_ip():
    head("IP & CIDR")
    v = ask("IPv4/IPv6 atau CIDR (8.8.8.8 / 192.168.1.0/24):")
    try:
        net = ipaddress.ip_network(v, strict=False)
        ip = ipaddress.ip_interface(v).ip
    except ValueError:
        print(R("Format tidak valid.")); return
    kv("Alamat", str(ip)); kv("Versi", f"IPv{net.version}")
    kv("Network", str(net.network_address)); kv("Netmask", f"{net.netmask} (/{net.prefixlen})")
    if net.version == 4: kv("Broadcast", str(net.broadcast_address))
    kv("Jumlah alamat", f"{net.num_addresses:,}")
    private = ip.is_private or ip.is_loopback or ip.is_link_local
    kv("Tipe", Y("Privat / loopback / link-local") if private else G("Publik"))
    if not private and net.num_addresses == 1:
        e = str(ip)
        show_links([
            ("Shodan", f"https://www.shodan.io/host/{e}", "port & layanan"),
            ("AbuseIPDB", f"https://www.abuseipdb.com/check/{e}", "laporan abuse"),
            ("VirusTotal", f"https://www.virustotal.com/gui/ip-address/{e}", "reputasi"),
            ("IPinfo", f"https://ipinfo.io/{e}", "geo & ASN"),
            ("GreyNoise", f"https://viz.greynoise.io/ip/{e}", "noise scanner"),
        ])

# ---------- 4. Username / Email ----------
def m_user():
    head("Username & Email Pivot")
    v = ask("Username atau email:")
    if not v: return
    e = up.quote(v)
    if "@" in v:
        show_links([
            ("Google exact", f"https://www.google.com/search?q={up.quote(chr(34)+v+chr(34))}", "penyebutan publik"),
            ("Have I Been Pwned", f"https://haveibeenpwned.com/account/{e}", "kebocoran data"),
            ("Epieos", f"https://epieos.com/?q={e}", "akun terkait"),
            ("GitHub commits", f"https://github.com/search?q={e}&type=commits", "jejak commit"),
        ])
    else:
        sites = {"GitHub": "https://github.com/", "GitLab": "https://gitlab.com/", "X / Twitter": "https://x.com/",
                 "Instagram": "https://instagram.com/", "Reddit": "https://reddit.com/user/", "TikTok": "https://tiktok.com/@",
                 "YouTube": "https://youtube.com/@", "Telegram": "https://t.me/", "Medium": "https://medium.com/@",
                 "Twitch": "https://twitch.tv/", "Keybase": "https://keybase.io/", "HackerOne": "https://hackerone.com/",
                 "Dev.to": "https://dev.to/", "Pinterest": "https://pinterest.com/"}
        show_links([(n, p + e, "profil") for n, p in sites.items()])

# ---------- 5. Dork Builder ----------
def m_dork():
    head("Dork Builder (recon pasif)")
    d = clean_domain(ask("Domain target (yang Anda miliki / berizin):"))
    if not d: return
    G_ = [("Subdomain", f"site:*.{d} -www"),
          ("Dokumen publik", f"site:{d} (filetype:pdf OR filetype:docx OR filetype:xlsx)"),
          ("Halaman login", f"site:{d} (inurl:login OR inurl:admin OR inurl:signin)"),
          ("Directory listing", f'site:{d} intitle:"index of"'),
          ("Berkas konfigurasi", f"site:{d} (ext:env OR ext:ini OR ext:conf OR ext:yml)"),
          ("Log & backup", f"site:{d} (ext:log OR ext:bak OR ext:sql OR ext:old)"),
          ("Pastebin", f'site:pastebin.com "{d}"'),
          ("GitHub", f'site:github.com "{d}"'),
          ("LinkedIn", f'site:linkedin.com/in "{d}"')]
    items = [(n, "https://www.google.com/search?q=" + up.quote(q), q) for n, q in G_]
    items += [("Shodan hostname", "https://www.shodan.io/search?query=" + up.quote(f"hostname:{d}"), f"hostname:{d}"),
              ("Shodan SSL", "https://www.shodan.io/search?query=" + up.quote(f"ssl.cert.subject.cn:{d}"), f"ssl.cert.subject.cn:{d}")]
    show_links(items)

# ---------- 6. Encode / Decode ----------
def m_encode():
    head("Encoder / Decoder")
    modes = ["Base64 encode", "Base64 decode", "Hex encode", "Hex decode", "URL encode", "URL decode", "ROT13", "Teks ke biner", "Biner ke teks"]
    for i, m in enumerate(modes, 1): print(f"  {G(str(i))}. {m}")
    sel = ask("Pilih mode:"); s = ask("Input:")
    try:
        b = s.encode()
        out = {"1": lambda: base64.b64encode(b).decode(), "2": lambda: base64.b64decode(s.strip()).decode(errors="replace"),
               "3": lambda: b.hex(), "4": lambda: bytes.fromhex(re.sub(r"\s|0x", "", s)).decode(errors="replace"),
               "5": lambda: up.quote(s, safe=""), "6": lambda: up.unquote(s), "7": lambda: codecs.encode(s, "rot13"),
               "8": lambda: " ".join(f"{x:08b}" for x in b),
               "9": lambda: bytes(int(x, 2) for x in s.split()).decode(errors="replace")}[sel]()
        print("\n" + G(out))
    except Exception:
        print(R("Input tidak valid untuk mode ini."))

# ---------- 7. Hash ----------
def m_hash():
    head("Hash Generator & Identifier")
    print(f"  {G('1')}. Hash teks   {G('2')}. Identifikasi hash   {G('3')}. Hash file")
    sel = ask("Pilih:")
    if sel == "1":
        d = ask("Teks:").encode()
        for a in ("md5", "sha1", "sha256", "sha512"): kv(a.upper(), hashlib.new(a, d).hexdigest())
    elif sel == "2":
        h = ask("Hash:")
        L = {32: "MD5 / NTLM / MD4", 40: "SHA-1", 56: "SHA-224", 64: "SHA-256 / SHA3-256", 96: "SHA-384", 128: "SHA-512 / SHA3-512"}
        if re.match(r"^\$2[aby]\$", h): r = "bcrypt"
        elif h.startswith("$argon2"): r = "Argon2"
        elif h.startswith("$6$"): r = "SHA-512 crypt (Linux)"
        elif h.startswith("$5$"): r = "SHA-256 crypt"
        elif h.startswith("$1$"): r = "MD5 crypt"
        elif re.fullmatch(r"[a-fA-F0-9]+", h): r = L.get(len(h))
        else: r = None
        print(G(f"Kemungkinan: {r}") if r else Y("Jenis tidak dikenali."))
    elif sel == "3":
        p = ask("Path file:")
        try:
            hs = {a: hashlib.new(a) for a in ("md5", "sha1", "sha256")}
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    for x in hs.values(): x.update(chunk)
            for a, x in hs.items(): kv(a.upper(), x.hexdigest())
            print(D("  Cek hash SHA256 di VirusTotal untuk reputasi file."))
        except OSError as e:
            print(R(f"Gagal membaca file: {e}"))

# ---------- 8. JWT ----------
def m_jwt():
    head("JWT Decoder")
    t = ask("Token JWT:")
    def dec(p): return json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))
    try:
        p = t.split("."); h, b = dec(p[0]), dec(p[1])
    except Exception:
        print(R("Bukan JWT yang valid.")); return
    alg = str(h.get("alg", ""))
    if not alg or alg.lower() == "none": print(R("! alg=none: token tanpa tanda tangan, sangat berisiko."))
    if alg.startswith("HS"): print(Y("! HMAC: pastikan secret kuat dan tidak mudah ditebak."))
    if "exp" in b:
        x = datetime.fromtimestamp(b["exp"], timezone.utc)
        print((R if x < datetime.now(timezone.utc) else G)(f"exp: {x.isoformat()} ({'kedaluwarsa' if x < datetime.now(timezone.utc) else 'berlaku'})"))
    else: print(Y("! Tidak ada klaim exp."))
    print(B("\nHEADER")); print(json.dumps(h, indent=2)); print(B("PAYLOAD")); print(json.dumps(b, indent=2))

# ---------- 9. Email header ----------
def m_mail():
    head("Email Header Analyzer")
    raw = ask_block("Tempel header mentah email:")
    msg = HeaderParser().parsestr(raw)
    for k in ("From", "Reply-To", "Return-Path", "Subject", "Date", "Message-ID"): kv(k, msg.get(k, "-"))
    auth = " ".join((msg.get_all("Authentication-Results") or []) + (msg.get_all("Received-SPF") or []))
    def st(k):
        m = re.search(k + r"=(\w+)", auth, re.I); return m.group(1).lower() if m else "tidak ada"
    print()
    for k in ("spf", "dkim", "dmarc"):
        v = st(k); print(f"  {D(k.upper().ljust(6))} {(G if v == 'pass' else Y if v == 'tidak ada' else R)(v)}")
    dom = lambda k: (re.search(r"@([\w.-]+)", msg.get(k, "") or "") or [None, None])[1]
    f, rp, rt = dom("From"), dom("Return-Path"), dom("Reply-To")
    if f and rp and f.lower() != rp.lower(): print(Y(f"\n! Domain From dan Return-Path berbeda ({f} vs {rp})"))
    if f and rt and f.lower() != rt.lower(): print(Y(f"! Reply-To mengarah ke domain lain ({rt})"))
    print(B("\nJalur relay (asal -> tujuan)"))
    for i, r in enumerate(reversed(msg.get_all("Received") or []), 1): print(f"  {i}. {' '.join(r.split())[:160]}")
    ips = sorted(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", raw)))
    print(B("\nIP ditemukan")); print("  " + (", ".join(ips) or "-"))

# ---------- 10. Defang ----------
def m_defang():
    head("Defang / Refang")
    s = ask("Teks:"); mode = ask("d=defang, r=refang:").lower()
    if mode == "r": print(G(refang(re.sub(r"\(\.\)", ".", s))))
    else: print(G(re.sub(r"https?://", lambda m: m.group(0).replace("http", "hxxp"), s).replace(".", "[.]").replace("@", "[at]")))

# ---------- 11. Timestamp ----------
def m_time():
    head("Timestamp Converter")
    v = ask("Epoch atau tanggal ISO (kosong = sekarang):")
    try:
        if not v: d = datetime.now(timezone.utc)
        elif v.isdigit(): d = datetime.fromtimestamp(int(v) / (1000 if len(v) > 11 else 1), timezone.utc)
        else: d = datetime.fromisoformat(v.replace("Z", "+00:00")); d = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        print(R("Format tidak dikenali.")); return
    kv("UTC", d.strftime("%a, %d %b %Y %H:%M:%S UTC")); kv("ISO 8601", d.isoformat())
    kv("Lokal", d.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")); kv("Epoch (detik)", int(d.timestamp())); kv("Epoch (ms)", int(d.timestamp() * 1000))

# ---------- 12. Phone Intel ----------
ID_PREFIX = {
    "Telkomsel": "811 812 813 821 822 823 851 852 853", "Indosat Ooredoo": "814 815 816 855 856 857 858",
    "XL Axiata": "817 818 819 859 877 878", "Axis": "831 832 833 838", "Tri (3)": "895 896 897 898 899",
    "Smartfren": "881 882 883 884 885 886 887 888 889"}
CC = {"62": "Indonesia", "1": "AS / Kanada", "44": "Inggris", "60": "Malaysia", "65": "Singapura", "61": "Australia",
      "91": "India", "81": "Jepang", "82": "Korea Selatan", "86": "Tiongkok", "49": "Jerman", "33": "Prancis",
      "7": "Rusia / Kazakhstan", "66": "Thailand", "63": "Filipina", "84": "Vietnam", "971": "UEA", "966": "Arab Saudi"}

def normalize_phone(raw):
    s = re.sub(r"[^\d+]", "", raw)
    if s.startswith("00"): s = "+" + s[2:]
    if s.startswith("0"): s = "+62" + s[1:]          # asumsi default: Indonesia
    elif not s.startswith("+"): s = "+" + s
    return s

def m_phone():
    head("Phone Number Intelligence")
    print(Y("  Catatan: tool ini membaca data PUBLIK dari struktur nomor (negara, operator awal, jenis jalur).\n"
            "  Ia TIDAK bisa menunjukkan lokasi real-time pemilik. Pelacakan semacam itu hanya sah\n"
            "  lewat operator/aparat dengan dasar hukum. Gunakan untuk verifikasi nomor yang menghubungi Anda.\n"))
    raw = ask("Nomor HP (contoh 0812xxxxxxx atau +62812xxxxxxx):")
    if not raw: return
    num = normalize_phone(raw); digits = num[1:]
    if HAS_PN:
        try:
            n = phonenumbers.parse(num, None)
        except Exception as e:
            print(R(f"Tidak bisa diparse: {e}")); return
        T = phonenumbers.PhoneNumberType
        types = {T.MOBILE: "Seluler", T.FIXED_LINE: "Telepon tetap", T.FIXED_LINE_OR_MOBILE: "Tetap / seluler", T.VOIP: "VoIP",
                 T.TOLL_FREE: "Bebas pulsa", T.PREMIUM_RATE: "Tarif premium", T.UAN: "UAN", T.PAGER: "Pager"}
        kv("Valid", G("ya") if phonenumbers.is_valid_number(n) else R("tidak"))
        kv("Mungkin valid", G("ya") if phonenumbers.is_possible_number(n) else R("tidak"))
        kv("Kode negara", f"+{n.country_code}")
        kv("Negara / wilayah", pn_geo.description_for_number(n, "id") or phonenumbers.region_code_for_number(n) or "-")
        kv("Operator awal", pn_carrier.name_for_number(n, "id") or "tidak diketahui")
        kv("Jenis jalur", types.get(phonenumbers.number_type(n), "tidak diketahui"))
        kv("Zona waktu", ", ".join(pn_tz.time_zones_for_number(n)) or "-")
        kv("Format E.164", phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164))
        kv("Internasional", phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
        kv("Nasional", phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.NATIONAL))
    else:
        cc = next((k for k in sorted(CC, key=len, reverse=True) if digits.startswith(k)), None)
        kv("Kode negara", f"+{cc}" if cc else "tidak dikenali")
        kv("Negara", CC.get(cc, "tidak dikenali"))
        if cc == "62":
            pre = digits[2:5]
            op = next((o for o, p in ID_PREFIX.items() if pre in p.split()), None)
            kv("Operator awal", op or "tidak dikenali (cek prefiks)")
            kv("Jenis jalur", "Seluler" if digits[2:3] == "8" else "Telepon tetap / lainnya")
            kv("Zona waktu", "WIB / WITA / WIT (tergantung kode area)")
            ok = 10 <= len(digits) <= 14
            kv("Panjang wajar", G("ya") if ok else R("tidak (biasanya 10-14 digit)"))
        kv("Format E.164", num)
        print(D("  Pasang `pip install phonenumbers` untuk validasi & operator yang lebih akurat."))
    print(Y("\n  Operator awal bisa berbeda jika nomor sudah dipindah (MNP)."))
    e164 = num; d = digits
    show_links([
        ("WhatsApp (cek akun)", f"https://wa.me/{d}", "apakah nomor terdaftar WA"),
        ("Telegram", f"https://t.me/+{d}", "apakah terdaftar Telegram"),
        ("Google exact", "https://www.google.com/search?q=" + up.quote(f'"{e164}" OR "{"0" + d[2:] if d.startswith("62") else d}"'), "penyebutan publik / penipuan"),
        ("Truecaller", f"https://www.truecaller.com/search/{'id' if d.startswith('62') else 'us'}/{d}", "nama penelepon (butuh login)"),
        ("Sync.me", f"https://sync.me/search/?number={up.quote(e164)}", "pencarian nomor"),
    ])

# ---------- main ----------
MENU = [("IOC Extractor", m_ioc), ("Domain / URL Pivot", m_domain), ("IP & CIDR", m_ip), ("Username / Email Pivot", m_user),
        ("Dork Builder", m_dork), ("Encode / Decode", m_encode), ("Hash Tools", m_hash), ("JWT Decoder", m_jwt),
        ("Email Header Analyzer", m_mail), ("Defang / Refang", m_defang), ("Timestamp Converter", m_time),
        ("Phone Number Intelligence", m_phone)]

def main():
    banner()
    while True:
        print(B("MENU"))
        for i, (n, _) in enumerate(MENU, 1): print(f"  {G(str(i).rjust(2))}. {n}")
        print(f"  {G(' 0')}. Keluar")
        s = ask("\nPilih modul:")
        if s in ("0", "q", "exit", ""):
            if s == "": continue
            print(D("Sampai jumpa.")); break
        if s.isdigit() and 1 <= int(s) <= len(MENU):
            try: MENU[int(s) - 1][1]()
            except KeyboardInterrupt: print(Y("\nDibatalkan."))
            print()
        else:
            print(R("Pilihan tidak valid.\n"))

if __name__ == "__main__":
    main()
