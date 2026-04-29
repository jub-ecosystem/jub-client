"""
Products examples — JUB API v2.

A "product" in the Cars Observatory is a car-production dataset:
  e.g. "Toyota Corolla Production 2022" tagged with spatial (JP),
  temporal (Y2022), brand (TOYOTA), color (WHITE), motor (GASOLINE).

Covers: create_product, list_products, get_product, update_product,
        delete_product, get_product_tags, add_product_tags,
        remove_product_tag, get_product_tag_details,
        upload_product, download_product.

Run:
    python examples/v2/cars/products/example_products.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

import jub.dto.v2 as DTO
from examples.v2.cars.common import get_client, print_result

# Replace with real IDs from your database.
OBSERVATORY_ID = os.environ.get("OBSERVATORY_ID")

# Catalog item IDs for tagging (spatial=JP, temporal=Y2022, brand=TOYOTA, color=WHITE, motor=GASOLINE)
SPATIAL_ITEM_ID                = os.environ.get("SPATIAL_ITEM_ID")
TEMPORAL_ITEM_ID               = os.environ.get("TEMPORAL_ITEM_ID")
INTEREST_ITEM_BRAND_ID         = os.environ.get("INTEREST_ITEM_BRAND_ID")
INTEREST_ITEM_COLOR_ID         = os.environ.get("INTEREST_ITEM_COLOR_ID")
INTEREST_ITEM_GASOLINE_TYPE_ID = os.environ.get("INTEREST_ITEM_GASOLINE_TYPE_ID")
INTEREST_ITEM_COLOR_SILVER_ID = os.environ.get("INTEREST_ITEM_COLOR_SILVER_ID")  # replace with real ID
PRODUCT_FILE_PATH = os.environ.get("PRODUCT_FILE_PATH")  # replace with real file path
DELETE_EXISTING_PRODUCT = os.environ.get("DELETE_EXISTING_PRODUCT", "0") == "1"  # set to "1" to enable deletion of existing product
async def main():
    client = await get_client()
    products = [
        (DTO.ProductCreateDTO(
            catalog_item_ids=["y1998","ford", "blue", "gasoline", "united_states"],
            description="A classic American muscle car with a V8 engine, produced in the USA in 1998.",
            name="Mustang - Azul - Gasoline - 1998 - USA",
            observatory_id=OBSERVATORY_ID,
            product_id="mustang"
        ),"/source/mustang_blue.jpg"),
        (DTO.ProductCreateDTO(
            name = "Golf - Red - Gasoline - 2020 - Germany",
            description = "A popular compact car with a turbocharged engine, manufactured in Germany in 2020.",
            catalog_item_ids = ["y2020", "vw", "red", "gasoline", "germany"],
            observatory_id = OBSERVATORY_ID,
            product_id = "golf"
        ),"/source/golf_red.jpg"),
        (DTO.ProductCreateDTO(
            name = "Toyota Supra - Black - Gasoline - 1998 - Japan",
            description = "An iconic sports car with a twin-turbo inline-six engine, produced in Japan in 1998.",
            catalog_item_ids = ["y1998", "toyota", "black", "gasoline", "japan"],
            observatory_id = OBSERVATORY_ID,
            product_id = "supra"
        ),"/source/toyota.jpg")
    ]
    # --- 1. Create a product -------------------------------------------
    for product, image_path in products:
        create_result = await client.create_product(product)
        print_result(f"create_product / {product.name}", create_result)

        if create_result.is_err:
            return

        product_id = create_result.unwrap().product_id
        link_result = await client.link_product_to_observatory(product_id, OBSERVATORY_ID)
        print_result(f"link_product_to_observatory / {product.name}", link_result)
        upload_result = await client.upload_product(product_id, image_path)
        print_result(f"upload_product / {product.name}", upload_result)
        # Link
        # )
    # )
    # print_result("create_product / Toyota Corolla 2022", create_result)

    # if create_result.is_err:
        # return

    # product_id = create_result.unwrap().product_id

    # --- 2. Create a second product (BMW electric) ---------------------
    # bmw_result = await client.create_product(
    #     DTO.ProductCreateDTO(
    #         name="BMW i4 Production 2023",
    #         description="Electric BMW i4 units manufactured in Germany during 2023.",
    #         observatory_id=OBSERVATORY_ID,
    #     )
    # )
    # print_result("create_product / BMW i4 2023", bmw_result)

    # # --- 3. List products (first 50) ----------------------------------
    # list_result = await client.list_products(limit=50)
    # print_result("list_products", list_result)

    # # --- 4. Fetch the Toyota Corolla product ---------------------------
    # get_result = await client.get_product(product_id)
    # print_result("get_product / Toyota Corolla 2022", get_result)

    # # --- 5. Update the product description ----------------------------
    # update_result = await client.update_product(
    #     product_id,
    #     DTO.ProductUpdateDTO(
    #         description="Toyota Corolla (12th gen) units produced at Takaoka plant, Japan, 2022.",
    #     ),
    # )
    # print_result("update_product / Toyota Corolla 2022", update_result)

    # # --- 6. Read current tags -----------------------------------------
    # tags_result = await client.get_product_tags(product_id)
    # print_result("get_product_tags / Toyota Corolla 2022", tags_result)

    # # --- 7. Add extra tag: color=SILVER --------------------------------
    # add_tags_result = await client.add_product_tags(
    #     product_id,
    #     DTO.TagProductDTO(catalog_item_ids=[INTEREST_ITEM_COLOR_SILVER_ID]),
    # )
    # print_result("add_product_tags / +SILVER", add_tags_result)

    # # --- 8. Get full catalog-item objects for each tag -----------------
    # tag_details = await client.get_product_tag_details(product_id)
    # print_result("get_product_tag_details / Toyota Corolla 2022", tag_details)

    # # --- 9. Remove the SILVER tag -------------------------------------
    # remove_tag_result = await client.remove_product_tag(product_id, INTEREST_ITEM_COLOR_SILVER_ID)
    # print_result("remove_product_tag / -SILVER", remove_tag_result)

    # # --- 10. Upload a CSV file with raw production records ------------
    # # Create a small in-memory CSV payload for demonstration purposes.
    # csv_bytes = (
    #     b"vin,plant,year,color,motor\n"
    #     b"JT2BF22K820012345,Takaoka,2022,WHITE,GASOLINE\n"
    #     b"JT2BF22K820012346,Takaoka,2022,BLACK,GASOLINE\n"
    # )
    # upload_result = await client.upload_product(product_id, csv_bytes)
    # # upload_result = await client.upload_product(product_id, PRODUCT_FILE_PATH)
    # print_result("upload_product / Toyota Corolla 2022 CSV", upload_result)

    # # --- 11. Download the product file --------------------------------
    # download_result = await client.download_product(product_id)
    # if download_result.is_ok:
    #     data = download_result.unwrap()
    #     print(f"[OK]  download_product: received {len(data)} bytes")
    # else:
    #     print(f"[ERR] download_product: {download_result.unwrap_err()}")

    # # --- 12. Delete the product (cleanup) -----------------------------
    # if DELETE_EXISTING_PRODUCT:
    #     delete_result = await client.delete_product(product_id)
    #     print_result("delete_product / Toyota Corolla 2022", delete_result)


if __name__ == "__main__":
    asyncio.run(main())
