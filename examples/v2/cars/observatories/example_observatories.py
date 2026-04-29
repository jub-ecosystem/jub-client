"""
Observatories examples — JUB API v2.

The "World Automotive Manufacturing Observatory" is the top-level container
that groups catalogs (SPATIAL, TEMPORAL, INTEREST) and products (datasets)
for car production data.

Two creation patterns are shown:
  - create_observatory  → immediate, enabled on return.
  - setup_observatory   → disabled, enabled only after complete_task() succeeds.

Covers: create_observatory, setup_observatory, list_observatories,
        get_observatory, update_observatory, delete_observatory,
        link_catalog_to_observatory, list_observatory_catalogs,
        unlink_catalog_from_observatory, bulk_assign_catalogs,
        list_observatory_products, link_product_to_observatory,
        unlink_product_from_observatory, bulk_assign_products.

Run:
    python examples/v2/cars/observatories/example_observatories.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result

# Replace with real catalog/product IDs from previous examples.
SPATIAL_CATALOG_ID  = os.environ.get("SPATIAL_CATALOG_ID")
TEMPORAL_CATALOG_ID = os.environ.get("TEMPORAL_CATALOG_ID")
BRAND_CATALOG_ID    = os.environ.get("CAR_BRAND_CATALOG_ID")
MOTOR_CATALOG_ID    = os.environ.get("CAR_MOTOR_CATALOG_ID")
COLOR_CATALOG_ID    = os.environ.get("CAR_COLOR_CATALOG_ID")
PRODUCT_ID          = os.environ.get("PRODUCT_ID")


async def main():
    client = await get_client()

    # --- 1. Create an observatory (immediate, enabled) -----------------
    create_result = await client.create_observatory(
        DTO.ObservatoryCreateDTO(
            observatory_id="world-automotive-manufacturing-observatory",  # Optional: specify your own observatory ID or let the system generate a random UUID.
            title="World Automotive Manufacturing Observatory",
            description=(
                "Tracks car production across countries (SPATIAL), "
                "model years (TEMPORAL), and vehicle attributes (INTEREST)."
            ),
            image_url="https://www.supplychainbrain.com/ext/resources/2023/05/25/CAR-MANUFACTURING-iStock--Traimak_Ivan--1069360792.webp?t=1685036316&width=800",
        )
    )
    print_result("create_observatory", create_result)

    if create_result.is_err:
        return

    obs_id = create_result.unwrap().observatory_id

    # --- 2. Create a second observatory using the two-step setup flow --
    # This observatory starts disabled; an external indexer enables it
    # via complete_task() (see tasks example).
    setup_result = await client.setup_observatory(
        DTO.ObservatorySetupDTO(
            title="Latin America Cars Observatory",
            description="Focused on Mexico and nearby markets.",
            metadata={"region": "LATAM", "owner": "team-cars"},
        )
    )
    print_result("setup_observatory", setup_result)

    # --- 3. List observatories (first page) ----------------------------
    list_result = await client.list_observatories(page_index=0, limit=10)
    print_result("list_observatories", list_result)

    # --- 4. Fetch the observatory by ID --------------------------------
    get_result = await client.get_observatory(obs_id)
    print_result("get_observatory", get_result)

    # --- 5. Update the observatory title and description ---------------
    update_result = await client.update_observatory(
        obs_id,
        DTO.ObservatoryUpdateDTO(
            title="Global Automotive Manufacturing Observatory",
            description="Updated: includes electric vehicles from 2020 onward.",
        ),
    )
    print_result("update_observatory", update_result)

    # --- 6. Link the SPATIAL catalog to the observatory ----------------
    link_spatial = await client.link_catalog_to_observatory(
        obs_id,
        DTO.LinkCatalogDTO(catalog_id=SPATIAL_CATALOG_ID, level=0),
    )
    print_result("link_catalog_to_observatory / SPATIAL", link_spatial)

    # --- 7. Link the TEMPORAL catalog ----------------------------------
    link_temporal = await client.link_catalog_to_observatory(
        obs_id,
        DTO.LinkCatalogDTO(
            catalog_id=TEMPORAL_CATALOG_ID,
            level=1
        )
    )

    print_result("link_catalog_to_observatory / TEMPORAL", link_temporal)
    link_interest_1 = await client.link_catalog_to_observatory(
        obs_id,
        DTO.LinkCatalogDTO(catalog_id=BRAND_CATALOG_ID, level=2),
    )
    print_result("link_catalog_to_observatory / BRAND", link_interest_1)
    link_interest_2 = await client.link_catalog_to_observatory(
        obs_id,
        DTO.LinkCatalogDTO(catalog_id=COLOR_CATALOG_ID, level=3),
    )
    print_result("link_catalog_to_observatory / COLOR", link_interest_2)
    link_interest_3 = await client.link_catalog_to_observatory(
        obs_id,
        DTO.LinkCatalogDTO(catalog_id=MOTOR_CATALOG_ID, level=4),
    )
    print_result("link_catalog_to_observatory / MOTOR", link_interest_3)

    # --- 8. List all catalogs linked to the observatory ----------------
    obs_catalogs = await client.list_observatory_catalogs(obs_id)
    print_result("list_observatory_catalogs", obs_catalogs)

    # --- 9. Unlink the TEMPORAL catalog --------------------------------
    unlink_result = await client.unlink_catalog_from_observatory(obs_id, TEMPORAL_CATALOG_ID)
    print_result("unlink_catalog_from_observatory / TEMPORAL", unlink_result)
    link_temporal = await client.link_catalog_to_observatory(
        obs_id,
        DTO.LinkCatalogDTO(catalog_id=TEMPORAL_CATALOG_ID, level=1),
    )
    print_result("link_catalog_to_observatory / TEMPORAL", link_temporal)

    # --- 10. Bulk-create and link three interest catalogs at once ------
    # Uncomment and replace with real catalog IDs if you want to test this part.
    # bulk_catalogs_result = await client.bulk_assign_catalogs(
    #     obs_id,
    #     DTO.BulkCatalogsDTO(
    #         catalogs=[
    #             DTO.CatalogCreateDTO(
    #                 name="Production Year",
    #                 value="PRODUCTION_YEAR",
    #                 catalog_type="TEMPORAL",
    #                 description="Year the car was built.",
    #                 items=[
    #                     DTO.CatalogItemCreateDTO(name="2022", value="Y2022", code=2022, value_type="DATETIME", temporal_value="2022-01-01T00:00:00"),
    #                     DTO.CatalogItemCreateDTO(name="2023", value="Y2023", code=2023, value_type="DATETIME", temporal_value="2023-01-01T00:00:00"),
    #                     DTO.CatalogItemCreateDTO(name="2024", value="Y2024", code=2024, value_type="DATETIME", temporal_value="2024-01-01T00:00:00"),
    #                 ],
    #             ),
    #             DTO.CatalogCreateDTO(
    #                 name="Car Color",
    #                 value="CAR_COLOR",
    #                 catalog_type="INTEREST",
    #                 description="Exterior color.",
    #                 items=[
    #                     DTO.CatalogItemCreateDTO(name="Black",  value="BLACK",  code=3, value_type="STRING"),
    #                     DTO.CatalogItemCreateDTO(name="White",  value="WHITE",  code=4, value_type="STRING"),
    #                     DTO.CatalogItemCreateDTO(name="Silver", value="SILVER", code=5, value_type="STRING"),
    #                 ],
    #             ),
    #         ]
    #     ),
    # )
    # print_result("bulk_assign_catalogs", bulk_catalogs_result)

    # --- 11. Link an unexisting product to the observatory ---------------
    link_product = await client.link_product_to_observatory(
        obs_id,
        DTO.LinkProductDTO(product_id=PRODUCT_ID),
    )
    print_result("link_product_to_observatory", link_product)

    # --- 12. List all products linked to the observatory ---------------
    obs_products = await client.list_observatory_products(obs_id)
    print_result("list_observatory_products", obs_products)

    # --- 13. Unlink the product ----------------------------------------
    unlink_prod = await client.unlink_product_from_observatory(obs_id, PRODUCT_ID)
    print_result("unlink_product_from_observatory", unlink_prod)

    # --- 14. Bulk-create and link two new products at once -------------
    # Uncomment and replace with real product IDs if you want to test this part.
    # bulk_products_result = await client.bulk_assign_products(
    #     obs_id,
    #     DTO.BulkProductsDTO(
    #         products=[
    #             DTO.BulkProductItemDTO(
    #                 product_id="bwm-i4-2023",  # Optional pre-defined ID; if not provided, a random UUID is generated.
    #                 name="BMW i4 Production 2023",
    #                 description="Electric BMW sedans produced in Germany, 2023.",
    #             ),
    #             DTO.BulkProductItemDTO(
    #                 product_id="toyota-corolla-2022",
    #                 name="Toyota Corolla Production 2022",
    #                 description="Gasoline Toyota sedans produced in Japan, 2022.",
    #             ),
    #         ]
    #     ),
    # )
    # print_result("bulk_assign_products", bulk_products_result)
    # obs_products = await client.list_observatory_products(obs_id)
    # print_result("list_observatory_products", obs_products)

    # --- 15. Delete the observatory (cleanup) --------------------------
    DELETE_EXISTING = os.environ.get("DELETE_EXISTING_OBSERVATORY", "0") == "1"
    if not DELETE_EXISTING:
        print("Skipping observatory deletion (set DELETE_EXISTING_OBSERVATORY=1 to enable)")
        return
    delete_result = await client.delete_observatory(obs_id)
    print_result("delete_observatory", delete_result)


if __name__ == "__main__":
    asyncio.run(main())
