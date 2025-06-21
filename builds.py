"""
Builds logic for QuantumOps: EAS CLI integration, build fetching, and Azure upload.
"""
import json
import logging
import os
import re
import subprocess
from typing import Any, Dict, List

from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)
logger.info("Loaded quantumops.builds module.")


def fetch_builds(platform: str) -> List[Dict[str, Any]]:
    logger.info(f"Called fetch_builds(platform={platform})")
    import shutil

    eas_config_src = "config/eas.json"
    eas_config_dst = "eas.json"
    try:
        shutil.copy2(eas_config_src, eas_config_dst)
        logger.info("Copied eas.json to root directory for EAS CLI")
        process = subprocess.Popen(
            [
                "npx",
                "eas",
                "build:list",
                "--platform",
                platform,
                "--json",
                "--non-interactive",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            logger.error(f"EAS CLI timed out for platform {platform}.")
            raise RuntimeError(f"EAS CLI timed out for platform {platform}.")
        if process.returncode != 0:
            logger.error(f"EAS CLI failed for platform {platform}: {stderr}")
            raise RuntimeError(f"EAS CLI failed for platform {platform}: {stderr}")
        json_output = stdout
        match = re.search(r"(\[.*\])", json_output, re.DOTALL)
        if not match:
            logger.error("Could not extract JSON array from EAS CLI output.")
            raise ValueError("Could not extract JSON array from EAS CLI output.")
        json_str = match.group(1)
        try:
            builds_json = json.loads(json_str)
            logger.info(
                f"Parsed {len(builds_json)} builds from EAS CLI output for {platform}"
            )
            builds = []
            for build in builds_json:
                builds.append(
                    {
                        "id": build.get("id", ""),
                        "status": build.get("status", ""),
                        "platform": build.get("platform", ""),
                        "profile": build.get("buildProfile", "N/A"),
                        "app_version": build.get("appVersion", "N/A"),
                        "build_url": build.get("artifacts", {}).get("buildUrl", ""),
                        "error": build.get("error", {}).get("message", "")
                        if build.get("error")
                        else "",
                        "fingerprint": build.get("gitCommitHash", "N/A")[:7],
                        "build_number": build.get("appBuildVersion", "N/A"),
                    }
                )
            return builds
        except Exception as e:
            logger.error(f"JSON parsing failed: {e}")
            raise
    finally:
        try:
            if os.path.exists(eas_config_dst):
                os.remove(eas_config_dst)
                logger.info("Cleaned up temporary eas.json file")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary eas.json: {e}")


def upload_build_to_azure(local_path: str, blob_name: str) -> str:
    # Load credentials from environment
    tenant_id = os.environ["AZURE_TENANT_ID"]
    client_id = os.environ["AZURE_CLIENT_ID"]
    client_secret = os.environ["AZURE_CLIENT_SECRET"]
    storage_account = os.environ["AZURE_STORAGE_ACCOUNT"]
    container_name = os.environ["AZURE_STORAGE_CONTAINER"]

    credential = ClientSecretCredential(
        tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
    )
    blob_service_client = BlobServiceClient(
        f"https://{storage_account}.blob.core.windows.net", credential=credential
    )
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    with open(local_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    return blob_client.url


def enable_refresh_button(main_window, platform):
    if platform == "android":
        main_window.android_refresh_btn.setEnabled(True)
    else:
        main_window.ios_refresh_btn.setEnabled(True)
