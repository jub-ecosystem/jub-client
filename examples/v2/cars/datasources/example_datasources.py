"""
Data Sources examples — JUB API v2.

A data source holds the raw production records for the Cars Observatory.
Each record maps a car unit to its spatial (country), temporal (year),
and interest (brand, color, motor) dimensions.

Covers: register_data_source, register_data_source_from_json,
        list_data_sources, get_data_source, delete_data_source,
        ingest_records, ingest_records_from_json, query_records.

Run:
    python examples/v2/cars/datasources/example_datasources.py
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result

# Replace with real catalog-item IDs from your database.
ITEM_JP       = "<catalog-item-id-JP>"
ITEM_DE       = "<catalog-item-id-DE>"
ITEM_Y2022    = "<catalog-item-id-Y2022>"
ITEM_Y2023    = "<catalog-item-id-Y2023>"
ITEM_TOYOTA   = "<catalog-item-id-TOYOTA>"
ITEM_BMW      = "<catalog-item-id-BMW>"
ITEM_WHITE    = "<catalog-item-id-WHITE>"
ITEM_BLACK    = "<catalog-item-id-BLACK>"
ITEM_GASOLINE = "<catalog-item-id-GASOLINE>"
ITEM_ELECTRIC = "<catalog-item-id-ELECTRIC>"


async def main():
    client = await get_client()

    # --- 1. Register a CSV data source --------------------------------
    register_result = await client.register_data_source(
        DTO.DataSourceCreateDTO(
            name="cars_production_db",
            description="Monthly car production records from global assembly plants.",
            format="csv",
        )
    )
    print_result("register_data_source / cars_production_db", register_result)

    if register_result.is_err:
        return

    source_id = register_result.unwrap().source_id

    # --- 2. Register a second source from a JSON string ---------------
    json_payload = json.dumps({
        "name": "ev_production_db",
        "description": "Electric vehicle production records only.",
        "format": "json",
    })
    register_json_result = await client.register_data_source_from_json(
        json_string=json_payload
    )
    print_result("register_data_source_from_json / ev_production_db", register_json_result)

    # --- 3. List all data sources ------------------------------------
    list_result = await client.list_data_sources()
    print_result("list_data_sources", list_result)

    # --- 4. Fetch the CSV source by ID --------------------------------
    get_result = await client.get_data_source(source_id)
    print_result("get_data_source / cars_production_db", get_result)

    # --- 5. Ingest a batch of production records ----------------------
    # Each record links a car unit to its SPATIAL, TEMPORAL, and INTEREST items.
    records = [
        DTO.DataRecordCreateDTO(
            record_id="VIN-JT2BF22K820012345",
            spatial_id=ITEM_JP,
            temporal_id=ITEM_Y2022,
            interest_ids=[ITEM_TOYOTA, ITEM_WHITE, ITEM_GASOLINE],
            numerical_interest_ids={"engine_cc": 1800.0, "doors": 4.0},
            raw_payload={"model": "Corolla", "plant": "Takaoka", "trim": "LE"},
        ),
        DTO.DataRecordCreateDTO(
            record_id="VIN-WBSKG9C50BE123456",
            spatial_id=ITEM_DE,
            temporal_id=ITEM_Y2023,
            interest_ids=[ITEM_BMW, ITEM_BLACK, ITEM_ELECTRIC],
            numerical_interest_ids={"range_km": 590.0, "doors": 4.0},
            raw_payload={"model": "i4 M50", "plant": "Munich", "trim": "xDrive"},
        ),
        DTO.DataRecordCreateDTO(
            record_id="VIN-JT2BF22K820099999",
            spatial_id=ITEM_JP,
            temporal_id=ITEM_Y2022,
            interest_ids=[ITEM_TOYOTA, ITEM_BLACK, ITEM_GASOLINE],
            numerical_interest_ids={"engine_cc": 1800.0, "doors": 4.0},
            raw_payload={"model": "Corolla", "plant": "Takaoka", "trim": "XSE"},
        ),
    ]
    ingest_result = await client.ingest_records(source_id, records)
    print_result("ingest_records / 3 car records", ingest_result)

    # --- 6. Ingest additional records from a JSON string --------------
    more_records_json = json.dumps([
        {
            "record_id": "VIN-HONDA-CIVIC-2022-001",
            "spatial_id": ITEM_JP,
            "temporal_id": ITEM_Y2022,
            "interest_ids": ["<catalog-item-id-HONDA>", ITEM_WHITE, ITEM_GASOLINE],
            "numerical_interest_ids": {"engine_cc": 1500.0, "doors": 4.0},
            "raw_payload": {"model": "Civic", "plant": "Suzuka", "trim": "Sport"},
        }
    ])
    ingest_json_result = await client.ingest_records_from_json(
        source_id, json_string=more_records_json
    )
    print_result("ingest_records_from_json / 1 Honda record", ingest_json_result)

    # --- 7. Query records using the JUB DSL ---------------------------
    # Find all cars manufactured in Japan with a gasoline engine.
    query_result = await client.query_records(
        source_id,
        DTO.DataSourceQueryDTO(
            query="jub.v1.VS(JP).VI(GASOLINE)",
            limit=10,
            skip=0,
        ),
    )
    print_result("query_records / VS(JP).VI(GASOLINE)", query_result)

    # --- 8. Delete the EV source (cleanup) ----------------------------
    if register_json_result.is_ok:
        ev_source_id = register_json_result.unwrap().source_id
        delete_result = await client.delete_data_source(ev_source_id)
        print_result("delete_data_source / ev_production_db", delete_result)


if __name__ == "__main__":
    asyncio.run(main())
