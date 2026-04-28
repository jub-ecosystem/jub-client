"""
Use Case 5 — Service Indexing

Creates the full service hierarchy:
  Building Block → Pattern → Stage → Workflow → Service

Two approaches are shown:

  Option A (one-shot)   — index_service() creates the entire tree atomically in
                          a single API call. This is the recommended approach when
                          you are creating everything from scratch.

  Option B (step-by-step) — each layer is created individually. Use this when you
                          need to reuse existing components (e.g. an already-created
                          building block or pattern) or when you need fine-grained
                          control over each step.

After creation, services are discoverable via search_services() using the SVC() DSL.

Run:
    python 5_service_indexing.py              # Option A (one-shot)
    python 5_service_indexing.py --step-by-step  # Option B

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
import jub.enums as ENUM
from uuid import uuid4

JUB_CLIENT_ENV_FILE_PATH = os.environ.get("JUB_CLIENT_ENV_FILE_PATH", ".env")
if os.path.exists(JUB_CLIENT_ENV_FILE_PATH):
    load_dotenv(JUB_CLIENT_ENV_FILE_PATH)
    print(f"Loaded environment variables from {JUB_CLIENT_ENV_FILE_PATH!r}")


# ── Option A: one-shot ────────────────────────────────────────────────────────

async def index_service_oneshot(client: JubClient) -> str:
    """
    POST /api/v2/services/index

    Creates the complete Service → Workflow → Stage → Pattern → BuildingBlock
    tree in a single atomic request. The response includes every generated ID
    so you can reference the components later.

    At each level you can either define an inline object (which creates a new
    entity) or pass an existing ID (which references an existing entity).
    """
    print("\n[Option A] Creating service tree with index_service()...")
    idd = uuid4().hex[:6]  # random suffix to avoid name collisions in repeated runs
    result = await client.index_service(DTO.ServiceIndexDTO(
        name        = f"cancer-ingest-svc-{idd}",
        owner_id    = client.user_id,
        description = "Automated ingestion pipeline for cancer mortality CSV reports.",
        public      = True,
        provider=   ENUM.ServiceProviderEnum.NEZ,
        workflow    = DTO.WorkflowInlineDTO(
            name   = f"Cancer Mortality Ingestion Workflow-{idd}",
            stages = [
                # Stage 1 — Fetch the source file and validate it
                DTO.StageInlineDTO(
                    name     = f"Fetch and Validate-{idd}",
                    source   = "s3://my-bucket/cancer/mortality.csv",
                    sink     = "jub://staging/cancer_validated",
                    endpoint = "http://validator-svc/run",
                    transformation = DTO.PatternInlineDTO(
                        name    = f"CSV Validator Pattern-{idd}",
                        task    = "validate",
                        pattern = "pipeline",
                        workers = 1,
                        building_block = DTO.BuildingBlockInlineDTO(
                            name        = f"CSV Validator-{idd}",
                            command     = "python validate.py --strict",
                            image       = "registry.example.com/csv-validator:latest",
                            description = "Validates CSV schema and rejects malformed rows.",
                        ),
                    ),
                ),
                # Stage 2 — Ingest validated records into the JUB data source
                DTO.StageInlineDTO(
                    name     = f"Ingest Records-{idd}",
                    source   = "jub://staging/cancer_validated",
                    sink     = "jub://datasources/ds_cancer_mx",
                    endpoint = "http://ingestor-svc/run",
                    transformation = DTO.PatternInlineDTO(
                        name    = f"CSV Ingest Pattern-{idd}",
                        task    = "ingest",
                        pattern = "pipeline",
                        workers = 2,
                        loadbalancer = "round-robin",
                        building_block = DTO.BuildingBlockInlineDTO(
                            name        = f"CSV Ingestor-{idd}",
                            command     = "python ingest.py --source cancer_validated",
                            image       = "registry.example.com/ingestor:latest",
                            description = "Transforms validated rows into DataRecordCreateDTO and pushes to the API.",
                        ),
                    ),
                ),
            ],
        ),
    ))

    if result.is_err:
        raise RuntimeError(f"index_service failed: {result.unwrap_err()}")

    resp = result.unwrap()
    print(f"  Service ID        : {resp.service_id}")
    print(f"  Workflow ID       : {resp.workflow_id}")
    print(f"  Stage IDs         : {resp.stage_ids}")
    print(f"  Pattern IDs       : {resp.pattern_ids}")
    print(f"  Building Block IDs: {resp.building_block_ids}")
    return resp.service_id


# ── Option B: step-by-step ────────────────────────────────────────────────────

async def index_service_step_by_step(client: JubClient) -> str:
    """
    Creates the same service tree as Option A, but one layer at a time.
    Useful when you want to reuse an existing building block or pattern,
    or when you need to inspect intermediate results before proceeding.
    """
    print("\n[Option B] Creating service tree step by step...")
    idd = uuid4().hex[:6]  # random suffix to avoid name collisions in repeated runs

    # 1. Building block — the containerised unit of work
    # POST /api/v2/building-blocks
    bb_result = await client.create_building_block(DTO.BuildingBlockCreateDTO(
        name        = f"CSV Ingestor-{idd}",
        command     = "python ingest.py --source cancer_validated",
        image       = "registry.example.com/ingestor:latest",
        description = "Transforms validated rows into DataRecordCreateDTO and pushes to the API.",
    ))
    if bb_result.is_err:
        raise RuntimeError(f"create_building_block failed: {bb_result.unwrap_err()}")
    bb = bb_result.unwrap()
    print(f"  Building block : {bb.building_block_id}  ({bb.name})")

    # 2. Pattern — execution strategy for the building block
    # POST /api/v2/patterns
    pattern_result = await client.create_pattern(DTO.PatternCreateDTO(
        name               = f"CSV Ingest Pattern-{idd}",
        task               = "ingest",
        pattern            = "pipeline",
        workers            = 2,
        loadbalancer       = "round-robin",
        building_block_id  = bb.building_block_id,
        description        = "Runs the ingestor with two parallel workers.",
    ))
    if pattern_result.is_err:
        raise RuntimeError(f"create_pattern failed: {pattern_result.unwrap_err()}")
    pattern = pattern_result.unwrap()
    print(f"  Pattern        : {pattern.pattern_id}  ({pattern.name})")

    # 3. Stage — one processing step: source → transformation → sink
    # POST /api/v2/stages
    stage_result = await client.create_stage(DTO.StageCreateDTO(
        name              = f"Ingest Records-{idd}",
        source            = "jub://staging/cancer_validated",
        sink              = "jub://datasources/ds_cancer_mx",
        endpoint          = "http://ingestor-svc/run",
        transformation_id = pattern.pattern_id,
    ))
    if stage_result.is_err:
        raise RuntimeError(f"create_stage failed: {stage_result.unwrap_err()}")
    stage = stage_result.unwrap()
    print(f"  Stage          : {stage.stage_id}  ({stage.name})")

    # 4. Workflow — ordered sequence of stages
    # POST /api/v2/workflows
    workflow_result = await client.create_workflow(DTO.WorkflowCreateDTO(
        name      = f"Cancer Mortality Ingestion Workflow-{idd}",
        stage_ids = [stage.stage_id],
    ))
    if workflow_result.is_err:
        raise RuntimeError(f"create_workflow failed: {workflow_result.unwrap_err()}")
    workflow = workflow_result.unwrap()
    print(f"  Workflow       : {workflow.workflow_id}  ({workflow.name})")

    # 5. Service — top-level entity that groups the workflow
    # POST /api/v2/services
    service_result = await client.create_service(DTO.ServiceCreateDTO(
        name        = f"cancer-ingest-svc-{idd}",
        owner_id    = client.user_id,
        description = "Automated ingestion pipeline for cancer mortality CSV reports.",
        public      = True,
        workflow_id = workflow.workflow_id,
        provider=   ENUM.ServiceProviderEnum.XELHUA,
    ))
    if service_result.is_err:
        raise RuntimeError(f"create_service failed: {service_result.unwrap_err()}")
    service = service_result.unwrap()
    print(f"  Service        : {service.service_id}  ({service.name})")

    return service.service_id


# ── Search for the service ────────────────────────────────────────────────────

async def search_for_service(client: JubClient, service_name: str) -> None:
    """
    POST /api/v2/search/services

    Searches services using the SVC() DSL operator. Supports filtering by
    name, public flag, and owner.

    SVC() operator syntax:
      SVC(*)                           — all services
      SVC(name=cancer)                 — name contains 'cancer'
      SVC(public=true)                 — public services only
      SVC(owner=<user_id>)             — by owner
      SVC(name=cancer,public=true)     — combined filters
    """
    print("\nSearching for the service...")

    result = await client.search_services(DTO.ServiceQueryDTO(
        query = f"jub.v1.SVC(name={service_name},public=true)",
        limit = 10,
    ))
    if result.is_err:
        raise RuntimeError(f"search_services failed: {result.unwrap_err()}")

    services = result.unwrap()
    print(f"  Found {len(services)} service(s)")
    for svc in services:
        print(f"  - {svc.service_id}  {svc.name}  public={svc.public}")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    step_by_step = "--step-by-step" in sys.argv

    result = await JubClientBuilder(
        api_url  = os.environ.get("JUB_API_URL",  "http://localhost:5000"),
        username = os.environ.get("JUB_USERNAME", "invitado"),
        password = os.environ.get("JUB_PASSWORD", "invitado"),
    ).build()
    if result.is_err:
        raise result.unwrap_err()

    client: JubClient = result.unwrap()
    print(f"Connected  user_id={client.user_id}")

    if step_by_step:
        service_id = await index_service_step_by_step(client)
    else:
        service_id = await index_service_oneshot(client)

    await search_for_service(client, "cancer")
    print(f"\nDone. Service ID: {service_id}")


if __name__ == "__main__":
    asyncio.run(main())
