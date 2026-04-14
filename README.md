# Laporan Penugasan Oprec NCC 2026 – Deployment Service `/health` dengan Docker di Azure VM

## Identitas Penugasan

Penugasan ini bertujuan untuk membuat sebuah service sederhana yang memiliki endpoint `/health`, menjalankannya menggunakan Docker, lalu mendeploy service tersebut ke Virtual Machine (VPS) agar dapat diakses secara publik.

Pada implementasi ini, service dibuat menggunakan **FastAPI** dengan dua endpoint utama:

- `/` untuk memastikan service berjalan
- `/health` untuk kebutuhan health check

Deployment dilakukan menggunakan **Docker** dan **Docker Compose**, kemudian service dijalankan pada **Azure Virtual Machine** dengan port publik **8080**.

---

## 1. Deskripsi Singkat Service

Service yang dibuat adalah API sederhana berbasis FastAPI. Endpoint root (`/`) mengembalikan pesan bahwa service sedang berjalan, sedangkan endpoint `/health` digunakan untuk memeriksa status kesehatan service. Endpoint `/health` mengembalikan HTTP status `200` dengan response JSON:

```json
{
  "status": "success",
  "message": "200 OK"
}
```

Implementasi endpoint tersebut terdapat pada file `app.py`, dengan dependency utama `fastapi` dan `uvicorn`. File `requirements.txt` hanya berisi dua package tersebut agar service tetap ringan dan sederhana.  

---

## 2. Struktur File

Berikut file-file yang digunakan pada penugasan ini:

```bash
.
├── app.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .dockerignore
```

Penjelasan singkat:
- `app.py` berisi source code API FastAPI
- `requirements.txt` berisi dependency Python
- `Dockerfile` digunakan untuk membangun image Docker
- `docker-compose.yml` digunakan untuk menjalankan container dengan konfigurasi yang lebih rapi
- `.dockerignore` digunakan untuk mengecualikan file yang tidak perlu ikut ke build context

---

## 3. Implementasi Aplikasi

### 3.1 Source Code API

Aplikasi dibuat menggunakan FastAPI. Berikut perilaku endpoint yang diimplementasikan:

- `GET /` mengembalikan:
  ```json
  {"message": "Service is running!"}
  ```

- `GET /health` mengembalikan:
  ```json
  {"status":"success","message":"200 OK"}
  ```

Endpoint `/health` inilah yang menjadi inti dari penugasan karena digunakan untuk membuktikan bahwa service aktif dan dapat diakses secara publik.

### 3.2 Dependency

Dependency pada project ini dibuat sesederhana mungkin, yaitu:

```txt
fastapi
uvicorn
```

Pemilihan dependency yang minimal membuat image lebih ringan, proses build lebih cepat, dan konfigurasi menjadi lebih sederhana.

---

## 4. Pembuatan Dockerfile

Agar service dapat dijalankan secara konsisten di berbagai environment, dibuat sebuah `Dockerfile`.

```dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Penjelasan langkah per langkah:

#### a. Menentukan base image
```dockerfile
FROM python:3.10-slim
```
Saya menggunakan `python:3.10-slim` karena image ini lebih ringan dibanding image Python biasa, sehingga ukuran image dapat lebih kecil.

#### b. Mengatur environment variable
```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```
- `PYTHONDONTWRITEBYTECODE=1` mencegah Python membuat file `.pyc`
- `PYTHONUNBUFFERED=1` memastikan output log langsung muncul tanpa buffering

#### c. Menentukan working directory
```dockerfile
WORKDIR /app
```
Semua proses di dalam container akan dijalankan dari direktori `/app`.

#### d. Menyalin file dependency
```dockerfile
COPY requirements.txt .
```
File dependency disalin terlebih dahulu agar proses caching Docker lebih optimal.

#### e. Menginstall dependency
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```
Dependency diinstall tanpa cache agar ukuran image tidak membengkak gara-gara sisa-sisa yang tidak diundang.

#### f. Menyalin source code
```dockerfile
COPY . .
```
Semua source code project disalin ke dalam working directory container.

#### g. Mengekspos port container
```dockerfile
EXPOSE 8000
```
Aplikasi di dalam container berjalan pada port `8000`.

#### h. Menambahkan health check
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```
Instruction ini digunakan agar Docker dapat melakukan pengecekan otomatis apakah endpoint `/health` di dalam container masih merespons dengan baik.

#### i. Menjalankan aplikasi
```dockerfile
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```
Perintah ini menjalankan FastAPI menggunakan Uvicorn agar service dapat menerima request dari luar container.

---

## 5. Optimasi Build Context dengan `.dockerignore`

Agar proses build lebih efisien, saya menambahkan file `.dockerignore`:

```dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
.env
.vscode/
Dockerfile
docker-compose.yml
```

Fungsi `.dockerignore` adalah mencegah file atau folder yang tidak diperlukan ikut dikirim ke Docker build context. Ini membantu mempercepat proses build dan membuat image lebih bersih.

---

## 6. Menjalankan Service dengan Docker Compose

Selain menggunakan `docker run`, saya juga menggunakan `docker-compose.yml` agar konfigurasi container lebih rapi.

```yaml
version: '3.8'

services:
  api-service:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: oprec_service_backend
    ports:
      - "8080:8000"
    restart: always
```

### Penjelasan:
- `api-service` adalah nama service
- `build.context: .` berarti Docker build dilakukan dari folder project saat ini
- `dockerfile: Dockerfile` menunjukkan file Dockerfile yang digunakan
- `container_name: oprec_service_backend` memberi nama container secara eksplisit
- `ports: "8080:8000"` berarti port `8080` pada host diarahkan ke port `8000` pada container
- `restart: always` membuat container otomatis mencoba aktif kembali saat berhenti atau saat VM reboot

---

## 7. Step by Step Build dan Run di Lokal

Berikut langkah-langkah yang dilakukan dari awal hingga service berjalan secara lokal.

### 7.1 Menyiapkan folder project
Pastikan file berikut ada dalam satu folder:

- `app.py`
- `requirements.txt`
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

### 7.2 Build image Docker
Jalankan perintah berikut:

```bash
docker compose build
```

Perintah ini akan:
1. Membaca konfigurasi dari `docker-compose.yml`
2. Membaca instruksi dari `Dockerfile`
3. Mengunduh base image `python:3.10-slim`
4. Menginstall dependency dari `requirements.txt`
5. Membuat image baru untuk service API

### 7.3 Menjalankan container
Setelah build selesai, jalankan:

```bash
docker compose up -d
```

Opsi `-d` berarti container berjalan di background.

### 7.4 Memastikan container berjalan
Untuk mengecek container yang aktif:

```bash
docker ps
```

Jika berhasil, akan terlihat container dengan nama `oprec_service_backend` dan mapping port `0.0.0.0:8080->8000/tcp`.

### 7.5 Menguji endpoint secara lokal
Coba akses:

```bash
curl http://localhost:8080/health
```

Jika berhasil, response yang muncul adalah:

```json
{"status":"success","message":"200 OK"}
```

Kita juga bisa membuka di browser:

```text
http://localhost:8080/health
```

---

## 8. Proses Deployment ke Azure Virtual Machine melalui Azure Portal

Pada tahap deployment, service dipindahkan dari environment lokal ke **Microsoft Azure Virtual Machine** agar endpoint dapat diakses secara publik. Pada implementasi ini, proses pembuatan server dilakukan melalui **Azure Portal**, lalu aplikasi dijalankan di dalam VM menggunakan Docker Compose.

### 8.1 Langkah 1: Pembuatan Virtual Machine (VM)

Langkah pertama adalah membuat server virtual di Azure.

1. Masuk ke **Azure Portal**
2. Pilih menu **Create a resource** lalu pilih **Virtual Machine**
3. Pada tab **Basics**, lakukan konfigurasi berikut:

#### Project Details
- Pilih **Subscription**
- Pilih **Resource Group** atau buat baru jika belum ada

#### Instance Details
- **Virtual machine name**: `vm-oprec-ncc`
- **Region**: **(Asia Pacific) Southeast Asia (Singapore)**  
  Region ini dipilih karena paling dekat dengan Indonesia sehingga latensi akses lebih baik
- **Availability options**: `No infrastructure redundancy required`
- **Security type**: `Standard`
- **Image**: `Ubuntu Server 24.04 LTS - x64 Gen 1`
- **Size**: `Standard_D2s_v3 (2 vCPUs, 8 GiB memory)`

#### Administrator Account
- **Authentication type**: `Password`
- Masukkan **username** dan **password** yang kuat  
  Kredensial ini nantinya digunakan saat login ke server melalui SSH

4. Setelah semua konfigurasi selesai, klik **Review + create**
5. Jika validasi berhasil, klik **Create**
6. Tunggu proses deployment VM selesai, lalu klik **Go to resource**

Dengan langkah ini, Azure akan menyediakan sebuah server Linux berbasis Ubuntu yang memiliki public IP dan siap digunakan sebagai host aplikasi.

### 8.2 Langkah 2: Konfigurasi Network Security Group (Membuka Port 8080)

Agar aplikasi dapat diakses dari browser atau internet publik, port `8080` harus dibuka pada firewall Azure.

Langkah-langkahnya:

1. Masuk ke halaman VM yang sudah dibuat
2. Pilih menu **Networking** pada sidebar kiri
3. Klik **Add inbound port rule**
4. Isi konfigurasi sebagai berikut:

- **Source port ranges**: `*`
- **Destination port ranges**: `8080`
- **Protocol**: `Any` atau `TCP`
- **Action**: `Allow`
- **Priority**: `310` atau biarkan default
- **Name**: `Allow_8080`

5. Klik **Add**

Setelah rule ini ditambahkan, request dari luar dapat masuk ke VM melalui port `8080`.

### 8.3 Langkah 3: Akses Server via SSH

Setelah VM aktif, langkah berikutnya adalah masuk ke server melalui SSH.

1. Buka terminal pada laptop, misalnya:
   - WSL
   - Command Prompt
   - PowerShell
   - Terminal Linux/macOS

2. Lihat **Public IP Address** pada halaman **Overview** VM di Azure

3. Login ke server dengan perintah:

```bash
ssh <username_kamu>@<ip_public_azure>
```

4. Masukkan password saat diminta

Contoh:

```bash
ssh azureuser@104.43.112.52
```

Jika login berhasil, berarti kita sudah masuk ke shell Ubuntu di Azure VM dan siap melakukan deployment aplikasi.

### 8.4 Langkah 4: Instalasi Docker dan Environment

Setelah berhasil masuk ke server, instal tools yang dibutuhkan untuk menjalankan aplikasi berbasis container.

#### a. Update sistem
```bash
sudo apt update && sudo apt upgrade -y
```

Perintah ini digunakan untuk memperbarui package list dan memastikan sistem dalam kondisi terbaru.

#### b. Install Docker, Docker Compose, dan Git
```bash
sudo apt install docker.io docker-compose-v2 git -y
sudo systemctl enable --now docker
```

Penjelasan:
- `docker.io` digunakan untuk menjalankan container
- `docker-compose-v2` digunakan untuk menjalankan konfigurasi multi-service dengan `docker compose`
- `git` digunakan untuk mengambil source code dari GitHub
- `systemctl enable --now docker` digunakan agar service Docker langsung aktif dan otomatis menyala saat server reboot

### 8.5 Langkah 5: Cloning Repository dan Menjalankan Aplikasi

Setelah environment siap, source code aplikasi dapat diambil dari GitHub.

#### a. Clone repository
```bash
git clone https://github.com/kenziemhs/oprecncc.git
cd oprecncc
```

#### b. Jalankan aplikasi dengan Docker Compose
```bash
sudo docker compose up -d --build
```

Perintah ini akan:
1. Membaca file `docker-compose.yml`
2. Melakukan build image berdasarkan `Dockerfile`
3. Menjalankan container di background
4. Membuat service aktif pada port yang sudah dikonfigurasi

#### c. Pastikan container berjalan
```bash
sudo docker ps
```

Jika berhasil, akan muncul container aktif dengan port mapping ke host, misalnya `8080->8000`.

### 8.6 Langkah 6: Verifikasi Hasil Deployment

Setelah container berjalan, aplikasi bisa diuji langsung dari browser pada laptop.

Buka alamat berikut:

```text
http://<IP_PUBLIC_AZURE>:8080/health
```

Contoh:

```text
http://104.43.112.52:8080/health
```

Jika deployment berhasil, maka endpoint akan menampilkan response:

```json
{"status":"success","message":"200 OK"}
```

Respons tersebut menunjukkan bahwa:
- aplikasi berhasil dijalankan di Azure VM
- Docker container aktif
- port `8080` berhasil dibuka
- endpoint `/health` dapat diakses secara publik dari internet


## 9. Bukti Endpoint Dapat Diakses Publik

Setelah deployment berhasil, endpoint `/health` dapat diakses menggunakan public IP Azure VM pada port `8080`.

Contoh akses publik:

```text
http://104.43.112.52:8080/health
```

Berdasarkan hasil pengujian, endpoint menampilkan response:

```json
{"status":"success","message":"200 OK"}
```

Hal ini menunjukkan bahwa:
1. Service berjalan dengan baik di dalam container
2. Port mapping Docker berjalan dengan benar
3. Port inbound Azure VM sudah terbuka
4. Endpoint dapat diakses secara publik melalui internet


<img width="946" height="267" alt="image" src="https://github.com/user-attachments/assets/79239bcc-cf2d-40ed-8720-e676a9a32515" />

---

