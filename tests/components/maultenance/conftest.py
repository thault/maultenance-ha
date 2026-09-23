"""Fixtures for mAultenance integration tests."""

from __future__ import annotations

import pytest

from custom_components.maultenance.const import CONF_API_TOKEN, CONF_BASE_URL, DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

BASE_URL = "http://maultenance.local:8080"
TOKEN = "test-token"

TASK = {
    "id": "task-1",
    "title": "Replace furnace filter",
    "created_by": "user-1",
    "current_due_date": "2026-10-01",
    "is_overdue": False,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading this custom component in every test."""
    return


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock mAultenance config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=BASE_URL,
        data={CONF_BASE_URL: BASE_URL, CONF_API_TOKEN: TOKEN},
        unique_id=BASE_URL,
    )
