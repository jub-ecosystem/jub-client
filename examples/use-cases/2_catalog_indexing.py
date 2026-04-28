"""
Use Case 2 — Catalog Indexing

Creates catalogs in bulk and assigns them to an existing observatory.
Use this when you need to extend an observatory with new dimensions
(a new geographic level, a new interest group, a new time series)
without going through the full setup flow.

Two modes (controlled by the --from-code flag):
  default      — loads catalog definitions from catalogs.json
  --from-code  — uses the inline Python definitions in this script

Run:
    python 2_catalog_indexing.py              # from JSON
    python 2_catalog_indexing.py --from-code  # from code

Environment variables (optional):
    JUB_API_URL   — API base URL    (default: http://localhost:5000)
    JUB_USERNAME  — Login username  (default: invitado)
    JUB_PASSWORD  — Login password  (default: invitado)
"""

import asyncio
import os
import sys

from jub.client.v2 import JubClient, JubClientBuilder
import jub.dto.v2 as DTO
from dotenv import load_dotenv

JUB_CLIENT_ENV_FILE_PATH = os.environ.get("JUB_CLIENT_ENV_FILE_PATH", ".env")
if os.path.exists(JUB_CLIENT_ENV_FILE_PATH):
    load_dotenv(JUB_CLIENT_ENV_FILE_PATH)
    print(f"Loaded environment variables from {JUB_CLIENT_ENV_FILE_PATH!r}")


# Change to the observatory you want to extend
OBSERVATORY_ID = os.environ.get("OBSERVATORY_ID", "obs_cancer_mx_2024")


# ── Mode A: load from JSON ────────────────────────────────────────────────────

async def create_catalogs_from_json(client: JubClient) -> list[str]:
    """
    POST /api/v2/catalogs/bulk  (payload read from catalogs.json)

    Reads a list of catalog definitions from catalogs.json and creates them
    all in a single API call. The JSON file must contain an array of objects
    matching the CatalogCreateDTO schema.
    """
    json_path = os.path.join(os.path.dirname(__file__), "catalogs.json")
    print(f"\nCreating catalogs from {json_path!r}...")

    result = await client.create_bulk_catalogs_from_json(json_path=json_path)
    if result.is_err:
        raise RuntimeError(f"create_bulk_catalogs_from_json failed: {result.unwrap_err()}")

    catalog_ids = result.unwrap().catalog_ids
    print(f"  Catalogs created: {catalog_ids}")
    return catalog_ids


# ── Mode B: define in code ────────────────────────────────────────────────────

async def create_catalogs_from_code(client: JubClient) -> list[str]:
    """
    POST /api/v2/catalogs/bulk  (payload defined inline)

    Defines three catalogs directly in Python and creates them in one call.
    Use this pattern when the catalog structure is generated programmatically
    (e.g. from a database query or a configuration object).
    """
    print("\nCreating catalogs from inline definitions...")

    result = await client.create_bulk_catalogs_from_json(data=[
        {
            "name":         "Biological Sex",
            "value":        "SEX",
            "catalog_type": "INTEREST",
            "description":  "Biological sex dimension for disaggregated analysis",
            "items": [
                {
                    "name": "Female", "value": "MUJER", "code": 2, "value_type": "STRING",
                    "aliases": [{"value": "F", "value_type": "STRING", "description": "Short code"}],
                },
                {
                    "name": "Male", "value": "HOMBRE", "code": 1, "value_type": "STRING",
                    "aliases": [{"value": "M", "value_type": "STRING", "description": "Short code"}],
                },
            ],
        },
        {
            "name":         "Five-Year Age Groups",
            "value":        "AGE_GROUPS",
            "catalog_type": "INTEREST",
            "description":  "Standard five-year age cohorts for epidemiological reporting",
            "items": [
                {"name": "0–4",   "value": "AG_00_04", "code": 1, "value_type": "STRING"},
                {"name": "5–14",  "value": "AG_05_14", "code": 2, "value_type": "STRING"},
                {"name": "15–24", "value": "AG_15_24", "code": 3, "value_type": "STRING"},
                {"name": "25–34", "value": "AG_25_34", "code": 4, "value_type": "STRING"},
                {"name": "35–44", "value": "AG_35_44", "code": 5, "value_type": "STRING"},
                {"name": "45–54", "value": "AG_45_54", "code": 6, "value_type": "STRING"},
                {"name": "55–64", "value": "AG_55_64", "code": 7, "value_type": "STRING"},
                {"name": "65+",   "value": "AG_65",    "code": 8, "value_type": "STRING"},
            ],
        },
        {
            "name":         "Report Years — Extended",
            "value":        "TEMPORAL_YEARS_EXT",
            "catalog_type": "TEMPORAL",
            "description":  "Annual time dimension extended to 2024",
            "items": [
                {
                    "name": str(y), "value": f"Y{y}", "code": y,
                    "value_type": "DATETIME", "temporal_value": f"{y}-01-01T00:00:00Z",
                }
                for y in range(2015, 2025)
            ],
        },
    ])

    if result.is_err:
        raise RuntimeError(f"create_bulk_catalogs failed: {result.unwrap_err()}")

    catalog_ids = result.unwrap().catalog_ids
    print(f"  Catalogs created: {catalog_ids}")
    return catalog_ids


# ── Assign to observatory ─────────────────────────────────────────────────────

async def assign_catalogs_to_observatory(
    client: JubClient,
    obs_id: str,
    catalog_ids: list[str],
) -> None:
    """
    POST /api/v2/observatories/{obs_id}/catalogs  (one call per catalog)

    Links each catalog to the given observatory. The 'level' parameter
    controls the display order in the UI (lower = higher priority).
    """
    print(f"\nLinking {len(catalog_ids)} catalog(s) to observatory {obs_id!r}...")

    for level, cat_id in enumerate(catalog_ids):
        result = await client.link_catalog_to_observatory(
            obs_id,
            DTO.LinkCatalogDTO(catalog_id=cat_id, level=level),
        )
        if result.is_err:
            print(f"  Failed to link {cat_id}: {result.unwrap_err()}")
        else:
            link = result.unwrap()
            print(f"  Linked catalog_id={link.catalog_id}  level={link.level}")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    from_code = "--from-code" in sys.argv

    result = await JubClientBuilder(
        api_url  = os.environ.get("JUB_API_URL",  "http://localhost:5000"),
        username = os.environ.get("JUB_USERNAME", "invitado"),
        password = os.environ.get("JUB_PASSWORD", "invitado"),
    ).build()
    if result.is_err:
        raise result.unwrap_err()

    client: JubClient = result.unwrap()
    print(f"Connected  user_id={client.user_id}")

    if from_code:
        catalog_ids = await create_catalogs_from_code(client)
    else:
        catalog_ids = await create_catalogs_from_json(client)

    await assign_catalogs_to_observatory(client, OBSERVATORY_ID, catalog_ids)

    print(f"\nDone. {len(catalog_ids)} catalog(s) assigned to {OBSERVATORY_ID!r}.")


if __name__ == "__main__":
    asyncio.run(main())
