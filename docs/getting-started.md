# Getting Started

This guide walks you through authenticating with the API and performing the most common operations. All examples assume you have already installed the library (see [Installation](installation.md)) and the API is running (see [Deployment](deployment.md)).

---

## 1. Authenticate

Create a client instance and call `authenticate()`. The JWT is stored in memory and attached to every subsequent request automatically.

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
    if result.is_ok:
        print("Authenticated — user_id:", client.user_id)
    else:
        print("Auth failed:", result.unwrap_err())

asyncio.run(main())
```

!!! tip "Use JubClientBuilder for cleaner code"
    `JubClientBuilder` authenticates during `.build()` and returns `Err` immediately if authentication fails — no extra `if` block needed.

    ```python
    from jub.client.v2 import JubClientBuilder

    result = await JubClientBuilder(
        api_url="http://localhost:5000",
        username="admin",
        password="secret",
    ).build()

    client = result.unwrap()  # raises if auth failed
    ```

---

## 2. Handle results

Every method returns `Result[T, Exception]`. Check `.is_ok` before unwrapping:

```python
result = await client.list_catalogs()

if result.is_ok:
    catalogs = result.unwrap()        # List[CatalogSummaryDTO]
    for c in catalogs:
        print(c.catalog_id, c.name)
else:
    error = result.unwrap_err()       # Exception
    print("Error:", error)
```

---

## 3. Create a catalog

```python
import jub.dto.v2 as DTO

result = await client.create_catalog(DTO.CatalogCreateDTO(
    name         = "Geographic Dimension",
    value        = "SPATIAL_MX",
    catalog_type = "SPATIAL",
    description  = "Country → State hierarchy for Mexico",
    items=[
        DTO.CatalogItemCreateDTO(
            name       = "Mexico",
            value      = "MX",
            code       = 0,
            value_type = "STRING",
        ),
    ],
))

if result.is_ok:
    print("Catalog ID:", result.unwrap().catalog_id)
```

---

## 4. Create an observatory

```python
result = await client.create_observatory(DTO.ObservatoryCreateDTO(
    title       = "Cancer Epidemiology — Mexico 2024",
    description = "Mortality and incidence data for the 2018-2023 period.",
    image_url   = "https://example.com/obs.png",
))

if result.is_ok:
    obs = result.unwrap()
    print("Observatory ID:", obs.observatory_id)
```

---

## 5. Create and tag a product

```python
result = await client.create_product(DTO.ProductCreateDTO(
    name             = "Cancer Mortality by State",
    description      = "Age-standardised rates per 100k by federal entity.",
    observatory_id   = obs.observatory_id,
    catalog_item_ids = ["item_id_1", "item_id_2"],
))

product = result.unwrap()
print("Product ID:", product.product_id)
```

---

## 6. Search with the JUB DSL

```python
result = await client.search(DTO.SearchQueryDTO(
    query          = "jub.v1.VS(MX).VT(>= 2020).VI(C_MAMA)",
    observatory_id = obs.observatory_id,
    limit          = 10,
))

if result.is_ok:
    products = result.unwrap()
    print(f"Found {len(products)} products")
```

---

## Next steps

- Read the full [API Reference](api-reference.md) for every method and parameter.
- Explore complete runnable scripts in [Examples](usage_examples.md).
