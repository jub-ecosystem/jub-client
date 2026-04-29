"""
Catalogs examples — JUB API v2.

Car Observatory uses three catalog types that map to the STORI model:
  - SPATIAL   → MANUFACTURING_COUNTRY  (where a car was built)
  - TEMPORAL  → PRODUCTION_YEAR        (when a car was built)
  - INTEREST  → CAR_BRAND, CAR_COLOR, MOTOR_TYPE  (what kind of car)

Covers: create_catalog, create_catalog_from_json,
        create_bulk_catalogs_from_json, list_catalogs, get_catalog.

Run:
    python examples/v2/cars/catalogs/example_catalogs.py
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result,USERNAME, PASSWORD



# ---------------------------------------------------------------------------
# Catalog definitions (inline Python)
# ---------------------------------------------------------------------------

SPATIAL_CATALOG = DTO.CatalogCreateDTO(
    catalog_id="spatial-catalog-001",  # Optional: specify your own catalog ID or let the system generate a random UUID.
    name="Manufacturing Country",
    value="MANUFACTURING_COUNTRY",
    catalog_type="SPATIAL",
    description="Countries where cars are manufactured.",
    items=[
        DTO.CatalogItemCreateDTO(catalog_item_id="mexico", name="Mexico",        value="MX", code=1, value_type="STRING"),
        DTO.CatalogItemCreateDTO(catalog_item_id="germany", name="Germany",       value="DE", code=2, value_type="STRING"),
        DTO.CatalogItemCreateDTO(catalog_item_id="japan", name="Japan",         value="JP", code=3, value_type="STRING"),
        DTO.CatalogItemCreateDTO(catalog_item_id="united_states", name="United States", value="US", code=4, value_type="STRING"),
        DTO.CatalogItemCreateDTO(catalog_item_id="south_korea", name="South Korea",   value="KR", code=5, value_type="STRING"),
    ],
)

# Temporal items use temporal_value (ISO 8601 year start)
TEMPORAL_CATALOG = DTO.CatalogCreateDTO(
    catalog_id="temporal-catalog-001",  # Optional: specify your own catalog ID or let the system generate a random UUID.
    name="Production Year",
    value="PRODUCTION_YEAR",
    catalog_type="TEMPORAL",
    description="Year in which the car was manufactured.",
    items=[
        DTO.CatalogItemCreateDTO(catalog_item_id="y1998", name="1998", value="Y1998", code=1998, value_type="DATETIME", temporal_value="1998-01-01T00:00:00"),
        DTO.CatalogItemCreateDTO(catalog_item_id="y2020", name="2020", value="Y2020", code=2020, value_type="DATETIME", temporal_value="2020-01-01T00:00:00"),
        DTO.CatalogItemCreateDTO(catalog_item_id="y2021", name="2021", value="Y2021", code=2021, value_type="DATETIME", temporal_value="2021-01-01T00:00:00"),
        DTO.CatalogItemCreateDTO(catalog_item_id="y2022", name="2022", value="Y2022", code=2022, value_type="DATETIME", temporal_value="2022-01-01T00:00:00"),
        DTO.CatalogItemCreateDTO(catalog_item_id="y2023", name="2023", value="Y2023", code=2023, value_type="DATETIME", temporal_value="2023-01-01T00:00:00"),
        DTO.CatalogItemCreateDTO(catalog_item_id="y2024", name="2024", value="Y2024", code=2024, value_type="DATETIME", temporal_value="2024-01-01T00:00:00"),
    ],
)

# Bulk payload: three interest catalogs in one request
INTEREST_CATALOGS_PAYLOAD = [
    {
        "catalog_id": "interest-catalog-001",  # Optional: specify your own catalog ID or let the system generate a random UUID.
        "name": "Car Brand",
        "value": "CAR_BRAND",
        "catalog_type": "INTEREST",
        "description": "Manufacturer brand of the car.",
        "items": [
            { "catalog_item_id":"toyota", "name": "Toyota",     "value": "TOYOTA", "code": 1, "value_type": "STRING"},
            { "catalog_item_id":"bmw", "name": "BMW",        "value": "BMW",    "code": 2, "value_type": "STRING"},
            { "catalog_item_id":"ford", "name": "Ford",       "value": "FORD",   "code": 3, "value_type": "STRING"},
            { "catalog_item_id":"honda", "name": "Honda",      "value": "HONDA",  "code": 4, "value_type": "STRING"},
            { "catalog_item_id":"volkswagen", "name": "Volkswagen", "value": "VW",     "code": 5, "value_type": "STRING"},
        ],
    },
    {
        "catalog_id": "interest-catalog-002",  # Optional: specify your own catalog ID or let the system generate a random UUID.
        "name": "Car Color",
        "value": "CAR_COLOR",
        "catalog_type": "INTEREST",
        "description": "Exterior color of the car.",
        "items": [
            { "catalog_item_id":"red", "name": "Red",    "value": "RED",    "code": 1, "value_type": "STRING"},
            { "catalog_item_id":"blue", "name": "Blue",   "value": "BLUE",   "code": 2, "value_type": "STRING"},
            { "catalog_item_id":"black", "name": "Black",  "value": "BLACK",  "code": 3, "value_type": "STRING"},
            { "catalog_item_id":"white", "name": "White",  "value": "WHITE",  "code": 4, "value_type": "STRING"},
            { "catalog_item_id":"silver", "name": "Silver", "value": "SILVER", "code": 5, "value_type": "STRING"},
        ],
    },
    {
        "catalog_id": "interest-catalog-003",  # Optional: specify your own catalog ID or let the system generate a random UUID.
        "name": "Motor Type",
        "value": "MOTOR_TYPE",
        "catalog_type": "INTEREST",
        "description": "Engine technology used in the car.",
        "items": [
            { "catalog_item_id":"gasoline", "name": "Gasoline", "value": "GASOLINE", "code": 1, "value_type": "STRING"},
            { "catalog_item_id":"electric", "name": "Electric", "value": "ELECTRIC", "code": 2, "value_type": "STRING"},
            { "catalog_item_id":"hybrid", "name": "Hybrid",   "value": "HYBRID",   "code": 3, "value_type": "STRING"},
            { "catalog_item_id":"diesel", "name": "Diesel",   "value": "DIESEL",   "code": 4, "value_type": "STRING"},
        ],
    },
]


async def main():
    client = await get_client(username=USERNAME, password=PASSWORD)

    # --- 1. Create the spatial catalog (countries) ---------------------
    spatial_result = await client.create_catalog(SPATIAL_CATALOG)
    print_result("create_catalog / SPATIAL", spatial_result)

    # --- 2. Create the temporal catalog from a JSON string -------------
    temporal_json = json.dumps(TEMPORAL_CATALOG.model_dump())
    temporal_result = await client.create_catalog_from_json(json_string=temporal_json)
    print_result("create_catalog_from_json / TEMPORAL", temporal_result)

    # --- 3. Create all three interest catalogs in one bulk request -----
    bulk_result = await client.create_bulk_catalogs_from_json(data=INTEREST_CATALOGS_PAYLOAD)
    print_result("create_bulk_catalogs_from_json / INTEREST (3 catalogs)", bulk_result)

    # --- 4. List all catalogs ------------------------------------------
    list_result = await client.list_catalogs()
    print_result("list_catalogs", list_result)

    # --- 5. Get full details for the spatial catalog -------------------
    if spatial_result.is_ok:
        catalog_id = spatial_result.unwrap().catalog_id
        get_result = await client.get_catalog(catalog_id)
        print_result("get_catalog / SPATIAL", get_result)


if __name__ == "__main__":
    asyncio.run(main())
