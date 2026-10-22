pipeline {

    agent {
        label 'docker-agent'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
    }

    environment {
        IMAGE_NAME = 'romeo2296/jenkinslab'
        DOCKERHUB_CREDENTIALS_ID = 'dockerhub-credentials'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm

                script {
                    env.IMAGE_TAG = sh(
                        script: 'git rev-parse --short=12 HEAD',
                        returnStdout: true
                    ).trim()

                    env.SMOKE_CONTAINER = "jenkins-smoke-${env.BUILD_NUMBER}"

                    echo "Commit: ${env.IMAGE_TAG}"
                }
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    python3 -m venv .venv

                    .venv/bin/python -m pip install \
                        -r requirements.txt

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
                    set -eu

                    : "${IMAGE_TAG:?IMAGE_TAG is empty}"

                    docker buildx build \
                        --load \
                        --label "org.opencontainers.image.revision=$(git rev-parse HEAD)" \
                        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
                        -t "${IMAGE_NAME}:latest" \
                        .
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    docker run -d \
                        --name "${SMOKE_CONTAINER}" \
                        "${IMAGE_NAME}:${IMAGE_TAG}"

                    python3 - <<'PY'
                    import os
                    import subprocess
                    import time

                    container = os.environ["SMOKE_CONTAINER"]

                    for attempt in range(1, 16):
                        result = subprocess.run(
                            [
                                "docker", "exec", container,
                                "python", "-c",
                                (
                                    "import urllib.request; "
                                    "r = urllib.request.urlopen("
                                    "'http://127.0.0.1:8000/health', timeout=3); "
                                    "assert r.status == 200"
                                )
                            ],
                            capture_output=True,
                            text=True
                        )

                        if result.returncode == 0:
                            print("Smoke test passed!", flush=True)
                            break

                        print(
                            f"Attempt {attempt}: {result.stderr.strip()}",
                            flush=True
                        )
                        time.sleep(2)
                    else:
                        raise SystemExit("Smoke test failed!")
                    PY
                '''
            }
        }

        stage('Publish') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: env.DOCKERHUB_CREDENTIALS_ID,
                        usernameVariable: 'DOCKERHUB_USERNAME',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu

                        export DOCKER_CONFIG="$WORKSPACE/.docker"
                        mkdir -p "$DOCKER_CONFIG"
                        chmod 700 "$DOCKER_CONFIG"

                        printf '%s' "$DOCKERHUB_TOKEN" |
                            docker login \
                                --username "$DOCKERHUB_USERNAME" \
                                --password-stdin

                        docker push "${IMAGE_NAME}:${IMAGE_TAG}"
                        docker push "${IMAGE_NAME}:latest"

                        docker logout
                    '''
                }
            }
        }
    }

    post {

        always {
            junit testResults: 'reports/results.xml',
                  allowEmptyResults: true

            echo 'Cleaning temporary resources...'

            sh '''
                docker rm -f "${SMOKE_CONTAINER}" \
                    2>/dev/null || true

                if [ -n "${IMAGE_TAG}" ]; then
                    docker rmi "${IMAGE_NAME}:${IMAGE_TAG}" \
                        2>/dev/null || true

                    docker rmi "${IMAGE_NAME}:latest" \
                        2>/dev/null || true
                fi

                rm -rf "$WORKSPACE/.docker"
            '''
        }

        success {
            echo "Image published: ${env.IMAGE_NAME}:${env.IMAGE_TAG}"
        }

        failure {
            echo 'CI pipeline failed!'
        }
    }
}