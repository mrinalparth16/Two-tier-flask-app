pipeline {
    agent {
        label 'devops'
    }

    stages {


        stage('Test') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install -r requirements.txt
                    .venv/bin/python -m pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t devops-tracker:${GIT_COMMIT} .
                '''
            }
        }

    }
}
