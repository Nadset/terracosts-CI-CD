pipeline {
    agent any

    environment {
        TERRACOSTS_API_KEY = credentials('TERRACOSTS_API_KEY')
        TERRACOSTS_API_URL = 'https://api.terracosts.com'
        TERRACOSTS_ORG     = 'IT consult'
        TERRACOSTS_BU      = 'IT Consult - BU'
        TERRACOSTS_PROJECT = 'Nader IT Project'
        CLOUD_PROVIDER     = 'aws'
        TF_WORKING_DIR     = 'terraform/aws'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Terraform Plan') {
            steps {
                dir("${env.TF_WORKING_DIR}") {
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
                dir("${env.TF_WORKING_DIR}") {
                    sh '''
                        set -e
                        echo "=========================================="
                        echo "Starting FinOps Gating for: ${TERRACOSTS_PROJECT} (${CLOUD_PROVIDER})"
                        echo "=========================================="

                        BRANCH_NAME="${GIT_BRANCH:-origin/main}"

                        RESPONSE=$(curl -s -w "\\n%{http_code}" -X POST "$TERRACOSTS_API_URL/api/gating/evaluate" \
                          -H "Authorization: Bearer $TERRACOSTS_API_KEY" \
                          -H "Content-Type: application/json" \
                          -d "$(jq -n \
                            --arg org "$TERRACOSTS_ORG" \
                            --arg bu "$TERRACOSTS_BU" \
                            --arg project_name "$TERRACOSTS_PROJECT" \
                            --arg provider "$CLOUD_PROVIDER" \
                            --arg engine "jenkins" \
                            --arg ci_platform "jenkins" \
                            --arg executor_engine "jenkins" \
                            --arg run_id "$BUILD_NUMBER" \
                            --arg branch "$BRANCH_NAME" \
                            --slurpfile plan tfplan.json \
                            '{
                              organization: $org,
                              business_unit: $bu,
                              project_name: $project_name,
                              provider: $provider,
                              engine: $engine,
                              ci_platform: $ci_platform,
                              executor_engine: $executor_engine,
                              pipeline_run_id: $run_id,
                              branch: $branch,
                              tfplan: $plan[0]
                            }')")

                        HTTP_BODY=$(echo "$RESPONSE" | head -n -1)
                        HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)

                        echo "HTTP Status: $HTTP_STATUS"
                        echo "$HTTP_BODY" | jq .

                        if [ "$HTTP_STATUS" -ge 400 ]; then
                            echo "ERROR: TerraCosts API returned HTTP error: $HTTP_STATUS"
                            exit 1
                        fi

                        STATUS=$(echo "$HTTP_BODY" | jq -r '.status // .verdict // "BLOCKED"')
                        if [ "$STATUS" != "SUCCESS" ] && [ "$STATUS" != "PASS" ] && [ "$STATUS" != "PASSED" ]; then
                            echo "BLOCKED: TerraCosts FinOps Gate returned status: $STATUS"
                            exit 1
                        fi

                        echo "PASSED: TerraCosts FinOps Gate approved the deployment."
                    '''
                }
            }
        }
    }

    post {
        always {
            dir("${env.TF_WORKING_DIR}") {
                sh 'rm -f tfplan.binary tfplan.json'
            }
        }
    }
}
