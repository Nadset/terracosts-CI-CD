pipeline {
    agent any
    environment {
        TERRACOSTS_API_KEY = credentials('TERRACOSTS_API_KEY')
        TERRACOSTS_API_URL = 'https://api.terracosts.com'
        FINOPS_STRICT_MODE = 'true'
        CI_PLATFORM        = 'jenkins'
        EXECUTOR_ENGINE    = 'jenkins'
        ORGANIZATION_ID    = '019a8da2-cacd-4f66-9c2f-4d49d9051bcf'
        PROJECT_NAME       = 'IT Project'
        PROVIDER           = 'aws'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Terraform Plan') {
            steps {
                dir('terraform/aws') {
                    sh '''
                        terraform init -input=false
                        terraform plan -input=false -out=tfplan.binary
                        terraform show -json tfplan.binary > tfplan.json
                    '''
                }
            }
        }
        stage('FinOps Gating Check') {
            steps {
                dir('terraform/aws') {
                    sh '''
                        echo "=========================================="
                        echo "Starting FinOps Gating for: ${PROJECT_NAME} (${PROVIDER})"
                        echo "=========================================="

                        python3 /home/terracosts-pro/scripts/finops_gating.py \
                            --plan tfplan.json \
                            --project "${PROJECT_NAME}" \
                            --provider "${PROVIDER}"
                    '''
                }
            }
        }
    }
    post {
        always {
            deleteDir()
        }
    }
}
