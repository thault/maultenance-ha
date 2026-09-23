"""Data update coordinator for the mAultenance integration."""

from __future__ import annotations

from typing import Any, override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
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
        """Fetch active tasks, keyed by task id, and prune devices for archived ones."""
        try:
            tasks = await self.client.async_list_tasks()
        except MaultenanceApiClientAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except MaultenanceApiClientCommunicationError as err:
            raise UpdateFailed(str(err)) from err

        new_data = {task["id"]: task for task in tasks}
        previous_ids = set(self.data) if self.data else set()
        removed_ids = previous_ids - new_data.keys()
        if removed_ids:
            self._async_remove_stale_devices(removed_ids)
        return new_data

    def _async_remove_stale_devices(self, removed_task_ids: set[str]) -> None:
        """Remove the device (and cascading entities) for tasks no longer active.

        A task drops out of GET /tasks once archived; there's no separate
        "deleted" event to react to, so this diffs each refresh against the
        previous one instead.
        """
        device_registry = dr.async_get(self.hass)
        for task_id in removed_task_ids:
            device = device_registry.async_get_device_by_identifier(
                (DOMAIN, task_id), self.config_entry.entry_id
            )
            if device is not None:
                device_registry.async_remove_device(device.id)
