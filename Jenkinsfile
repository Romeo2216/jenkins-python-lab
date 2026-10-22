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

        stage('Update GitOps') {
            steps {
                dir('gitops') {

                    // Récupérer le dépôt GitOps
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: '*/main']],
                        userRemoteConfigs: [[
                            url: 'https://github.com/romeo2216/jenkinslab-gitops.git',
                            credentialsId: 'github-gitops-credentials'
                        ]]
                    ])

                    // Modifier le tag et publier le commit
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'github-gitops-credentials',
                            usernameVariable: 'GITOPS_USERNAME',
                            passwordVariable: 'GITOPS_TOKEN'
                        )
                    ]) {
                        sh '''
                            set -eu
                            set +x

                            : "${IMAGE_TAG:?Missing image tag}"

                            echo "Updating GitOps to image: ${IMAGE_NAME}:${IMAGE_TAG}"

                            # Sécuriser la valeur utilisée dans le YAML
                            printf '%s' "$IMAGE_TAG" |
                                grep -Eq '^[0-9a-f]{12}$'

                            FILE="environments/dev/kustomization.yaml"

                            test -f "$FILE"

                            # Vérifier qu'une seule entrée newTag existe
                            COUNT=$(grep -Ec '^[[:space:]]*newTag:' "$FILE")
                            test "$COUNT" -eq 1

                            # Mettre à jour le tag
                            sed -i -E \
                                "s/^([[:space:]]*newTag:).*/\\\\1 \\"${IMAGE_TAG}\\"/" \
                                "$FILE"

                            # Préparer le commit
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@localhost"

                            git add "$FILE"

                            # Éviter les commits inutiles
                            if git diff --cached --quiet; then
                                echo "GitOps already uses this image."
                                exit 0
                            fi

                            git commit -m "ci: deploy ${IMAGE_TAG} to dev"

                            # Authentification Git sans token dans l'URL
                            ASKPASS=$(mktemp)
                            chmod 700 "$ASKPASS"

                            trap 'rm -f "$ASKPASS"' EXIT

                            cat > "$ASKPASS" <<'EOF'
        #!/bin/sh
        case "$1" in
        *Username*) printf '%s\\n' "$GITOPS_USERNAME" ;;
        *Password*) printf '%s\\n' "$GITOPS_TOKEN" ;;
        *) exit 1 ;;
        esac
        EOF

                            export GIT_ASKPASS="$ASKPASS"
                            export GIT_TERMINAL_PROMPT=0

                            git -c credential.helper= push origin HEAD:main

                            echo "GitOps repository updated."
                        '''
                    }
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