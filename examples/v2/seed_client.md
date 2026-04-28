# seed_client.py

Client-based seed script for the JUB API v2. Populates the platform with three
Mexican public health observatories, their associated catalogs, products, and
chart files — using the `JubClient` async Python wrapper instead of raw HTTP calls.

This is the recommended approach for Python integrators. It handles authentication,
JWT propagation, and error handling through the `Result` pattern automatically.

---

## What it creates

Three observatories, each with its own catalog dimensions and products:

| Observatory | Catalogs | Products |
|---|---|---|
| Observatorio de Mortalidad — Mexico | spatial, temporal, sex, age group, cause of death | 3 products (heatmap + 2 radar) |
| Observatorio de Cancer — Mexico | spatial, temporal, sex, age group, CIE-10 cancer | 3 products (1 radar + 1 heatmap + 1 radar) |
| Observatorio de Enfermedades Cronicas | spatial, temporal, sex, cause of death, derechohabiencia | 3 products (1 heatmap + 2 radar) |

Each catalog is fully populated with items and their aliases. Each product is
tagged with catalog item IDs and has an HTML chart file attached.

---

## Prerequisites

```sh
# Install the client dependencies
pip install poetry
poetry install
poetry shell

# The chart files must exist in the jub_api sibling project
ls ~/Programming/Python/jub_api/source/heatmap.html
ls ~/Programming/Python/jub_api/source/radar.html
```

---

## Usage

```sh
# Seed with default credentials (invitado / invitado)
python examples/v2/seed_client.py

# Point at a different API instance
python examples/v2/seed_client.py --api-url http://localhost:5000

# Use custom credentials
python examples/v2/seed_client.py --username admin --password secret

# Create the user first, then seed
python examples/v2/seed_client.py \
    --signup \
    --username newuser \
    --password mypassword \
    --email me@example.com \
    --first-name Ada \
    --last-name Lovelace

# Delete existing observatories before re-seeding (idempotent re-run)
python examples/v2/seed_client.py --clean
```

---

## How it works — step by step

The script follows the **two-phase observatory provisioning** pattern defined by
the JUB API. The same six steps repeat for each observatory:

### Step 1 — Setup observatory (`client.setup_observatory`)

Creates the observatory in a **disabled** state and queues a background
`PENDING` task. The observatory is not yet visible to public users.

The client automatically injects `user_id` from the authenticated session —
no manual header or payload manipulation needed.

```python
setup_resp = await client.setup_observatory(ObservatorySetupDTO(
    observatory_id = "obs_mortalidad_mx",
    title          = "Observatorio de Mortalidad — Mexico",
    ...
))
obs_id  = setup_resp.observatory_id
task_id = setup_resp.task_id
```

### Step 2 — Bulk-create catalogs (`client.bulk_assign_catalogs`)

Sends all catalog definitions for this observatory in a single request.
Each catalog type (SPATIAL, TEMPORAL, INTEREST) is built by a dedicated
`build_*_dto()` function that returns a dict matching `CatalogCreateDTO`.

```python
catalog_dtos = [CATALOG_BUILDERS[label]() for label in catalog_labels]
bulk_cats    = await client.bulk_assign_catalogs(obs_id, {"catalogs": catalog_dtos})
catalog_ids  = bulk_cats.catalog_ids
```

### Step 3 — Fetch catalogs to get item IDs (`client.get_catalog`)

The bulk endpoint returns only catalog IDs. To tag products (Step 4), we need
the individual `catalog_item_id` values. `get_catalog()` returns a
`CatalogResponseDTO` with a full nested item tree.

The SPATIAL catalog has a two-level hierarchy (Mexico → 32 states), so
`extract_item_ids()` walks the tree recursively to collect all IDs.

```python
cat_resp = await client.get_catalog(cat_id)
item_ids = extract_item_ids(cat_resp.items)   # flattens country -> state tree
```

### Step 4 — Bulk-create products (`client.bulk_assign_products`)

Creates all products for this observatory and links each one to the observatory
in a single request. Each product receives up to 5 item IDs per referenced
catalog dimension as tags, enabling DSL search and filtering.

```python
await client.bulk_assign_products(obs_id, {"products": [
    {
        "product_id":       "prod_mort_causa_estado",
        "name":             "Mortalidad por Causa y Estado",
        "catalog_item_ids": [...],   # from step 3
    },
    ...
]})
```

### Step 5 — Upload chart files (`client.upload_product`)

Associates an HTML chart with each product. Geographic products get a
`heatmap.html`; multi-dimensional products get `radar.html`.
`upload_product()` handles the multipart encoding internally.

```python
await client.upload_product(product_id, "/path/to/heatmap.html")
```

### Step 6 — Complete the task (`client.complete_task`)

Marks the setup task as `success=True`. The API flips the observatory's
`disabled` flag to `False`, making it publicly queryable. This is the
signal that provisioning is done.

```python
await client.complete_task(task_id, TaskCompleteDTO(
    success = True,
    message = "Observatory seeded via seed_client.py.",
))
```

---

## Error handling

Every `JubClient` method returns `Result[T, Exception]` from the `option` library.
The `_ok()` helper unwraps `Ok` values and calls `sys.exit(1)` on `Err`, keeping
the seed logic clean without nested `if/else` chains:

```python
def _ok(result, label):
    if result.is_err:
        print(f"  ERROR {label}: {result.unwrap_err()}")
        sys.exit(1)
    return result.unwrap()
```

In production code you would replace `sys.exit` with proper exception handling
or retry logic as needed.

---

## Differences from `seed_api.py`

| Aspect | `seed_api.py` (raw httpx) | `seed_client.py` (JubClient) |
|---|---|---|
| Auth | Manual `Authorization` header set on the httpx client | `client.authenticate()` stores the token; all methods send it automatically |
| `user_id` | Read from login response, passed explicitly | Injected by `client.setup_observatory()` from `client.user_id` |
| Error handling | `_check()` reads HTTP status codes | `_ok()` unwraps `Result[T, Exception]` |
| Response access | Raw `dict` with `.get(...)` | Typed DTOs with attribute access (`.observatory_id`, `.task_id`, …) |
| Item tree traversal | `extract_item_ids` walks `List[dict]` | `extract_item_ids` walks `List[CatalogItemResponseDTO]` |
| Base URL | Must include `/api/v2` | Must NOT include `/api/v2` — the client appends it |
