# GHOST ENGINE // Terminal Visual Engine

Demo visual untuk terminal bergaya "hacker dashboard": hujan matrix, boot sequence, globe ASCII, wireframe 3D, torus, serta panel kode dan hex yang bergulir. Ditulis dalam satu file Python tanpa dependensi.

> **Catatan:** proyek ini murni kosmetik. Semua data (log, hex, "link", peta globe) adalah angka acak/simulasi. Tidak ada koneksi jaringan, tidak ada pemindaian, dan tidak ada akses ke sistem apa pun.

## Fitur

- **Boot sequence**: hujan matrix dengan kotak *Initialization Sequence* dan progress bar.
- **Globe ASCII** yang berputar, lengkap dengan cincin orbit dan garis link simulasi.
- **Wireframe 3D**: icosahedron dan kubus yang berputar berlawanan arah.
- **Torus (donut)** dengan shading karakter.
- **Panel kode** yang bergulir seperti sedang diketik.
- **Hex dump** yang berubah-ubah dan **log stream** simulasi.
- **Finale**: logo blok besar dari nama kamu di atas hujan matrix.
- Berulang otomatis dalam satu siklus sekitar 35 detik.

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
| `q` / `Q` | Keluar |
| `Esc` | Keluar |
| `Ctrl+C` | Keluar |

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
| `main` | Loop utama, timeline fase, dan penanganan tombol |

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

**Muncul pesan "Perbesar terminal".**
Perbesar jendela sampai minimal 70x20 (disarankan 100x30).

**`ModuleNotFoundError: No module named '_curses'` di Windows.**
Jalankan `pip install windows-curses`.

## Tips merekam

Untuk membuat video seperti demo aslinya, gunakan terminal dengan latar gelap dan font monospace, lalu rekam jendela terminal dalam mode layar penuh. Tema gelap kebiruan membuat warna hijau dan cyan tampil lebih menonjol.
