"""
EAS Service for fetching builds from Expo Application Services.
"""
import logging
import subprocess
import json
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EasService:
    """Service for interacting with EAS CLI."""
    
    @staticmethod
    def fetch_builds(platform: str) -> List[Dict[str, Any]]:
        """Fetch builds using EAS CLI."""
        logger.info(f"Fetching builds for {platform} from EAS...")
        try:
            command = [
                "npx", "eas", "build:list", 
                "--platform", platform, 
                "--json", 
                "--non-interactive",
                "--limit", "50"  # Fetch more builds
            ]
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            stdout, stderr = process.communicate(timeout=120)
            
            if process.returncode != 0:
                error_message = f"EAS CLI command failed with return code {process.returncode}.\nStderr: {stderr}"
                logger.error(error_message)
                raise RuntimeError(error_message)

            # EAS CLI can sometimes output other text, so we find the JSON block
            match = re.search(r'(\[.*\])', stdout, re.DOTALL)
            if not match:
                logger.error(f"Could not extract JSON from EAS output: {stdout}")
                raise ValueError("Could not find JSON in EAS CLI output.")
                
            json_str = match.group(1)
            builds = json.loads(json_str)
            logger.info(f"Successfully fetched {len(builds)} builds for {platform}.")
            return builds
            
        except FileNotFoundError:
            logger.error("`npx` command not found. Please ensure Node.js and npm are installed and in your PATH.")
            raise
        except subprocess.TimeoutExpired:
            logger.error("EAS CLI command timed out.")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from EAS CLI: {e}\nOutput: {stdout}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching builds: {e}")
            raise 