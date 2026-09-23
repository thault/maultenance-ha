"""Tests for the mAultenance data update coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.maultenance.api import (
    MaultenanceApiClientAuthError,
    MaultenanceApiClientCommunicationError,
)
from custom_components.maultenance.const import DOMAIN
from custom_components.maultenance.coordinator import MaultenanceDataUpdateCoordinator

from .conftest import BASE_URL, TASK

TASKS_URL = f"{BASE_URL}/api/v1/tasks"

OTHER_TASK = {
    "id": "task-2",
    "title": "Clean gutters",
    "created_by": "user-1",
    "current_due_date": "2026-11-15",
    "is_overdue": False,
}


async def test_update_data_keys_tasks_by_id(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Tasks are returned keyed by their id for O(1) lookups."""
    mock_config_entry.add_to_hass(hass)
    client = AsyncMock()
    client.async_list_tasks.return_value = [TASK]
    coordinator = MaultenanceDataUpdateCoordinator(hass, mock_config_entry, client)

    data = await coordinator._async_update_data()

    assert data == {TASK["id"]: TASK}


async def test_auth_error_raises_config_entry_auth_failed(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """An auth error from the client surfaces as ConfigEntryAuthFailed (triggers reauth)."""
    mock_config_entry.add_to_hass(hass)
    client = AsyncMock()
    client.async_list_tasks.side_effect = MaultenanceApiClientAuthError("401")
    coordinator = MaultenanceDataUpdateCoordinator(hass, mock_config_entry, client)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_communication_error_raises_update_failed(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """A connection/communication error surfaces as UpdateFailed."""
    mock_config_entry.add_to_hass(hass)
    client = AsyncMock()
    client.async_list_tasks.side_effect = MaultenanceApiClientCommunicationError("boom")
    coordinator = MaultenanceDataUpdateCoordinator(hass, mock_config_entry, client)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_archived_task_device_and_entities_are_removed(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """A task that drops out of a later refresh has its device+entities removed."""
    aioclient_mock.get(TASKS_URL, json=[TASK, OTHER_TASK])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    entry_id = mock_config_entry.entry_id

    def get_device(task_id: str):
        return device_registry.async_get_device_by_identifier((DOMAIN, task_id), entry_id)

    assert get_device(OTHER_TASK["id"]) is not None
    assert entity_registry.async_get_entity_id("sensor", DOMAIN, f"{OTHER_TASK['id']}_due_date")

    aioclient_mock.clear_requests()
    aioclient_mock.get(TASKS_URL, json=[TASK])  # OTHER_TASK archived
    await mock_config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert get_device(OTHER_TASK["id"]) is None
    assert not entity_registry.async_get_entity_id(
        "sensor", DOMAIN, f"{OTHER_TASK['id']}_due_date"
    )
    assert not entity_registry.async_get_entity_id(
        "binary_sensor", DOMAIN, f"{OTHER_TASK['id']}_overdue"
    )
    # TASK's device/entities are untouched.
    assert get_device(TASK["id"]) is not None
    assert entity_registry.async_get_entity_id("sensor", DOMAIN, f"{TASK['id']}_due_date")
