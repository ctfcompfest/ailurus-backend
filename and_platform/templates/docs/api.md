### Informasi Umum
Host yang digunakan untuk mengakses API platform adalah `https://and-be.rorre.me`. Seluruh request dan response body API menggunakan format JSON. Pastikan Anda telah menyesuaikan konfigurasi dengan tepat.

### Submit Flags
API ini digunakan untuk melakukan submit atas flag yang berhasil dicuri dari diri sendiri ataupun tim lain. Perlu diingat kembali bahwa sebuah flag hanya berlaku pada tick tersebut.

Kirim POST-request ke endpoint `/api/v1/submit`. Body dari request haruslah memiliki format sebuah entri `flags` yang berisi array dari flag yang akan disubmit. Perlu diperhatikan bahwa maksimal 100 flag yang dapat disubmit dalam sebuah request. Autentikasi melalui JWT team diperlukan untuk dapat mengaksek API ini.

Contoh request:
```
curl -H 'Content-Type: application/json' -H 'Authentication: Bearer <team JWT>' \
    -X POST --data '{"flags": ["COMPFEST15{incorrect}", "COMPFEST15{expired}", "COMPFEST15{siwlzc8}", "COMPFEST15{siwlzc8}"]}' \
    https://and-be.rorre.me/api/v1/submit
```

Contoh response:
```
{
    "data": [
        {
            "flag": "COMPFEST15{incorrect}",
            "verdict": "flag is wrong or expired."
        },
        {
            "flag": "COMPFEST15{expired}",
            "verdict": "flag is wrong or expired."
        },
        {
            "flag": "COMPFEST15{siwlzc8}",
            "verdict": "flag is correct."
        },
        {
            "flag": "COMPFEST15{siwlzc8}",
            "verdict": "flag already submitted."
        }
    ],
    "status": "success"
}
```

### List Challenges
API ini digunakan untuk melihat daftar challenge yang ada.

Kirim GET-request ke endpoint `/api/v1/challenges`.

Contoh request:
```
curl https://and-be.rorre.me/api/v1/challenges
```

Contoh response:
```
{
    "data": [
        {
            "id": 1,
            "name": "Calc"
        },
        {
            "id": 2,
            "name": "Morse"
        }
    ],
    "status": "success"
}
```

### List Teams
API ini digunakan untuk melihat daftar team yang ada.

Kirim GET-request ke endpoint `/api/v1/teams`.

Contoh request:
```
curl https://and-be.rorre.me/api/v1/teams
```

Contoh response:
```
{
    "data": [
        {
            "id": 10,
            "name": "Love of my life"
        },
        {
            "id": 11,
            "name": "Easy come easy go"
        }
    ],
    "status": "success"
}
```

### List Services
API ini digunakan untuk melihat daftar alamat service dari setiap challenge milik setiap tim yang ada. Alamat service ini nantinya akan digunakan untuk melakukan attack.

Kirim GET-request ke endpoint `/api/v1/services`.

Contoh request:
```
curl https://and-be.rorre.me/api/v1/services
```

Contoh response:
```
{
    "data": {
        "1": { // "1" is challenge's id from list challenges endpoint
            "10": [ // "10" is team's id from list teams endpoint
                "10.0.0.4:50101"
            ],
            "11": ["10.0.0.5:50101"]
        },
        "2": {
            "10": ["10.0.0.4:50101"],
            "11": ["10.0.0.5:50101"]
        }
    },
    "status": "success"
}
```