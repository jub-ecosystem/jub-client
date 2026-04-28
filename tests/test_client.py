"""
Integration tests for JubClient v2.

These tests run against a live JUB API at http://localhost:5000.
Start the API server before running:

    cd ~/Programming/Python/jub_api && poetry run uvicorn jubapi.server:app --port 5000

All tests use the 'invitado' account and clean up after themselves.
"""

import pytest
from jub.client.v2 import JubClient, JubClientBuilder
import jub.dto.v2 as DTO

API_URL  = "http://localhost:5000"
USERNAME = "invitado"
PASSWORD = "invitado"


# ── Fixtures ───────────────────────────────────────────────────


@pytest.fixture
async def client():
    """Authenticated JubClient. Skips all tests if the API is unreachable."""
    result = await JubClientBuilder()\
        .with_api_url(API_URL)\
        .with_credentials(USERNAME, PASSWORD)\
        .build()

    if result.is_err:
        pytest.skip(f"API unavailable or credentials invalid: {result.unwrap_err()}")

    return result.unwrap()


# ── Authentication ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_authentication_succeeds(client: JubClient):
    assert client._token is not None
    assert client.user_id is not None


@pytest.mark.asyncio
async def test_get_current_user(client: JubClient):
    result = await client.get_current_user()
    assert result.is_ok, f"get_current_user failed: {result.unwrap_err()}"
    user = result.unwrap()
    assert isinstance(user, DTO.UserProfileDTO)
    assert user.user_id == client.user_id


# ── Observatories ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_delete_observatory(client: JubClient):
    # Create
    result = await client.create_observatory(
        DTO.ObservatoryCreateDTO(
            title="Integration Test Observatory",
            description="Created by test_create_and_delete_observatory",
        )
    )
    assert result.is_ok, f"create_observatory failed: {result.unwrap_err()}"
    obs = result.unwrap()
    assert isinstance(obs, DTO.ObservatoryXDTO)
    assert obs.title == "Integration Test Observatory"
    assert obs.observatory_id

    # Verify it appears in the list
    list_result = await client.list_observatories(limit=100)
    assert list_result.is_ok
    ids = [o.observatory_id for o in list_result.unwrap()]
    assert obs.observatory_id in ids

    # Get by ID
    get_result = await client.get_observatory(obs.observatory_id)
    assert get_result.is_ok
    assert get_result.unwrap().observatory_id == obs.observatory_id

    # Update
    update_result = await client.update_observatory(
        obs.observatory_id,
        DTO.ObservatoryUpdateDTO(description="Updated by integration test"),
    )
    assert update_result.is_ok
    assert update_result.unwrap().description == "Updated by integration test"

    # Delete
    del_result = await client.delete_observatory(obs.observatory_id)
    assert del_result.is_ok, f"delete_observatory failed: {del_result.unwrap_err()}"
    assert isinstance(del_result.unwrap(), DTO.ObservatoryDeleteResponseDTO)
    assert del_result.unwrap().deleted is True


@pytest.mark.asyncio
async def test_list_observatories(client: JubClient):
    result = await client.list_observatories(page_index=0, limit=10)
    assert result.is_ok, f"list_observatories failed: {result.unwrap_err()}"
    items = result.unwrap()
    assert isinstance(items, list)
    assert all(isinstance(o, DTO.ObservatoryXDTO) for o in items)


# ── Catalogs ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_catalog_and_get(client: JubClient):
    result = await client.create_catalog(
        DTO.CatalogCreateDTO(
            name="Integration Test Catalog",
            value="INTEGRATION_TEST_CAT",
            catalog_type="INTEREST",
            description="Created by integration test",
            items=[
                DTO.CatalogItemCreateDTO(name="Item A", value="ITEM_A", code=1001, value_type="STRING"),
                DTO.CatalogItemCreateDTO(name="Item B", value="ITEM_B", code=1002, value_type="STRING"),
            ],
        )
    )
    assert result.is_ok, f"create_catalog failed: {result.unwrap_err()}"
    created = result.unwrap()
    assert isinstance(created, DTO.CatalogCreatedResponseDTO)
    assert created.catalog_id

    # Fetch full catalog
    get_result = await client.get_catalog(created.catalog_id)
    assert get_result.is_ok, f"get_catalog failed: {get_result.unwrap_err()}"
    catalog = get_result.unwrap()
    assert isinstance(catalog, DTO.CatalogResponseDTO)
    assert catalog.catalog_id == created.catalog_id
    assert len(catalog.items) == 2


@pytest.mark.asyncio
async def test_list_catalogs(client: JubClient):
    result = await client.list_catalogs()
    assert result.is_ok, f"list_catalogs failed: {result.unwrap_err()}"
    items = result.unwrap()
    assert isinstance(items, list)
    assert all(isinstance(c, DTO.CatalogSummaryDTO) for c in items)


# ── Products ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_product(client: JubClient):
    result = await client.create_observatory(
        dto = DTO.ObservatoryCreateDTO(
            title       = "Temp Obs for Product Upload Test",
            description = "Created by test_upload_product (should be deleted by cleanup)",
            image_url   = ""
        )
    )
    assert result.is_ok, f"create_observatory failed: {result.unwrap_err()}"
    obs_r = result.unwrap()
    # 
    result = await client.create_product(
        dto = DTO.ProductCreateDTO(
            name             = "Test Product for Upload",
            catalog_item_ids = [],
            description      = "Created by test_upload_product (should be deleted by cleanup)",
            observatory_id   = obs_r.observatory_id,
            product_type     = ""
        )
    )
    assert result.is_ok, f"create_product failed: {result.unwrap_err()}"
    prod_r = result.unwrap()

    result = await client.upload_product(
        product_id= prod_r.product_id,
        file_path= "/source/01.pdf"
    )
    assert result.is_ok, f"upload_product failed: {result.unwrap_err()}"
    

@pytest.mark.asyncio
async def test_create_and_delete_product(client: JubClient):
    # Need an observatory first
    obs_r = await client.create_observatory(
        DTO.ObservatoryCreateDTO(title="Temp Obs for Product Test")
    )
    assert obs_r.is_ok
    obs_id = obs_r.unwrap().observatory_id

    # Create product
    result = await client.create_product(
        DTO.ProductCreateDTO(
            name="Integration Test Product",
            description="Created by test_create_and_delete_product",
            observatory_id=obs_id,
        )
    )
    assert result.is_ok, f"create_product failed: {result.unwrap_err()}"
    product = result.unwrap()
    assert isinstance(product, DTO.ProductSimpleDTO)
    assert product.product_id

    # Get it
    get_r = await client.get_product(product.product_id)
    assert get_r.is_ok
    assert get_r.unwrap().name == "Integration Test Product"

    # Delete product then observatory
    del_p = await client.delete_product(product.product_id)
    assert del_p.is_ok
    assert isinstance(del_p.unwrap(), DTO.ProductDeleteResponseDTO)
    assert del_p.unwrap().deleted is True

    await client.delete_observatory(obs_id)


# ── Data sources ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_and_delete_data_source(client: JubClient):
    result = await client.register_data_source(
        DTO.DataSourceCreateDTO(name="Integration Test Source", format="csv")
    )
    assert result.is_ok, f"register_data_source failed: {result.unwrap_err()}"
    source = result.unwrap()
    assert isinstance(source, DTO.DataSourceDTO)
    assert source.source_id

    # Get it
    get_r = await client.get_data_source(source.source_id)
    assert get_r.is_ok
    assert get_r.unwrap().source_id == source.source_id

    # List it
    list_r = await client.list_data_sources()
    assert list_r.is_ok
    ids = [s.source_id for s in list_r.unwrap()]
    assert source.source_id in ids

    # Delete
    del_r = await client.delete_data_source(source.source_id)
    assert del_r.is_ok, f"delete_data_source failed: {del_r.unwrap_err()}"
    assert isinstance(del_r.unwrap(), DTO.DataSourceDeleteResponseDTO)
    assert del_r.unwrap().deleted is True


@pytest.mark.asyncio
async def test_ingest_and_query_records(client: JubClient):
    src_r = await client.register_data_source(
        DTO.DataSourceCreateDTO(name="Ingest Test Source", format="csv")
    )
    assert src_r.is_ok
    src_id = src_r.unwrap().source_id

    records = [
        DTO.DataRecordCreateDTO(
            record_id=f"rec-test-{i}",
            spatial_id="MX",
            temporal_id=f"2024-0{i+1}-01T00:00:00",
            interest_ids=["C_MAMA"],
            numerical_interest_ids={"TASA_100K": float(i * 10)},
        )
        for i in range(3)
    ]
    ingest_r = await client.ingest_records(src_id, records)
    assert ingest_r.is_ok, f"ingest_records failed: {ingest_r.unwrap_err()}"
    assert ingest_r.unwrap()["inserted"] == 3

    # Clean up
    await client.delete_data_source(src_id)


# ── Tasks ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_task_stats(client: JubClient):
    result = await client.get_task_stats()
    assert result.is_ok, f"get_task_stats failed: {result.unwrap_err()}"
    stats = result.unwrap()
    assert isinstance(stats, DTO.TasksStatsDTO)
    assert stats.pending >= 0


@pytest.mark.asyncio
async def test_list_my_tasks(client: JubClient):
    result = await client.list_my_tasks(limit=10)
    assert result.is_ok, f"list_my_tasks failed: {result.unwrap_err()}"
    tasks = result.unwrap()
    assert isinstance(tasks, list)
    assert all(isinstance(t, DTO.TaskXDTO) for t in tasks)




# ── Use case: full observatory provisioning (happy path) ───────


@pytest.mark.asyncio
async def test_happy_path_observatory_provisioning(client: JubClient):
    """
    Full provisioning flow using the two-step setup pattern:

      1. setup_observatory  — creates a DISABLED observatory + queues a PENDING task
      2. bulk_assign_catalogs — links two catalogs (spatial + interest)
      3. bulk_assign_products — links one dataset product
      4. register_data_source — registers a CSV source
      5. ingest_records       — uploads 1 data record
      6. complete_task        — marks the task SUCCESS → observatory becomes enabled
    """
    # ── 1. Setup observatory ──────────────────────────────────
    setup_r = await client.setup_observatory(
        DTO.ObservatorySetupDTO(
            title="Happy Path Observatory",
            description="Created by test_happy_path_observatory_provisioning",
        )
    )
    assert setup_r.is_ok, f"setup_observatory failed: {setup_r.unwrap_err()}"
    setup = setup_r.unwrap()
    assert isinstance(setup, DTO.ObservatorySetupResponseDTO)
    obs_id  = setup.observatory_id
    task_id = setup.task_id
    assert obs_id and task_id

    # ── 2. Assign catalogs ────────────────────────────────────
    catalogs_r = await client.bulk_assign_catalogs(
        obs_id,
        DTO.BulkCatalogsDTO(
            catalogs=[
                DTO.CatalogCreateDTO(
                    name="Spatial Mexico",
                    value="SPATIAL_MX_HP",
                    catalog_type="SPATIAL",
                    items=[
                        DTO.CatalogItemCreateDTO(
                            name="México", value="MX_HP", code=9901, value_type="STRING"
                        )
                    ],
                ),
                DTO.CatalogCreateDTO(
                    name="Cancer Types",
                    value="CANCER_HP",
                    catalog_type="INTEREST",
                    items=[
                        DTO.CatalogItemCreateDTO(
                            name="Breast Cancer", value="C_MAMA_HP", code=9902, value_type="STRING"
                        )
                    ],
                ),
            ]
        ),
    )
    assert catalogs_r.is_ok, f"bulk_assign_catalogs failed: {catalogs_r.unwrap_err()}"
    catalogs = catalogs_r.unwrap()
    assert isinstance(catalogs, DTO.BulkCatalogsResponseDTO)
    assert catalogs.observatory_id == obs_id
    assert len(catalogs.catalog_ids) == 2

    # Verify catalogs are linked
    obs_cats_r = await client.list_observatory_catalogs(obs_id)
    assert obs_cats_r.is_ok
    linked_cat_ids = [c.catalog_id for c in obs_cats_r.unwrap()]
    for cid in catalogs.catalog_ids:
        assert cid in linked_cat_ids

    # ── 3. Assign product ─────────────────────────────────────
    products_r = await client.bulk_assign_products(
        obs_id,
        DTO.BulkProductsDTO(
            products=[
                DTO.BulkProductItemDTO(
                    name="Cancer Incidence Dataset",
                    description="Annual cancer rates per 100k inhabitants.",
                )
            ]
        ),
    )
    assert products_r.is_ok, f"bulk_assign_products failed: {products_r.unwrap_err()}"
    products = products_r.unwrap()
    assert isinstance(products, DTO.BulkProductsResponseDTO)
    assert products.observatory_id == obs_id
    assert len(products.products) == 1
    product_id = products.products[0].product_id

    # Verify product is linked
    obs_prods_r = await client.list_observatory_products(obs_id)
    assert obs_prods_r.is_ok
    linked_prod_ids = [p.product_id for p in obs_prods_r.unwrap()]
    assert product_id in linked_prod_ids

    # ── 4. Register data source ───────────────────────────────
    src_r = await client.register_data_source(
        DTO.DataSourceCreateDTO(name="Happy Path CSV", format="csv")
    )
    assert src_r.is_ok, f"register_data_source failed: {src_r.unwrap_err()}"
    source = src_r.unwrap()
    assert isinstance(source, DTO.DataSourceDTO)
    source_id = source.source_id

    # ── 5. Ingest 1 record ────────────────────────────────────
    ingest_r = await client.ingest_records(
        source_id,
        [
            DTO.DataRecordCreateDTO(
                record_id="hp-rec-001",
                spatial_id="MX_HP",
                temporal_id="2024-06-15T00:00:00",
                interest_ids=["C_MAMA_HP"],
                numerical_interest_ids={"TASA_100K": 18.3},
                raw_payload={"source": "SINAIS", "year": 2024},
            )
        ],
    )
    assert ingest_r.is_ok, f"ingest_records failed: {ingest_r.unwrap_err()}"
    assert ingest_r.unwrap()["inserted"] == 1

    # ── 6. Complete task → enables observatory ────────────────
    complete_r = await client.complete_task(
        task_id,
        DTO.TaskCompleteDTO(success=True, message="Provisioning complete"),
    )
    assert complete_r.is_ok, f"complete_task failed: {complete_r.unwrap_err()}"
    completion = complete_r.unwrap()
    assert isinstance(completion, DTO.TaskCompleteResponseDTO)
    assert completion.task_id == task_id
    assert completion.observatory_enabled is True

    # Verify observatory is now enabled (is_disabled should be absent/False)
    obs_r = await client.get_observatory(obs_id)
    assert obs_r.is_ok
    obs = obs_r.unwrap()
    assert obs.observatory_id == obs_id

    # ── Cleanup ───────────────────────────────────────────────
    await client.delete_data_source(source_id)
    await client.delete_observatory(obs_id)
