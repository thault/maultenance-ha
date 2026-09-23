"""Sensor platform for mAultenance: one due-date sensor per task."""

from __future__ import annotations

from datetime import date
from typing import Any, override

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import MaultenanceConfigEntry
from .entity import MaultenanceTaskEntity

# Keys present on the task dict that should ride along as sensor attributes,
# beyond the ones already surfaced elsewhere (id/current_due_date/is_overdue).
_ATTRIBUTE_KEYS = (
    "title",
    "description",
    "rrule",
    "rrule_dtstart",
    "anchor_mode",
    "done",
    "last_completed_at",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MaultenanceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up mAultenance due-date sensors."""
    coordinator = entry.runtime_data
    known_task_ids: set[str] = set()

    @callback
    def _async_add_new_entities() -> None:
        new_ids = set(coordinator.data) - known_task_ids
        if not new_ids:
            return
        known_task_ids.update(new_ids)
        async_add_entities(MaultenanceDueDateSensor(coordinator, task_id) for task_id in new_ids)

    _async_add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_async_add_new_entities))


class MaultenanceDueDateSensor(MaultenanceTaskEntity, SensorEntity):
    """The current due date of a task."""

    _attr_device_class = SensorDeviceClass.DATE
    _attr_name = "Due date"

    def __init__(self, coordinator, task_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, task_id)
        self._attr_unique_id = f"{task_id}_due_date"

    @property
    @override
    def native_value(self) -> date:
        """Return the task's current due date."""
        return date.fromisoformat(self.task["current_due_date"])

    @property
    @override
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the task fields not already covered elsewhere."""
        return {key: self.task[key] for key in _ATTRIBUTE_KEYS if key in self.task}
