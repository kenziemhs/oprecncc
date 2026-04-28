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
        success {
            echo 'Pipeline sukses'
        }
        failure {
            echo 'Pipeline gagal'
        }
    }
}
