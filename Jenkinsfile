#!/usr/bin/env bash
set -eu
set -o pipefail

# --- Environment Variables ---
export TERRACOSTS_API_URL="https://api.terracosts.com"
export FINOPS_STRICT_MODE="true"
export CI_PLATFORM="jenkins"
export EXECUTOR_ENGINE="jenkins"

# --- Parameters ---
PROJECT_NAME="terracosts-azure-core"
PROVIDER="azure"
LOCAL_BRANCH="New/budget-killer"
CONTAINER_NAME="terracosts-engine"
CONTAINER_PLAN_PATH="/app/tfplan.json"

echo "=========================================="
echo "Starting FinOps Gating for: ${PROJECT_NAME} (${PROVIDER})"
echo "=========================================="

# 1. Génération du plan Terraform factice (4 clusters -> ~102.00$)
cat << 'EOF' > tfplan.json
{
  "format_version": "1.0",
  "planned_values": {
    "root_module": {
      "resources": [
        { "address": "azurerm_postgresql_cluster.db1", "mode": "managed", "type": "azurerm_postgresql_cluster", "name": "db1", "provider_name": "registry.terraform.io/hashicorp/azurerm", "values": { "sku_name": "GP_Gen5_32", "storage_mb": 512000 } },
        { "address": "azurerm_postgresql_cluster.db2", "mode": "managed", "type": "azurerm_postgresql_cluster", "name": "db2", "provider_name": "registry.terraform.io/hashicorp/azurerm", "values": { "sku_name": "GP_Gen5_32", "storage_mb": 512000 } },
        { "address": "azurerm_postgresql_cluster.db3", "mode": "managed", "type": "azurerm_postgresql_cluster", "name": "db3", "provider_name": "registry.terraform.io/hashicorp/azurerm", "values": { "sku_name": "GP_Gen5_32", "storage_mb": 512000 } },
        { "address": "azurerm_postgresql_cluster.db4", "mode": "managed", "type": "azurerm_postgresql_cluster", "name": "db4", "provider_name": "registry.terraform.io/hashicorp/azurerm", "values": { "sku_name": "GP_Gen5_32", "storage_mb": 512000 } }
      ]
    }
  },
  "resource_changes": [
    { "address": "azurerm_postgresql_cluster.db1", "type": "azurerm_postgresql_cluster", "name": "db1", "provider_name": "registry.terraform.io/hashicorp/azurerm", "change": { "actions": ["create"], "before": null, "after": { "sku_name": "GP_Gen5_32", "storage_mb": 512000 } } },
    { "address": "azurerm_postgresql_cluster.db2", "type": "azurerm_postgresql_cluster", "name": "db2", "provider_name": "registry.terraform.io/hashicorp/azurerm", "change": { "actions": ["create"], "before": null, "after": { "sku_name": "GP_Gen5_32", "storage_mb": 512000 } } },
    { "address": "azurerm_postgresql_cluster.db3", "type": "azurerm_postgresql_cluster", "name": "db3", "provider_name": "registry.terraform.io/hashicorp/azurerm", "change": { "actions": ["create"], "before": null, "after": { "sku_name": "GP_Gen5_32", "storage_mb": 512000 } } },
    { "address": "azurerm_postgresql_cluster.db4", "type": "azurerm_postgresql_cluster", "name": "db4", "provider_name": "registry.terraform.io/hashicorp/azurerm", "change": { "actions": ["create"], "before": null, "after": { "sku_name": "GP_Gen5_32", "storage_mb": 512000 } } }
  ]
}
EOF

# 2. Copie du plan généré vers le conteneur Docker
echo "[INFO] Copying generated plan into container ${CONTAINER_NAME}..."
docker cp tfplan.json "${CONTAINER_NAME}:${CONTAINER_PLAN_PATH}"

# 3. Injection du patch SSL temporaire dans le conteneur
docker exec "${CONTAINER_NAME}" bash -c "mkdir -p /tmp/patch && cat << 'EOF' > /tmp/patch/sitecustomize.py
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
EOF"

# 4. Exécution du script FinOps Gating
echo "[INFO] Executing gating script inside container..."
docker exec \
  -e CI_PLATFORM="${CI_PLATFORM}" \
  -e EXECUTOR_ENGINE="${EXECUTOR_ENGINE}" \
  -e ORGANIZATION_ID="11111111-1111-1111-1111-111111111111" \
  -e BRANCH_NAME="${LOCAL_BRANCH}" \
  -e GIT_BRANCH="${LOCAL_BRANCH}" \
  -e JENKINS_URL="https://jenkins.terracosts.com/" \
  -e TERRACOSTS_API_KEY="${TERRACOSTS_API_KEY:-}" \
  -e TERRACOSTS_API_URL="${TERRACOSTS_API_URL}" \
  -e FINOPS_STRICT_MODE="${FINOPS_STRICT_MODE}" \
  -e PYTHONPATH="/tmp/patch" \
  "${CONTAINER_NAME}" \
  python3 /app/scripts/finops_gating.py \
    --plan "${CONTAINER_PLAN_PATH}" \
    --project "${PROJECT_NAME}" \
    --provider "${PROVIDER}"
