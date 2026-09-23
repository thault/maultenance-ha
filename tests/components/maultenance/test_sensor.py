"""Tests for the mAultenance due-date sensor platform."""

from __future__ import annotations

from datetime import date

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .conftest import BASE_URL, TASK

TASKS_URL = f"{BASE_URL}/api/v1/tasks"

OTHER_TASK = {
    "id": "task-2",
    "title": "Clean gutters",
    "created_by": "user-1",
    "current_due_date": "2026-11-15",
    "is_overdue": True,
}


async def test_sensor_created_for_each_task(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """One due-date sensor is created per active task."""
    aioclient_mock.get(TASKS_URL, json=[TASK, OTHER_TASK])
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.replace_furnace_filter_due_date")
    assert state is not None
    assert state.state == date.fromisoformat(TASK["current_due_date"]).isoformat()
    assert state.attributes["title"] == TASK["title"]

    other_state = hass.states.get("sensor.clean_gutters_due_date")
    assert other_state is not None
    assert other_state.state == date.fromisoformat(OTHER_TASK["current_due_date"]).isoformat()


async def test_sensor_added_dynamically_on_refresh(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """A task that appears in a later refresh gets its own sensor without a reload."""
    aioclient_mock.get(TASKS_URL, json=[TASK])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.clean_gutters_due_date") is None

    aioclient_mock.clear_requests()
    aioclient_mock.get(TASKS_URL, json=[TASK, OTHER_TASK])
    await mock_config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("sensor.clean_gutters_due_date") is not None
