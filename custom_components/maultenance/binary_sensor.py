"""Binary sensor platform for mAultenance: one overdue flag per task."""

from __future__ import annotations

from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MaultenanceConfigEntry
from .entity import MaultenanceTaskEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MaultenanceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up mAultenance overdue binary sensors."""
    coordinator = entry.runtime_data
    known_task_ids: set[str] = set()

    @callback
    def _async_add_new_entities() -> None:
        new_ids = set(coordinator.data) - known_task_ids
        if not new_ids:
            return
        known_task_ids.update(new_ids)
        async_add_entities(MaultenanceOverdueSensor(coordinator, task_id) for task_id in new_ids)

    _async_add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_entities))


class MaultenanceOverdueSensor(MaultenanceTaskEntity, BinarySensorEntity):
    """Whether a task is currently overdue."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_name = "Overdue"

    def __init__(self, coordinator, task_id: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, task_id)
        self._attr_unique_id = f"{task_id}_overdue"

    @property
    @override
    def is_on(self) -> bool:
        """Return True if the task is overdue."""
        return self.task["is_overdue"]
