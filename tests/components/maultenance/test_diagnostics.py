"""Tests for mAultenance diagnostics."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.maultenance.diagnostics import async_get_config_entry_diagnostics

from .conftest import BASE_URL, TASK, TOKEN

TASKS_URL = f"{BASE_URL}/api/v1/tasks"


async def test_diagnostics_redacts_token(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """The PAT is redacted; task data passes through."""
    aioclient_mock.get(TASKS_URL, json=[TASK])
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert TOKEN not in str(diagnostics["entry_data"])
    assert diagnostics["tasks"] == [TASK]
