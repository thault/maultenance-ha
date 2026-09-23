"""Tests for the mAultenance overdue binary sensor platform."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .conftest import BASE_URL, TASK

TASKS_URL = f"{BASE_URL}/api/v1/tasks"

OVERDUE_TASK = {
    "id": "task-2",
    "title": "Clean gutters",
    "created_by": "user-1",
    "current_due_date": "2026-01-01",
    "is_overdue": True,
}


async def test_binary_sensor_reflects_overdue_state(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """The binary sensor state matches is_overdue for each task."""
    aioclient_mock.get(TASKS_URL, json=[TASK, OVERDUE_TASK])
    mock_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.replace_furnace_filter_overdue").state == "off"
    assert hass.states.get("binary_sensor.clean_gutters_overdue").state == "on"
