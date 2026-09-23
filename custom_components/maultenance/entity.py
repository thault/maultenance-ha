"""Base entity for per-task mAultenance entities."""

from __future__ import annotations

from typing import Any, override

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MaultenanceDataUpdateCoordinator


class MaultenanceTaskEntity(CoordinatorEntity[MaultenanceDataUpdateCoordinator]):
    """Base for entities backed by a single task, grouped as one device per task."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: MaultenanceDataUpdateCoordinator, task_id: str) -> None:
        """Initialize the entity for the given task id."""
        super().__init__(coordinator)
        self.task_id = task_id

    @property
    def task(self) -> dict[str, Any]:
        """Return the current task data for this entity."""
        return self.coordinator.data[self.task_id]

    @property
    @override
    def available(self) -> bool:
        """Return True if the task still exists in the latest refresh."""
        return super().available and self.task_id in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info, recomputed so a renamed task's device name follows."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.task_id)},
            name=self.task["title"],
            manufacturer="mAultenance",
            model="Task",
        )
