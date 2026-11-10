// ==============================================================================
// TerraCosts FinOps CI/CD Gate — Jenkins Declarative Pipeline (Fixed)
// Target Path : Jenkinsfile
// Organization: TerraCosts Enterprise
// Business Unit: BU Core Payment
// Project     : My New project
// Provider    : aws
// ==============================================================================

pipeline {
    agent any

    environment {
        TERRACOSTS_API_URL = 'https://api.terracosts.com'
        TERRACOSTS_ORG     = 'TerraCosts Enterprise'
        TERRACOSTS_BU      = 'BU Core Payment'
        TERRACOSTS_PROJECT = 'My New project'
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

                        RESPONSE=$(curl -s -w "\\n%{http_code}" -X POST "$TERRACOSTS_API_URL/api/gating/evaluate" \
                          -H "Authorization: Bearer $TERRACOSTS_API_KEY" \
                          -H "Content-Type: application/json" \
                          -d "$(jq -n \
                            --arg org "$TERRACOSTS_ORG" \
                            --arg bu "$TERRACOSTS_BU" \
                            --arg project "$TERRACOSTS_PROJECT" \
                            --arg provider "$CLOUD_PROVIDER" \
                            --arg engine "jenkins" \
                            --arg run_id "$BUILD_NUMBER" \
                            --arg branch "${GIT_BRANCH:-main}" \
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
                            echo "ERROR: TerraCosts API returned HTTP error: $HTTP_STATUS"
                            exit 1
                        fi

                        VERDICT=$(echo "$HTTP_BODY" | jq -r '.verdict // .status // "FAIL"')
                        if [ "$VERDICT" != "PASS" ]; then
                            echo "BLOCKED: TerraCosts FinOps Gate verdict is $VERDICT"
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
