pipeline {

    agent {
        label 'docker-agent'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        IMAGE_NAME = 'romeo2296/jenkinslab'
        DOCKERHUB_CREDENTIALS_ID = 'dockerhub-credentials'
        CONTAINER_NAME = 'python-lab-app'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Tests') {
            steps {
                sh '''
                    mkdir -p reports

                    .venv/bin/python -m pytest \
                        -v \
                        --junitxml=reports/results.xml
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build \
                        -t ${IMAGE_NAME}:${BUILD_NUMBER} \
                        -t ${IMAGE_NAME}:latest \
                        .
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker rm -f ${CONTAINER_NAME} 2>/dev/null || true

                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        --restart unless-stopped \
                        -p 8000:8000 \
                        ${IMAGE_NAME}:${BUILD_NUMBER}
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    .venv/bin/python - <<'PY'
import time
import urllib.request

url = "http://docker-dind:8000/health"

for attempt in range(1, 16):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            if response.status == 200:
                print("Application is healthy!")
                break
    except Exception as error:
        print(f"Attempt {attempt}: {error}")

    time.sleep(2)
else:
    raise SystemExit("Health check failed!")
PY
                '''
            }
        }

        stage('Publish') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: env.DOCKERHUB_CREDENTIALS_ID,
                    usernameVariable: 'DOCKERHUB_USERNAME',
                    passwordVariable: 'DOCKERHUB_TOKEN'
                )]) {
                    sh '''
                        trap 'docker logout >/dev/null 2>&1 || true' EXIT

                        printf '%s' "$DOCKERHUB_TOKEN" | docker login \
                            --username "$DOCKERHUB_USERNAME" \
                            --password-stdin

                        docker push ${IMAGE_NAME}:${BUILD_NUMBER}
                        docker push ${IMAGE_NAME}:latest
                    '''
                }
            }
        }

        stage('Cleanup') {
            steps {
                sh '''
                    docker stop ${CONTAINER_NAME} || true
                    docker rm ${CONTAINER_NAME} || true
                    docker rmi ${IMAGE_NAME}:${BUILD_NUMBER} || true
                    docker rmi ${IMAGE_NAME}:latest || true
                    docker system prune -f
                    docker volume prune -f
                    docker network prune -f
                '''
            }
        }
    }

    post {

        always {
            junit testResults: 'reports/results.xml',
                  allowEmptyResults: true
        }

        success {
            echo 'CI/CD pipeline completed successfully!'
        }

        failure {
            echo 'CI/CD pipeline failed!'
        }
    }
}