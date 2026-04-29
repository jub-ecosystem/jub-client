"""
Patterns examples — JUB API v2.

A pattern defines how a building block runs: how many workers, which
load-balancing strategy, and what kind of task it performs.
For the Cars Observatory, a map-reduce pattern parallelises CSV normalisation
across multiple plant files.

Covers: create_pattern, list_patterns, get_pattern,
        update_pattern, delete_pattern.

Run:
    python examples/v2/cars/patterns/example_patterns.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result

# Replace with the building_block_id from example_building_blocks.py.
BUILDING_BLOCK_ID = "<your-building-block-id>"


async def main():
    client = await get_client()

    # --- 1. Create a map-reduce pattern for parallel CSV ingestion ----
    create_result = await client.create_pattern(
        DTO.PatternCreateDTO(
            name="car-csv-map-reduce",
            task="ingest",
            pattern="map-reduce",
            description="Distributes plant CSV files across 4 worker containers.",
            workers=4,
            loadbalancer="round-robin",
            building_block_id=BUILDING_BLOCK_ID,
        )
    )
    print_result("create_pattern / car-csv-map-reduce", create_result)

    if create_result.is_err:
        return

    pattern_id = create_result.unwrap().pattern_id

    # --- 2. Create a single-worker pipeline pattern for EV data -------
    ev_pattern_result = await client.create_pattern(
        DTO.PatternCreateDTO(
            name="ev-pipeline",
            task="transform",
            pattern="pipeline",
            description="Single-worker sequential transform for EV telemetry batches.",
            workers=1,
            loadbalancer="round-robin",
        )
    )
    print_result("create_pattern / ev-pipeline", ev_pattern_result)

    # --- 3. List all patterns (first 50) ------------------------------
    list_result = await client.list_patterns(skip=0, limit=50)
    print_result("list_patterns", list_result)

    # --- 4. Fetch the map-reduce pattern by ID ------------------------
    get_result = await client.get_pattern(pattern_id)
    print_result("get_pattern / car-csv-map-reduce", get_result)

    # --- 5. Scale up to 8 workers for peak production periods ---------
    update_result = await client.update_pattern(
        pattern_id,
        DTO.PatternUpdateDTO(
            workers=8,
            description="Scaled to 8 workers for end-of-year production surge.",
        ),
    )
    print_result("update_pattern / car-csv-map-reduce → 8 workers", update_result)

    # --- 6. Delete the EV pattern (cleanup) ---------------------------
    if ev_pattern_result.is_ok:
        ev_pattern_id = ev_pattern_result.unwrap().pattern_id
        delete_ev = await client.delete_pattern(ev_pattern_id)
        print_result("delete_pattern / ev-pipeline", delete_ev)

    # --- 7. Delete the map-reduce pattern (cleanup) -------------------
    delete_result = await client.delete_pattern(pattern_id)
    print_result("delete_pattern / car-csv-map-reduce", delete_result)


if __name__ == "__main__":
    asyncio.run(main())
