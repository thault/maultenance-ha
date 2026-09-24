"""Tests for setting up and unloading the mAultenance config entry."""

from __future__ import annotations

import logging

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .conftest import BASE_URL, TASK, TOKEN

TASKS_URL = f"{BASE_URL}/api/v1/tasks"


async def test_setup_and_unload_entry(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The entry sets up, performs a first refresh, and unloads cleanly.

    Also confirms setup/unload log the base_url (never the token).
    """
    aioclient_mock.get(TASKS_URL, json=[TASK])
    mock_config_entry.add_to_hass(hass)

    with caplog.at_level(logging.DEBUG, logger="custom_components.maultenance"):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.LOADED
        assert mock_config_entry.runtime_data.data == {TASK["id"]: TASK}

        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.NOT_LOADED

    assert BASE_URL in caplog.text
    assert TOKEN not in caplog.text


async def test_setup_entry_auth_failure_triggers_reauth(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """A 401 on first refresh leaves the entry in SETUP_ERROR and starts reauth."""
    aioclient_mock.get(TASKS_URL, status=401)
    mock_config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(mock_config_entry.domain)
    assert any(flow["context"].get("source") == "reauth" for flow in flows)
