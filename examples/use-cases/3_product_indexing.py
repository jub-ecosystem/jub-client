"""
Use Case 3 — Product Indexing

Adds products in bulk to an existing observatory, uploads a chart or report
file for each product, and optionally adds extra catalog item tags.

Use this pattern when your catalogs are already in place and you only need
to add or update products — for example when a new report becomes available
or when an existing product needs a new file attached.

Run:
    python 3_product_indexing.py

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


# Target observatory — must already exist
OBSERVATORY_ID = os.environ.get("OBSERVATORY_ID", "obs_cancer_mx_2024")

# Catalog item IDs to tag the products with.
# Replace these with real IDs from your observatory's catalogs.
# You can retrieve them with client.get_catalog(catalog_id).
CATALOG_ITEM_IDS: list[str] = [
    # Example placeholders — fill in with actual catalog_item_id values
    # "<item_id:C_MAMA>",
    # "<item_id:C_CERVIX>",
    # "<item_id:MUJER>",
    # "<item_id:Y2022>",
]

# Chart/report files to upload (product_id → file path on disk)
CHART_FILES: dict[str, str] = {
    "prod_cancer_sex_age_2022":     "/source/radar.html",
    "prod_cancer_geography_2022":   "/source/heatmap.html",
    "prod_cancer_cie10_breakdown":  "/source/cie10_breakdown.html",
    # "prod_cancer_sex_age_2022":     "charts/sex_age_2022.html",
    # "prod_cancer_geography_2022":   "charts/geography_2022.html",
    # "prod_cancer_cie10_breakdown":  "charts/cie10_breakdown.html",
}


# ── Create products ───────────────────────────────────────────────────────────

async def bulk_create_products(
    client: JubClient,
    obs_id: str,
    item_ids: list[str],
) -> list[str]:
    """
    POST /api/v2/observatories/{obs_id}/products/bulk

    Creates multiple products in one request and links them to the observatory.
    Each product is tagged with the provided catalog item IDs.
    Returns the list of created product IDs.
    """
    print("\nCreating products in bulk...")

    result = await client.bulk_assign_products(obs_id, DTO.BulkProductsDTO(
        products=[
            DTO.BulkProductItemDTO(
                product_id       = "prod_cancer_sex_age_2022",
                name             = "Cancer by Sex and Age Group — 2022",
                description      = "Distribution of cancer cases by biological sex and five-year age cohort for 2022.",
                catalog_item_ids = item_ids,
            ),
            DTO.BulkProductItemDTO(
                product_id       = "prod_cancer_geography_2022",
                name             = "Cancer Geographic Distribution — 2022",
                description      = "State-level incidence and mortality rates for 2022.",
                catalog_item_ids = item_ids,
            ),
            DTO.BulkProductItemDTO(
                product_id       = "prod_cancer_cie10_breakdown",
                name             = "Cancer Breakdown by CIE-10 Group",
                description      = "Relative frequency of each cancer type across the full reporting period.",
                catalog_item_ids = item_ids,
            ),
        ]
    ))

    if result.is_err:
        raise RuntimeError(f"bulk_assign_products failed: {result.unwrap_err()}")

    product_ids = [p.product_id for p in result.unwrap().products]
    print(f"  Products created: {product_ids}")
    return product_ids


# ── Add extra tags ────────────────────────────────────────────────────────────

async def add_extra_tags(
    client: JubClient,
    product_id: str,
    extra_item_ids: list[str],
) -> None:
    """
    POST /api/v2/products/{product_id}/tags

    Adds more catalog item tags to a product after it has been created.
    Useful when the full set of tags is not known at creation time.
    """
    if not extra_item_ids:
        return

    result = await client.add_product_tags(
        product_id,
        DTO.TagProductDTO(catalog_item_ids=extra_item_ids),
    )
    if result.is_err:
        print(f"  Failed to add tags to {product_id}: {result.unwrap_err()}")
    else:
        tags = result.unwrap()
        print(f"  Tags on {product_id}: {tags.catalog_item_ids}")


# ── Upload chart files ────────────────────────────────────────────────────────

async def upload_chart_files(
    client: JubClient,
    product_ids: list[str],
) -> None:
    """
    POST /api/v2/products/{product_id}/upload

    Uploads an HTML chart or static report file and attaches it to the product.
    The file is processed by a background job; job_id is returned immediately.

    Supported file types: HTML, PDF, PNG, and any format your API instance
    is configured to handle.
    """
    print("\nUploading chart files...")

    for product_id in product_ids:
        file_path = CHART_FILES.get(product_id)
        if not file_path:
            print(f"  No chart configured for {product_id}")
            continue
        if not os.path.exists(file_path):
            print(f"  Skipping {product_id}: file not found at {file_path!r}")
            continue

        result = await client.upload_product(product_id, file_path)
        if result.is_err:
            print(f"  Upload failed for {product_id}: {result.unwrap_err()}")
            continue

        upload = result.unwrap()
        print(f"  {product_id} → job_id={upload.job_id}  status={upload.status}")

        # Optional: poll until the job finishes
        # import asyncio
        # while True:
        #     task = (await client.get_task(upload.job_id)).unwrap()
        #     if task.current_status in ("SUCCESS", "FAILED"):
        #         print(f"  Job {upload.job_id}: {task.current_status}")
        #         break
        #     await asyncio.sleep(2)


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    result = await JubClientBuilder(
        api_url  = os.environ.get("JUB_API_URL",  "http://localhost:5000"),
        username = os.environ.get("JUB_USERNAME", "invitado"),
        password = os.environ.get("JUB_PASSWORD", "invitado"),
    ).build()
    if result.is_err:
        raise result.unwrap_err()

    client: JubClient = result.unwrap()
    print(f"Connected  user_id={client.user_id}")

    # If CATALOG_ITEM_IDS is empty, try to retrieve them from the observatory's catalogs
    item_ids = CATALOG_ITEM_IDS
    if not item_ids:
        print("\nNo CATALOG_ITEM_IDS configured — fetching from observatory catalogs...")
        catalogs = (await client.list_observatory_catalogs(OBSERVATORY_ID)).unwrap()
        for cat_summary in catalogs:
            cat = (await client.get_catalog(cat_summary.catalog_id)).unwrap()
            item_ids.extend(item.catalog_item_id for item in cat.items[:2])
        print(f"  Using {len(item_ids)} item ID(s) from the observatory")

    product_ids = await bulk_create_products(client, OBSERVATORY_ID, item_ids)

    # Add a few extra tags to the first product as an example
    if product_ids and item_ids:
        await add_extra_tags(client, product_ids[0], item_ids[:1])

    await upload_chart_files(client, product_ids)

    print(f"\nDone. {len(product_ids)} product(s) indexed in {OBSERVATORY_ID!r}.")


if __name__ == "__main__":
    asyncio.run(main())
