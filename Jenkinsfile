pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
             steps {
                 sh '''
                     python3 -m venv .venv
                     .venv/bin/pip install -r requirements.txt
                     .venv/bin/python -m pytest
                    '''
    }
}

    }
}
