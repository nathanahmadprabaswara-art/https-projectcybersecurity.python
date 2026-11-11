# GHOST ENGINE // Terminal Visual Engine

Demo visual untuk terminal bergaya "hacker dashboard": hujan matrix, boot sequence, globe ASCII, wireframe 3D, torus, serta panel kode dan hex yang bergulir. Ditulis dalam satu file Python tanpa dependensi.

> **Catatan:** animasi intro murni kosmetik. Semua datanya (log, hex, "link", peta globe) adalah angka acak/simulasi. Hanya **menu OSINT** yang melakukan kueri sungguhan, dan itu terbatas pada informasi publik tentang domain/IP (lihat bagian [Menu OSINT](#menu-osint)).

## File

Semua dalam satu file: `ghost_engine.py` (animasi intro, antarmuka, dan semua tool OSINT). Tidak ada file lain yang perlu disalin.

## Fitur

- **Boot sequence**: hujan matrix dengan kotak *Initialization Sequence* dan progress bar.
- **Globe ASCII** yang berputar, lengkap dengan cincin orbit dan garis link simulasi.
- **Wireframe 3D**: icosahedron dan kubus yang berputar berlawanan arah.
- **Torus (donut)** dengan shading karakter.
- **Panel kode** yang bergulir seperti sedang diketik.
- **Hex dump** yang berubah-ubah dan **log stream** simulasi.
- **Finale**: logo blok besar dari nama kamu di atas hujan matrix.
- **Menu OSINT** setelah intro selesai (sekitar 35 detik, atau tekan `Enter` untuk melewati): tool pasif berbasis domain dan IP. Menunya ikut hidup seperti intro (lihat [Menu OSINT](#menu-osint)).

## Kebutuhan

- Python 3.6 atau lebih baru
- Terminal dengan dukungan warna dan UTF-8 (hampir semua terminal modern)
- Linux atau macOS. Modul `curses` sudah bawaan Python di keduanya.
- Windows: install dulu `pip install windows-curses`, lalu jalankan lewat Windows Terminal.

Tidak ada paket lain yang perlu diinstal.

## Cara menjalankan

```bash
python3 ghost_engine.py
```

Agar bisa dijalankan langsung:

```bash
chmod +x ghost_engine.py
./ghost_engine.py
```

Ukuran terminal yang disarankan adalah **100x30 atau lebih**. Di bawah 70x20, script hanya menampilkan peringatan untuk memperbesar jendela. Ukuran jendela bisa diubah saat script berjalan dan tampilan akan menyesuaikan.

## Kontrol

| Tombol | Fungsi |
| --- | --- |
Saat intro:

| Tombol | Fungsi |
| --- | --- |
| `Enter` / `Spasi` | Lewati intro, langsung ke menu |
| `q` / `Esc` / `Ctrl+C` | Keluar |

Di menu OSINT:

| Tombol | Fungsi |
| --- | --- |
| `↑` `↓` (atau `j` `k`) | Pilih tool |
| `Enter` atau angka `1`-`8` | Pilih tool dan masukkan target |
| `R` | Putar ulang intro |
| `q` | Keluar |
| `Esc` | Batal / kembali ke menu |
| `↑` `↓` `PgUp` `PgDn` | Gulir hasil |
| `s` | Simpan hasil ke `osint_reports/` |
| Klik kiri | Pilih dan jalankan tool di daftar menu |
| Roda mouse | Ganti pilihan (menu) atau gulir (hasil) |

## Menu OSINT

**Tampilan interaktif:**

- Masuk menu dengan transisi hujan matrix yang menyapu layar.
- Panel kiri bawah menampilkan scene 3D yang hidup (globe, wireframe, torus). Scene berganti mengikuti tool yang dipilih, dan berubah menjadi globe saat tool berjalan.
- Panel info diisi hujan matrix, dengan kursor berkedip saat mengetik target.
- Saat tool berjalan: spinner, bar pemindai, penghitung waktu, dan aliran hex.
- Hasil muncul baris demi baris dengan efek ketik.
- Mouse didukung: klik untuk memilih tool dan roda untuk menggulir.

Semua tool bersifat **pasif atau permintaan ringan biasa**, hanya memakai pustaka standar Python.

| # | Tool | Fungsi |
| --- | --- | --- |
| 1 | DNS Records | A, AAAA, CNAME, NS, MX, TXT, plus cek SPF dan DMARC |
| 2 | WHOIS | Registrar, tanggal, name server, status (domain) atau netname/org/CIDR (IP) |
| 3 | HTTP & Security Headers | Satu request biasa, lalu audit header keamanan (HSTS, CSP, dan lainnya) |
| 4 | TLS Certificate | Penerbit, masa berlaku, versi TLS, daftar SAN |
| 5 | Subdomain (CT Logs) | Subdomain dari log Certificate Transparency via crt.sh |
| 6 | robots & security.txt | Ambil `/robots.txt` dan `/.well-known/security.txt` |
| 7 | IP / Reverse DNS | Resolusi domain ke IP dan pencarian PTR |
| 8 | Laporan Lengkap | DNS, WHOIS, TLS, HTTP, dan Subdomain dalam satu laporan |

**Batasan yang disengaja:**

- Hanya **domain dan IP**. Tidak ada pencarian orang, akun media sosial, email, atau nomor telepon.
- Tidak ada pemindaian port atau eksploitasi.
- WHOIS menyaring field yang berisi alamat email, jadi data kontak pribadi tidak ditampilkan.
- Gunakan hanya pada target milikmu atau yang kamu punya izin untuk dianalisis.

**Catatan teknis:**

- Butuh koneksi internet. Tool 5 (crt.sh) kadang lambat atau menolak permintaan, coba lagi beberapa saat kemudian.
- Input target dibersihkan otomatis: `https://Example.com:8443/path` menjadi `example.com`.
- Hasil yang disimpan (tombol `s`) ada di folder `osint_reports/` pada direktori tempat kamu menjalankan script.
- Menambah tool sendiri: tulis fungsi yang menerima target dan mengembalikan list baris teks, lalu daftarkan di list `TOOLS` pada bagian OSINT di `ghost_engine.py`. Awalan baris mengatur warna: `## ` judul, `+ ` baik, `! ` peringatan, `- ` info redup.

## Kustomisasi

Semua pengaturan ada di bagian atas `ghost_engine.py`.

| Variabel | Fungsi | Default |
| --- | --- | --- |
| `NAME` | Nama di header dan logo finale | `"GHOST ENGINE"` |
| `FPS` | Frame per detik | `30` |
| `BOOT, GLOBE, WIRE, TORUS, FINALE` | Durasi tiap fase (detik) | `6, 9, 7, 7, 6` |

Tips untuk `NAME`:

- Gunakan **dua kata** supaya logo tersusun dua baris, misalnya `"NAMA KAMU"`.
- Logo hanya mendukung huruf **A-Z**. Karakter lain (angka, simbol) ditampilkan sebagai ruang kosong.
- Jika terlalu lebar untuk terminal, logo otomatis dikecilkan.

Contoh mengubah urutan atau menghilangkan sebuah fase: atur durasinya mendekati `0`, misalnya `TORUS = 0.01`.

## Struktur kode

| Bagian | Isi |
| --- | --- |
| `Canvas` | Buffer dengan z-buffer untuk menggambar scene 3D |
| `Rain` | Efek hujan matrix |
| `Globe`, `render_wire`, `render_torus` | Renderer tiga scene |
| `Dash` | Layout tiga panel, header, dan footer |
| `draw_boot`, `draw_finale` | Layar penuh untuk awal dan akhir siklus |
| `Menu` | Menu OSINT: pilih tool, input target, jalankan di thread, tampilkan dan simpan hasil |
| `main` | Loop utama, timeline intro, dan penanganan tombol |
| Bagian `OSINT TOOLKIT` | Klien DNS UDP, WHOIS, HTTP, TLS, CT logs, dan daftar `TOOLS` |

## Pemecahan masalah

**Karakter blok atau garis tampil rusak (`?` atau kotak).**
Terminal belum memakai UTF-8. Jalankan dengan:
```bash
LC_ALL=en_US.UTF-8 python3 ghost_engine.py
```

**Warna tampak pudar atau tidak muncul.**
Pastikan `TERM` mendukung warna:
```bash
TERM=xterm-256color python3 ghost_engine.py
```

**Tampilan patah-patah atau lambat.**
Turunkan `FPS` ke `20`, atau perkecil jendela terminal. Scene torus paling berat karena menghitung ribuan titik per frame.

**Tool OSINT menampilkan galat jaringan.**
Pastikan ada koneksi internet dan port 53 (DNS) serta 43 (WHOIS) tidak diblokir firewall. Jaringan kantor atau kampus sering memblokir salah satunya.

**Tidak bisa menyeleksi teks dengan mouse.**
Itu efek dukungan mouse. Tahan `Shift` (atau `Option` di macOS) saat menyeleksi, atau gunakan tombol `s` untuk menyimpan hasil ke file.

**Muncul pesan "Perbesar terminal".**
Perbesar jendela sampai minimal 70x20 (disarankan 100x30).

**`ModuleNotFoundError: No module named '_curses'` di Windows.**
Jalankan `pip install windows-curses`.

## Tips merekam

Untuk membuat video seperti demo aslinya, gunakan terminal dengan latar gelap dan font monospace, lalu rekam jendela terminal dalam mode layar penuh. Tema gelap kebiruan membuat warna hijau dan cyan tampil lebih menonjol.
