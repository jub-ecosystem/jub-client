"""
Workflows examples — JUB API v2.

A workflow chains an ordered list of stages into a full data pipeline.
For the Cars Observatory, the pipeline is:
  1. plant-csv-ingest  — pull CSVs from S3, normalise, ingest records.
  2. vin-quality-check — validate ingested VINs and flag anomalies.

Covers: create_workflow, list_workflows, get_workflow,
        update_workflow, delete_workflow (with cascade).

Run:
    python examples/v2/cars/workflows/example_workflows.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result

# Replace with real stage IDs from example_stages.py.
INGEST_STAGE_ID = "<your-ingest-stage-id>"
QC_STAGE_ID     = "<your-qc-stage-id>"


async def main():
    client = await get_client()

    # --- 1. Create the cars ingestion workflow ------------------------
    create_result = await client.create_workflow(
        DTO.WorkflowCreateDTO(
            name="cars-ingest-pipeline",
            stage_ids=[INGEST_STAGE_ID, QC_STAGE_ID],
        )
    )
    print_result("create_workflow / cars-ingest-pipeline", create_result)

    if create_result.is_err:
        return

    workflow_id = create_result.unwrap().workflow_id

    # --- 2. Create a second workflow for EV-only data -----------------
    ev_wf_result = await client.create_workflow(
        DTO.WorkflowCreateDTO(
            name="ev-only-pipeline",
            stage_ids=[INGEST_STAGE_ID],  # single stage for EV subset
        )
    )
    print_result("create_workflow / ev-only-pipeline", ev_wf_result)

    # --- 3. List all workflows (first 50) ----------------------------
    list_result = await client.list_workflows(skip=0, limit=50)
    print_result("list_workflows", list_result)

    # --- 4. Fetch the main workflow by ID ----------------------------
    get_result = await client.get_workflow(workflow_id)
    print_result("get_workflow / cars-ingest-pipeline", get_result)

    # --- 5. Update the workflow name ---------------------------------
    update_result = await client.update_workflow(
        workflow_id,
        DTO.WorkflowUpdateDTO(name="cars-ingest-pipeline-v2"),
    )
    print_result("update_workflow / rename to v2", update_result)

    # --- 6. Delete the EV workflow (no cascade) ----------------------
    if ev_wf_result.is_ok:
        ev_wf_id = ev_wf_result.unwrap().workflow_id
        delete_ev = await client.delete_workflow(ev_wf_id, cascade=False)
        print_result("delete_workflow / ev-only-pipeline", delete_ev)

    # --- 7. Delete the main workflow with cascade (also removes stages)
    delete_result = await client.delete_workflow(workflow_id, cascade=True)
    print_result("delete_workflow / cars-ingest-pipeline-v2 (cascade=True)", delete_result)


if __name__ == "__main__":
    asyncio.run(main())
