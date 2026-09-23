"""Data update coordinator for the mAultenance integration."""

from __future__ import annotations

from typing import Any, override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    MaultenanceApiClient,
    MaultenanceApiClientAuthError,
    MaultenanceApiClientCommunicationError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER

type MaultenanceConfigEntry = ConfigEntry[MaultenanceDataUpdateCoordinator]


class MaultenanceDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator that polls GET /api/v1/tasks, keyed by task id."""

    config_entry: MaultenanceConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: MaultenanceConfigEntry,
        client: MaultenanceApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    @override
    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch active tasks, keyed by task id."""
        try:
            tasks = await self.client.async_list_tasks()
        except MaultenanceApiClientAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except MaultenanceApiClientCommunicationError as err:
            raise UpdateFailed(str(err)) from err
        return {task["id"]: task for task in tasks}
