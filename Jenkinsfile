// TerraCosts FinOps CI/CD Gating — Jenkins (API-first, no docker exec)
//
// Credentials (Jenkins → Manage Jenkins → Credentials):
//   Secret text id: terracosts-api-key   → JWT
// Optional:
//   Secret text id: terracosts-api-url   → https://terracosts.com
//
// Job: Multibranch or Pipeline from SCM. Triggers on changes under terraform/**

pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    TERRACOSTS_API_KEY = credentials('terracosts-api-key')
    // If you also created terracosts-api-url credential, uncomment:
    // TERRACOSTS_API_URL = credentials('terracosts-api-url')
    TERRACOSTS_API_URL = "${env.TERRACOSTS_API_URL ?: 'https://terracosts.com'}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('FinOps Matrix Gating') {
      steps {
        script {
          def matrix = [
            [project: 'Production-API', provider: 'aws',   dir: 'terraform/aws'],
            [project: 'Frontend-App',   provider: 'azure', dir: 'terraform/azure'],
            [project: 'Data-Pipeline',  provider: 'oci',   dir: 'terraform/oci'],
            [project: 'Core-Backend',   provider: 'gcp',   dir: 'terraform/gcp'],
          ]

          def branches = [:]
          matrix.each { m ->
            def label = "${m.project} (${m.provider})"
            branches[label] = {
              stage(label) {
                def planFile = "${env.WORKSPACE}/plan-${m.provider}.json"
                def changed = sh(
                  script: """
                    set +e
                    if [ ! -d '${m.dir}' ]; then
                      echo none
                      exit 0
                    fi
                    # Compare to previous commit when available
                    if git rev-parse HEAD~1 >/dev/null 2>&1; then
                      git diff --name-only HEAD~1 HEAD -- '${m.dir}' | grep -q . && echo yes || echo no
                    else
                      echo yes
                    fi
                  """,
                  returnStdout: true
                ).trim()

                if (changed == 'yes') {
                  sh """
                    set -euo pipefail
                    cd '${m.dir}'
                    terraform init -input=false
                    terraform plan -input=false -out=tfplan.binary
                    terraform show -json tfplan.binary > '${planFile}'
                  """
                } else {
                  sh """
                    echo '{"format_version":"1.0","resource_changes":[]}' > '${planFile}'
                    echo "No changes in ${m.dir} — empty plan"
                  """
                }

                sh """
                  set -euo pipefail
                  test -f '${planFile}'
                  test -n "\$TERRACOSTS_API_KEY"

                  jq -n \\
                    --slurpfile plan '${planFile}' \\
                    --arg project '${m.project}' \\
                    --arg provider '${m.provider}' \\
                    --arg branch "\${GIT_BRANCH:-main}" \\
                    '{
                      plan: \$plan[0],
                      project: \$project,
                      provider: \$provider,
                      branch: \$branch,
                      organization: "Research & Development",
                      bu: "BU Core Payment",
                      ci_platform: "jenkins",
                      strict_mode: true
                    }' > /tmp/gating-body-${m.provider}.json

                  echo "Calling \$TERRACOSTS_API_URL/api/gating/analyze for ${m.project}..."
                  HTTP_BODY=\$(curl -sS -X POST "\$TERRACOSTS_API_URL/api/gating/analyze" \\
                    -H "Authorization: Bearer \$TERRACOSTS_API_KEY" \\
                    -H "X-TerraCosts-API-Key: \$TERRACOSTS_API_KEY" \\
                    -H "Content-Type: application/json" \\
                    -d @/tmp/gating-body-${m.provider}.json)

                  echo "\$HTTP_BODY" | jq .
                  EXIT_CODE=\$(echo "\$HTTP_BODY" | jq -r '.exit_code // 1')
                  exit "\$EXIT_CODE"
                """
              }
            }
          }
          parallel branches
        }
      }
    }
  }

  post {
    always {
      echo 'TerraCosts gating matrix finished'
    }
  }
}
