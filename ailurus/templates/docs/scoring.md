Scoring dibagi menjadi tiga, yaitu:
- Attack
- Defend
- SLA

### Attack

Scoring dari attribut attack untuk satu flag adalah seperti berikut:

$$attack = \sqrt{\frac{1}{otherTeamCaptures}} * motivation$$

Agar penilaian menjadi lebih dinamis, terdapat atribut `motivation`, yang berjalan apabila attacker dari service tersebut berada di posisi lebih rendah dari pemilik service yang diserang.

$$motivation = \frac{\Delta leaderboard}{teams - 1}$$

Nilai attack untuk satu flag dijamin berada di range $[1, inf)$. Nilai attack untuk setiap flag akan dijumlahkan.

### Defense

Scoring dari attribut defense untuk satu service adalah seperti berikut:

$$defense = \sqrt{ \frac{ teams - 1 - otherTeamCaptures + services * SLA }{teams - 1 + services} }$$

Secara esensi, cukup melihat berapa banyak tim lain yang telah mengambil flagmu, dan juga SLA dari servicemu. Perkalian dengan jumlah service disini untuk adanya balance antara SLA dan jumlah tim yang bermain.

Nilai defense untuk satu service dijamin berada di range $[0, 1]$. Nilai defense untuk setiap service akan dijumlahkan.

### SLA

Scoring dari attribut defense untuk satu service adalah seperti berikut:

$$SLA = \frac{numValid}{numValid+numFaulty}$$

Nilai SLA untuk satu service dijamin berada di range $[0, 1]$. Nilai SLA untuk setiap service akan dijumlahkan.

### Total Score

Total score hanya akan menjumlah nilai attack, defense, dan SLA.