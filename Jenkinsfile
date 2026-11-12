// ==============================================================================
// TerraCosts FinOps CI/CD Gate — Jenkins Declarative Pipeline
// Target Path : Jenkinsfile
// Organization: IT consult
// Business Unit: IT Consult - BU
// Project     : Nader IT Project
// Provider    : AWS
// ==============================================================================

pipeline {
    agent any

    environment {
        TERRACOSTS_API_URL = 'https://terracosts.com'
        TERRACOSTS_ORG     = 'IT consult'
        TERRACOSTS_BU      = 'IT Consult - BU'
        TERRACOSTS_PROJECT = 'Nader IT Project'
        CLOUD_PROVIDER     = 'aws'
        TF_WORKING_DIR     = 'terraform/aws'
        TERRACOSTS_API_KEY = credentials('TERRACOSTS_API_KEY')
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

        stage('TerraCosts FinOps Gate') {
            steps {
                dir("${env.TF_WORKING_DIR}") {
                    sh '''
                        set -e
                        echo "Sending Terraform plan to TerraCosts FinOps Gate..."

                        RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$TERRACOSTS_API_URL/api/v1/gating/evaluate" \
                          -H "Authorization: Bearer $TERRACOSTS_API_KEY" \
                          -H "Content-Type: application/json" \
                          -d "$(jq -n \
                            --arg org "$TERRACOSTS_ORG" \
                            --arg bu "$TERRACOSTS_BU" \
                            --arg project "$TERRACOSTS_PROJECT" \
                            --arg provider "$CLOUD_PROVIDER" \
                            --arg engine "jenkins" \
                            --arg run_id "$BUILD_NUMBER" \
                            --arg branch "$GIT_BRANCH" \
                            --slurpfile plan tfplan.json \
                            '{
                              organization: $org,
                              business_unit: $bu,
                              project: $project,
                              provider: $provider,
                              engine: $engine,
                              pipeline_run_id: $run_id,
                              branch: $branch,
                              tfplan: $plan[0]
                            }')")

                        HTTP_BODY=$(echo "$RESPONSE" | sed '$d')
                        HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)

                        echo "$HTTP_BODY" | jq .

                        if [ "$HTTP_STATUS" -ge 400 ]; then
                            error("TerraCosts API returned HTTP error: $HTTP_STATUS")
                        fi

                        VERDICT=$(echo "$HTTP_BODY" | jq -r '.verdict // .status // "FAIL"')
                        if [ "$VERDICT" != "PASS" ]; then
                            error("BLOCKED: TerraCosts FinOps Gate verdict is $VERDICT")
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
