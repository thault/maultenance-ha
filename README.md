# maultenance-ha

A Home Assistant custom integration for [mAultenance](https://github.com/thault/maultenance), a self-hosted household maintenance/task tracker. Polls the mAultenance API and exposes tasks in Home Assistant as a to-do list plus per-task sensors, for use in dashboards, automations, and displays.

## What it adds

- **`todo.maultenance`** — a checklist of every active task. Checking an item off marks it complete in mAultenance. Works with the built-in to-do list card and Assist voice.
- **One device per task**, each with:
  - `sensor.<task>_due_date` (`device_class: date`) — the task's current due date, with title/description/rrule/anchor mode/completion info as attributes.
  - `binary_sensor.<task>_overdue` (`device_class: problem`) — on when the task is overdue.
- Tasks are polled every 5 minutes. A task archived in mAultenance has its device and entities removed from Home Assistant on the next poll.

## Installation

**Via HACS**: add this repository as a custom repository (category: Integration), then install "mAultenance".

**Manually**: copy `custom_components/maultenance` into your Home Assistant `custom_components` directory and restart.

Then, in mAultenance's web UI, create a Personal Access Token for a dedicated account (e.g. a "Home Assistant" user) via Settings → Tokens. Add the integration in Home Assistant (Settings → Devices & Services → Add Integration → mAultenance) with your mAultenance base URL and that token.

## Development

Requires Python 3.14+ (matches current Home Assistant core).

```
python3 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/pytest tests/ -v
```

## Status

Read/write task sync (todo list + per-task sensors) is implemented. A digest/aggregate sensor for physical displays (e-ink, receipt printer) is a planned follow-up — see open issues.
