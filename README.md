[![Build Status](https://common-remodeler-strangle.ngrok-free.dev/buildStatus/icon?job=demo-jenkins-pipeline)](https://common-remodeler-strangle.ngrok-free.dev/job/demo-jenkins-pipeline/)

# Laporan CI/CD Pipeline — demo-jenkins

> **Oprec NCC 2026 — Pertemuan 2: CI/CD dengan Jenkins & SonarQube**

---

## Deskripsi Proyek

Repository `demo-jenkins` adalah aplikasi Go sederhana yang mengekspos endpoint `/health` untuk mengecek status service. Proyek ini digunakan sebagai bahan praktik implementasi pipeline CI/CD menggunakan **Jenkins** dan **SonarQube**, mencakup tahap build, test, analisis kualitas kode, dan Quality Gate.

### Struktur Proyek

```
demo-jenkins/
├── main.go          # Entry point aplikasi (HTTP server + health endpoint)
├── go.mod           # Go module definition (module: demo-jenkins, go 1.23.2)
└── Jenkinsfile      # Pipeline as Code (CI/CD definition)
```

### `main.go`

```go
package main

import (
    "encoding/json"
    "log"
    "net/http"
)

type HealthResponse struct {
    Status  string `json:"status"`
    Message string `json:"message"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
    response := HealthResponse{
        Status:  "OK",
        Message: "Service is healthy",
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(response)
}

func main() {
    http.HandleFunc("/health", healthHandler)
    log.Println("Server running on port", "8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

---

## Alur Pipeline (Flow CI/CD)

```
Developer Push Code (GitHub)
        │
        ▼  (Webhook trigger)
[Jenkins] Checkout Repository
        │
        ▼
[Docker: golang:1.23-bookworm]
  ├── Setup (go mod download)
  └── Parallel Execution
        ├── Build  → go build -v ./...
        └── Test   → go test ./... -v -coverprofile=coverage.out
        │
        ▼
[SonarQube Analysis]
  sonar-scanner → kirim hasil ke SonarQube Server
        │
        ▼
[Quality Gate Check]
  Passed ✅ → Pipeline sukses
  Failed ❌ → Pipeline digagalkan (abortPipeline: true)
```

---

## Persiapan & Instalasi

### 1. Setup Docker Network

```bash
docker network create jenkins
```

### 2. Jalankan Docker-in-Docker (DinD)

```bash
docker run \
  --name jenkins-docker \
  --rm --detach --privileged \
  --network jenkins \
  --network-alias docker \
  --env DOCKER_TLS_CERTDIR=/certs \
  --volume jenkins-docker-certs:/certs/client \
  --volume jenkins-data:/var/jenkins_home \
  --publish 2376:2376 \
  docker:dind \
  --storage-driver overlay2
```

### 3. Buat Custom Jenkins Image

Buat file `Dockerfile`:

```dockerfile
FROM jenkins/jenkins:2.541.3-jdk21
USER root
RUN apt-get update && apt-get install -y lsb-release ca-certificates curl && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
    https://download.docker.com/linux/debian $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && apt-get install -y docker-ce-cli && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
USER jenkins
RUN jenkins-plugin-cli --plugins "blueocean docker-workflow json-path-api"
```

Build dan jalankan:

```bash
docker build -t myjenkins-blueocean:2.541.3-1 .

docker run \
  --name jenkins-blueocean \
  --restart=on-failure --detach \
  --network jenkins \
  --env DOCKER_HOST=tcp://docker:2376 \
  --env DOCKER_CERT_PATH=/certs/client \
  --env DOCKER_TLS_VERIFY=1 \
  --publish 8090:8080 \
  --publish 50000:50000 \
  --volume jenkins-data:/var/jenkins_home \
  --volume jenkins-docker-certs:/certs/client:ro \
  myjenkins-blueocean:2.541.3-1
```

Akses Jenkins di `http://localhost:8090`.

### 4. Instalasi SonarQube

```bash
docker volume create --name sonarqube_data
docker volume create --name sonarqube_logs
docker volume create --name sonarqube_extensions

docker run -d --name sonarqube \
  -p 9000:9000 \
  -v sonarqube_data:/opt/sonarqube/data \
  -v sonarqube_extensions:/opt/sonarqube/extensions \
  -v sonarqube_logs:/opt/sonarqube/logs \
  sonarqube
```

Akses SonarQube di `http://localhost:9000`.

---

## Konfigurasi Integrasi

### Jenkins ↔ SonarQube

1. Install plugin **SonarQube Scanner** di Jenkins (Manage Jenkins → Plugins).
2. Install **SonarQube Scanner** tool di Manage Jenkins → Tools → SonarQube Scanner installations → beri nama `SonarScanner`.
3. Di SonarQube, buat token melalui **My Account → Security → Generate Token**.
4. Di Jenkins, tambahkan credential token tersebut (Secret Text).
5. Di Manage Jenkins → System → SonarQube servers, tambahkan koneksi dengan nama `SonarQube` dan masukkan URL serta credential token.
6. Di SonarQube, buat webhook ke Jenkins: **Administration → Configuration → Webhooks** → arahkan ke `http://<jenkins-url>/sonarqube-webhook/`.

### Jenkins ↔ GitHub

1. Buat **Personal Access Token** di GitHub dengan scope `repo` dan `admin:repo_hook`.
2. Tambahkan token ke Jenkins credentials (Secret Text).
3. Di Manage Jenkins → System → GitHub, tambahkan server GitHub dengan credential tersebut.
4. Di repository GitHub, tambahkan webhook: **Settings → Webhooks** → masukkan URL Jenkins `http://<jenkins-url>/github-webhook/` dengan Content type `application/json`.

---

## Pembuatan Job di Jenkins

1. Buka Jenkins → **New Item**.
2. Pilih nama job: `demo-jenkins-pipeline`, tipe: **Pipeline**.
3. Di bagian **Build Triggers**, centang **GitHub hook trigger for GITScm polling** (untuk webhook otomatis).
4. Di bagian **Pipeline**, pilih **Pipeline script from SCM**:
   - SCM: Git
   - Repository URL: `https://github.com/<username>/demo-jenkins.git`
   - Branch: `*/main` atau `*/pertemuan-2`
   - Script Path: `Jenkinsfile`
5. Klik **Save**.

---

## Jenkinsfile

Pipeline ini menggunakan **Declarative Pipeline** dengan fitur:
- Environment variable untuk konfigurasi SonarQube
- Docker agent untuk build/test (isolated, clean environment)
- **Parallel stage** untuk menjalankan Build dan Test secara bersamaan (optimasi waktu)
- SonarQube Analysis dengan `withSonarQubeEnv`
- Quality Gate dengan timeout 20 menit dan `abortPipeline: true`

```groovy
pipeline {
    agent any

    environment {
        SONARQUBE_ENV = 'SonarQube'
        PROJECT_KEY   = 'demo-jenkins'
        PROJECT_NAME  = 'demo-jenkins'
        SCANNER_HOME  = tool 'SonarScanner'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/kenziemhs/demo-jenkins.git'
            }
        }

        stage('Build and Test') {
            agent {
                docker {
                    image 'golang:1.23-bookworm'
                    args '-u root -e HOME=/tmp -e GOCACHE=/tmp/go-cache -e GOPATH=/tmp/go'
                    reuseNode true
                }
            }
            stages {
                stage('Setup') {
                    steps {
                        sh 'git config --global --add safe.directory ${WORKSPACE}'
                        sh 'go mod download'
                    }
                }
                stage('Parallel Execution') {
                    parallel {
                        stage('Build') {
                            steps {
                                sh 'go build -v ./...'
                            }
                        }
                        stage('Test') {
                            steps {
                                sh 'go test ./... -v -coverprofile=coverage.out'
                                sh 'chmod 777 coverage.out'
                            }
                        }
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv("${SONARQUBE_ENV}") {
                    sh """
                        ${SCANNER_HOME}/bin/sonar-scanner \
                          -Dsonar.projectKey=${PROJECT_KEY} \
                          -Dsonar.projectName=${PROJECT_NAME} \
                          -Dsonar.sources=. \
                          -Dsonar.go.coverage.reportPaths=coverage.out
                    """
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 20, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }

    post {
        success { echo 'Pipeline sukses' }
        failure { echo 'Pipeline gagal' }
    }
}
```

---

## Hasil Build Jenkins

<img width="1915" height="875" alt="image" src="https://github.com/user-attachments/assets/938fc24c-e94f-4daf-8b18-399a5c6a808e" />

<img width="1261" height="212" alt="image" src="https://github.com/user-attachments/assets/92e64eb7-808c-4c0b-9453-42459abc2c6b" />

Pipeline telah berjalan sebanyak **17 kali** dengan mayoritas sukses:

| Build | Status | Durasi |
|---|---|---|
| #16 | ✅ Sukses | 25 detik |
| #15 | ✅ Sukses | 23 detik |
| #14 | ✅ Sukses | 26 detik |
| #13 | ❌ Gagal | 0.66 detik |
| #12 | ❌ Gagal | 0.83 detik |
| #11 | ✅ Sukses | 32 detik |

Build gagal (#5, #6, #12, #13) disebabkan oleh error konfigurasi awal sebelum pipeline stabil.

---

## Penjelasan Integrasi Jenkins & SonarQube

Alur integrasi Jenkins dan SonarQube bekerja sebagai berikut:

1. **Jenkins** menjalankan `sonar-scanner` di stage `SonarQube Analysis` menggunakan `withSonarQubeEnv` untuk meng-inject URL dan token SonarQube secara otomatis dari credential yang telah dikonfigurasi.
2. `sonar-scanner` menganalisis kode sumber dan coverage report (`coverage.out`) lalu mengirim hasilnya ke **SonarQube Server**.
3. SonarQube memproses hasil analisis dan mengevaluasi **Quality Gate**.
4. SonarQube mengirim notifikasi hasil Quality Gate ke Jenkins melalui **webhook**.
5. Jenkins menerima notifikasi di stage `Quality Gate` → jika gagal, pipeline dihentikan (`abortPipeline: true`).

---

## Fitur yang Diimplementasikan

| Fitur | Keterangan |
|---|---|
| Jenkins Pipeline (Jenkinsfile) | Pipeline didefinisikan sebagai kode dalam `Jenkinsfile` menggunakan **Declarative Pipeline** syntax, disimpan di repository sehingga bisa di-version control bersama kode aplikasi. |
| Stage terstruktur (Checkout, Build, Test, Analyze, Quality Gate) | Pipeline terdiri dari 4 stage utama: `Checkout` (clone repo), `Build and Test` (kompilasi + unit test), `SonarQube Analysis` (kirim hasil analisis), dan `Quality Gate` (validasi standar kualitas). |
| Parallel stage (Build + Test berjalan bersamaan) | Di dalam stage `Build and Test`, sub-stage `Build` (`go build -v ./...`) dan `Test` (`go test ./... -v -coverprofile=coverage.out`) dijalankan secara **paralel** menggunakan blok `parallel {}`, menghemat waktu eksekusi pipeline. |
| Integrasi SonarQube + Quality Gate | Stage `SonarQube Analysis` menjalankan `sonar-scanner` dengan `withSonarQubeEnv` untuk mengirim hasil analisis dan coverage report (`coverage.out`) ke SonarQube. Stage `Quality Gate` kemudian menunggu keputusan dari SonarQube via webhook — jika gagal, pipeline otomatis dihentikan (`abortPipeline: true`). |
| Webhook GitHub (trigger otomatis saat push) | Jenkins dikonfigurasi dengan **GitHub webhook** sehingga setiap `git push` ke repository akan otomatis men-trigger pipeline tanpa perlu manual build. |
| Environment variable & credential management | Konfigurasi sensitif seperti nama SonarQube server, project key, dan lokasi scanner dikelola melalui blok `environment {}` di Jenkinsfile (`SONARQUBE_ENV`, `PROJECT_KEY`, `SCANNER_HOME`), sementara token SonarQube disimpan sebagai **Jenkins Credentials** dan di-inject otomatis via `withSonarQubeEnv`. |
| Build status badge di README | README menampilkan badge status build Jenkins secara real-time menggunakan URL: `https://<jenkins-url>/buildStatus/icon?job=demo-jenkins-pipeline`. |
| Docker agent (isolated build environment) | Stage `Build and Test` menggunakan Docker image `golang:1.23-bookworm` sebagai agent (`agent { docker { image '...' } }`), memastikan build berjalan di environment yang bersih dan konsisten tanpa perlu Go terinstall di mesin Jenkins. |
---

## Kendala yang Dihadapi

- **Build #5, #6 (1 day 19hr ago)**: Pipeline gagal pada tahap awal karena konfigurasi `DOCKER_HOST` belum terhubung dengan benar ke DinD container. Diselesaikan dengan memastikan network alias `docker` sudah tersedia.
- **Build #12, #13**: Gagal karena credential SonarQube belum dikonfigurasi ulang setelah reset container. Diselesaikan dengan menambahkan ulang token di Jenkins credentials.
- **Coverage "Not computed"**: SonarQube tidak menghitung coverage karena file `coverage.out` membutuhkan permission yang sesuai — diatasi dengan `chmod 777 coverage.out` setelah test.

---
