"""Tests for the mAultenance data update coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.maultenance.api import (
    MaultenanceApiClientAuthError,
    MaultenanceApiClientCommunicationError,
)
from custom_components.maultenance.coordinator import MaultenanceDataUpdateCoordinator

from .conftest import TASK


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
