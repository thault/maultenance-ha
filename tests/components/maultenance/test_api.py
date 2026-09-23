"""Tests for the mAultenance API client."""

from __future__ import annotations

import aiohttp
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.maultenance.api import (
    MaultenanceApiClient,
    MaultenanceApiClientAuthError,
    MaultenanceApiClientCommunicationError,
)

BASE_URL = "http://maultenance.local:8080"
TOKEN = "test-token"

TASK = {
    "id": "task-1",
    "title": "Replace furnace filter",
    "created_by": "user-1",
    "current_due_date": "2026-10-01",
    "is_overdue": False,
}


@pytest.fixture
async def client(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> MaultenanceApiClient:
    # aioclient_mock must be resolved before async_get_clientsession() creates
    # (and hass caches) the session, or it'll cache the real, unpatched one.
    return MaultenanceApiClient(BASE_URL, TOKEN, async_get_clientsession(hass))


async def test_list_tasks_success(
    client: MaultenanceApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(f"{BASE_URL}/api/v1/tasks", json=[TASK])

    tasks = await client.async_list_tasks()

    assert tasks == [TASK]


async def test_list_tasks_sends_bearer_token(
    client: MaultenanceApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(f"{BASE_URL}/api/v1/tasks", json=[])

    await client.async_list_tasks()

    assert aioclient_mock.mock_calls[0][3]["Authorization"] == f"Bearer {TOKEN}"


async def test_list_tasks_with_status_filter(
    client: MaultenanceApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(f"{BASE_URL}/api/v1/tasks", json=[TASK])

    tasks = await client.async_list_tasks(status="overdue")

    assert tasks == [TASK]
    assert aioclient_mock.mock_calls[0][1].query["status"] == "overdue"


async def test_list_tasks_auth_error(
    client: MaultenanceApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(f"{BASE_URL}/api/v1/tasks", status=401)

    with pytest.raises(MaultenanceApiClientAuthError):
        await client.async_list_tasks()


async def test_list_tasks_server_error(
    client: MaultenanceApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(f"{BASE_URL}/api/v1/tasks", status=500)

    with pytest.raises(MaultenanceApiClientCommunicationError):
        await client.async_list_tasks()


async def test_list_tasks_connection_error(
    client: MaultenanceApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(f"{BASE_URL}/api/v1/tasks", exc=aiohttp.ClientConnectionError("boom"))

    with pytest.raises(MaultenanceApiClientCommunicationError):
        await client.async_list_tasks()


async def test_complete_task_sends_completed_at(
    client: MaultenanceApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.post(
        f"{BASE_URL}/api/v1/tasks/task-1/completions", status=201, json={"id": "c-1"}
    )

    await client.async_complete_task("task-1", completed_at="2026-09-20T00:00:00Z")

    assert aioclient_mock.mock_calls[0][2] == {"completed_at": "2026-09-20T00:00:00Z"}


async def test_complete_task_defaults_to_now(
    client: MaultenanceApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.post(
        f"{BASE_URL}/api/v1/tasks/task-1/completions", status=201, json={"id": "c-1"}
    )

    await client.async_complete_task("task-1")

    assert aioclient_mock.mock_calls[0][2] is None


async def test_complete_task_not_found(
    client: MaultenanceApiClient, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.post(f"{BASE_URL}/api/v1/tasks/task-1/completions", status=404)

    with pytest.raises(MaultenanceApiClientCommunicationError):
        await client.async_complete_task("task-1")
