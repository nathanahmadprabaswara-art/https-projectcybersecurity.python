#!/usr/bin/env python3
"""
Real Storage Explorer — xDEX-UI
---------------------------------
Tool NYATA (bukan simulasi) untuk melihat isi folder-folder asli di
komputermu: Home, Downloads, Documents, Temp/Cache sistem, dan
Recycle Bin / Trash. Hanya membaca (read-only) — tidak menghapus apa pun
kecuali kamu pakai perintah 'empty' secara eksplisit dan konfirmasi.

Jalankan di KOMPUTERMU SENDIRI (bukan di sini/chat):
    python3 real_storage_explorer.py

Kompatibel Windows / macOS / Linux (deteksi otomatis).
"""

import os
import sys
import platform
import tempfile
import shutil
import datetime
from pathlib import Path

RESET = "\033[0m"
PURPLE = "\033[38;5;135m"
VIOLET = "\033[38;5;99m"
DIM = "\033[38;5;60m"
GREEN = "\033[38;5;120m"
YELLOW = "\033[38;5;221m"
RED = "\033[38;5;203m"
WHITE = "\033[97m"
BOLD = "\033[1m"

SYSTEM = platform.system()  # 'Windows', 'Darwin', 'Linux'
HOME = Path.home()


def human_size(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def folder_size(path, limit_files=200000):
    total = 0
    count = 0
    try:
        for root, dirs, files in os.walk(path, onerror=lambda e: None):
            for f in files:
                count += 1
                if count > limit_files:
                    return total, count, True  # dibatasi, folder sangat besar
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    except Exception:
        pass
    return total, count, False


def get_locations():
    """Mengembalikan dict lokasi folder nyata sesuai OS."""
    locs = {
        "home": HOME,
        "downloads": HOME / "Downloads",
        "documents": HOME / "Documents",
        "temp": Path(tempfile.gettempdir()),
    }

    if SYSTEM == "Windows":
        locs["recyclebin"] = Path(os.environ.get("SystemDrive", "C:") + "\\$Recycle.Bin")
        locs["browsercache_chrome"] = HOME / "AppData/Local/Google/Chrome/User Data/Default/Cache"
        locs["fonts"] = Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"
    elif SYSTEM == "Darwin":
        locs["trash"] = HOME / ".Trash"
        locs["browsercache_chrome"] = HOME / "Library/Caches/Google/Chrome"
        locs["fonts"] = Path("/Library/Fonts")
    else:  # Linux
        locs["trash"] = HOME / ".local/share/Trash/files"
        locs["browsercache_chrome"] = HOME / ".cache/google-chrome"
        locs["fonts"] = Path("/usr/share/fonts")

    return locs


def list_dir(path, n=20):
    path = Path(path)
    if not path.exists():
        print(RED + f"  Folder tidak ditemukan / tidak bisa diakses: {path}" + RESET)
        return
    if not os.access(path, os.R_OK):
        print(RED + f"  Tidak ada izin baca ke: {path} (coba jalankan dengan hak akses lebih/admin)" + RESET)
        return
    try:
        entries = list(path.iterdir())
    except PermissionError:
        print(RED + f"  Permission denied: {path}" + RESET)
        return
    entries.sort(key=lambda p: (not p.is_dir(), p.name.lower()))
    print(VIOLET + f"  {path}  ({len(entries)} item)" + RESET)
    for e in entries[:n]:
        try:
            stat = e.stat()
            size = human_size(stat.st_size) if e.is_file() else "<DIR>"
            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            size, mtime = "?", "?"
        tag = GREEN + "[DIR] " + RESET if e.is_dir() else DIM + "      " + RESET
        print(f"  {tag}{e.name:<40.40} {size:>10}  {mtime}")
    if len(entries) > n:
        print(DIM + f"  ... dan {len(entries)-n} item lainnya (gunakan 'ls <key> <jumlah>' untuk lihat lebih banyak)" + RESET)


def cmd_overview(locs):
    print(PURPLE + BOLD + f"\n  REAL STORAGE — {SYSTEM}" + RESET)
    print(DIM + "  (read-only scan, bisa agak lama untuk folder besar)\n" + RESET)
    for key, path in locs.items():
        exists = path.exists()
        if not exists:
            print(f"  {key:<20} " + DIM + f"{path}  (tidak ditemukan)" + RESET)
            continue
        size, count, truncated = folder_size(path)
        flag = " (dibatasi, folder sangat besar)" if truncated else ""
        print(f"  {key:<20} " + WHITE + f"{human_size(size):>10}" + RESET +
              DIM + f"  {count} file{flag}  -> {path}" + RESET)
    print()


def cmd_empty_trash(locs):
    key = "recyclebin" if SYSTEM == "Windows" else "trash"
    path = locs.get(key)
    if not path or not path.exists():
        print(RED + "  Lokasi trash/recycle bin tidak ditemukan di sistem ini." + RESET)
        return
    confirm = input(YELLOW + f"  Yakin ingin MENGHAPUS PERMANEN isi {path}? Ketik 'HAPUS' untuk lanjut: " + RESET)
    if confirm.strip() != "HAPUS":
        print(DIM + "  Dibatalkan." + RESET)
        return
    try:
        for item in path.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)
        print(GREEN + "  Selesai dikosongkan." + RESET)
    except Exception as e:
        print(RED + f"  Gagal: {e}" + RESET)


def main():
    locs = get_locations()
    print(VIOLET + BOLD + "Real Storage Explorer — xDEX-UI" + RESET)
    print(DIM + f"OS terdeteksi: {SYSTEM} | Home: {HOME}\n" + RESET)
    cmd_overview(locs)
    print(DIM + "Perintah: overview | ls <key> [jumlah] | empty-trash | keys | exit\n" + RESET)

    while True:
        try:
            raw = input(VIOLET + "storage> " + RESET).strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "overview":
            cmd_overview(locs)
        elif cmd == "keys":
            print(", ".join(locs.keys()))
        elif cmd == "ls":
            if len(parts) < 2 or parts[1] not in locs:
                print(RED + f"  usage: ls <key>  (key: {', '.join(locs.keys())})" + RESET)
            else:
                n = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 20
                list_dir(locs[parts[1]], n)
        elif cmd == "empty-trash":
            cmd_empty_trash(locs)
        elif cmd in ("exit", "quit"):
            break
        else:
            print(RED + "  perintah tidak dikenali. Ketik: overview | ls <key> | empty-trash | keys | exit" + RESET)


if __name__ == "__main__":
    main()
