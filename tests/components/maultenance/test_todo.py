"""Tests for the mAultenance todo list entity."""

from __future__ import annotations

from datetime import date

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .conftest import BASE_URL, TASK

TASKS_URL = f"{BASE_URL}/api/v1/tasks"
COMPLETIONS_URL = f"{BASE_URL}/api/v1/tasks/{TASK['id']}/completions"

DONE_ONE_OFF_TASK = {
    "id": "task-3",
    "title": "File taxes",
    "created_by": "user-1",
    "current_due_date": "2026-04-15",
    "is_overdue": False,
    "done": True,
    "last_completed_at": "2026-04-01T00:00:00Z",
}


async def test_todo_items_reflect_tasks(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Active tasks show up as todo items; a completed one-off shows as completed."""
    aioclient_mock.get(TASKS_URL, json=[TASK, DONE_ONE_OFF_TASK])
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("todo.maultenance")
    assert state is not None
    assert state.state == "1"  # one NEEDS_ACTION item


async def test_completing_todo_item_calls_api(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Checking off a task item calls the completions endpoint and refreshes."""
    aioclient_mock.get(TASKS_URL, json=[TASK])
    aioclient_mock.post(COMPLETIONS_URL, status=201, json={"id": "c-1"})
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        "todo",
        "update_item",
        {"entity_id": "todo.maultenance", "item": TASK["id"], "status": "completed"},
        blocking=True,
    )
    await hass.async_block_till_done()

    completion_calls = [c for c in aioclient_mock.mock_calls if str(c[1]).endswith("/completions")]
    assert len(completion_calls) == 1


async def test_uncompleting_todo_item_is_rejected(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """mAultenance has no 'uncomplete' endpoint, so that direction is rejected."""
    aioclient_mock.get(TASKS_URL, json=[DONE_ONE_OFF_TASK])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "todo",
            "update_item",
            {
                "entity_id": "todo.maultenance",
                "item": DONE_ONE_OFF_TASK["id"],
                "status": "needs_action",
            },
            blocking=True,
        )
