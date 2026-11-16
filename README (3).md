# xDEX-UI Toolkit

Kumpulan tool bertema "hacker HUD" ungu, terdiri dari 3 file:

| File | Jenis | Fungsi |
|---|---|---|
| `hacker-hud.html` | Halaman web (artifact) | Tampilan HUD visual + terminal **simulasi** |
| `hacker_hud.py` | Script Python (CLI) | Versi terminal dari HUD **simulasi** |
| `real_storage_explorer.py` | Script Python (CLI) | Tool **nyata** untuk membaca storage asli di komputer |

---

## 1. `hacker-hud.html`

Halaman web mandiri (satu file, tanpa server) yang mereplikasi tampilan
boot sequence + dashboard sistem ala video referensi: panel CPU/RAM,
grafik network, "world view", dock ikon, dan keyboard backlit ungu.

**Cara pakai:** buka file-nya langsung di browser (double-click, atau
drag ke tab browser).

**Terminal di dalamnya** menerima perintah: `help`, `osint <nama>`,
`nmap <target>`, `sqlmap <url>`, `neofetch`, `clear`. Semua output
dari perintah ini **acak/fiktif** — tidak ada koneksi jaringan atau
pemindaian nyata yang dilakukan.

---

## 2. `hacker_hud.py`

Versi terminal (CLI) dari HUD di atas, dengan efek ketikan otomatis
dan statistik CPU/RAM (pakai data asli komputer kalau `psutil`
terpasang, kalau tidak dipakai angka acak).

**Cara pakai:**
```bash
python3 hacker_hud.py
# opsional, agar CPU/RAM memakai data asli:
pip install psutil
```

**Perintah di dalam shell:** `help`, `osint <nama>`, `nmap <target>`,
`sqlmap <url>`, `neofetch`, `stats`, `clear`, `exit`.

⚠️ Sama seperti versi HTML — perintah `osint`/`nmap`/`sqlmap` di sini
**simulasi**, bukan alat pemindaian atau serangan nyata ke jaringan
atau sistem apa pun. Tidak ada koneksi internet yang dipakai.

---

## 3. `real_storage_explorer.py`

Tool yang **benar-benar** membaca folder nyata di komputermu
(read-only, kecuali perintah `empty-trash` yang minta konfirmasi).
Otomatis mendeteksi Windows / macOS / Linux.

**Cara pakai:**
```bash
python3 real_storage_explorer.py
```
Harus dijalankan langsung di komputermu sendiri — tidak berfungsi di
dalam chat ini karena di sini tidak ada akses ke file komputermu.

**Lokasi yang dibaca:**
- `home`, `downloads`, `documents` — folder pengguna
- `temp` — folder temporary/cache sistem
- `browsercache_chrome` — cache browser Chrome (jika ada)
- `fonts` — folder font sistem
- `recyclebin` (Windows) / `trash` (macOS & Linux)

**Perintah di dalam shell:**
| Perintah | Keterangan |
|---|---|
| `overview` | ringkasan ukuran & jumlah file tiap lokasi |
| `keys` | daftar nama lokasi yang bisa diakses |
| `ls <key> [jumlah]` | isi folder tersebut (nama, ukuran, tanggal) |
| `empty-trash` | kosongkan Recycle Bin/Trash (minta ketik `HAPUS` dulu) |
| `exit` | keluar |

⚠️ `empty-trash` **menghapus permanen** — gunakan dengan hati-hati,
tidak bisa di-undo.

---

## Persyaratan

- Python 3.8+ untuk kedua file `.py`
- Tidak perlu instalasi tambahan, kecuali mau statistik CPU/RAM asli
  di `hacker_hud.py` (`pip install psutil`, opsional)
- `hacker-hud.html` hanya butuh browser modern, tidak perlu internet
