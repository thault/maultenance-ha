"""Todo platform for mAultenance: a single checklist of active tasks."""

from __future__ import annotations

from datetime import date
from typing import Any, override

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MaultenanceConfigEntry, MaultenanceDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MaultenanceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the mAultenance todo list entity."""
    async_add_entities([MaultenanceTodoListEntity(entry.runtime_data, entry.entry_id)])


def _todo_item_for_task(task: dict[str, Any]) -> TodoItem:
    """Build a TodoItem for a task.

    `done` only exists for one-off tasks, so a recurring task never renders
    as COMPLETED here - completing one just advances current_due_date on
    the next refresh rather than marking a fixed item done.
    """
    completed = task.get("done", False)
    return TodoItem(
        uid=task["id"],
        summary=task["title"],
        status=TodoItemStatus.COMPLETED if completed else TodoItemStatus.NEEDS_ACTION,
        due=None if completed else date.fromisoformat(task["current_due_date"]),
    )


class MaultenanceTodoListEntity(
    CoordinatorEntity[MaultenanceDataUpdateCoordinator], TodoListEntity
):
    """A single checklist of all active mAultenance tasks."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM

    def __init__(self, coordinator: MaultenanceDataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the todo list entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_todo"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="mAultenance",
            manufacturer="mAultenance",
        )

    @property
    @override
    def todo_items(self) -> list[TodoItem]:
        """Return all active tasks as todo items."""
        return [_todo_item_for_task(task) for task in self.coordinator.data.values()]

    @override
    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Mark a task complete.

        mAultenance has no "uncomplete" endpoint, so any update that isn't a
        transition to COMPLETED (unchecking an item, or any other change -
        renaming isn't supported either) is rejected.
        """
        if item.status != TodoItemStatus.COMPLETED or item.uid is None:
            raise HomeAssistantError(
                "mAultenance tasks can only be marked done from Home Assistant"
            )
        await self.coordinator.client.async_complete_task(item.uid)
        await self.coordinator.async_request_refresh()
