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

        stage('Trivy Scan') {
            steps {
                sh '''
                    trivy image --severity CRITICAL devops-tracker:${GIT_COMMIT}
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

        stage('Deploy') {
            steps {
                sh '''
                    aws ecr get-login-password --region "$AWS_REGION" | \
                    docker login --username AWS --password-stdin "$ECR_REGISTRY"

                    export IMAGE_TAG=${GIT_COMMIT}

                    docker compose pull
                    docker compose up -d
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    for i in 1 2 3 4 5; do
                        if curl -f http://localhost:5000/health; then
                            echo "Health check passed"
                            exit 0
                        else
                            echo "Health check failed. Retrying in 5 seconds..."
                            sleep 5
                        fi
                    done
                    echo "Health check failed after 5 attempts. Exiting with error."
                    exit 1
                '''
            }
        }
        stage('Clean Up') {
            steps {
                sh '''
                    docker image prune -f
                    docker builder prune -f
                '''
            }
        }

    }
}
