"""
Shared helpers for the Cars Observatory examples.

Every example imports get_client() to obtain an authenticated JubClient.
Change API_URL, USERNAME, and PASSWORD to match your local JUB API instance.
"""

import asyncio
from jub.client.v2 import JubClient
import os
from dotenv import load_dotenv
from uuid import uuid4

JUB_ENV_FILE_PATH = os.environ.get("JUB_ENV_FILE_PATH", os.path.join(os.path.dirname(__file__), ".env"))
if os.path.exists(JUB_ENV_FILE_PATH):
    print(f"Loading environment variables from {JUB_ENV_FILE_PATH}")
    load_dotenv(JUB_ENV_FILE_PATH)

API_URL  = os.environ.get("API_URL", "http://localhost:5000")
iid = uuid4().hex[:8]  # Short random string for unique usernames in examples
USERNAME = os.environ.get("USERNAME", f"cars_analyst_{iid}")
PASSWORD = os.environ.get("PASSWORD", "CarPass123!")


async def get_client(username: str=None, password: str=None) -> JubClient:
    """Return an authenticated JubClient, ready to make API calls."""
    if username is None:
        username = USERNAME
    if password is None:
        password = PASSWORD
    client = JubClient(api_url=API_URL, username=username, password=password)
    result = await client.authenticate()
    if result.is_err:
        raise RuntimeError(f"Authentication failed: {result.unwrap_err()}")
    return client


def print_result(label: str, result) -> None:
    """Print Ok/Err result with a descriptive label."""
    if result.is_ok:
        print(f"[OK]  {label}: {result.unwrap()}")
    else:
        print(f"[ERR] {label}: {result.unwrap_err()}")
