# ==============================================================================
# TerraCosts FinOps CI/CD Gate — GitLab CI/CD Pipeline
# Target Path   : .gitlab-ci.yml
# Organization  : IT consult (019a8da2-cacd-4f66-9c2f-4d49d9051bcf)
# Business Unit : IT Consult - BU
# Project       : Nader IT Project
# Cloud Provider: AWS
# Required Auth : AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
# ==============================================================================

stages:
  - plan
  - finops_gate

variables:
  TERRACOSTS_API_URL: "https://api.terracosts.com"
  TERRACOSTS_ORG: "IT consult"
  TERRACOSTS_ORG_ID: "019a8da2-cacd-4f66-9c2f-4d49d9051bcf"
  TERRACOSTS_BU: "IT Consult - BU"
  TERRACOSTS_PROJECT: "Nader IT Project"
  CLOUD_PROVIDER: "aws"
  TF_WORKING_DIR: "terraform/aws"

terraform_plan:
  stage: plan
  image:
    name: hashicorp/terraform:1.7.5
    entrypoint: [""]
  rules:
    - changes:
        - terraform/**/*
        - "*.tf"
  script:
    - cd "$TF_WORKING_DIR"
    - terraform init -input=false
    - terraform plan -input=false -out=tfplan.binary
    - terraform show -json tfplan.binary > tfplan.json
  artifacts:
    paths:
      - $TF_WORKING_DIR/tfplan.json
    expire_in: 1 hour

terracosts_finops_gate:
  stage: finops_gate
  image: alpine:3.20
  needs:
    - job: terraform_plan
      artifacts: true
  rules:
    - changes:
        - terraform/**/*
        - "*.tf"
  before_script:
    - apk add --no-cache curl jq
  script:
    - |
      set -e
      cd "$TF_WORKING_DIR"

      if [ -z "$TERRACOSTS_API_KEY" ]; then
        echo "ERROR: TERRACOSTS_API_KEY variable is missing in GitLab CI/CD Settings."
        exit 1
      fi

      BRANCH_NAME="${CI_MERGE_REQUEST_SOURCE_BRANCH_NAME:-$CI_COMMIT_REF_NAME}"

      RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$TERRACOSTS_API_URL/api/gating/evaluate" \
        -H "Authorization: Bearer $TERRACOSTS_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$(jq -n \
          --arg org "$TERRACOSTS_ORG" \
          --arg org_id "$TERRACOSTS_ORG_ID" \
          --arg bu "$TERRACOSTS_BU" \
          --arg project_name "$TERRACOSTS_PROJECT" \
          --arg provider "$CLOUD_PROVIDER" \
          --arg engine "gitlab_ci" \
          --arg run_id "$CI_PIPELINE_ID" \
          --arg branch "$BRANCH_NAME" \
          --slurpfile plan tfplan.json \
          '{
            organization: $org,
            organization_id: (if $org_id != "" then $org_id else null end),
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

      HTTP_BODY=$(echo "$RESPONSE" | sed '$d')
      HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)

      echo "$HTTP_BODY" | jq .

      if [ "$HTTP_STATUS" -ge 400 ]; then
        echo "ERROR: TerraCosts API returned HTTP error $HTTP_STATUS."
        exit 1
      fi

      STATUS=$(echo "$HTTP_BODY" | jq -r '.status // .verdict // "BLOCKED"')
      if [ "$STATUS" != "SUCCESS" ] && [ "$STATUS" != "PASS" ] && [ "$STATUS" != "PASSED" ]; then
        echo "BLOCKED: TerraCosts FinOps Gate rejected the infrastructure plan ($STATUS)."
        exit 1
      fi

      echo "PASSED: TerraCosts FinOps Gate approved the deployment."
