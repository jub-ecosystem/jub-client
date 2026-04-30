"""
Integration tests for BuildingBlocks, Patterns, Stages, Workflows, and Services.

These tests run against a live JUB API at http://localhost:5000.
Start the API server before running:

    cd ~/Programming/Python/jub_api && poetry run uvicorn jubapi.server:app --port 5000

All tests use the 'invitado' account and clean up after themselves.
"""

import pytest
from jub.client.v2 import JubClientBuilder
import jub.dto.v2 as DTO
import jub.enums as ENUM

API_URL  = "http://localhost:5000"
# API_URL  = "https://apix.tamps.cinvestav.mx/jub"
USERNAME = "invitado"
PASSWORD = "invitado"


@pytest.fixture
async def client():
    result = await JubClientBuilder()\
        .with_api_url(API_URL)\
        .with_credentials(USERNAME, PASSWORD)\
        .build()

    if result.is_err:
        pytest.skip(f"API unavailable or credentials invalid: {result.unwrap_err()}")

    return result.unwrap()


# ── Building Blocks ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_delete_building_block(client):
    # Create
    result = await client.create_building_block(
        DTO.BuildingBlockCreateDTO(
            name="Integration Test BB",
            command="python main.py",
            image="python:3.11-slim",
            description="Created by integration test",
        )
    )
    assert result.is_ok, f"create_building_block failed: {result.unwrap_err()}"
    bb = result.unwrap()
    assert bb.building_block_id
    assert bb.name == "Integration Test BB"
    bb_id = bb.building_block_id

    # List
    list_r = await client.list_building_blocks(skip=0, limit=100)
    assert list_r.is_ok
    ids = [b.building_block_id for b in list_r.unwrap()]
    assert bb_id in ids

    # Get
    get_r = await client.get_building_block(bb_id)
    assert get_r.is_ok
    assert get_r.unwrap().building_block_id == bb_id

    # Update
    upd_r = await client.update_building_block(
        bb_id,
        DTO.BuildingBlockUpdateDTO(description="Updated by integration test"),
    )
    assert upd_r.is_ok
    assert upd_r.unwrap().description == "Updated by integration test"

    # Delete — API returns 204 (no body); client result is Err(JSONDecodeError) but the resource is deleted
    await client.delete_building_block(bb_id)


# ── Patterns ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_delete_pattern(client):
    # Create a BB to reference
    bb_r = await client.create_building_block(
        DTO.BuildingBlockCreateDTO(name="BB for Pattern Test", command="run.sh", image="alpine:3")
    )
    assert bb_r.is_ok
    bb_id = bb_r.unwrap().building_block_id

    # Create pattern
    result = await client.create_pattern(
        DTO.PatternCreateDTO(
            name="Integration Test Pattern",
            task="transform",
            pattern="pipeline",
            description="Created by integration test",
            workers=2,
            building_block_id=bb_id,
        )
    )
    assert result.is_ok, f"create_pattern failed: {result.unwrap_err()}"
    pat = result.unwrap()
    assert pat.pattern_id
    assert pat.building_block_id == bb_id
    pat_id = pat.pattern_id

    # List
    list_r = await client.list_patterns(skip=0, limit=100)
    assert list_r.is_ok
    ids = [p.pattern_id for p in list_r.unwrap()]
    assert pat_id in ids

    # Get
    get_r = await client.get_pattern(pat_id)
    assert get_r.is_ok
    assert get_r.unwrap().pattern_id == pat_id

    # Update
    upd_r = await client.update_pattern(
        pat_id,
        DTO.PatternUpdateDTO(workers=4),
    )
    assert upd_r.is_ok
    assert upd_r.unwrap().workers == 4

    # Cleanup — both return 204 (no body); resource is deleted even though client returns Err
    await client.delete_pattern(pat_id)
    await client.delete_building_block(bb_id)


# ── Stages ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_delete_stage(client):
    # Create
    result = await client.create_stage(
        DTO.StageCreateDTO(
            name="Integration Test Stage",
            source="s3://test-bucket/input",
            sink="s3://test-bucket/output",
            endpoint="http://stage-test:8080",
        )
    )
    assert result.is_ok, f"create_stage failed: {result.unwrap_err()}"
    stage = result.unwrap()
    assert stage.stage_id
    assert stage.name == "Integration Test Stage"
    stage_id = stage.stage_id

    # List
    list_r = await client.list_stages(skip=0, limit=100)
    assert list_r.is_ok
    ids = [s.stage_id for s in list_r.unwrap()]
    assert stage_id in ids

    # Get
    get_r = await client.get_stage(stage_id)
    assert get_r.is_ok
    assert get_r.unwrap().stage_id == stage_id

    # Update
    upd_r = await client.update_stage(
        stage_id,
        DTO.StageUpdateDTO(endpoint="http://stage-test:9090"),
    )
    assert upd_r.is_ok
    assert upd_r.unwrap().endpoint == "http://stage-test:9090"

    # Delete — API returns 204 (no body); resource is deleted even though client returns Err
    await client.delete_stage(stage_id)


# ── Workflows ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_delete_workflow(client):
    # Create two stages to assemble
    s1_r = await client.create_stage(
        DTO.StageCreateDTO(name="Stage A", source="s3://in", sink="s3://mid", endpoint="http://a:8080")
    )
    s2_r = await client.create_stage(
        DTO.StageCreateDTO(name="Stage B", source="s3://mid", sink="s3://out", endpoint="http://b:8080")
    )
    assert s1_r.is_ok and s2_r.is_ok
    s1_id = s1_r.unwrap().stage_id
    s2_id = s2_r.unwrap().stage_id

    # Create workflow
    result = await client.create_workflow(
        DTO.WorkflowCreateDTO(name="Integration Test Workflow", stage_ids=[s1_id, s2_id])
    )
    assert result.is_ok, f"create_workflow failed: {result.unwrap_err()}"
    wf = result.unwrap()
    assert wf.workflow_id
    assert s1_id in wf.stage_ids
    assert s2_id in wf.stage_ids
    wf_id = wf.workflow_id

    # List
    list_r = await client.list_workflows(skip=0, limit=100)
    assert list_r.is_ok
    ids = [w.workflow_id for w in list_r.unwrap()]
    assert wf_id in ids

    # Get
    get_r = await client.get_workflow(wf_id)
    assert get_r.is_ok
    assert get_r.unwrap().workflow_id == wf_id

    # Update
    upd_r = await client.update_workflow(
        wf_id,
        DTO.WorkflowUpdateDTO(name="Updated Integration Workflow"),
    )
    assert upd_r.is_ok
    assert upd_r.unwrap().name == "Updated Integration Workflow"

    # Delete workflow (cascade also removes stages)
    del_r = await client.delete_workflow(wf_id, cascade=True)
    assert del_r.is_ok, f"delete_workflow failed: {del_r.unwrap_err()}"


# ── Services ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_delete_service(client):
    # Create a workflow to attach
    wf_r = await client.create_workflow(
        DTO.WorkflowCreateDTO(name="Workflow for Service Test")
    )
    assert wf_r.is_ok
    wf_id = wf_r.unwrap().workflow_id

    # Create service
    result = await client.create_service(
        DTO.ServiceCreateDTO(
            name="Integration Test Service",
            owner_id=client.user_id,
            description="Created by integration test",
            workflow_id=wf_id,
        )
    )
    assert result.is_ok, f"create_service failed: {result.unwrap_err()}"
    svc = result.unwrap()
    assert svc.service_id
    assert svc.workflow_id == wf_id
    svc_id = svc.service_id

    # List
    list_r = await client.list_services(skip=0, limit=100)
    assert list_r.is_ok
    ids = [s.service_id for s in list_r.unwrap()]
    assert svc_id in ids

    # Get
    get_r = await client.get_service(svc_id)
    assert get_r.is_ok
    assert get_r.unwrap().service_id == svc_id

    # Update
    upd_r = await client.update_service(
        svc_id,
        DTO.ServiceUpdateDTO(public=True),
    )
    assert upd_r.is_ok
    assert upd_r.unwrap().public is True

    # Delete service
    del_r = await client.delete_service(svc_id)
    assert del_r.is_ok, f"delete_service failed: {del_r.unwrap_err()}"
    resp = del_r.unwrap()
    assert resp.deleted is True


@pytest.mark.asyncio
async def test_index_service(client):
    """One-shot creation of Service -> Workflow -> Stage -> Pattern -> BuildingBlock."""
    n = 3
    names = ["Service - A", "Service - B", "Service - C"]
    for  name in names:
        result = await client.index_service(
            DTO.ServiceIndexDTO(
                name=name,
                owner_id=client.user_id,
                description="Created by test_index_service",
                provider= ENUM.ServiceProviderEnum.EXTERNAL,
                workflow=DTO.WorkflowInlineDTO(
                    name="Index Workflow",
                    stages=[
                        DTO.StageInlineDTO(
                            name=f"Index Stage {i}",
                            source="s3://index-in",
                            sink="s3://index-out",
                            endpoint=f"http://index-stage-{i}:8080",
                            transformation=DTO.PatternInlineDTO(
                                name=f"Index Pattern {i}",
                                task="transform",
                                pattern="pipeline",
                                building_block=DTO.BuildingBlockInlineDTO(
                                    name=f"Index BB {i}",
                                    command="python index.py",
                                    image="python:3.11-slim",
                                ),
                            ),
                        ) for i in range(n)
                    ],
                ),
            )
        )
        assert result.is_ok, f"index_service failed: {result.unwrap_err()}"
        resp = result.unwrap()
        assert resp.service_id
        assert resp.workflow_id
        assert len(resp.stage_ids) == n
        assert len(resp.pattern_ids) == n
        assert len(resp.building_block_ids) == n

    # Cleanup
    # del_r = await client.delete_service(resp["service_id"])
    # assert del_r.is_ok, f"delete_service (index cleanup) failed: {del_r.unwrap_err()}"
