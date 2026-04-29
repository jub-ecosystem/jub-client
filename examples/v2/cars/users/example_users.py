"""
Users examples — JUB API v2.

Covers: signup, authenticate, get_current_user,
        get_user_settings, update_user_settings.

Run:
    python examples/v2/cars/users/example_users.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from jub.client.v2 import JubClient
import jub.dto.v2 as DTO
from examples.v2.cars.common import API_URL, get_client, print_result,USERNAME, PASSWORD




async def main(*args):
    # --- 1. Sign up a new user -----------------------------------------
    # Only needed once. Comment out after the account is created.
    anon = JubClient(api_url=API_URL, username="", password="")
    signup_result = await anon.signup(
        DTO.SignUpDTO(
            username   = USERNAME,
            email      = f"{USERNAME}@example.com",
            password   = PASSWORD,
            first_name = "Carlos",
            last_name  = "Rodriguez",
        )
    )
    print_result("signup", signup_result)

    # --- 2. Authenticate (get a token) ---------------------------------
    client = JubClient(api_url=API_URL, username=USERNAME, password=PASSWORD)
    auth_result = await client.authenticate()
    print_result("authenticate", auth_result)

    # All subsequent calls use the authenticated client from common.py
    client = await get_client(username=USERNAME, password=PASSWORD)

    # --- 3. Fetch the profile of the authenticated user ----------------
    me_result = await client.get_current_user()
    print_result("get_current_user", me_result)

    if me_result.is_err:
        return

    user_id = me_result.unwrap().user_id

    # --- 4. Read user settings -----------------------------------------
    settings_result = await client.get_user_settings(user_id)
    print_result("get_user_settings", settings_result)

    # --- 5. Update user settings ---------------------------------------
    updated_prefs = DTO.UserPreferencesDTO(
        appearance=DTO.AppearanceSettingsDTO(theme="dark", font_size=16),
        exploration=DTO.ExplorationSettingsDTO(items_per_page=24, default_view="grid"),
        export=DTO.ExportSettingsDTO(default_format="json", include_metadata=True),
    )
    update_result = await client.update_user_settings(user_id, updated_prefs)
    print_result("update_user_settings", update_result)


if __name__ == "__main__":
    asyncio.run(main())
