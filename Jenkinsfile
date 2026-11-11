pipeline {
    agent any
    environment {
        TERRACOSTS_API_KEY = credentials('TERRACOSTS_API_KEY')
        TERRACOSTS_API_URL = 'https://api.terracosts.com'
        FINOPS_STRICT_MODE = 'true'
        CI_PLATFORM        = 'jenkins'
        EXECUTOR_ENGINE    = 'jenkins'
        ORGANIZATION_ID    = '11111111-1111-1111-1111-111111111111'
        PROJECT_NAME       = 'My New project'
        PROVIDER           = 'azure'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Terraform Plan') {
            steps {
                dir('terraform/azure') {
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
                dir('terraform/azure') {
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
