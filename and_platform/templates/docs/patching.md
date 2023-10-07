File patch adalah file `tar`. Gunakan command berikut untuk menghasilkan file tar yang akan disubmit:

```
tar cvf patch.tar [patch_dir]
```

Platform akan melakukan file patching pada setiap container dengan command berikut:

```
tar -xmv --strip-components=1 -f {NAMA_PATCH_FILE} {NAMA_CONTAINER}
```

Melakukan patching memerlukan informasi berikut:

- Nama container  
  Dapat dilihat di `docker-compose.yml`, dalam atribut `container_name` atau nama dari service tersebut
- Base path  
  Dapat dilihat dari `Dockerfile` service tersebut, lihat path di mana source code diletakkan
  
Sebagai contoh, terdapat `docker-compose.yml` dan `Dockerfile` seperti berikut:
```yaml
version: '3'
services:
  web:
    build: src
    volumes:
    - "__FLAG_DIR__:/flag:ro"
    ports:
    - "__PORT__:3000"
```

```Dockerfile
FROM node:20-bookworm

WORKDIR /opt/app
COPY package.json .
RUN yarn install --production=true

COPY . .
RUN yarn build

ENTRYPOINT "yarn start"
```

Artinya container name adalah `web` dan base pathnya adalah `/opt/app`. Untuk melakukan patch, cukup membuat suatu file `.tar` yang memiliki struktur `<nama_container>/<base_path>`. Dalam kasus contoh, berarti strukturnya adalah `web/opt/app`. Di dalam folder tersebut, kamu dapat melakukan patching terhadap folder/file tersebut.

Apabila kamu ingin mengubah file `index.js` yang ada di dalam container tersebut, maka kamu dapat melakukannya dengan struktur seperti berikut:

```
web
 |--- opt
       |--- app
             |--- index.js
```

Selanjutnya buat file tar dari direktori tersebut menggunakan command:

```
tar cvf patch.tar web
```

Submit, lalu kamu telah melakukan patch terhadap service! Perlu diperhatikan bahwa terdapat whitelist dan blacklist untuk file-file yang dapat dipatch, dapat dilihat di file `patchrule.yml`.
  
> Apabila patch yang dilakukan adalah suatu binary, pastikan permission yang diberikan ke dalam tar sudah benar. Patcher tidak akan melakukan manage permission, sebab tar sudah memiliki kapabilitas untuk melakukan hal tersebut. Gagal melakukan hal ini dapat membuat service kamu tidak berjalan sama sekali.

### Log Patching
Beberapa log penting ketika melakukan patching:
- `[+] patch is valid`: Patch yang diunggah valid. Valid di sini hanya berarti patch yang diunggah sesuai format. Patch yang valid belum tentu 100% lolos checker.
- `[+] patch applied`: Patch yang diunggah telah diterapkan pada service.
- `[-] patching failed`: Patch yang dilakukan gagal dan tidak diterapkan pada service. Hal ini mungkin terjadi karena file patching yang diunggah mengandung path yang tidak diperbolehkan untuk dipatch atau terdapat internal error (silakan hubungi panitia jika mendapatkan internal error).