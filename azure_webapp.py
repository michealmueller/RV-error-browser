"""
Azure Web App log streaming functionality for QuantumOps.
"""
import gc
import logging
import os
import threading
import time
import xml.etree.ElementTree as ET
from collections import deque
from typing import Any, Callable, Dict, Generator, List, Optional
from urllib.parse import urljoin

import requests
from azure.core.exceptions import (
    HttpResponseError,
    ResourceNotFoundError,
)
from azure.identity import ClientSecretCredential
from azure.mgmt.web import WebSiteManagementClient
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)
logger.info("Loaded quantumops.azure_webapp module.")

# Constants for memory management
MAX_LOG_BUFFER_SIZE = 1000  # Maximum number of log lines to keep in memory
LOG_BUFFER_CLEANUP_INTERVAL = 60  # Seconds between buffer cleanup
MAX_CONCURRENT_STREAMS = 5  # Maximum number of concurrent log streams


class LogBuffer:
    """Thread-safe circular buffer for log lines with memory management."""

    def __init__(self, max_size: int = MAX_LOG_BUFFER_SIZE):
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()
        self._last_cleanup = time.time()

    def append(self, line: str) -> None:
        """Add a line to the buffer with automatic cleanup."""
        with self.lock:
            self.buffer.append(line)
            current_time = time.time()
            if current_time - self._last_cleanup > LOG_BUFFER_CLEANUP_INTERVAL:
                self._cleanup()
                self._last_cleanup = current_time

    def _cleanup(self) -> None:
        """Clean up old entries and force garbage collection."""
        with self.lock:
            # Keep only the most recent entries
            while len(self.buffer) > MAX_LOG_BUFFER_SIZE:
                self.buffer.popleft()
            gc.collect()


class AzureCreds:
    """Class to hold Azure credentials."""

    def __init__(self):
        self.AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT")
        self.AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER")
        self.AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        self.AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
        self.AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        self.AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")


class AzureWebApp:
    def __init__(self, app_name, resource_group):
        self.creds = AzureCreds()
        self.app_name = app_name
        self.resource_group = resource_group
        self.credential = ClientSecretCredential(
            tenant_id=self.creds.AZURE_TENANT_ID,
            client_id=self.creds.AZURE_CLIENT_ID,
            client_secret=self.creds.AZURE_CLIENT_SECRET,
        )
        self.web_client = WebSiteManagementClient(
            self.credential, self.creds.AZURE_SUBSCRIPTION_ID
        )
        self.active_streams = 0
        self.stream_lock = threading.Lock()
        self.log_buffer = LogBuffer()

    def get_properties(self):
        """Get web app properties."""
        return self.web_client.web_apps.get(self.resource_group, self.app_name)

    def get_app_settings(self):
        """Get web app settings."""
        return self.web_client.web_apps.list_application_settings(
            self.resource_group, self.app_name
        )

    def update_app_settings(self, settings):
        """Update web app settings."""
        return self.web_client.web_apps.update_application_settings(
            self.resource_group, self.app_name, settings
        )

    def restart(self):
        """Restart web app."""
        self.web_client.web_apps.restart(self.resource_group, self.app_name)

    def start(self):
        """Start web app."""
        self.web_client.web_apps.start(self.resource_group, self.app_name)

    def stop(self):
        """Stop web app."""
        self.web_client.web_apps.stop(self.resource_group, self.app_name)

    def get_publishing_user(self):
        """Get publishing user."""
        return self.web_client.get_publishing_user()

    def list_source_controls(self):
        """List source controls."""
        return self.web_client.list_source_controls()

    def get_source_control(self):
        """Get source control."""
        return self.web_client.web_apps.get_source_control(
            self.resource_group, self.app_name
        )

    def sync_repository(self):
        """Sync repository."""
        self.web_client.web_apps.sync_repository(self.resource_group, self.app_name)

    def list_publishing_credentials(self):
        """List publishing credentials."""
        return self.web_client.web_apps.list_publishing_credentials(
            self.resource_group, self.app_name
        ).result()

    def stream_logs(self, duration_minutes=5):
        """Stream logs for a given duration."""
        # This is a simplified example. In a real application, you would use
        # the 'requests' library to stream the logs from the SCM endpoint.
        scm_url = f"https://{self.app_name}.scm.azurewebsites.net/api/logstream"
        print(f"Streaming logs from {scm_url} for {duration_minutes} minutes.")
        # Example of how you might stream with requests:
        # with requests.get(scm_url, auth=(user, password), stream=True) as r:
        #     for chunk in r.iter_content(chunk_size=1024):
        #         if chunk:
        #             print(chunk.decode('utf-8'), end='')

    def get_scm_url(self):
        """
        Constructs the SCM (Kudu) URL for the web app.
        """
        return f"https://{self.app_name}.scm.azurewebsites.net"

    def _get_auth(self):
        """
        Retrieves publishing credentials and returns a tuple for basic auth.
        """
        creds = self.list_publishing_credentials()
        return (creds.publishing_user_name, creds.publishing_password)

    def stream_live_logs(self, log_output_widget):
        """
        Streams live logs from the Kudu log stream endpoint.
        """
        scm_url = f"{self.get_scm_url()}/api/logstream"
        auth = self._get_auth()

        def stream():
            try:
                with requests.get(scm_url, auth=auth, stream=True, timeout=300) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            log_output_widget.append(chunk.decode("utf-8"))
            except requests.exceptions.RequestException as e:
                log_output_widget.append(f"\\nError streaming logs: {e}")

        thread = threading.Thread(target=stream)
        thread.daemon = True
        thread.start()

    def get_web_apps(self) -> List[Dict[str, Any]]:
        """Get list of web apps in the subscription."""
        try:
            web_apps = []
            for web_app in self.web_client.web_apps.list():
                web_apps.append(
                    {
                        "name": web_app.name,
                        "resource_group": web_app.resource_group,
                        "state": web_app.state,
                        "default_host_name": web_app.default_host_name,
                    }
                )
            return web_apps
        except HttpResponseError as e:
            logger.error(f"Azure API error while getting web apps: {str(e)}")
            raise RuntimeError(f"Failed to get web apps: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while getting web apps: {str(e)}")
            raise RuntimeError(f"Failed to get web apps: {str(e)}")

    def get_publishing_credentials(
        self, resource_group: str, web_app_name: str
    ) -> Dict[str, str]:
        """Get publishing credentials for a web app."""
        try:
            credentials = self.web_client.web_apps.begin_list_publishing_credentials(
                resource_group_name=resource_group, name=web_app_name
            ).result()
            return {
                "username": credentials.publishing_user_name,
                "password": credentials.publishing_password,
            }
        except ResourceNotFoundError:
            error_msg = f"Web app '{web_app_name}' not found in resource group '{resource_group}'"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except HttpResponseError as e:
            logger.error(
                f"Azure API error while getting publishing credentials: {str(e)}"
            )
            raise RuntimeError(f"Failed to get publishing credentials: {str(e)}")
        except Exception as e:
            logger.error(
                f"Unexpected error while getting publishing credentials: {str(e)}"
            )
            raise RuntimeError(f"Failed to get publishing credentials: {str(e)}")

    def stream_logs(
        self,
        resource_group: str,
        web_app_name: str,
        callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Stream logs from a web app with memory management."""
        with self.stream_lock:
            if self.active_streams >= MAX_CONCURRENT_STREAMS:
                raise RuntimeError("Maximum number of concurrent log streams reached")
            self.active_streams += 1

        try:
            # Get publishing credentials
            credentials = self.get_publishing_credentials(resource_group, web_app_name)

            # Construct log streaming URL
            base_url = f"https://{web_app_name}.scm.azurewebsites.net"
            log_url = urljoin(base_url, "/api/logstream")

            # Create session with retry logic
            session = requests.Session()
            retry_strategy = Retry(
                total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)

            # Start log streaming with timeout
            with session.get(
                log_url,
                auth=(credentials["username"], credentials["password"]),
                stream=True,
                timeout=30,
            ) as response:
                response.raise_for_status()

                # Stream logs with memory management
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        self.log_buffer.append(decoded_line)
                        if callback:
                            callback(decoded_line)

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to connect to log stream: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            logger.error(f"Error streaming logs: {str(e)}")
            raise RuntimeError(f"Failed to stream logs: {str(e)}")
        finally:
            with self.stream_lock:
                self.active_streams -= 1
            # Force cleanup
            gc.collect()

    def get_webapp_logs(
        self, webapp_name: str, resource_group: str
    ) -> Generator[str, None, None]:
        """Stream logs from Azure Web App."""
        try:
            # Get web app details
            webapp = self.web_client.web_apps.get(resource_group, webapp_name)
            if not webapp:
                raise ValueError(f"Web app {webapp_name} not found")

            # Get publishing profile (returns a stream/generator)
            publishing_profile_stream = (
                self.web_client.web_apps.list_publishing_profile_xml_with_secrets(
                    resource_group, webapp_name, {"format": "WebDeploy"}
                )
            )
            # Read the stream into a string
            publishing_profile = b"".join(
                [chunk for chunk in publishing_profile_stream]
            ).decode("utf-8")

            try:
                root = ET.fromstring(publishing_profile)
            except Exception as e:
                logger.error(
                    f"Failed to parse publishing profile XML: {e}\nRaw XML: {publishing_profile}"
                )
                raise

            # Find any publishProfile element
            publish_profile_elem = None
            for elem in root.iter("publishProfile"):
                publish_profile_elem = elem
                break
            if publish_profile_elem is None:
                logger.error(
                    f"No <publishProfile> element found in publishing profile XML. Raw XML: {publishing_profile}"
                )
                raise ValueError("Could not find publishing profile data")

            # Get the SCM URL from the publishProfile
            scm_url = publish_profile_elem.get("publishUrl")
            if not scm_url:
                logger.error(
                    f"No publishUrl attribute found in <publishProfile>. Raw XML: {publishing_profile}"
                )
                raise ValueError("Could not determine SCM URL from publishing profile")

            # Construct the log stream URL
            log_stream_url = f"https://{scm_url}/api/logstream"

            # Get access token
            token = self.credential.get_token(
                "https://management.azure.com/.default"
            ).token

            # Stream logs
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "text/event-stream",
            }
            with requests.get(
                log_stream_url, headers=headers, stream=True, timeout=30
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        yield line.decode("utf-8")
        except Exception as e:
            logger.error(f"Error streaming logs: {str(e)}")
            raise

    def get_webapp_resource_group(self, webapp_name: str) -> Optional[str]:
        """
        Get the resource group name for a web app.

        Args:
            webapp_name: The name of the web app

        Returns:
            The resource group name if found, None otherwise
        """
        try:
            # List all web apps in the subscription
            webapps = self.web_client.web_apps.list()

            # Find the matching web app
            for webapp in webapps:
                if webapp.name == webapp_name:
                    # Extract resource group from the web app's ID
                    # Format: /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Web/sites/{name}
                    return webapp.id.split("/")[4]

            return None

        except Exception as e:
            logger.error(f"Error finding resource group: {str(e)}")
            return None

    def list_webapps(self) -> List[Dict[str, str]]:
        """List all web apps in the subscription.

        Returns:
            List of dictionaries containing web app information
        """
        try:
            # Get web apps from the subscription
            webapps = []
            for webapp in self.web_client.web_apps.list():
                webapps.append(
                    {
                        "name": webapp.name,
                        "resource_group": webapp.resource_group,
                        "state": webapp.state,
                        "default_host_name": webapp.default_host_name,
                    }
                )
            return webapps
        except Exception as e:
            logger.error(f"Error listing web apps: {str(e)}")
            raise

    def stream_logs(self, webapp_name: str, callback: Callable[[str], None]) -> None:
        """Stream logs from the specified web app."""
        try:
            # Get the web app
            webapp = self.web_client.web_apps.get(
                resource_group_name=self.get_webapp_resource_group(webapp_name),
                name=webapp_name,
            )

            # Get publish profile
            publish_profile = (
                self.web_client.web_apps.list_publishing_profile_xml_with_secrets(
                    resource_group_name=self.get_webapp_resource_group(webapp_name),
                    name=webapp_name,
                    publishing_profile_options=WebAppPublishingProfileOptions(),
                )
            )

            # Parse publish profile
            publish_profile_dict = {}
            for line in publish_profile.decode("utf-8").split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    publish_profile_dict[key.strip()] = value.strip()

            # Get SCM URL
            scm_url = publish_profile_dict.get("MSDeployServiceURL", "").replace(
                "https://", ""
            )
            if not scm_url:
                raise ValueError("Could not find SCM URL in publish profile")

            # Create session with retry logic
            session = requests.Session()
            retry_strategy = Retry(
                total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)

            # Stream logs with timeout handling
            url = f"https://{scm_url}/api/logstream"
            auth = (
                publish_profile_dict.get("userName", ""),
                publish_profile_dict.get("userPWD", ""),
            )

            with session.get(url, auth=auth, stream=True, timeout=30) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            callback(line.decode("utf-8"))
                        except Exception as e:
                            logger.error(f"Error processing log line: {e}")
                            continue

        except requests.exceptions.Timeout:
            logger.error("Timeout while streaming logs")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error streaming logs: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error streaming logs: {e}")
            raise

    def list_resource_groups(self) -> List[str]:
        """List all resource groups in the subscription.

        Returns:
            List of resource group names
        """
        try:
            resource_groups = []
            for rg in self.web_client.resource_client.resource_groups.list():
                resource_groups.append(rg.name)
            return resource_groups
        except Exception as e:
            logger.error(f"Error listing resource groups: {str(e)}")
            raise

    def list_webapps_by_resource_group(
        self, resource_group: str
    ) -> List[Dict[str, str]]:
        """List all web apps in a specific resource group.

        Args:
            resource_group: The name of the resource group

        Returns:
            List of dictionaries containing web app information
        """
        try:
            # Get web apps from the resource group
            webapps = []
            for webapp in self.web_client.web_apps.list_by_resource_group(
                resource_group
            ):
                webapps.append(
                    {
                        "name": webapp.name,
                        "resource_group": webapp.resource_group,
                        "state": webapp.state,
                        "default_host_name": webapp.default_host_name,
                    }
                )
            return webapps
        except Exception as e:
            logger.error(
                f"Error listing web apps for resource group {resource_group}: {str(e)}"
            )
            raise
