"""
Use Case 1 — Full Observatory Setup (Async Provisioning)

Demonstrates the complete lifecycle for provisioning a new observatory:

  Step 1: Initialize the observatory in disabled state  →  receives a task_id
  Step 2: Bulk-create and link catalogs                 →  spatial, interest, temporal
  Step 3: Bulk-create and link products                 →  tagged with catalog item IDs
  Step 4: Upload a chart/report file for each product   →  queued for background ingestion
  Step 5: Complete the setup task                       →  observatory becomes active

Observatories are created disabled so that all their content can be indexed before
they are exposed to end users. The setup task is the gate: call complete_task with
success=True when everything is in place.

Run:
    python 1_full_observatory_setup.py

Environment variables (optional):
    JUB_API_URL   — API base URL    (default: http://localhost:5000)
    JUB_USERNAME  — Login username  (default: invitado)
    JUB_PASSWORD  — Login password  (default: invitado)
"""

import asyncio
import os

from jub.client.v2 import JubClient, JubClientBuilder
import jub.dto.v2 as DTO
from dotenv import load_dotenv

JUB_CLIENT_ENV_FILE_PATH = os.environ.get("JUB_CLIENT_ENV_FILE_PATH", ".env")
if os.path.exists(JUB_CLIENT_ENV_FILE_PATH):
    load_dotenv(JUB_CLIENT_ENV_FILE_PATH)
    print(f"Loaded environment variables from {JUB_CLIENT_ENV_FILE_PATH!r}")


# Change these to match your observatory
OBSERVATORY_ID = os.environ.get("OBSERVATORY_ID", "obs_cancer_mx_2024")

# Chart files to upload (path on disk → product_id)
# Replace with paths to real files before running.
CHART_FILES: dict[str, str] = {
    "prod_cancer_mortality_by_state": "charts/mortality_by_state.html",
    "prod_cancer_incidence_trends":   "charts/incidence_trends.html",
    "prod_cancer_sex_age":            "charts/sex_age_distribution.html",
}


# ── Step 1 ────────────────────────────────────────────────────────────────────

async def step1_setup_observatory(client: JubClient) -> tuple[str, str]:
    """
    POST /api/v2/observatories/setup

    Creates the observatory in disabled state and returns its ID and the
    associated background task ID. Keep the task_id — you will need it
    in Step 5 to enable the observatory.
    """
    print("\n[Step 1] Initializing observatory...")

    result = await client.setup_observatory(DTO.ObservatorySetupDTO(
        observatory_id = OBSERVATORY_ID,
        title          = "Cancer Epidemiology Observatory — Mexico 2024",
        description    = (
            "Epidemiological surveillance of cancer incidence in Mexico. "
            "Covers mortality rates by state, sex, age, and CIE-10 diagnosis group."
        ),
        image_url = "https://example.com/obs-cancer-mx.png",
        metadata  = {
            "country":       "MX",
            "source":        "INCAN / SINAIS",
            "data_year_min": "2018",
            "data_year_max": "2023",
        },
    ))

    if result.is_err:
        raise RuntimeError(f"setup_observatory failed: {result.unwrap_err()}")

    setup = result.unwrap()
    print(f"  Observatory ID : {setup.observatory_id}")
    print(f"  Task ID        : {setup.task_id}  ← needed for Step 5")
    return setup.observatory_id, setup.task_id


# ── Step 2 ────────────────────────────────────────────────────────────────────

async def step2_bulk_assign_catalogs(
    client: JubClient,
    obs_id: str,
) -> list[str]:
    """
    POST /api/v2/observatories/{obs_id}/catalogs/bulk

    Creates three catalogs (spatial, interest, temporal) and links all of them
    to the observatory in one request. Returns the list of catalog IDs.
    """
    print("\n[Step 2] Creating and linking catalogs...")

    result = await client.bulk_assign_catalogs(obs_id, DTO.BulkCatalogsDTO(
        catalogs=[
            # ── Spatial: geographic hierarchy ────────────────────────────────
            DTO.CatalogCreateDTO(
                name         = "Spatial Dimension — Mexico",
                value        = "SPATIAL_MX",
                catalog_type = "SPATIAL",
                description  = "Geographic hierarchy: Country → State",
                items=[
                    DTO.CatalogItemCreateDTO(
                        name        = "Mexico",
                        value       = "MX",
                        code        = 0,
                        value_type  = "STRING",
                        description = "United Mexican States",
                        aliases=[
                            DTO.CatalogItemAliasCreateDTO(value="MEX", value_type="STRING",
                                description="ISO 3166-1 alpha-3"),
                            DTO.CatalogItemAliasCreateDTO(value="484", value_type="NUMBER",
                                description="ISO numeric code"),
                        ],
                        children=[
                            DTO.CatalogItemCreateDTO(
                                name="Ciudad de Mexico", value="CDMX", code=9,
                                value_type="STRING",
                                aliases=[DTO.CatalogItemAliasCreateDTO(value="09", value_type="NUMBER")],
                            ),
                            DTO.CatalogItemCreateDTO(
                                name="Jalisco", value="JALISCO", code=14,
                                value_type="STRING",
                                aliases=[DTO.CatalogItemAliasCreateDTO(value="14", value_type="NUMBER")],
                            ),
                            DTO.CatalogItemCreateDTO(
                                name="Nuevo Leon", value="NL", code=19,
                                value_type="STRING",
                                aliases=[DTO.CatalogItemAliasCreateDTO(value="19", value_type="NUMBER")],
                            ),
                        ],
                    ),
                ],
            ),
            # ── Interest: cancer diagnosis groups (CIE-10) ───────────────────
            DTO.CatalogCreateDTO(
                name         = "CIE-10 Cancer Groups",
                value        = "CIE10_CANCER",
                catalog_type = "INTEREST",
                description  = "Main cancer diagnosis groups following CIE-10 coding",
                items=[
                    DTO.CatalogItemCreateDTO(name="Breast cancer",    value="C_MAMA",     code=1,
                        value_type="STRING", aliases=[DTO.CatalogItemAliasCreateDTO(value="C50", value_type="STRING")]),
                    DTO.CatalogItemCreateDTO(name="Cervical cancer",   value="C_CERVIX",   code=2,
                        value_type="STRING", aliases=[DTO.CatalogItemAliasCreateDTO(value="C53", value_type="STRING")]),
                    DTO.CatalogItemCreateDTO(name="Ovarian cancer",    value="C_OVARIO",   code=3,
                        value_type="STRING", aliases=[DTO.CatalogItemAliasCreateDTO(value="C56", value_type="STRING")]),
                    DTO.CatalogItemCreateDTO(name="Prostate cancer",   value="C_PROSTATA", code=4,
                        value_type="STRING", aliases=[DTO.CatalogItemAliasCreateDTO(value="C61", value_type="STRING")]),
                    DTO.CatalogItemCreateDTO(name="Colorectal cancer", value="C_COLON",    code=5,
                        value_type="STRING", aliases=[DTO.CatalogItemAliasCreateDTO(value="C18", value_type="STRING")]),
                ],
            ),
            # ── Temporal: annual reporting years ─────────────────────────────
            DTO.CatalogCreateDTO(
                name         = "Reporting Years",
                value        = "TEMPORAL_YEARS",
                catalog_type = "TEMPORAL",
                description  = "Annual time dimension for the epidemiological series (2018–2023)",
                items=[
                    DTO.CatalogItemCreateDTO(
                        name           = str(year),
                        value          = f"Y{year}",
                        code           = year,
                        value_type     = "DATETIME",
                        temporal_value = f"{year}-01-01T00:00:00Z",
                    )
                    for year in range(2018, 2024)
                ],
            ),
        ]
    ))

    if result.is_err:
        raise RuntimeError(f"bulk_assign_catalogs failed: {result.unwrap_err()}")

    catalog_ids = result.unwrap().catalog_ids
    print(f"  Catalogs created and linked: {catalog_ids}")
    return catalog_ids


# ── Step 3 ────────────────────────────────────────────────────────────────────

async def step3_bulk_assign_products(
    client: JubClient,
    obs_id: str,
    catalog_ids: list[str],
) -> list[str]:
    """
    POST /api/v2/observatories/{obs_id}/products/bulk

    Fetches catalog items from the interest catalog to use as product tags,
    then creates three products and links them to the observatory.
    Returns a list of product IDs.
    """
    print("\n[Step 3] Creating and linking products...")

    # Collect catalog item IDs to tag the products with.
    # Here we pull all items from every catalog; in practice you would
    # select only the relevant ones for each product.
    item_ids: list[str] = []
    for cat_id in catalog_ids:
        cat_result = await client.get_catalog(cat_id)
        if cat_result.is_err:
            print(f"  Could not fetch catalog {cat_id}: {cat_result.unwrap_err()}")
            continue
        item_ids.extend(item.catalog_item_id for item in cat_result.unwrap().items)

    result = await client.bulk_assign_products(obs_id, DTO.BulkProductsDTO(
        products=[
            DTO.BulkProductItemDTO(
                product_id       = "prod_cancer_mortality_by_state",
                name             = "Cancer Mortality by State",
                description      = "Age-standardised mortality rates per 100k by federal entity.",
                catalog_item_ids = item_ids,
            ),
            DTO.BulkProductItemDTO(
                product_id       = "prod_cancer_incidence_trends",
                name             = "Cancer Incidence Trends",
                description      = "Annual incidence trends from 2018 to 2023.",
                catalog_item_ids = item_ids,
            ),
            DTO.BulkProductItemDTO(
                product_id       = "prod_cancer_sex_age",
                name             = "Cancer by Sex and Age Group",
                description      = "Distribution across sex and five-year age cohorts.",
                catalog_item_ids = item_ids,
            ),
        ]
    ))

    if result.is_err:
        raise RuntimeError(f"bulk_assign_products failed: {result.unwrap_err()}")

    product_ids = [p.product_id for p in result.unwrap().products]
    print(f"  Products created and linked: {product_ids}")
    return product_ids


# ── Step 4 ────────────────────────────────────────────────────────────────────

async def step4_upload_product_files(
    client: JubClient,
    product_ids: list[str],
) -> None:
    """
    POST /api/v2/products/{product_id}/upload

    Uploads an HTML chart or report file for each product. The file is queued
    for background ingestion; a job_id is returned immediately and can be
    polled via get_task() if you need to wait for completion.
    """
    print("\n[Step 4] Uploading product files...")

    for product_id in product_ids:
        file_path = CHART_FILES.get(product_id)
        if not file_path:
            print(f"  Skipping {product_id}: no chart file configured in CHART_FILES")
            continue
        if not os.path.exists(file_path):
            print(f"  Skipping {product_id}: file not found at {file_path!r}")
            continue

        upload_result = await client.upload_product(product_id, file_path)
        if upload_result.is_err:
            print(f"  Upload failed for {product_id}: {upload_result.unwrap_err()}")
            continue

        upload = upload_result.unwrap()
        print(f"  {product_id} → job_id={upload.job_id}  status={upload.status}")


# ── Step 5 ────────────────────────────────────────────────────────────────────

async def step5_complete_observatory(client: JubClient, task_id: str) -> None:
    """
    POST /api/v2/tasks/{task_id}/complete

    Marks the setup task as successful. This is the signal that enables the
    observatory: after this call it becomes visible and searchable in the UI.

    Pass success=False and a message if the provisioning failed, which will
    leave the observatory disabled.
    """
    print("\n[Step 5] Completing observatory setup...")

    result = await client.complete_task(task_id, DTO.TaskCompleteDTO(
        success = True,
        message = "Initial provisioning complete. All catalogs and products indexed.",
    ))

    if result.is_err:
        raise RuntimeError(f"complete_task failed: {result.unwrap_err()}")

    done = result.unwrap()
    print(f"  Task status        : {done.status}")
    print(f"  Observatory active : {done.observatory_enabled}")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    result = await JubClientBuilder(
        api_url  = os.environ.get("JUB_API_URL",  "http://localhost:5000"),
        username = os.environ.get("JUB_USERNAME", "invitado"),
        password = os.environ.get("JUB_PASSWORD", "invitado"),
    ).build()
    if result.is_err:
        print(f"Error creating client: {result.unwrap_err()}")
        raise result.unwrap_err()

    client: JubClient = result.unwrap()
    print(f"Connected  user_id={client.user_id}")

    obs_id, task_id = await step1_setup_observatory(client)
    catalog_ids     = await step2_bulk_assign_catalogs(client, obs_id)
    product_ids     = await step3_bulk_assign_products(client, obs_id, catalog_ids)
    await step4_upload_product_files(client, product_ids)
    await step5_complete_observatory(client, task_id)

    print(f"\nObservatory {obs_id!r} is now live.")


if __name__ == "__main__":
    asyncio.run(main())
