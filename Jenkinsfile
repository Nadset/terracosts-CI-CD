sh '''
    jq -n \
      --arg org "TerraCosts Enterprise" \
      --arg bu "BU Core Payment" \
      --arg proj "My New project" \
      --arg prov "aws" \
      --arg eng "jenkins" \
      --arg run_id "${env.BUILD_NUMBER}" \
      --arg branch "origin/main" \
      --slurpfile plan tfplan.json \
      '{
        organization: $org,
        business_unit: $bu,
        project_name: $proj,
        provider: $prov,
        engine: $eng,
        pipeline_run_id: $run_id,
        branch: $branch,
        tfplan: $plan[0]
      }' > payload.json

    curl -s -w "\\n%{http_code}" -X POST https://api.terracosts.com/api/gating/evaluate \
         -H "Authorization: Bearer ${TERRACOSTS_API_KEY}" \
         -H "Content-Type: application/json" \
         -d @payload.json
'''
