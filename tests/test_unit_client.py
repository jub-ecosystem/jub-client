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


@pytest.mark.asyncio
async def test_check_auth_decorator_returns_err_when_no_token():
    c = JubClient("http://localhost:5000", "admin", "secret")
    result = await c.get_current_user()
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
        {"observatory_id":None,"title": "Climate Watch", "description": "Global sensors", "image_url": "", "metadata": None},
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
    client._get = _ok({
        "items": [
            {"catalog_id": "cat-001", "name": "Geography", "value": "GEO", "catalog_type": "spatial"},
        ],
        "total": 1,
        "skip": 0,
        "limit": 50,
    })

    result = await client.list_catalogs()

    assert result.is_ok
    page = result.unwrap()
    assert page.total == 1
    assert isinstance(page.items[0], DTO.CatalogSummaryDTO)
    assert page.items[0].catalog_id == "cat-001"


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
    assert result.unwrap().inserted == 1


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


# ── API sync: catalogs ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_catalog_handles_no_content(client):
    client._delete_no_content = _ok(True)

    result = await client.delete_catalog("cat-001")

    assert result.is_ok and result.unwrap() is True
    client._delete_no_content.assert_awaited_once_with("http://localhost:5000/api/v2/catalogs/cat-001")


@pytest.mark.asyncio
async def test_list_catalogs_sends_filters(client):
    client._get = _ok({"items": [], "total": 0, "skip": 10, "limit": 5})

    result = await client.list_catalogs(catalog_type=["SPATIAL", "TEMPORAL"], q="mex", skip=10, limit=5)

    assert result.is_ok
    client._get.assert_awaited_once_with(
        "http://localhost:5000/api/v2/catalogs",
        params={"skip": 10, "limit": 5, "catalog_type": ["SPATIAL", "TEMPORAL"], "q": "mex"},
    )


@pytest.mark.asyncio
async def test_list_catalog_items_for_catalog(client):
    client._get = _ok([_catalog_item()])

    result = await client.list_catalog_items_for_catalog("cat-001")

    assert result.is_ok
    assert result.unwrap()[0].catalog_item_id == "itm-001"
    client._get.assert_awaited_once_with("http://localhost:5000/api/v2/catalogs/cat-001/items")


# ── API sync: observatories ────────────────────────────────────


@pytest.mark.asyncio
async def test_observatory_parses_status_and_view_count(client):
    client._get = _ok({**_obs(), "is_disabled": True, "view_count": 7})

    result = await client.get_observatory("obs-001")

    assert result.is_ok
    obs = result.unwrap()
    assert obs.is_disabled is True
    assert obs.view_count == 7


@pytest.mark.asyncio
async def test_set_observatory_status(client):
    client._patch = _ok({**_obs(), "is_disabled": True})

    result = await client.set_observatory_status("obs-001", DTO.ObservatoryStatusUpdateDTO(is_disabled=True))

    assert result.is_ok and result.unwrap().is_disabled is True
    client._patch.assert_awaited_once_with(
        "http://localhost:5000/api/v2/observatories/obs-001/status", {"is_disabled": True}
    )


@pytest.mark.asyncio
async def test_increment_observatory_view(client):
    client._post = _ok({"observatory_id": "obs-001", "view_count": 3})

    result = await client.increment_observatory_view("obs-001")

    assert result.is_ok and result.unwrap().view_count == 3


@pytest.mark.asyncio
async def test_observatory_review_crud(client):
    review = {
        "review_id": "rev-001", "observatory_id": "obs-001", "user_id": "user-abc",
        "content": "Useful", "rating": 4, "created_at": TS, "updated_at": TS,
    }
    client._get = _ok([review])
    client._post = _ok(review)
    client._put = _ok({**review, "rating": 5})
    client._delete_no_content = _ok(True)

    listed = await client.list_observatory_reviews("obs-001")
    created = await client.create_observatory_review("obs-001", DTO.CreateReviewDTO(content="Useful", rating=4))
    updated = await client.update_observatory_review("obs-001", "rev-001", {"rating": 5})
    deleted = await client.delete_observatory_review("obs-001", "rev-001")

    assert listed.unwrap()[0].review_id == "rev-001"
    assert created.unwrap().rating == 4
    assert updated.unwrap().rating == 5
    assert deleted.unwrap() is True
    client._delete_no_content.assert_awaited_once_with(
        "http://localhost:5000/api/v2/observatories/obs-001/reviews/rev-001"
    )


def test_create_review_dto_rejects_out_of_range_rating():
    with pytest.raises(ValueError):
        DTO.CreateReviewDTO(content="x", rating=6)


# ── API sync: products ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_filter_products_sends_metadata_as_query_params(client):
    client._get = _ok([{**_product(), "metadata": {"extension": "csv"}}])

    result = await client.filter_products({"extension": "csv"}, limit=20)

    assert result.is_ok
    assert result.unwrap()[0].metadata == {"extension": "csv"}
    client._get.assert_awaited_once_with(
        "http://localhost:5000/api/v2/products/filter", params={"extension": "csv", "limit": 20}
    )


@pytest.mark.asyncio
async def test_filter_products_rejects_reserved_limit_key(client):
    client._get = _ok([])

    result = await client.filter_products({"limit": "5"})

    assert result.is_err
    client._get.assert_not_awaited()


@pytest.mark.asyncio
async def test_tag_product_from_catalog(client):
    client._post = _ok({"product_id": "prod-001", "catalog_id": "cat-001", "linked_items": 12})

    result = await client.tag_product_from_catalog("prod-001", "cat-001")

    assert result.is_ok and result.unwrap().linked_items == 12


@pytest.mark.asyncio
async def test_related_products(client):
    client._get = _ok([_product("prod-002")])
    client._post = _ok({"product_id": "prod-001", "related_product_id": "prod-002"})
    client._delete_no_content = _ok(True)

    listed = await client.list_related_products("prod-001")
    added = await client.add_related_product("prod-001", DTO.RelateProductDTO(related_product_id="prod-002"))
    removed = await client.remove_related_product("prod-001", "prod-002")

    assert listed.unwrap()[0].product_id == "prod-002"
    assert added.unwrap().related_product_id == "prod-002"
    assert removed.unwrap() is True
    client._post.assert_awaited_once_with(
        "http://localhost:5000/api/v2/products/prod-001/related", {"related_product_id": "prod-002"}
    )


# ── API sync: search suggestions and tasks ─────────────────────


@pytest.mark.asyncio
async def test_product_search_suggestions_omits_unset_observatory(client):
    client._get = _ok({"observatory_id": "", "suggestions": [{"query": "jub.v1.VS(MX)", "hit_count": 4}]})

    result = await client.get_product_search_suggestions()

    assert result.is_ok and result.unwrap().suggestions[0].hit_count == 4
    client._get.assert_awaited_once_with(
        "http://localhost:5000/api/v2/search/products/suggestions", params={"limit": 5}
    )


@pytest.mark.asyncio
async def test_observatory_search_suggestions(client):
    client._get = _ok({"suggestions": [{"query": "jub.v1.VS(MX)", "hit_count": 2}]})

    result = await client.get_observatory_search_suggestions(limit=3)

    assert result.is_ok and result.unwrap().suggestions[0].query == "jub.v1.VS(MX)"


@pytest.mark.asyncio
async def test_list_my_tasks_sends_skip(client):
    client._get = _ok([])

    await client.list_my_tasks(limit=10, skip=20)

    client._get.assert_awaited_once_with("http://localhost:5000/api/v2/tasks", params={"limit": 10, "skip": 20})


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
    assert ingest_result.unwrap().inserted == 1

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
