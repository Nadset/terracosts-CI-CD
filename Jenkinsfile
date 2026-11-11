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
        stage('Mock Terraform Plan') {
            steps {
                dir('terraform/aws') {
                    sh '''
                        echo "Generating mock tfplan.json for testing delta..."
                        cat << 'EOF' > tfplan.json
{
  "format_version": "1.0",
  "planned_values": {
    "root_module": {
      "resources": [
        { "address": "aws_db_instance.db1", "mode": "managed", "type": "aws_db_instance", "name": "db1", "provider_name": "registry.terraform.io/hashicorp/aws", "values": { "instance_class": "db.m5.2xlarge", "allocated_storage": 500 } },
        { "address": "aws_db_instance.db2", "mode": "managed", "type": "aws_db_instance", "name": "db2", "provider_name": "registry.terraform.io/hashicorp/aws", "values": { "instance_class": "db.m5.2xlarge", "allocated_storage": 500 } },
        { "address": "aws_db_instance.db3", "mode": "managed", "type": "aws_db_instance", "name": "db3", "provider_name": "registry.terraform.io/hashicorp/aws", "values": { "instance_class": "db.m5.2xlarge", "allocated_storage": 500 } },
        { "address": "aws_db_instance.db4", "mode": "managed", "type": "aws_db_instance", "name": "db4", "provider_name": "registry.terraform.io/hashicorp/aws", "values": { "instance_class": "db.m5.2xlarge", "allocated_storage": 500 } },
        { "address": "aws_db_instance.db4", "mode": "managed", "type": "aws_db_instance", "name": "db5", "provider_name": "registry.terraform.io/hashicorp/aws", "values": { "instance_class": "db.m5.2xlarge", "allocated_storage": 1000 } }
      ]
    }
  },
  "resource_changes": [
    { "address": "aws_db_instance.db1", "type": "aws_db_instance", "name": "db1", "provider_name": "registry.terraform.io/hashicorp/aws", "change": { "actions": ["create"], "before": null, "after": { "instance_class": "db.m5.2xlarge", "allocated_storage": 500 } } },
    { "address": "aws_db_instance.db2", "type": "aws_db_instance", "name": "db2", "provider_name": "registry.terraform.io/hashicorp/aws", "change": { "actions": ["create"], "before": null, "after": { "instance_class": "db.m5.2xlarge", "allocated_storage": 500 } } },
    { "address": "aws_db_instance.db3", "type": "aws_db_instance", "name": "db3", "provider_name": "registry.terraform.io/hashicorp/aws", "change": { "actions": ["create"], "before": null, "after": { "instance_class": "db.m5.2xlarge", "allocated_storage": 500 } } },
    { "address": "aws_db_instance.db4", "type": "aws_db_instance", "name": "db4", "provider_name": "registry.terraform.io/hashicorp/aws", "change": { "actions": ["create"], "before": null, "after": { "instance_class": "db.m5.2xlarge", "allocated_storage": 500 } } },
    { "address": "aws_db_instance.db5", "type": "aws_db_instance", "name": "db5", "provider_name": "registry.terraform.io/hashicorp/aws", "change": { "actions": ["create"], "before": null, "after": { "instance_class": "db.m5.2xlarge", "allocated_storage": 1000 } } }

}
EOF
                        # Vérification de la validité du JSON généré
                        jq . tfplan.json > /dev/null && echo "JSON syntax is valid."
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
    --argjson delta 102.00 \
    --arg engine "jenkins" \
    --arg ci_plat "jenkins" \
    --arg exec_eng "jenkins" \
    --arg run_id "$BUILD_NUMBER" \
    --arg branch "${GIT_BRANCH:-origin/main}" \
    --slurpfile plan tfplan.json \
    '{
      organization: $org,
      business_unit: $bu,
      project_name: $project_name,
      provider: $provider,
      delta: $delta,
      engine: $engine,
      ci_platform: $ci_plat,
      executor_engine: $exec_eng,
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
