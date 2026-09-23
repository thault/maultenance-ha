"""Constants for the mAultenance integration."""

from datetime import timedelta

DOMAIN = "maultenance"

CONF_BASE_URL = "base_url"
CONF_API_TOKEN = "api_token"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
