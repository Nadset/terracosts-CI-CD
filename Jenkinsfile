# 1. Génération d'un plan Terraform avec 4 clusters pour exploser le budget (4 x 25.50$ = 102.00$)
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

# 🚀 Nom de la branche
LOCAL_BRANCH="feature/budget-killer"

# 2. Copie du plan généré à l'intérieur du conteneur Docker
docker cp tfplan.json terracosts-engine:/app/tfplan.json

# 3. Exécution du Gating à l'intérieur du conteneur
docker exec \
  -e CI_PLATFORM="jenkins" \
  -e EXECUTOR_ENGINE="jenkins" \
  -e ORGANIZATION_ID="11111111-1111-1111-1111-111111111111" \
  -e BRANCH_NAME="$LOCAL_BRANCH" \
  -e GIT_BRANCH="$LOCAL_BRANCH" \
  -e JENKINS_URL="https://jenkins.terracosts.com/" \
  -e TERRACOSTS_API_KEY="${TERRACOSTS_API_KEY:-}" \
  terracosts-engine \
  python3 /app/scripts/finops_gating.py \
    --plan /app/tfplan.json \
    --project "Production-API" \
    --provider "Aws"
