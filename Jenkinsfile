pipeline {
    agent { label 'master' } // S'exécute sur le nœud principal de ton VPS

    environment {
        // ID du secret de type "Secret text" à configurer dans l'interface de Jenkins
        TERRACOSTS_API_KEY = credentials('TERRACOSTS_API_SECRET_KEY') 
        TERRACOSTS_API_URL = 'https://api.terracosts.com'
        FINOPS_STRICT_MODE = 'true'
        CI_PLATFORM        = 'jenkins'
    }

    stages {
        stage('Parallel Cloud Architecture Scan') {
            parallel {
                stage('Matrix: Production-API') {
                    environment {
                        PROJECT_NAME = 'Production-API'
                        PROVIDER     = 'aws'
                        WORKING_DIR  = 'terraform/aws'
                        PLAN_PATH    = 'plan_aws.json'
                    }
                    steps {
                        script { executeFinOpsGating() }
                    }
                }
                stage('Matrix: Frontend-App') {
                    environment {
                        PROJECT_NAME = 'Frontend-App'
                        PROVIDER     = 'azure'
                        WORKING_DIR  = 'terraform/azure'
                        PLAN_PATH    = 'plan_azure.json'
                    }
                    steps {
                        script { executeFinOpsGating() }
                    }
                }
                stage('Matrix: Data-Pipeline') {
                    environment {
                        PROJECT_NAME = 'Data-Pipeline'
                        PROVIDER     = 'oci'
                        WORKING_DIR  = 'terraform/oci'
                        PLAN_PATH    = 'plan_oci.json'
                    }
                    steps {
                        script { executeFinOpsGating() }
                    }
                }
                stage('Matrix: Core-Backend') {
                    environment {
                        PROJECT_NAME = 'Core-Backend'
                        PROVIDER     = 'gcp'
                        WORKING_DIR  = 'terraform/gcp'
                        PLAN_PATH    = 'plan_gcp.json'
                    }
                    steps {
                        script { executeFinOpsGating() }
                    }
                }
            }
        }
    }
}

def executeFinOpsGating() {
    echo "Processing change detection for ${env.PROJECT_NAME}..."
    
    // Détection des fichiers modifiés dans le commit courant
    def changedFiles = sh(script: "git diff --name-only HEAD~1 HEAD || true", returnStdout: true).trim()
    def targetChanged = changedFiles.contains("${env.WORKING_DIR}/")

    if (targetChanged) {
        echo "Changes detected in ${env.WORKING_DIR}. Running terraform plan..."
        sh """
            cd ${env.WORKING_DIR}
            terraform init
            terraform plan -out=tfplan.binary
            terraform show -json tfplan.binary > ${WORKSPACE}/${env.PLAN_PATH}
        """
    } else {
        echo "No changes in ${env.WORKING_DIR}. Generating fallback plan..."
        sh "echo '{\"format_version\": \"1.0\", \"resource_changes\": []}' > ${WORKSPACE}/${env.PLAN_PATH}"
    }

    // Injection du patch SSL temporaire pour le workspace Jenkins
    sh """
        mkdir -p ${WORKSPACE}/patch
        cat << 'EOF' > ${WORKSPACE}/patch/sitecustomize.py
import warnings
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass
try:
    import requests
    from requests.adapters import HTTPAdapter
    orig_send = HTTPAdapter.send
    def patched_send(self, request, **kwargs):
        kwargs['verify'] = False
        return orig_send(self, request, **kwargs)
    HTTPAdapter.send = patched_send
except Exception:
    pass
EOF
    """

    // Exécution du script centralisé
    echo "Executing FinOps gating analysis..."
    withEnv(["PYTHONPATH=${WORKSPACE}/patch"]) {
        sh """
            python3 /home/terracosts-pro/scripts/finops_gating.py \
                --plan "${WORKSPACE}/${env.PLAN_PATH}" \
                --project "${env.PROJECT_NAME}" \
                --provider "${env.PROVIDER}"
        """
    }
}
