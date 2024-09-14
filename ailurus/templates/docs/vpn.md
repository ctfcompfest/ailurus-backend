### Linux
- Pastikan sudah mengunduh wireguard melalui package manager (i.e. apt, yum).
- Pindahkan file `*.conf` ke folder `/etc/wireguard`. Pastikan panjang nama file konfigurasi tidak lebih dari 10 karakter.
- Jalankan `sudo wg-quick up <nama-file-tanpa-.conf>`.
  Misalkan nama file konfigurasi yang telah Anda pindahkan adalah `user5.client.conf`, maka jalankan `sudo wg-quick up user5.client`.
- Pastikan tidak ada error. Untuk Kali linux, kemungkinan Anda akan menemukan error `resolvconf: command not found`, silakan ikuti [tutorial berikut](https://superuser.com/questions/1500691/usr-bin-wg-quick-line-31-resolvconf-command-not-found-wireguard-debian).
- Untuk mematikan koneksi VPN, jalankan `sudo wg-quick down <nama-file-tanpa-.conf>`.
- Untuk mengecek koneksi VPN, jalankan `sudo wg` dan seharusnya Anda menemukan interface dengan nama sesuai file konfigurasi.

### Windows
- Unduh wireguard untuk windows.
- Lakukan import pada file `*.conf`.
- Klik tombol "Activate" untuk menjalankan VPN.