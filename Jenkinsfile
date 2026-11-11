pipeline {
    agent any
    environment {
        TERRACOSTS_API_KEY = credentials('TERRACOSTS_API_KEY')
        TERRACOSTS_API_URL = 'https://api.terracosts.com'
        FINOPS_STRICT_MODE = 'true'
        CI_PLATFORM        = 'jenkins'
        EXECUTOR_ENGINE    = 'jenkins'
        TERRACOSTS_ORG     = '019a8da2-cacd-4f66-9c2f-4d49d9051bcf'
        TERRACOSTS_BU      = 'IT Consult - BU'
        TERRACOSTS_PROJECT = 'Nader IT Project'
        CLOUD_PROVIDER     = 'aws'
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
                        echo "Starting FinOps Gating for: ${TERRACOSTS_PROJECT} (${CLOUD_PROVIDER})"
                        echo "=========================================="

                        RESPONSE=$(curl -s -w "\\n%{http_code}" -X POST "$TERRACOSTS_API_URL/api/gating/evaluate" \
  -H "Authorization: Bearer $TERRACOSTS_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg org "$TERRACOSTS_ORG" \
    --arg bu "$TERRACOSTS_BU" \
    --arg project_name "$TERRACOSTS_PROJECT" \
    --arg provider "$CLOUD_PROVIDER" \
    --arg engine "jenkins" \
    --arg run_id "$BUILD_NUMBER" \
    --arg branch "${GIT_BRANCH:-origin/main}" \
    --slurpfile plan tfplan.json \
    '{
      organization: $org,
      business_unit: $bu,
      project_name: $project_name,
      provider: $provider,
      engine: $engine,
      ci_platform: $engine,
      executor_engine: $engine,
      pipeline_run_id: $run_id,
      branch: $branch,
      tfplan: $plan[0]
    }')")

                        HTTP_BODY=$(echo "$RESPONSE" | head -n -1)
                        HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)

                        echo "HTTP Status: $HTTP_STATUS"
                        echo "Response Body: $HTTP_BODY"

                        if [ "$HTTP_STATUS" -ge 400 ]; then
                            echo "ERROR: TerraCosts API returned HTTP error: $HTTP_STATUS"
                            exit 1
                        fi
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
