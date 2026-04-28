# Examples

Complete, runnable examples for the most common workflows. All examples assume you have a running JUB API (see [Deployment](deployment.md)) and the library installed (see [Installation](installation.md)).

---

## Initialize the client

=== "Authenticate manually"

    ```python
    import asyncio
    from jub.client.v2 import JubClient

    async def main():
        client = JubClient(
            api_url  = "http://localhost:5000",
            username = "admin",
            password = "secret",
        )
        result = await client.authenticate()
        if result.is_err:
            raise result.unwrap_err()
        print("Authenticated — user_id:", client.user_id)

    asyncio.run(main())
    ```

=== "Use JubClientBuilder"

    ```python
    import asyncio, os
    from jub.client.v2 import JubClientBuilder

    async def main():
        result = await JubClientBuilder(
            api_url  = os.environ.get("JUB_API_URL",  "http://localhost:5000"),
            username = os.environ.get("JUB_USERNAME", "admin"),
            password = os.environ.get("JUB_PASSWORD", "secret"),
        ).build()

        if result.is_err:
            raise result.unwrap_err()

        client = result.unwrap()
        print("Ready — user_id:", client.user_id)

    asyncio.run(main())
    ```

---

## Create a catalog

```python
import jub.dto.v2 as DTO

result = await client.create_catalog(DTO.CatalogCreateDTO(
    name         = "CIE-10 Cancer Groups",
    value        = "CIE10_CANCER",
    catalog_type = "INTEREST",
    description  = "Main cancer diagnosis groups following CIE-10 coding",
    items=[
        DTO.CatalogItemCreateDTO(
            name       = "Breast cancer",
            value      = "C_MAMA",
            code       = 1,
            value_type = "STRING",
            aliases=[
                DTO.CatalogItemAliasCreateDTO(value="C50", value_type="STRING"),
            ],
        ),
        DTO.CatalogItemCreateDTO(
            name="Cervical cancer", value="C_CERVIX", code=2, value_type="STRING",
        ),
        DTO.CatalogItemCreateDTO(
            name="Prostate cancer", value="C_PROSTATA", code=3, value_type="STRING",
        ),
    ],
))

if result.is_ok:
    catalog_id = result.unwrap().catalog_id
    print("Catalog ID:", catalog_id)
else:
    print("Error:", result.unwrap_err())
```

---

## Create an observatory

=== "Immediate (enabled)"

    ```python
    result = await client.create_observatory(DTO.ObservatoryCreateDTO(
        title       = "Cancer Epidemiology — Mexico 2024",
        description = "Mortality and incidence data for the 2018-2023 period.",
        image_url   = "https://example.com/obs.png",
    ))

    obs = result.unwrap()
    print("Observatory ID:", obs.observatory_id)
    ```

=== "Provisioned (disabled until indexed)"

    ```python
    result = await client.setup_observatory(DTO.ObservatorySetupDTO(
        observatory_id = "obs_cancer_mx_2024",
        title          = "Cancer Epidemiology — Mexico 2024",
        description    = "National cancer surveillance for Mexico.",
        metadata       = {"country": "MX", "source": "INCAN"},
    ))

    setup = result.unwrap()
    print("Observatory ID:", setup.observatory_id)
    print("Task ID (save this):", setup.task_id)
    ```

---

## Full observatory provisioning workflow

The recommended way to set up an observatory with all its content before making it visible.

```python
import asyncio, os
from jub.client.v2 import JubClientBuilder
import jub.dto.v2 as DTO

async def main():
    # 1. Connect
    client = (await JubClientBuilder(
        api_url  = os.environ.get("JUB_API_URL", "http://localhost:5000"),
        username = os.environ.get("JUB_USERNAME", "admin"),
        password = os.environ.get("JUB_PASSWORD", "secret"),
    ).build()).unwrap()

    # 2. Create observatory in disabled state
    setup = (await client.setup_observatory(DTO.ObservatorySetupDTO(
        observatory_id = "obs_cancer_mx_2024",
        title          = "Cancer Epidemiology — Mexico 2024",
    ))).unwrap()
    obs_id, task_id = setup.observatory_id, setup.task_id

    # 3. Bulk-create catalogs and link them
    catalogs = (await client.bulk_assign_catalogs(obs_id, DTO.BulkCatalogsDTO(
        catalogs=[
            DTO.CatalogCreateDTO(
                name="Geographic Dimension", value="SPATIAL_MX",
                catalog_type="SPATIAL",
                items=[
                    DTO.CatalogItemCreateDTO(
                        name="Mexico", value="MX", code=0, value_type="STRING",
                    ),
                ],
            ),
            DTO.CatalogCreateDTO(
                name="CIE-10 Cancer Groups", value="CIE10_CANCER",
                catalog_type="INTEREST",
                items=[
                    DTO.CatalogItemCreateDTO(name="Breast cancer", value="C_MAMA",     code=1, value_type="STRING"),
                    DTO.CatalogItemCreateDTO(name="Cervical cancer", value="C_CERVIX", code=2, value_type="STRING"),
                ],
            ),
        ]
    ))).unwrap()
    print("Catalog IDs:", catalogs.catalog_ids)

    # 4. Bulk-create products and link them
    products = (await client.bulk_assign_products(obs_id, DTO.BulkProductsDTO(
        products=[
            DTO.BulkProductItemDTO(
                product_id  = "prod_mortality_by_state",
                name        = "Cancer Mortality by State",
                description = "Age-standardised mortality rates per 100k.",
            ),
        ]
    ))).unwrap()
    print("Product IDs:", [p.product_id for p in products.products])

    # 5. Enable the observatory
    done = (await client.complete_task(task_id, DTO.TaskCompleteDTO(
        success = True,
        message = "Provisioning complete.",
    ))).unwrap()
    print("Observatory enabled:", done.observatory_enabled)

asyncio.run(main())
```

---

## Register a data source and ingest records

```python
# Register
ds = (await client.register_data_source(DTO.DataSourceCreateDTO(
    name        = "Cancer mortality records",
    format      = "json",
    description = "Annual mortality data from SINAIS",
))).unwrap()

source_id = ds.source_id

# Ingest a batch
result = await client.ingest_records(source_id, [
    DTO.DataRecordCreateDTO(
        record_id   = "rec_001",
        spatial_id  = "item_id_MX",        # catalog item ID for Mexico
        temporal_id = "2022-01-01T00:00:00Z",
        interest_ids = ["item_id_C_MAMA"],
        numerical_interest_ids = {"item_id_TASA_100K": 18.5},
        raw_payload = {"source_file": "sinais_2022.csv"},
    ),
])

inserted = result.unwrap()
print("Records inserted:", inserted.inserted)
```

---

## Search with the JUB DSL

=== "Product search"

    ```python
    result = await client.search(DTO.SearchQueryDTO(
        query          = "jub.v1.VS(MX).VT(>= 2020).VI(C_MAMA OR C_CERVIX)",
        observatory_id = "obs_cancer_mx_2024",
        limit          = 20,
    ))

    products = result.unwrap()
    print(f"Found {len(products)} products")
    ```

=== "Raw record query"

    ```python
    result = await client.search_records(DTO.SearchQueryDTO(
        query = "jub.v1.VS(MX).VT(>= 2022).VI(C_MAMA)",
        limit = 100,
    ))
    records = result.unwrap()
    ```

=== "Generate a plot"

    ```python
    result = await client.generate_plot(DTO.PlotQueryDTO(
        query      = "jub.v1.VS(MX).VI(C_MAMA OR C_OVARIO).VO(AVG(TASA_100K)).BY(CIE10_CANCER)",
        chart_type = "bar",
    ))

    echarts_config = result.unwrap()
    # Pass echarts_config directly to an ECharts instance in your front end
    ```

---

## Index a service with one call

```python
result = await client.index_service(DTO.ServiceIndexDTO(
    name        = "Cancer Data Pipeline",
    owner_id    = client.user_id,
    description = "Ingestion pipeline for SINAIS cancer records.",
    public      = True,
    workflow    = DTO.WorkflowInlineDTO(
        name   = "Cancer Ingestion Workflow",
        stages = [
            DTO.StageInlineDTO(
                name     = "Ingest Stage",
                source   = "s3://raw-data/sinais/",
                sink     = "jub://datasource/cancer_records",
                endpoint = "http://ingestor:8080/ingest",
                transformation = DTO.PatternInlineDTO(
                    name    = "Map-Reduce Ingestor",
                    task    = "ingest",
                    pattern = "map-reduce",
                    workers = 4,
                    building_block = DTO.BuildingBlockInlineDTO(
                        name    = "Python Ingestor",
                        command = "python ingest.py",
                        image   = "python:3.11-slim",
                    ),
                ),
            ),
        ],
    ),
))

index = result.unwrap()
print("Service ID:", index.service_id)
print("Workflow ID:", index.workflow_id)
print("Stage IDs:", index.stage_ids)
```

---

## Ingest from JSON files

```python
# Catalog from a JSON file
result = await client.create_catalog_from_json(json_path="catalogs/spatial.json")
catalog_id = result.unwrap().catalog_id

# Records from a JSON file
result = await client.ingest_records_from_json(
    source_id   = source_id,
    json_path   = "records/cancer_2022.json",
)
print("Inserted:", result.unwrap().inserted)
```

---

## Upload and download product files

```python
# Upload an HTML chart
upload = (await client.upload_product(
    product_id = "prod_mortality_by_state",
    file_path  = "charts/mortality_by_state.html",
)).unwrap()
print(f"Queued as job {upload.job_id} (status: {upload.status})")

# Download later
raw_bytes = (await client.download_product("prod_mortality_by_state")).unwrap()
with open("output.html", "wb") as f:
    f.write(raw_bytes)
```
