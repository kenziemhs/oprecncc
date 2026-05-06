# Laporan Pertemuan 3 NCC — Monitoring System dengan Prometheus & Grafana

Nama  : Kenzie Maheswara

NRP   : 5025241001

---

## Pendahuluan

Pada pertemuan ini, saya membangun sebuah sistem monitoring menggunakan **Prometheus** dan **Grafana** yang dideploy pada **Microsoft Azure**. Sistem monitoring ini berfungsi untuk mengumpulkan, menyimpan, serta memvisualisasikan metrics dari server target sehingga performa sistem dapat dipantau secara real-time.

Berbeda dari panduan utama yang menggunakan AWS EC2, saya memilih Azure sebagai cloud provider. Hal ini dimungkinkan karena Prometheus, Grafana, dan Node Exporter bersifat **cloud-agnostic**, sehingga arsitekturnya tetap sama persis. Yang berbeda hanyalah istilah layanannya:

| AWS              | Azure                          |
| ---------------- | ------------------------------ |
| EC2 Instance     | Virtual Machine (VM)           |
| Security Group   | Network Security Group (NSG)   |
| Key Pair (.pem)  | SSH Key Pair (.pem)            |

---

## Pengertian Komponen

### Prometheus

Prometheus adalah sistem monitoring open source yang berfungsi mengumpulkan dan menyimpan metrics dalam bentuk **time-series data**. Prometheus bekerja dengan metode **pull-based scraping**, yaitu Prometheus secara aktif menarik data dari endpoint target dalam interval waktu tertentu.

Karakteristik utama Prometheus:
- Berbasis pull (scraping)
- Menyimpan data dalam database time-series
- Mendukung query language sendiri (PromQL)
- Mendukung alerting via Alertmanager
- Ringan dan scalable

### Grafana

Grafana adalah tools open source untuk **visualisasi data**. Grafana tidak mengumpulkan atau menyimpan data, melainkan hanya berperan sebagai layer visualisasi yang terhubung ke data source seperti Prometheus.

Fungsi Grafana:
- Menampilkan metrics dari Prometheus dalam bentuk dashboard
- Membuat dashboard custom & interaktif
- Membuat alert berbasis threshold visual
- Mengirim notifikasi alert ke channel eksternal (Discord, Slack, Email, dll)

### Node Exporter

Node Exporter adalah exporter resmi dari ekosistem Prometheus untuk mengekspos metrics level sistem operasi (CPU, RAM, Disk, Network, dsb) melalui endpoint HTTP pada port `9100`.

---

## Arsitektur Sistem

```
        Internet
           |
         HTTPS
           |
   [VM-1: Grafana-Server]
       (Port 3000)
           |
     Private Network
           |
   [VM-2: Prometheus-Server]
       (Port 9090)
           |
     Scraping Metrics
           |
[Node Exporter di kedua VM (Port 9100)]
```

**Alur monitoring:**
1. **Node Exporter** berjalan pada masing-masing VM (Grafana & Prometheus) dan mengekspos metrics sistem pada port `9100`.
2. **Prometheus** melakukan scraping metrics dari Node Exporter setiap 15 detik dan menyimpannya sebagai time-series data.
3. **Grafana** terhubung ke Prometheus sebagai data source, lalu menampilkan metrics dalam bentuk dashboard custom.
4. Saat metrics melewati threshold tertentu, **alert** akan trigger dan dikirim ke channel notifikasi eksternal (Discord).

---

## Infrastruktur yang Digunakan

Project ini menggunakan **Microsoft Azure** sebagai cloud provider dengan dua Virtual Machine:

| VM                | Fungsi                            | Size            | OS                    |
| ----------------- | --------------------------------- | --------------- | --------------------- |
| Grafana-Server    | Visualisasi & dashboard           | Standard_B1s    | Ubuntu Server 22.04   |
| Prometheus-Server | Metrics collection & storage      | Standard_B1s    | Ubuntu Server 22.04   |

Kedua VM berada dalam satu **Resource Group** bernama `NCC-Monitoring-RG` di region **Southeast Asia**.

---

## Fase 1 — Persiapan Server & Jaringan

### 1. Membuat VM Grafana-Server

Langkah-langkah pembuatan VM Grafana di Azure Portal:
- Login ke `portal.azure.com`
- Search **Virtual Machines** → klik **Create** → **Azure virtual machine**
- Konfigurasi:
  - **Resource group**: `NCC-Monitoring-RG` (Create new)
  - **Virtual machine name**: `Grafana-Server`
  - **Region**: Southeast Asia
  - **Image**: Ubuntu Server 22.04 LTS
  - **Size**: Standard_B1s (Free tier eligible)
  - **Authentication type**: SSH public key
  - **Username**: `azureuser`
  - **SSH key source**: Generate new key pair → nama `kunci-ncc-azure`
  - **Inbound ports**: Allow SSH (22)
- Klik **Review + create** → **Create**
- Download private key (.pem) saat prompt muncul

### 2. Konfigurasi NSG Grafana

Tambahkan inbound port rule untuk akses Grafana dan monitoring:

| Port | Protocol | Source     | Name                    | Fungsi                |
| ---- | -------- | ---------- | ----------------------- | --------------------- |
| 22   | TCP      | Any        | Default-SSH             | Remote akses          |
| 3000 | TCP      | Any        | Allow-Grafana-3000      | Akses dashboard       |
| 9100 | TCP      | (Private)  | Allow-NodeExporter-9100 | Metrics Node Exporter |

<img width="1565" height="517" alt="image" src="https://github.com/user-attachments/assets/eedb0973-03a4-4ca3-9649-1270795099fd" />


### 3. Membuat VM Prometheus-Server

Ulangi proses pembuatan VM dengan ketentuan:
- **Resource group**: `NCC-Monitoring-RG` (gunakan yang sudah ada)
- **VM name**: `Prometheus-Server`
- **Image & Size**: sama (Ubuntu 22.04 LTS, Standard_B1s)
- **SSH key source**: **Use existing key stored in Azure** → pilih `kunci-ncc-azure`
- **Inbound ports**: SSH (22) saja

### 4. Konfigurasi NSG Prometheus

Catat **Private IP** dari Prometheus-Server, lalu tambahkan inbound rule:

| Port | Protocol | Source                  | Name                    |
| ---- | -------- | ----------------------- | ----------------------- |
| 22   | TCP      | Any                     | Default-SSH             |
| 9090 | TCP      | Private IP Grafana      | Allow-Prometheus-9090   |
| 9100 | TCP      | Private IP Grafana      | Allow-NodeExporter-9100 |

> **Note:** Port 9090 dibatasi hanya dari IP Grafana untuk alasan keamanan, agar Prometheus tidak ter-expose ke publik.

<img width="1563" height="521" alt="image" src="https://github.com/user-attachments/assets/079ffc14-cce5-4687-90a7-05d9521f15fe" />


### 5. SSH ke Kedua VM

```bash
# Ubah permission key
chmod 400 kunci-ncc-azure.pem

# SSH ke Grafana-Server
ssh -i "kunci-ncc-azure.pem" azureuser@PUBLIC_IP_GRAFANA

# SSH ke Prometheus-Server (terminal baru)
ssh -i "kunci-ncc-azure.pem" azureuser@PUBLIC_IP_PROMETHEUS

# Update kedua server
sudo apt update && sudo apt upgrade -y
```

<img width="688" height="561" alt="image" src="https://github.com/user-attachments/assets/f551213f-2035-450d-9807-af47d5f325d0" />

<img width="694" height="566" alt="image" src="https://github.com/user-attachments/assets/79f4924a-07d3-43b4-a7e1-1bc445ba855c" />


## Fase 2 — Instalasi Prometheus

Dilakukan pada **VM Prometheus-Server**.

### Download & Extract Prometheus

```bash
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.52.0/prometheus-2.52.0.linux-amd64.tar.gz

tar xvf prometheus-*.tar.gz
cd prometheus-*.linux-amd64
```

### Pindahkan Binary & Buat Folder Konfigurasi

```bash
sudo mv prometheus /usr/local/bin/
sudo mv promtool /usr/local/bin/

sudo mkdir /etc/prometheus
sudo mkdir /var/lib/prometheus

sudo cp prometheus.yml /etc/prometheus/

sudo useradd --no-create-home --shell /bin/false prometheus

sudo chown prometheus:prometheus /etc/prometheus
sudo chown prometheus:prometheus /var/lib/prometheus
```

### Buat Systemd Service

```bash
sudo nano /etc/systemd/system/prometheus.service
```

Isi dengan:

```ini
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus \
  --storage.tsdb.retention.time=3d \
  --web.listen-address=0.0.0.0:9090

[Install]
WantedBy=multi-user.target
```

### Jalankan Prometheus

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus
sudo systemctl status prometheus
```

---

## Fase 3 — Instalasi Node Exporter

Node Exporter di-install di **kedua VM** (Prometheus-Server & Grafana-Server) dengan langkah yang sama.

### Download & Setup

```bash
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v1.8.1/node_exporter-1.8.1.linux-amd64.tar.gz
tar xvf node_exporter-*.tar.gz
cd node_exporter-*.linux-amd64

sudo mv node_exporter /usr/local/bin/
sudo useradd --no-create-home --shell /bin/false node_exporter
```

### Buat Systemd Service

```bash
sudo nano /etc/systemd/system/node_exporter.service
```

Isi dengan:

```ini
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=default.target
```

### Jalankan Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
sudo systemctl status node_exporter
```

---

## Fase 4 — Konfigurasi Scraping Prometheus

Edit konfigurasi Prometheus di VM Prometheus-Server agar melakukan scraping ke kedua Node Exporter.

```bash
sudo nano /etc/prometheus/prometheus.yml
```

Isi konfigurasi:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "node"
    static_configs:
      - targets:
          - "localhost:9100"
          - "PRIVATE_IP_GRAFANA:9100"
```

Restart Prometheus:

```bash
sudo systemctl restart prometheus
sudo systemctl status prometheus
```

---

## Fase 5 — Instalasi Grafana

Dilakukan pada **VM Grafana-Server**.

### Install Prerequisite & Repository

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https wget gnupg

sudo mkdir -p /etc/apt/keyrings
sudo wget -O /etc/apt/keyrings/grafana.asc https://apt.grafana.com/gpg-full.key
sudo chmod 644 /etc/apt/keyrings/grafana.asc

echo "deb [signed-by=/etc/apt/keyrings/grafana.asc] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
```

### Install & Jalankan Grafana

```bash
sudo apt-get update
sudo apt-get install -y grafana

sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
sudo systemctl status grafana-server
```

Akses Grafana di browser:

```
http://PUBLIC_IP_GRAFANA:3000
```

Login default `admin / admin`, lalu set password baru.

<img width="1919" height="870" alt="image" src="https://github.com/user-attachments/assets/c4d66753-14a2-4754-8def-4c6d1d737fc0" />

---

## Fase 6 — Integrasi Grafana dengan Prometheus

1. Login Grafana → menu **Connections** → **Data sources**
2. Klik **Add data source** → pilih **Prometheus**
3. Pada bagian **Connection → URL**, masukkan:
   ```
   http://PRIVATE_IP_PROMETHEUS:9090
   ```
4. Klik **Save & test** → harus muncul "Successfully queried the Prometheus API"

<img width="1641" height="878" alt="image" src="https://github.com/user-attachments/assets/c29b25c9-ef12-4f05-9090-1d95e9280d63" />

---

## Fase 7 — Custom Dashboard Grafana

Sesuai requirement penugasan, dashboard dibuat secara **custom tanpa menggunakan template bawaan** (tidak menggunakan dashboard ID 1860 atau sejenisnya).

### Panel yang Dibuat

Berikut panel custom yang saya buat beserta query PromQL-nya:

#### 1. CPU Usage (%)

Menampilkan persentase CPU yang sedang digunakan (non-idle), menggunakan fungsi `rate()` untuk mendapatkan perubahan per detik:

```promql
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

#### 2. Memory Usage (%)

Menampilkan persentase pemakaian RAM:

```promql
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

#### 3. Disk Usage (%)

Menampilkan persentase pemakaian disk pada root filesystem:

```promql
100 - ((node_filesystem_avail_bytes{mountpoint="/"} * 100) / node_filesystem_size_bytes{mountpoint="/"})
```

<img width="769" height="308" alt="image" src="https://github.com/user-attachments/assets/44c1db0c-1a22-4743-b13e-2c74567d2f70" />

<img width="773" height="309" alt="image" src="https://github.com/user-attachments/assets/00ecf5b6-aa37-4258-8471-88febf7af633" />

---

## Fase 8 — Alerting & Notifikasi Discord (Poin Plus)

### Setup Contact Point Discord

1. Di Discord, masuk ke server → **Server Settings** → **Integrations** → **Webhooks** → **New Webhook**
2. Salin URL Webhook
3. Di Grafana: **Alerting** → **Contact points** → **Add contact point**
4. Konfigurasi:
   - **Name**: `Discord-Notif`
   - **Integration**: Discord
   - **Webhook URL**: paste URL Discord
5. Klik **Test** untuk memastikan notifikasi terkirim
6. **Save contact point**

<img width="1611" height="112" alt="image" src="https://github.com/user-attachments/assets/8b32afa5-e9ab-4bef-a4c3-37c37e6feae4" />


### Buat Alert Rule

Saya membuat alert rule untuk mendeteksi CPU usage tinggi:

- **Name**: `High CPU Usage Alert`
- **Query (PromQL)**:
  ```promql
  100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)
  ```
- **Condition**: `IS ABOVE 80`
- **Evaluation**: Setiap 1 menit
- **For**: 1 menit (alert hanya trigger jika kondisi bertahan ≥ 1 menit)

### Notification Policy

Routing default policy diarahkan ke contact point `Discord-Notif`.

<img width="1639" height="870" alt="image" src="https://github.com/user-attachments/assets/c65d6c9a-e3d4-43b6-b922-f7a5ddb9d029" />

---

## Fase 9 — Simulasi Anomali

Untuk menguji dashboard dan alerting, dilakukan stress test pada VM Grafana-Server:

```bash
sudo apt install stress -y
stress --cpu 2 --timeout 120
```

**Hasil yang teramati:**
- Panel CPU Usage di Grafana menunjukkan kenaikan signifikan hingga > 90%
- Setelah ~1 menit kondisi bertahan di atas threshold, alert ter-trigger
- Notifikasi otomatis terkirim ke channel Discord


<img width="1368" height="779" alt="image" src="https://github.com/user-attachments/assets/5c3e6222-4fd6-4e75-8191-ccb27eeb87d8" />

<img width="1353" height="129" alt="image" src="https://github.com/user-attachments/assets/ab049182-dcf0-4d60-bfe2-0d376e699069" />

<img width="1216" height="549" alt="image" src="https://github.com/user-attachments/assets/743aeee4-599b-4192-bb64-69d330526077" />


---

## Penjelasan Alur Monitoring End-to-End

```
[Node Exporter]  →  [Prometheus]  →  [Grafana Dashboard]
   (port 9100)        (port 9090)         (port 3000)
                                              ↓
                                        [Alert Rule]
                                              ↓
                                       [Contact Point]
                                              ↓
                                     [Discord Notification]
```

1. **Metrics Collection** — Node Exporter di setiap VM mengekspos metrics OS pada `:9100/metrics`.
2. **Scraping & Storage** — Prometheus scraping tiap 15 detik dan menyimpan sebagai time-series.
3. **Visualization** — Grafana query Prometheus via PromQL → render dashboard custom.
4. **Evaluation** — Grafana mengevaluasi alert rule berdasarkan query PromQL.
5. **Notification** — Jika alert trigger, notifikasi dikirim ke Discord via webhook.

---

## Kesimpulan

Sistem monitoring berbasis Prometheus & Grafana berhasil dibangun di atas Microsoft Azure dengan fitur lengkap meliputi:

- ✅ Multi-server monitoring (2 VM target)
- ✅ Custom Grafana dashboard tanpa template bawaan
- ✅ PromQL kompleks (`rate`, `avg by`, ekspresi aritmatika)
- ✅ Alerting system dengan threshold
- ✅ Integrasi notifikasi eksternal ke Discord
- ✅ Validasi melalui simulasi anomali (stress test)

Implementasi ini membuktikan bahwa stack Prometheus + Grafana + Node Exporter bersifat **cloud-agnostic** dan dapat dijalankan di berbagai cloud provider dengan arsitektur identik. Sistem ini siap digunakan sebagai fondasi observability untuk lingkungan production yang membutuhkan deteksi cepat dan respons proaktif terhadap masalah infrastruktur.

---

