"""
Builds logic for QuantumOps: EAS CLI integration, build fetching, and Azure upload.
"""
from typing import List, Dict, Any, Optional
import subprocess
import json
import re
import requests
from azure.storage.blob import BlobClient
import os
import logging

logger = logging.getLogger(__name__)
logger.info("Loaded quantumops.builds module.")

def fetch_builds(platform: str) -> List[Dict[str, Any]]:
    logger.info(f"Called fetch_builds(platform={platform})")
    process = subprocess.Popen([
        "npx", "eas", "build:list", "--platform", platform, "--json", "--non-interactive"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    json_output = ""
    while True:
        stdout_line = process.stdout.readline() if process.stdout else ''
        stderr_line = process.stderr.readline() if process.stderr else ''
        if stdout_line:
            json_output += stdout_line
        if not stdout_line and not stderr_line and process.poll() is not None:
            break
    process.wait()
    match = re.search(r'(\[.*\])', json_output, re.DOTALL)
    if not match:
        logger.error("Could not extract JSON array from EAS CLI output.")
        raise ValueError("Could not extract JSON array from EAS CLI output.")
    json_str = match.group(1)
    try:
        builds = json.loads(json_str)
        logger.info(f"Parsed {len(builds)} builds from EAS CLI output for {platform}")
        return builds
    except Exception as e:
        logger.error(f"JSON parsing failed: {e}")
        raise

def upload_build_to_azure(local_path: str, blob_url: str, sas_token: str) -> str:
    logger.info(f"Called upload_build_to_azure(local_path={local_path}, blob_url={blob_url})")
    blob_client = BlobClient.from_blob_url(f"{blob_url}?{sas_token.split('?',1)[1]}")
    with open(local_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    if not blob_client.exists():
        logger.error("Blob not found after upload!")
        raise RuntimeError("Blob not found after upload!")
    os.remove(local_path)
    logger.info(f"Upload complete: {blob_url}")
    return blob_url 