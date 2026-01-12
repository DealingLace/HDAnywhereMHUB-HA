"""API Client for HDAnywhere MHUB devices."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout

from .const import (
    API_BASE_PATH,
    API_ENDPOINT_DEVICE_STATE,
    API_ENDPOINT_POWER,
    API_ENDPOINT_SWITCH,
    API_ENDPOINT_SYSTEM_INFO,
    API_ENDPOINT_ZONE_DATA,
    API_VERSION_2_1,
    BACKOFF_MULTIPLIER,
    CONNECTION_TIMEOUT,
    DEFAULT_TIMEOUT,
    MAX_CONNECTIONS,
    MAX_RETRIES,
    RETRY_DELAY,
)
from .exceptions import (
    MHUBCommandError,
    MHUBConnectionError,
    MHUBInvalidResponse,
    MHUBTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


class MHUBApiClient:
    """API Client for HDAnywhere MHUB devices with advanced features.

    Features:
    - Connection pooling for efficient resource usage
    - Automatic retry with exponential backoff
    - Comprehensive error handling and logging
    - Timeout management
    - Session reuse
    """

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        api_version: str = API_VERSION_2_1,
    ) -> None:
        """Initialize the MHUB API client.

        Args:
            host: IP address or hostname of the MHUB device
            session: Optional aiohttp session for connection pooling
            timeout: Request timeout in seconds
            api_version: API version to use (2.0 or 2.1)
        """
        self.host = host
        self.base_url = f"http://{host}{API_BASE_PATH}"
        self._session = session
        self._timeout = timeout
        self._api_version = api_version
        self._own_session = session is None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=MAX_CONNECTIONS,
                limit_per_host=MAX_CONNECTIONS,
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
            )
            timeout = aiohttp.ClientTimeout(
                total=CONNECTION_TIMEOUT,
                connect=self._timeout,
                sock_read=self._timeout,
            )
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                raise_for_status=False,
            )
        return self._session

    async def _request(
        self,
        method: str,
        endpoint: str,
        retry_count: int = 0,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            retry_count: Current retry attempt number
            **kwargs: Additional arguments for the request

        Returns:
            JSON response as dictionary

        Raises:
            MHUBConnectionError: Connection to device failed
            MHUBTimeoutError: Request timed out
            MHUBInvalidResponse: Invalid response from device
        """
        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()

        try:
            async with async_timeout.timeout(self._timeout):
                _LOGGER.debug("Making %s request to %s (attempt %d)", method, url, retry_count + 1)

                async with session.request(method, url, **kwargs) as response:
                    response_text = await response.text()

                    if response.status == 200:
                        try:
                            data = await response.json()
                            _LOGGER.debug("Received response from %s: %s", endpoint, data)
                            return data
                        except (aiohttp.ContentTypeError, ValueError) as err:
                            _LOGGER.error("Invalid JSON response from %s: %s", url, response_text)
                            raise MHUBInvalidResponse(f"Invalid JSON response: {err}") from err
                    else:
                        _LOGGER.warning(
                            "Request to %s failed with status %d: %s",
                            url,
                            response.status,
                            response_text,
                        )

                        # Retry on specific status codes
                        if response.status in (500, 502, 503, 504) and retry_count < MAX_RETRIES:
                            delay = RETRY_DELAY * (BACKOFF_MULTIPLIER ** retry_count)
                            _LOGGER.info("Retrying request to %s after %s seconds", url, delay)
                            await asyncio.sleep(delay)
                            return await self._request(method, endpoint, retry_count + 1, **kwargs)

                        raise MHUBConnectionError(
                            f"Request failed with status {response.status}: {response_text}"
                        )

        except asyncio.TimeoutError as err:
            if retry_count < MAX_RETRIES:
                delay = RETRY_DELAY * (BACKOFF_MULTIPLIER ** retry_count)
                _LOGGER.info("Request to %s timed out, retrying after %s seconds", url, delay)
                await asyncio.sleep(delay)
                return await self._request(method, endpoint, retry_count + 1, **kwargs)

            _LOGGER.error("Request to %s timed out after %d retries", url, retry_count)
            raise MHUBTimeoutError(f"Request timed out after {retry_count + 1} attempts") from err

        except aiohttp.ClientError as err:
            if retry_count < MAX_RETRIES:
                delay = RETRY_DELAY * (BACKOFF_MULTIPLIER ** retry_count)
                _LOGGER.info("Connection error to %s, retrying after %s seconds: %s", url, delay, err)
                await asyncio.sleep(delay)
                return await self._request(method, endpoint, retry_count + 1, **kwargs)

            _LOGGER.error("Connection error to %s after %d retries: %s", url, retry_count, err)
            raise MHUBConnectionError(f"Connection failed: {err}") from err

    async def get_system_info(self) -> dict[str, Any]:
        """Retrieve system information from the MHUB device.

        Returns:
            Dictionary containing system information including:
            - mhub_name: Device name
            - io_data: Input/output configuration
            - firmware_version: Firmware version
            - hardware_version: Hardware version
        """
        _LOGGER.debug("Fetching system information from %s", self.host)
        response = await self._request("GET", API_ENDPOINT_SYSTEM_INFO)

        if "data" not in response:
            raise MHUBInvalidResponse("System info response missing 'data' field")

        return response["data"]

    async def get_zone_data(self) -> dict[int, dict[str, Any]]:
        """Retrieve zone configuration data (API v2.1 only).

        Returns:
            Dictionary mapping output IDs to zone information:
            {
                output_id: {
                    "zone_label": "Living Room",
                    "arc_input": 1,
                    "auto_switch_mode": False
                }
            }
        """
        _LOGGER.debug("Fetching zone data from %s", self.host)
        response = await self._request("GET", API_ENDPOINT_ZONE_DATA)

        if "data" not in response:
            raise MHUBInvalidResponse("Zone data response missing 'data' field")

        zone_data = response["data"]
        zone_mapping: dict[int, dict[str, Any]] = {}

        for zone in zone_data:
            for output in zone.get("outputs", []):
                output_id = output.get("output_id")
                if output_id:
                    zone_mapping[output_id] = {
                        "zone_label": zone.get("zone_label", "Unknown Zone"),
                        "arc_input": output.get("arc_input"),
                        "auto_switch_mode": zone.get("auto_switch_mode", False),
                    }

        _LOGGER.debug("Retrieved %d zone mappings", len(zone_mapping))
        return zone_mapping

    async def get_device_state(self) -> dict[str, Any]:
        """Get current device power state and other status information.

        Returns:
            Dictionary containing device state:
            - power: Boolean indicating if device is powered on
            - Additional status information
        """
        _LOGGER.debug("Fetching device state from %s", self.host)
        response = await self._request("GET", API_ENDPOINT_DEVICE_STATE)

        if "data" not in response:
            raise MHUBInvalidResponse("Device state response missing 'data' field")

        return response["data"]

    async def set_power(self, power_on: bool) -> bool:
        """Set the power state of the MHUB device.

        Args:
            power_on: True to power on, False to power off

        Returns:
            True if command was successful

        Raises:
            MHUBCommandError: Command execution failed
        """
        power_value = 1 if power_on else 0
        endpoint = f"{API_ENDPOINT_POWER}/{power_value}/"

        _LOGGER.debug("Setting power state to %s on %s", "ON" if power_on else "OFF", self.host)

        try:
            await self._request("POST", endpoint)
            _LOGGER.info("Successfully set power to %s", "ON" if power_on else "OFF")
            return True
        except Exception as err:
            _LOGGER.error("Failed to set power state: %s", err)
            raise MHUBCommandError(f"Failed to set power state: {err}") from err

    async def switch_output(self, output_id: str, input_id: str) -> bool:
        """Switch an output to a specific input source.

        Args:
            output_id: Output identifier (e.g., 'a', 'b', 'c')
            input_id: Input identifier (e.g., '1', '2', '3')

        Returns:
            True if command was successful

        Raises:
            MHUBCommandError: Command execution failed
        """
        endpoint = f"{API_ENDPOINT_SWITCH}/{output_id.lower()}/{input_id}/"

        _LOGGER.debug("Switching output %s to input %s on %s", output_id, input_id, self.host)

        try:
            await self._request("GET", endpoint)
            _LOGGER.info("Successfully switched output %s to input %s", output_id, input_id)
            return True
        except Exception as err:
            _LOGGER.error("Failed to switch output: %s", err)
            raise MHUBCommandError(f"Failed to switch output: {err}") from err

    async def test_connection(self) -> bool:
        """Test connection to the MHUB device.

        Returns:
            True if connection is successful
        """
        try:
            await self.get_device_state()
            _LOGGER.debug("Connection test to %s successful", self.host)
            return True
        except Exception as err:
            _LOGGER.error("Connection test to %s failed: %s", self.host, err)
            return False

    async def close(self) -> None:
        """Close the API client and cleanup resources."""
        if self._session and not self._session.closed and self._own_session:
            _LOGGER.debug("Closing API client session for %s", self.host)
            await self._session.close()
            # Give the connector time to close properly
            await asyncio.sleep(0.25)
