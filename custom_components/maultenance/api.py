"""Async client for the mAultenance /api/v1 HTTP API.

Deliberately framework-light (no Home Assistant imports) so it can be
unit-tested with a plain aiohttp.ClientSession, independent of the HA
test harness.
"""

from __future__ import annotations

from typing import Any

import aiohttp


class MaultenanceApiClientError(Exception):
    """Base error for the mAultenance API client."""


class MaultenanceApiClientAuthError(MaultenanceApiClientError):
    """Raised when the API rejects the configured token."""


class MaultenanceApiClientCommunicationError(MaultenanceApiClientError):
    """Raised when the API can't be reached or returns an unexpected error."""


class MaultenanceApiClient:
    """Thin wrapper around the mAultenance /api/v1 HTTP API."""

    def __init__(self, base_url: str, token: str, session: aiohttp.ClientSession) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._session = session

    async def async_list_tasks(self, status: str | None = None) -> list[dict[str, Any]]:
        """Return active tasks, optionally filtered by status (overdue|upcoming)."""
        params = {"status": status} if status else None
        return await self._request("GET", "/api/v1/tasks", params=params)

    async def async_complete_task(self, task_id: str, completed_at: str | None = None) -> None:
        """Record a completion for the given task (completed_at is RFC3339, omit for now)."""
        json_body = {"completed_at": completed_at} if completed_at else None
        await self._request("POST", f"/api/v1/tasks/{task_id}/completions", json=json_body)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with self._session.request(
                method, url, headers=headers, params=params, json=json
            ) as response:
                if response.status in (401, 403):
                    raise MaultenanceApiClientAuthError(f"{method} {path} returned {response.status}")
                if response.status >= 400:
                    raise MaultenanceApiClientCommunicationError(
                        f"{method} {path} returned {response.status}"
                    )
                body = await response.read()
                if response.status == 204 or not body:
                    return None
                return await response.json()
        except MaultenanceApiClientError:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise MaultenanceApiClientCommunicationError(f"{method} {path} failed: {err}") from err
