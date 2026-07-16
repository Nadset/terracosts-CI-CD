#!/usr/bin/env python3
import os
import sys
import json
import argparse
import logging
import subprocess
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TerraCostsGating")

def detect_ci_platform():
    """
    Auto-détecte le moteur/plateforme d'exécution CI/CD pour la télémétrie FinOps.
    Gère GitHub Actions, AWS CodeBuild, Azure DevOps, Jenkins, GCP Cloud Build et OCI DevOps.
    """
    # 🔍 LOGS DE DIAGNOSTIC AVANT DETECTION
    logger.info("======= DEBUG CI DETECTION =======")
    logger.info(f"CWD actuel : {os.getcwd()}")
    logger.info(f"Variable GITHUB_ACTIONS : {os.environ.get('GITHUB_ACTIONS')}")
    logger.info(f"Variable CI_PLATFORM : {os.environ.get('CI_PLATFORM')}")
    logger.info(f"Variable EXECUTOR_ENGINE : {os.environ.get('EXECUTOR_ENGINE')}")
    logger.info(f"Variable TF_BUILD : {os.environ.get('TF_BUILD')}")
    logger.info(f"Variable JENKINS_URL : {os.environ.get('JENKINS_URL')}")
    logger.info(f"Variable CODEBUILD_BUILD_ID : {os.environ.get('CODEBUILD_BUILD_ID')}")
    logger.info("==================================")

    # 1. Détection prioritaire par variables d'environnement explicites ou pures
    if os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI_PLATFORM") in ["github", "github_actions"]:
        return "github_actions"
    
    if os.environ.get("CODEBUILD_BUILD_ID") is not None or os.environ.get("CI_PLATFORM") in ["aws_codebuild", "codebuild"]:
        return "aws_codebuild"
        
    if os.environ.get("TF_BUILD") == "True" or os.environ.get("CI_PLATFORM") == "azure_devops":
        return "azure_devops"
        
    if os.environ.get("JENKINS_URL") is not None or os.environ.get("CI_PLATFORM") == "jenkins":
        return "jenkins"

    if os.environ.get("OCI_BUILD_ID") is not None or os.environ.get("CI_PLATFORM") == "oci_devops":
        return "oci_devops"

    if os.environ.get("GCP_BUILD_ID") is not None or os.environ.get("CI_PLATFORM") == "gcp_cloudbuild":
        return "gcp_cloudbuild"

    # 2. Détection par analyse du chemin du répertoire courant (CWD)
    current_cwd = os.getcwd().lower()
    if "codebuild" in current_cwd:
        return "aws_codebuild"
    elif "actions-runner" in current_cwd or "_work" in current_cwd:
        return "github_actions"
    elif "azdo" in current_cwd or "vsts" in current_cwd or "azure" in current_cwd:
        return "azure_devops"
    elif "jenkins" in current_cwd or "workspace" in current_cwd:
        return "jenkins"

    # 3. Scan global des clés d'environnement
    try:
        env_dump = str(os.environ).lower()
        if "codebuild" in env_dump or "aws_build" in env_dump:
            return "aws_codebuild"
        if "github" in env_dump or "actions" in env_dump:
            return "github_actions"
        if "azure" in env_dump or "vsts" in env_dump:
            return "azure_devops"
        if "jenkins" in env_dump:
            return "jenkins"
    except Exception:
        pass

    # 4. Fallback direct sur la variable explicite si elle existe
    explicit_platform = os.environ.get("CI_PLATFORM") or os.environ.get("EXECUTOR_ENGINE")
    if explicit_platform:
        return explicit_platform

    return "unknown"

def get_git_branch():
    # CODEBUILD_SOURCE_VERSION contient souvent la branche (ex: refs/heads/main ou juste main)
    ci_env_vars = ["GITHUB_REF_NAME", "BUILD_SOURCEBRANCHNAME", "GIT_BRANCH", "BRANCH_NAME", "CI_COMMIT_REF_NAME", "CODEBUILD_SOURCE_VERSION"]
    for var in ci_env_vars:
        if os.environ.get(var):
            branch = os.environ.get(var)
            # Nettoyage des préfixes Git classiques si présents
            if "refs/heads/" in branch:
                branch = branch.replace("refs/heads/", "")
            return branch.split('/')[-1] if '/' in branch else branch
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL)
        return branch.decode("utf-8").strip()
    except Exception:
        return "unknown-branch"

def parse_args():
    parser = argparse.ArgumentParser(description="TerraCosts FinOps CI/CD Gating Engine")
    parser.add_argument("--plan", required=True, help="Path to the Terraform plan.json file")
    parser.add_argument("--project", required=True, help="Unique name of the target cloud project")
    parser.add_argument("--provider", required=True, help="Cloud provider identifier (aws, gcp, azure, oci)")
    return parser.parse_args()

def main():
    args = parse_args()
    api_url = os.environ.get("TERRACOSTS_API_URL", "http://localhost:8000")
    api_key = os.environ.get("TERRACOSTS_API_KEY")
    strict_mode_env = os.environ.get("FINOPS_STRICT_MODE", "true").lower()
    is_strict_mode = strict_mode_env in ["true", "1", "yes"]

    if not api_key:
        logger.error("CRITICAL CONFIGURATION ERROR: 'TERRACOSTS_API_KEY' environment variable is missing.")
        sys.exit(1)

    if not os.path.exists(args.plan):
        logger.error(f"STRUCTURE ERROR: Planned artifact file not found at path: {args.plan}")
        sys.exit(1)

    try:
        with open(args.plan, "r") as f:
            plan_data = json.load(f)
    except Exception as e:
        logger.error(f"PARSING ERROR: Failed to decode target JSON plan file: {str(e)}")
        sys.exit(1)

    try:
        resource_changes = plan_data.get("resource_changes", [])
        active_changes = [r for r in resource_changes if "no-op" not in r.get("change", {}).get("actions", [])]
        if len(active_changes) > 0:
            cost_delta = float(len(active_changes) * 25.50)
        else:
            cost_delta = 0.00
    except Exception as e:
        cost_delta = 10.00

    headers = {"X-TerraCosts-API-Key": api_key, "Content-Type": "application/json"}
    target_get_url = f"{api_url.rstrip('/')}/api/intelligence/projects"

    budget_limit = 50.00
    try:
        response = requests.get(target_get_url, headers=headers, timeout=5)
        if response.status_code == 200:
            projects_list = response.json()
            matched_project = next((p for p in projects_list if p.get("name") == args.project), None)
            if matched_project and "threshold_limit" in matched_project:
                budget_limit = float(matched_project["threshold_limit"])
    except requests.RequestException:
        if is_strict_mode:
            logger.error(f"STRICT MODE: Target API unavailable during project validation scan.")
            sys.exit(1)

    is_compliant = cost_delta <= budget_limit
    git_branch = get_git_branch()
    ci_platform = detect_ci_platform()

    payload = {
        "project": str(args.project),
        "branch": str(git_branch),
        "provider": str(args.provider).lower(),
        "delta": float(cost_delta),
        "compliant": bool(is_compliant),
        "ci_platform": str(ci_platform),
        "engine": str(ci_platform),
        "executor_engine": str(ci_platform),
        "execution_engine": str(ci_platform),
        "business_unit_id": 1,
        "user_id": 1
    }

    target_post_url = f"{api_url.rstrip('/')}/api/intelligence/estimate/history"
    try:
        post_response = requests.post(target_post_url, json=payload, headers=headers, timeout=5)
        if post_response.status_code in [200, 201]:
            logger.info("Gating analysis successfully compiled and recorded to central API.")
        else:
            logger.error(f"API Audit ledger rejection {post_response.status_code}: {post_response.text}")
    except requests.RequestException as e:
        logger.error(f"Failed to transmit audit telemetry to central ledger: {str(e)}")

    if not is_compliant:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
