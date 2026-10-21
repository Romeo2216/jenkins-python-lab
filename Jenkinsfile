pipeline {

    agent {
        label 'docker-agent'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Environment') {
            steps {
                sh '''
                    echo "=== AGENT ==="
                    echo "$NODE_NAME"

                    echo "=== PYTHON ==="
                    python3 --version

                    echo "=== WORKSPACE ==="
                    pwd
                '''
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

        stage('Package') {
            steps {
                sh '''
                    mkdir -p dist

                    tar \
                        --exclude='__pycache__' \
                        -czf dist/application.tar.gz \
                        app/
                '''
            }
        }
    }

    post {

        always {
            junit testResults: 'reports/results.xml',
                  allowEmptyResults: true

            archiveArtifacts artifacts: 'dist/*.tar.gz',
                             allowEmptyArchive: true,
                             fingerprint: true

            echo 'Pipeline finished.'
        }

        success {
            echo 'All tests passed!'
        }

        failure {
            echo 'Pipeline failed!'
        }
    }
}