"""
Building Blocks examples — JUB API v2.

A building block is a containerised unit of work (Docker image + command).
For the Cars Observatory, a typical building block runs a Python script
that normalises raw CSV data from an assembly plant.

Covers: create_building_block, list_building_blocks, get_building_block,
        update_building_block, delete_building_block.

Run:
    python examples/v2/cars/building_blocks/example_building_blocks.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result


async def main():
    client = await get_client()

    # --- 1. Create a building block that normalises car CSV data ------
    create_result = await client.create_building_block(
        DTO.BuildingBlockCreateDTO(
            name="car-csv-normalizer",
            command="python normalize_cars.py --input /data/input.csv --output /data/output.json",
            image="python:3.11-slim",
            description="Reads raw assembly-plant CSV, validates VINs, and outputs normalised JSON.",
        )
    )
    print_result("create_building_block / car-csv-normalizer", create_result)

    if create_result.is_err:
        return

    bb_id = create_result.unwrap().building_block_id

    # --- 2. Create a second building block for EV telemetry -----------
    ev_result = await client.create_building_block(
        DTO.BuildingBlockCreateDTO(
            name="ev-telemetry-ingestor",
            command="python ingest_ev.py --source kafka://ev-topic",
            image="ghcr.io/madtec/ev-ingestor:latest",
            description="Consumes EV battery telemetry from Kafka and pushes to JUB.",
        )
    )
    print_result("create_building_block / ev-telemetry-ingestor", ev_result)

    # --- 3. List all building blocks (first 50) -----------------------
    list_result = await client.list_building_blocks(skip=0, limit=50)
    print_result("list_building_blocks", list_result)

    # --- 4. Fetch the CSV normalizer block by ID ----------------------
    get_result = await client.get_building_block(bb_id)
    print_result("get_building_block / car-csv-normalizer", get_result)

    # --- 5. Update the image to a newer Python version ----------------
    update_result = await client.update_building_block(
        bb_id,
        DTO.BuildingBlockUpdateDTO(
            image="python:3.12-slim",
            description="Upgraded to Python 3.12; adds VIN check-digit validation.",
        ),
    )
    print_result("update_building_block / car-csv-normalizer", update_result)

    # --- 6. Delete the EV telemetry block (cleanup) -------------------
    if ev_result.is_ok:
        ev_bb_id = ev_result.unwrap().building_block_id
        delete_ev = await client.delete_building_block(ev_bb_id)
        print_result("delete_building_block / ev-telemetry-ingestor", delete_ev)

    # --- 7. Delete the CSV normalizer block (cleanup) -----------------
    delete_result = await client.delete_building_block(bb_id)
    print_result("delete_building_block / car-csv-normalizer", delete_result)


if __name__ == "__main__":
    asyncio.run(main())
