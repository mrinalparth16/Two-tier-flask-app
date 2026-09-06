pipeline {
    agent {
        label 'devops'
    }

    environment {
        AWS_REGION = 'ap-south-1'
        ECR_REGISTRY = '870461445156.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_REPOSITORY = 'devops-tracker'
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

        stage('Push Docker Image to ECR') {
            steps {
                sh '''
                    aws ecr get-login-password --region "$AWS_REGION" | \
                    docker login --username AWS --password-stdin "$ECR_REGISTRY"

                    docker tag "devops-tracker:${GIT_COMMIT}" \
                   "$ECR_REGISTRY/$ECR_REPOSITORY:${GIT_COMMIT}"

                    docker push \
                   "$ECR_REGISTRY/$ECR_REPOSITORY:${GIT_COMMIT}"
                '''
            }
        }

    }
}
