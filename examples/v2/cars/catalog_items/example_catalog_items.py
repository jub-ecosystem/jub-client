"""
Catalog Items examples — JUB API v2.

Demonstrates all catalog-item operations using the Cars Observatory theme.
We add a new brand "Tesla" to the CAR_BRAND catalog as a standalone item,
then exercise hierarchy (parent/child), aliases, and catalog linking.

Covers: create_catalog_item, list_catalog_items, get_catalog_item,
        update_catalog_item, delete_catalog_item,
        add_catalog_item_alias, list_catalog_item_aliases, delete_catalog_item_alias,
        link_catalog_item_child, list_catalog_item_children, unlink_catalog_item_child,
        link_item_to_catalog, list_catalogs_for_item, unlink_item_from_catalog,
        list_products_for_item.

Run:
    python examples/v2/cars/catalog_items/example_catalog_items.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result

# Replace these IDs with real values from your database.
# Run example_catalogs.py first and copy the returned catalog_id for CAR_BRAND.
CAR_BRAND_CATALOG_ID = os.environ.get("CAR_BRAND_CATALOG_ID")
MOTOR_TYPE_CATALOG_ID = os.environ.get("MOTOR_TYPE_CATALOG_ID")


async def main():
    client = await get_client()

    # --- 1. Add "Tesla" as a new standalone brand item -----------------
    create_result = await client.create_catalog_item(
        DTO.CatalogItemStandaloneCreateDTO(
            catalog_id  = CAR_BRAND_CATALOG_ID,
            name        = "Tesla",
            value       = "TESLA",
            code        = 6,
            value_type  = "STRING",
            description = "American electric vehicle manufacturer.",
        )
    )
    print_result("create_catalog_item / Tesla", create_result)

    if create_result.is_err:
        return

    tesla_id = create_result.unwrap().catalog_item_id

    # --- 2. List all catalog items (first 50) --------------------------
    list_result = await client.list_catalog_items(limit=50)
    print_result("list_catalog_items", list_result)

    # --- 3. Fetch the Tesla item by ID ---------------------------------
    get_result = await client.get_catalog_item(tesla_id)
    print_result("get_catalog_item / Tesla", get_result)

    # --- 4. Update the Tesla item description --------------------------
    update_result = await client.update_catalog_item(
        tesla_id,
        DTO.CatalogItemUpdateDTO(description="Founded 2003, known for Model S, 3, X, Y."),
    )
    print_result("update_catalog_item / Tesla", update_result)

    # --- 5. Add an alias so "TSLA" also resolves to Tesla --------------
    alias_result = await client.add_catalog_item_alias(
        tesla_id,
        DTO.CatalogItemAliasCreateDTO(
            value="TSLA",
            value_type="STRING",
            description="Stock ticker alias for Tesla.",
        ),
    )
    print_result("add_catalog_item_alias / TSLA", alias_result)

    # --- 6. List aliases for the Tesla item ----------------------------
    aliases_result = await client.list_catalog_item_aliases(tesla_id)
    print_result("list_catalog_item_aliases / Tesla", aliases_result)

    # --- 7. Remove the alias -------------------------------------------
    if alias_result.is_ok:
        alias_id = alias_result.unwrap().catalog_item_alias_id
        del_alias_result = await client.delete_catalog_item_alias(tesla_id, alias_id)
        print_result("delete_catalog_item_alias / TSLA", del_alias_result)

    # --- 8. Create a child item: "Tesla Model S" under Tesla -----------
    child_result = await client.create_catalog_item(
        DTO.CatalogItemStandaloneCreateDTO(
            catalog_id     = CAR_BRAND_CATALOG_ID,
            name           = "Tesla Model S",
            value          = "TESLA_MODEL_S",
            code           = 61,
            value_type     = "STRING",
            description    = "Tesla's flagship sedan.",
            parent_item_id = tesla_id,
        )
    )
    print_result("create_catalog_item / Tesla Model S (child)", child_result)

    # --- 9. Link the child explicitly (alternative to parent_item_id) --
    if child_result.is_ok:
        model_s_id = child_result.unwrap().catalog_item_id
        link_child_result = await client.link_catalog_item_child(
            tesla_id,
            DTO.CatalogItemChildLinkCreateDTO(child_item_id=model_s_id),
        )
        print_result("link_catalog_item_child / Tesla → Model S", link_child_result)

        # --- 10. List children of Tesla --------------------------------
        children_result = await client.list_catalog_item_children(tesla_id)
        print_result("list_catalog_item_children / Tesla", children_result)

        # --- 11. Remove the child link ---------------------------------
        unlink_child_result = await client.unlink_catalog_item_child(tesla_id, model_s_id)
        print_result("unlink_catalog_item_child / Tesla → Model S", unlink_child_result)

    # --- 12. Link Tesla to a second catalog (MOTOR_TYPE) ---------------
    link_cat_result = await client.link_item_to_catalog(
        tesla_id,
        DTO.CatalogItemCatalogLinkCreateDTO(catalog_id=MOTOR_TYPE_CATALOG_ID),
    )
    print_result("link_item_to_catalog / Tesla → MOTOR_TYPE", link_cat_result)

    # --- 13. List catalogs that contain the Tesla item -----------------
    cats_for_item = await client.list_catalogs_for_item(tesla_id)
    print_result("list_catalogs_for_item / Tesla", cats_for_item)

    # --- 14. Remove Tesla from MOTOR_TYPE catalog ----------------------
    unlink_cat_result = await client.unlink_item_from_catalog(tesla_id, MOTOR_TYPE_CATALOG_ID)
    print_result("unlink_item_from_catalog / Tesla → MOTOR_TYPE", unlink_cat_result)

    # --- 15. List products tagged with this item -----------------------
    products_result = await client.list_products_for_item(tesla_id)
    print_result("list_products_for_item / Tesla", products_result)

    # --- 16. Delete the Tesla item (cleanup) ---------------------------
    delete_result = await client.delete_catalog_item(tesla_id)
    print_result("delete_catalog_item / Tesla", delete_result)


if __name__ == "__main__":
    asyncio.run(main())
