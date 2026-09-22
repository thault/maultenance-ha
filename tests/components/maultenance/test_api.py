"""Tests for the mAultenance API client."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

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
async def client() -> MaultenanceApiClient:
    async with aiohttp.ClientSession() as session:
        yield MaultenanceApiClient(BASE_URL, TOKEN, session)


async def test_list_tasks_success(client: MaultenanceApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/v1/tasks", payload=[TASK])
        tasks = await client.async_list_tasks()

    assert tasks == [TASK]


async def test_list_tasks_sends_bearer_token(client: MaultenanceApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/v1/tasks", payload=[])
        await client.async_list_tasks()

    request = next(iter(m.requests.values()))[0]
    assert request.kwargs["headers"]["Authorization"] == f"Bearer {TOKEN}"


async def test_list_tasks_with_status_filter(client: MaultenanceApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/v1/tasks?status=overdue", payload=[TASK])
        tasks = await client.async_list_tasks(status="overdue")

    assert tasks == [TASK]


async def test_list_tasks_auth_error(client: MaultenanceApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/v1/tasks", status=401)
        with pytest.raises(MaultenanceApiClientAuthError):
            await client.async_list_tasks()


async def test_list_tasks_server_error(client: MaultenanceApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/v1/tasks", status=500)
        with pytest.raises(MaultenanceApiClientCommunicationError):
            await client.async_list_tasks()


async def test_list_tasks_connection_error(client: MaultenanceApiClient) -> None:
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/v1/tasks", exception=aiohttp.ClientConnectionError("boom"))
        with pytest.raises(MaultenanceApiClientCommunicationError):
            await client.async_list_tasks()


async def test_complete_task_sends_completed_at(client: MaultenanceApiClient) -> None:
    with aioresponses() as m:
        m.post(f"{BASE_URL}/api/v1/tasks/task-1/completions", status=201, payload={"id": "c-1"})
        await client.async_complete_task("task-1", completed_at="2026-09-20T00:00:00Z")

    request = next(iter(m.requests.values()))[0]
    assert request.kwargs["json"] == {"completed_at": "2026-09-20T00:00:00Z"}


async def test_complete_task_defaults_to_now(client: MaultenanceApiClient) -> None:
    with aioresponses() as m:
        m.post(f"{BASE_URL}/api/v1/tasks/task-1/completions", status=201, payload={"id": "c-1"})
        await client.async_complete_task("task-1")

    request = next(iter(m.requests.values()))[0]
    assert request.kwargs["json"] is None


async def test_complete_task_not_found(client: MaultenanceApiClient) -> None:
    with aioresponses() as m:
        m.post(f"{BASE_URL}/api/v1/tasks/task-1/completions", status=404)
        with pytest.raises(MaultenanceApiClientCommunicationError):
            await client.async_complete_task("task-1")
