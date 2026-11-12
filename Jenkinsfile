// ==============================================================================
// TerraCosts FinOps CI/CD Gate — Jenkins Declarative Pipeline
// Target Path   : Jenkinsfile
// Organization  : IT consult (019a8da2-cacd-4f66-9c2f-4d49d9051bcf)
// Business Unit : IT Consult - BU
// Project       : Nader IT Project
// Cloud Provider: AWS
// Required Auth : AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
// ==============================================================================

pipeline {
    agent any

    environment {
        TERRACOSTS_API_KEY = credentials('TERRACOSTS_API_KEY')
        TERRACOSTS_API_URL = 'https://api.terracosts.com'
        TERRACOSTS_ORG     = 'IT consult'
        TERRACOSTS_ORG_ID  = '019a8da2-cacd-4f66-9c2f-4d49d9051bcf'
        TERRACOSTS_BU      = 'IT Consult - BU'
        TERRACOSTS_PROJECT = 'Nader IT Project'
        CLOUD_PROVIDER     = 'aws'
        CI_PLATFORM        = 'jenkins'
        EXECUTOR_ENGINE    = 'jenkins'
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

                        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$TERRACOSTS_API_URL/api/gating/evaluate" \
                          -H "Authorization: Bearer $TERRACOSTS_API_KEY" \
                          -H "Content-Type: application/json" \
                          -d "$(jq -n \
                            --arg org "$TERRACOSTS_ORG" \
                            --arg org_id "$TERRACOSTS_ORG_ID" \
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
                              organization_id: (if $org_id != "" then $org_id else null end),
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
                        DELTA=$(echo "$HTTP_BODY" | jq -r '.metrics.delta // 0')
                        GATE_LIMIT=$(echo "$HTTP_BODY" | jq -r '.metrics.commit_threshold // "N/A"')

                        echo "--------------------------------------------------"
                        echo "Verdict   : $STATUS"
                        echo "Cost Delta: $$DELTA (Threshold: $$GATE_LIMIT)"
                        echo "--------------------------------------------------"

                        if [ "$STATUS" != "SUCCESS" ] && [ "$STATUS" != "PASS" ] && [ "$STATUS" != "PASSED" ]; then
                            echo "BLOCKED: Infrastructure changes exceed TerraCosts FinOps policy thresholds."
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
            deleteDir()
        }
    }
}
