"""
Unit tests for JubClient v2.

All HTTP calls are mocked — no running server required.
Internal _post/_get/_put/_delete/_patch helpers are patched directly
for method-level tests; httpx.AsyncClient is patched for authenticate().
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from option import Ok, Err

from jub.client.v2 import JubClient, JubClientBuilder
import jub.dto.v2 as DTO

# ── Helpers ────────────────────────────────────────────────────

TS = "2024-01-01T00:00:00"  # reusable timestamp for mock responses


def _ok(data):
    return AsyncMock(return_value=Ok(data))


def _err(msg="server error"):
    return AsyncMock(return_value=Err(Exception(msg)))


def _make_httpx_ctx(json_data):
    """Wraps json_data in a fake httpx async context-manager response."""
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()

    http = AsyncMock()
    http.post.return_value = resp

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=http)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx, http


def _obs(observatory_id="obs-001", title="Climate Watch"):
    return {
        "observatory_id": observatory_id,
        "title": title,
        "description": "Test observatory",
        "image_url": None,
        "metadata": {},
        "created_at": TS,
        "updated_at": TS,
    }


def _product(product_id="prod-001", name="Cancer Rates"):
    return {"product_id": product_id, "name": name, "description": "", "created_at": TS, "updated_at": TS}


def _catalog_item(catalog_item_id="itm-001"):
    return {
        "catalog_item_id": catalog_item_id, "name": "México", "value": "MX",
        "code": 9, "value_type": "string", "description": "",
        "created_at": TS, "updated_at": TS,
    }


# ── Fixtures ───────────────────────────────────────────────────


@pytest.fixture
def client():
    """Pre-authenticated client with a fake token (no HTTP needed)."""
    c = JubClient("http://localhost:5000", "admin", "secret")
    c._token = "test-token"
    c.user_id = "user-abc"
    return c


# ── Authentication ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_authenticate_stores_token():
    auth_response = {
        "access_token": "jwt-token-xyz",
        "temporal_secret_key": "tsk-123",
        "user_profile": {"user_id": "user-001"},
    }
    ctx, http = _make_httpx_ctx(auth_response)

    with patch("httpx.AsyncClient", return_value=ctx):
        c = JubClient("http://localhost:5000", "admin", "secret")
        result = await c.authenticate()

    assert result.is_ok
    assert c._token == "jwt-token-xyz"
    assert c.user_id == "user-001"
    assert c.temporal_secret_key == "tsk-123"


@pytest.mark.asyncio
async def test_authenticate_failure_returns_err():
    ctx, http = _make_httpx_ctx({})
    http.post.side_effect = Exception("401 Unauthorized")

    with patch("httpx.AsyncClient", return_value=ctx):
        c = JubClient("http://localhost:5000", "bad", "creds")
        result = await c.authenticate()

    assert result.is_err


def test_check_auth_decorator_returns_err_when_no_token():
    c = JubClient("http://localhost:5000", "admin", "secret")
    # _token is None — check_auth returns Err synchronously (not a coroutine)
    result = c.get_current_user()
    assert result.is_err
    assert "not authenticated" in str(result.unwrap_err()).lower()


# ── Observatories ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_observatory(client):
    client._post = _ok(_obs())

    result = await client.create_observatory(
        DTO.ObservatoryCreateDTO(title="Climate Watch", description="Global sensors")
    )

    assert result.is_ok
    obs = result.unwrap()
    assert isinstance(obs, DTO.ObservatoryXDTO)
    assert obs.observatory_id == "obs-001"
    assert obs.title == "Climate Watch"
    client._post.assert_awaited_once_with(
        "http://localhost:5000/api/v2/observatories",
        {"title": "Climate Watch", "description": "Global sensors", "image_url": ""},
    )


@pytest.mark.asyncio
async def test_create_observatory_accepts_dict(client):
    client._post = _ok(_obs("obs-002"))
    result = await client.create_observatory({"title": "Minimal Obs"})
    assert result.is_ok
    assert isinstance(result.unwrap(), DTO.ObservatoryXDTO)


@pytest.mark.asyncio
async def test_list_observatories(client):
    client._get = _ok([_obs("obs-001"), _obs("obs-002", "Second")])

    result = await client.list_observatories(page_index=0, limit=10)

    assert result.is_ok
    items = result.unwrap()
    assert len(items) == 2
    assert all(isinstance(i, DTO.ObservatoryXDTO) for i in items)
    client._get.assert_awaited_once_with(
        "http://localhost:5000/api/v2/observatories",
        params={"page_index": 0, "limit": 10},
    )


@pytest.mark.asyncio
async def test_get_observatory(client):
    client._get = _ok(_obs())
    result = await client.get_observatory("obs-001")
    assert result.is_ok
    assert result.unwrap().title == "Climate Watch"


@pytest.mark.asyncio
async def test_create_observatory_http_error_returns_err(client):
    client._post = _err("500 Internal Server Error")
    result = await client.create_observatory(DTO.ObservatoryCreateDTO(title="X"))
    assert result.is_err


# ── Catalogs ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_catalogs(client):
    client._get = _ok([
        {"catalog_id": "cat-001", "name": "Geography", "value": "GEO", "catalog_type": "spatial"},
    ])

    result = await client.list_catalogs()

    assert result.is_ok
    items = result.unwrap()
    assert isinstance(items[0], DTO.CatalogSummaryDTO)
    assert items[0].catalog_id == "cat-001"


@pytest.mark.asyncio
async def test_create_catalog(client):
    client._post = _ok({"catalog_id": "cat-001"})

    dto = DTO.CatalogCreateDTO(
        name="Sex",
        value="SEX",
        catalog_type="INTEREST",
        items=[
            DTO.CatalogItemCreateDTO(name="Female", value="FEMALE", code=1, value_type="STRING"),
        ],
    )
    result = await client.create_catalog(dto)

    assert result.is_ok
    assert isinstance(result.unwrap(), DTO.CatalogCreatedResponseDTO)
    assert result.unwrap().catalog_id == "cat-001"


@pytest.mark.asyncio
async def test_bulk_assign_catalogs_parses_response(client):
    client._post = _ok({"observatory_id": "obs-001", "catalog_ids": ["cat-001", "cat-002"]})

    dto = DTO.BulkCatalogsDTO(
        catalogs=[DTO.CatalogCreateDTO(name="Spatial MX", value="SPATIAL_MX", catalog_type="SPATIAL")]
    )
    result = await client.bulk_assign_catalogs("obs-001", dto)

    assert result.is_ok
    parsed = result.unwrap()
    assert isinstance(parsed, DTO.BulkCatalogsResponseDTO)
    assert parsed.observatory_id == "obs-001"
    assert "cat-001" in parsed.catalog_ids


@pytest.mark.asyncio
async def test_bulk_assign_catalogs_server_error_returns_err(client):
    client._post = _err("422 Unprocessable Entity")
    result = await client.bulk_assign_catalogs("obs-001", DTO.BulkCatalogsDTO())
    assert result.is_err


@pytest.mark.asyncio
async def test_create_catalog_from_json_no_source_returns_err(client):
    result = await client.create_catalog_from_json()
    assert result.is_err
    assert isinstance(result.unwrap_err(), ValueError)


@pytest.mark.asyncio
async def test_create_catalog_from_json_with_dict(client):
    client._post = _ok({"catalog_id": "cat-99"})
    result = await client.create_catalog_from_json(
        data={"name": "Test", "value": "TEST", "catalog_type": "INTEREST", "items": []}
    )
    assert result.is_ok
    assert isinstance(result.unwrap(), DTO.CatalogCreatedResponseDTO)


# ── Products ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_product(client):
    client._post = _ok(_product())

    dto = DTO.ProductCreateDTO(
        name="Cancer Rates",
        description="Annual cancer incidence per 100k",
        product_type="DATASET",
        observatory_id="obs-001",
    )
    result = await client.create_product(dto)

    assert result.is_ok
    p = result.unwrap()
    assert isinstance(p, DTO.ProductSimpleDTO)
    assert p.product_id == "prod-001"


@pytest.mark.asyncio
async def test_bulk_assign_products_parses_response(client):
    client._post = _ok({
        "observatory_id": "obs-001",
        "products": [{"product_id": "prod-001", "name": "Cancer Rates"}],
    })

    dto = DTO.BulkProductsDTO(
        products=[
            DTO.BulkProductItemDTO(name="Cancer Rates", catalog_item_ids=["C_MAMA"])
        ]
    )
    result = await client.bulk_assign_products("obs-001", dto)

    assert result.is_ok
    parsed = result.unwrap()
    assert isinstance(parsed, DTO.BulkProductsResponseDTO)
    assert parsed.observatory_id == "obs-001"
    assert parsed.products[0].product_id == "prod-001"


@pytest.mark.asyncio
async def test_list_products(client):
    client._get = _ok([_product("p1", "A"), _product("p2", "B")])
    result = await client.list_products(limit=50)
    assert result.is_ok
    items = result.unwrap()
    assert len(items) == 2
    assert all(isinstance(p, DTO.ProductSimpleDTO) for p in items)


# ── Data sources ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_data_source_parses_dto(client):
    client._post = _ok({"source_id": "src-001", "name": "Cancer CSV", "description": "", "format": "csv"})

    dto = DTO.DataSourceCreateDTO(name="Cancer CSV", format="csv")
    result = await client.register_data_source(dto)

    assert result.is_ok
    parsed = result.unwrap()
    assert isinstance(parsed, DTO.DataSourceDTO)
    assert parsed.source_id == "src-001"


@pytest.mark.asyncio
async def test_ingest_records(client):
    client._post = _ok({"inserted": 1})

    records = [
        DTO.DataRecordCreateDTO(
            record_id="rec-001",
            spatial_id="MX",
            temporal_id="2024-01-01T00:00:00",
            interest_ids=["FEMALE", "C_MAMA"],
            numerical_interest_ids={"TASA_100K": 12.5},
        )
    ]
    result = await client.ingest_records("src-001", records)

    assert result.is_ok
    assert result.unwrap()["inserted"] == 1


@pytest.mark.asyncio
async def test_ingest_records_from_json_no_source_returns_err(client):
    result = await client.ingest_records_from_json("src-001")
    assert result.is_err
    assert isinstance(result.unwrap_err(), ValueError)


# ── Tasks ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_complete_task(client):
    client._post = _ok({
        "task_id": "task-001",
        "status": "SUCCESS",
        "observatory_id": "obs-001",
        "observatory_enabled": True,
    })

    result = await client.complete_task(
        "task-001", DTO.TaskCompleteDTO(success=True, message="Indexed OK")
    )

    assert result.is_ok
    resp = result.unwrap()
    assert isinstance(resp, DTO.TaskCompleteResponseDTO)
    assert resp.observatory_enabled is True
    client._post.assert_awaited_once_with(
        "http://localhost:5000/api/v2/tasks/task-001/complete",
        {"success": True, "message": "Indexed OK"},
    )


@pytest.mark.asyncio
async def test_get_task_stats(client):
    client._get = _ok({"pending": 2, "running": 1, "success": 10, "failed": 0})
    result = await client.get_task_stats()
    assert result.is_ok
    stats = result.unwrap()
    assert isinstance(stats, DTO.TasksStatsDTO)
    assert stats.pending == 2


# ── JubClientBuilder ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_builder_returns_authenticated_client():
    auth_response = {
        "access_token": "builder-token",
        "temporal_secret_key": None,
        "user_profile": {"user_id": "user-builder"},
    }
    ctx, _ = _make_httpx_ctx(auth_response)

    with patch("httpx.AsyncClient", return_value=ctx):
        result = await (
            JubClientBuilder()
            .with_api_url("http://localhost:5000")
            .with_credentials("admin", "secret")
            .build()
        )

    assert result.is_ok
    assert result.unwrap()._token == "builder-token"


@pytest.mark.asyncio
async def test_builder_returns_err_on_auth_failure():
    ctx, http = _make_httpx_ctx({})
    http.post.side_effect = Exception("connection refused")

    with patch("httpx.AsyncClient", return_value=ctx):
        result = await JubClientBuilder("http://bad-host", "u", "p").build()

    assert result.is_err
    assert "Authentication failed" in str(result.unwrap_err())


# ── Use case: full observatory provisioning (happy path) ───────


@pytest.mark.asyncio
async def test_happy_path_observatory_provision():
    """
    Complete provisioning workflow:
      1. setup_observatory  → disabled observatory + task queued
      2. bulk_assign_catalogs → spatial catalog linked
      3. bulk_assign_products → dataset product linked
      4. register_data_source → CSV source registered
      5. ingest_records       → 1 record uploaded
      6. complete_task        → observatory enabled
    """
    OBS_ID = "obs-happy"
    TASK_ID = "task-happy"
    SRC_ID = "src-happy"

    auth_response = {
        "access_token": "happy-token",
        "temporal_secret_key": None,
        "user_profile": {"user_id": "user-happy"},
    }
    ctx, _ = _make_httpx_ctx(auth_response)

    with patch("httpx.AsyncClient", return_value=ctx):
        client = JubClient("http://localhost:5000", "admin", "secret")
        await client.authenticate()

    assert client._token == "happy-token"

    # Step 1 — setup_observatory (disabled, returns task_id)
    client._post = _ok({"observatory_id": OBS_ID, "task_id": TASK_ID, "status": "pending", "message": ""})
    setup_result = await client.setup_observatory(
        DTO.ObservatorySetupDTO(
            title="National Cancer Observatory",
            description="Tracks cancer incidence across Mexico.",
        )
    )
    assert setup_result.is_ok, f"setup_observatory failed: {setup_result.unwrap_err()}"
    setup = setup_result.unwrap()
    assert isinstance(setup, DTO.ObservatorySetupResponseDTO)
    assert setup.observatory_id == OBS_ID
    assert setup.task_id == TASK_ID

    # Step 2 — bulk_assign_catalogs
    client._post = _ok({"observatory_id": OBS_ID, "catalog_ids": ["cat-spatial", "cat-interest"]})
    catalogs_result = await client.bulk_assign_catalogs(
        OBS_ID,
        DTO.BulkCatalogsDTO(
            catalogs=[
                DTO.CatalogCreateDTO(
                    name="Spatial Mexico",
                    value="SPATIAL_MX",
                    catalog_type="SPATIAL",
                    items=[DTO.CatalogItemCreateDTO(name="México", value="MX", code=9, value_type="STRING")],
                ),
                DTO.CatalogCreateDTO(
                    name="Cancer Types",
                    value="CANCER_TYPE",
                    catalog_type="INTEREST",
                    items=[DTO.CatalogItemCreateDTO(name="Breast Cancer", value="C_MAMA", code=1, value_type="STRING")],
                ),
            ]
        ),
    )
    assert catalogs_result.is_ok, f"bulk_assign_catalogs failed: {catalogs_result.unwrap_err()}"
    catalogs = catalogs_result.unwrap()
    assert catalogs.observatory_id == OBS_ID
    assert len(catalogs.catalog_ids) == 2

    # Step 3 — bulk_assign_products
    client._post = _ok({
        "observatory_id": OBS_ID,
        "products": [{"product_id": "prod-001", "name": "Cancer Incidence Dataset"}],
    })
    products_result = await client.bulk_assign_products(
        OBS_ID,
        DTO.BulkProductsDTO(
            products=[
                DTO.BulkProductItemDTO(
                    name="Cancer Incidence Dataset",
                    description="Annual cancer rates per 100k inhabitants.",
                    catalog_item_ids=["C_MAMA"],
                )
            ]
        ),
    )
    assert products_result.is_ok, f"bulk_assign_products failed: {products_result.unwrap_err()}"
    products = products_result.unwrap()
    assert products.products[0].product_id == "prod-001"

    # Step 4 — register_data_source
    client._post = _ok({"source_id": SRC_ID, "name": "Cancer CSV 2024", "format": "csv"})
    source_result = await client.register_data_source(
        DTO.DataSourceCreateDTO(name="Cancer CSV 2024", format="csv")
    )
    assert source_result.is_ok, f"register_data_source failed: {source_result.unwrap_err()}"
    assert source_result.unwrap().source_id == SRC_ID

    # Step 5 — ingest_records (1 record)
    client._post = _ok({"inserted": 1})
    ingest_result = await client.ingest_records(
        SRC_ID,
        [
            DTO.DataRecordCreateDTO(
                record_id="rec-2024-001",
                spatial_id="MX",
                temporal_id="2024-01-01T00:00:00",
                interest_ids=["C_MAMA"],
                numerical_interest_ids={"TASA_100K": 18.3},
                raw_payload={"source": "SINAIS", "year": 2024},
            )
        ],
    )
    assert ingest_result.is_ok, f"ingest_records failed: {ingest_result.unwrap_err()}"
    assert ingest_result.unwrap()["inserted"] == 1

    # Step 6 — complete_task (enables the observatory)
    client._post = _ok({
        "task_id": TASK_ID,
        "status": "SUCCESS",
        "observatory_id": OBS_ID,
        "observatory_enabled": True,
    })
    complete_result = await client.complete_task(
        TASK_ID,
        DTO.TaskCompleteDTO(success=True, message="Indexing complete"),
    )
    assert complete_result.is_ok, f"complete_task failed: {complete_result.unwrap_err()}"
    completion = complete_result.unwrap()
    assert isinstance(completion, DTO.TaskCompleteResponseDTO)
    assert completion.observatory_enabled is True
