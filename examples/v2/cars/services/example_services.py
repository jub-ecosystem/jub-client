"""
Services examples — JUB API v2.

A service exposes a named, discoverable unit of functionality. It can reference
an existing workflow or have one created inline via index_service().

For the Cars Observatory:
  "cars-ingest-service"   — public service that runs the full ingestion pipeline.
  "ev-analytics-service"  — private service for EV-specific analytics.

The index_service() call is the most powerful: it creates the full
Service → Workflow → Stages → Patterns → BuildingBlocks tree in one request.

Covers: create_service, index_service, list_services, get_service,
        update_service, delete_service.

Run:
    python examples/v2/cars/services/example_services.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result

# Replace with a real workflow_id if you want to attach an existing workflow.
WORKFLOW_ID = "<your-workflow-id>"


async def main():
    client = await get_client()

    # We need the authenticated user's ID to set as owner.
    me_result = await client.get_current_user()
    if me_result.is_err:
        print(f"[ERR] Could not fetch user: {me_result.unwrap_err()}")
        return
    owner_id = me_result.unwrap().user_id

    # --- 1. Create a simple service that attaches to an existing workflow
    create_result = await client.create_service(
        DTO.ServiceCreateDTO(
            name="cars-ingest-service",
            owner_id=owner_id,
            description="Ingests monthly CSV exports from all global assembly plants.",
            public=True,
            workflow_id=WORKFLOW_ID,
        )
    )
    print_result("create_service / cars-ingest-service", create_result)

    if create_result.is_err:
        return

    service_id = create_result.unwrap().service_id

    # --- 2. Use index_service to create a full service tree at once ---
    # This builds: Service → Workflow → Stage → Pattern → BuildingBlock
    index_result = await client.index_service(
        DTO.ServiceIndexDTO(
            name="ev-analytics-service",
            owner_id=owner_id,
            description="End-to-end analytics pipeline for electric vehicle data.",
            public=False,
            workflow=DTO.WorkflowInlineDTO(
                name="ev-analytics-workflow",
                stages=[
                    DTO.StageInlineDTO(
                        name="ev-data-fetch",
                        source="s3://cars-data/ev/",
                        sink="jub://datasources/ev_production_db/records",
                        endpoint="http://ev-ingestor.internal:8082/run",
                        transformation=DTO.PatternInlineDTO(
                            name="ev-map-reduce",
                            task="ingest",
                            pattern="map-reduce",
                            description="Parallel EV data ingestion.",
                            workers=2,
                            building_block=DTO.BuildingBlockInlineDTO(
                                name="ev-ingestor-block",
                                command="python ingest_ev.py",
                                image="python:3.11-slim",
                                description="Ingests EV battery + range records.",
                            ),
                        ),
                    ),
                ],
            ),
        )
    )
    print_result("index_service / ev-analytics-service (full tree)", index_result)

    # --- 3. List services (first 20) ----------------------------------
    list_result = await client.list_services(skip=0, limit=20)
    print_result("list_services", list_result)

    # --- 4. Fetch the cars ingest service by ID ----------------------
    get_result = await client.get_service(service_id)
    print_result("get_service / cars-ingest-service", get_result)

    # --- 5. Update the service to make it private --------------------
    update_result = await client.update_service(
        service_id,
        DTO.ServiceUpdateDTO(
            public=False,
            description="Ingestion pipeline — now internal only.",
        ),
    )
    print_result("update_service / cars-ingest-service → private", update_result)

    # --- 6. Delete the EV analytics service (cascade removes workflow) -
    if index_result.is_ok:
        ev_service_id = index_result.unwrap().service_id
        delete_ev = await client.delete_service(ev_service_id)
        print_result("delete_service / ev-analytics-service", delete_ev)

    # --- 7. Delete the cars ingest service ---------------------------
    delete_result = await client.delete_service(service_id)
    print_result("delete_service / cars-ingest-service", delete_result)


if __name__ == "__main__":
    asyncio.run(main())
