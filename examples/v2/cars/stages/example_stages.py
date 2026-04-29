"""
Stages examples — JUB API v2.

A stage represents one step in a data pipeline: a source, a transformation
(pattern), and a sink. For the Cars Observatory:
  - Source: S3 bucket with monthly CSV exports from assembly plants.
  - Transformation: car-csv-map-reduce pattern (normalise + validate).
  - Sink: JUB datasource endpoint for ingestion.

Covers: create_stage, list_stages, get_stage,
        update_stage, delete_stage.

Run:
    python examples/v2/cars/stages/example_stages.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result

# Replace with the pattern_id from example_patterns.py.
PATTERN_ID = "<your-pattern-id>"


async def main():
    client = await get_client()

    # --- 1. Create the ingestion stage --------------------------------
    create_result = await client.create_stage(
        DTO.StageCreateDTO(
            name="plant-csv-ingest",
            source="s3://cars-data/plants/monthly/",
            sink="jub://datasources/cars_production_db/records",
            endpoint="http://car-ingestor.internal:8080/run",
            transformation_id=PATTERN_ID,
        )
    )
    print_result("create_stage / plant-csv-ingest", create_result)

    if create_result.is_err:
        return

    stage_id = create_result.unwrap().stage_id

    # --- 2. Create a quality-check stage that runs after ingestion ----
    qc_result = await client.create_stage(
        DTO.StageCreateDTO(
            name="vin-quality-check",
            source="jub://datasources/cars_production_db/records",
            sink="jub://datasources/cars_qc_report/records",
            endpoint="http://car-qc.internal:8081/check",
        )
    )
    print_result("create_stage / vin-quality-check", qc_result)

    # --- 3. List all stages (first 50) --------------------------------
    list_result = await client.list_stages(skip=0, limit=50)
    print_result("list_stages", list_result)

    # --- 4. Fetch the ingestion stage by ID ---------------------------
    get_result = await client.get_stage(stage_id)
    print_result("get_stage / plant-csv-ingest", get_result)

    # --- 5. Update the source bucket path for 2024 data ---------------
    update_result = await client.update_stage(
        stage_id,
        DTO.StageUpdateDTO(
            source="s3://cars-data/plants/2024/",
            endpoint="http://car-ingestor.internal:8080/run-v2",
        ),
    )
    print_result("update_stage / plant-csv-ingest → 2024 path", update_result)

    # --- 6. Delete the QC stage (cleanup) -----------------------------
    if qc_result.is_ok:
        qc_stage_id = qc_result.unwrap().stage_id
        delete_qc = await client.delete_stage(qc_stage_id)
        print_result("delete_stage / vin-quality-check", delete_qc)

    # --- 7. Delete the ingestion stage (cleanup) ----------------------
    delete_result = await client.delete_stage(stage_id)
    print_result("delete_stage / plant-csv-ingest", delete_result)


if __name__ == "__main__":
    asyncio.run(main())
