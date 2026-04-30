# jub-client

[![TestPyPI](https://img.shields.io/badge/TestPyPI-0.1.0a2-blue?logo=pypi&logoColor=white)](https://test.pypi.org/project/jub/0.1.0a2/)
[![Status](https://img.shields.io/badge/status-alpha-orange)](https://test.pypi.org/project/jub/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-run%20tests-lightgrey)](#running-tests)

Official async Python client for the **JUB API v2** — part of the MADTEC-2025-M-478 project.

jub-client gives you a fully-typed, async Python interface to the JUB national data hub. It organises information into **Observatories**, **Catalogs**, and **Products** following the STORI model (Spatial, Temporal, Observable, Reference, Interest).

---

## Table of contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [Core concepts](#core-concepts)
  - [STORI model](#stori-model)
  - [Result type](#result-type)
  - [Authentication](#authentication)
- [API overview](#api-overview)
- [JUB query language](#jub-query-language)
- [Environment variables](#environment-variables)
- [Development setup](#development-setup)
- [Running tests](#running-tests)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

> **Alpha release** — `jub` is currently published on [TestPyPI](https://test.pypi.org/project/jub/). Use the commands below until it reaches a stable release on PyPI.

### From TestPyPI (recommended for users)

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ jub==0.1.0a2
```

The `--extra-index-url` flag lets pip resolve standard dependencies (e.g. `pydantic`, `httpx`) from PyPI while pulling `jub` itself from TestPyPI.

### From source (recommended for contributors)

**Prerequisites:** Python 3.10+, [Poetry](https://python-poetry.org/)

```bash
git clone https://github.com/jub-ecosystem/jub-client
cd jub-client
poetry install
poetry self add poetry-plugin-shell
poetry shell
```

Deploy the required services (JUB API + MongoDB) before running any code:

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## Quick start

```python
import asyncio
import jub.dto.v2 as DTO
from jub.client.v2 import JubClient

async def main():
    # Connect and authenticate
    client = JubClient(
        api_url  = "http://localhost:5000",
        username = "admin",
        password = "secret",
    )
    await client.authenticate()

    # Create a catalog
    result = await client.create_catalog(DTO.CatalogCreateDTO(
        name         = "Geographic Dimension",
        value        = "SPATIAL_MX",
        catalog_type = "SPATIAL",
        items=[
            DTO.CatalogItemCreateDTO(
                name="Mexico", value="MX", code=0, value_type="STRING",
            ),
        ],
    ))
    catalog_id = result.unwrap().catalog_id
    print("Catalog created:", catalog_id)

    # Create an observatory
    obs = (await client.create_observatory(DTO.ObservatoryCreateDTO(
        title       = "Cancer Epidemiology — Mexico 2024",
        description = "National cancer surveillance data.",
    ))).unwrap()
    print("Observatory created:", obs.observatory_id)

asyncio.run(main())
```

**Using `JubClientBuilder`** — authenticates on construction and returns `Err` immediately if it fails:

```python
from jub.client.v2 import JubClientBuilder
import os

result = await JubClientBuilder(
    api_url  = os.environ.get("JUB_API_URL",  "http://localhost:5000"),
    username = os.environ.get("JUB_USERNAME", "admin"),
    password = os.environ.get("JUB_PASSWORD", "secret"),
).build()

client = result.unwrap()
```

---

## Core concepts

### STORI model

Data in JUB is indexed along five dimensions:

| Prefix | Dimension | Description |
|--------|-----------|-------------|
| `VS` | Spatial | Geographic scope (country, state, region) |
| `VT` | Temporal | Time range (year, date, period) |
| `VO` | Observable | Numeric aggregation target (COUNT, AVG, SUM) |
| — | Reference | Metadata and structural context |
| `VI` | Interest | Categorical filters (diagnoses, demographics, etc.) |

### Result type

Every client method returns `Result[T, Exception]` from the [`option`](https://pypi.org/project/option/) library. The client **never raises** — callers always check `.is_ok` or `.is_err`.

```python
result = await client.list_catalogs()

if result.is_ok:
    catalogs = result.unwrap()        # List[CatalogSummaryDTO]
else:
    error = result.unwrap_err()       # Exception
    print("Error:", error)
```

### Authentication

Call `authenticate()` once — the JWT is stored in memory and attached to every subsequent request via the `Authorization: Bearer` header.

```python
client = JubClient("http://localhost:5000", "admin", "secret")
await client.authenticate()
# All subsequent calls are authenticated automatically
```

---

## API overview

All methods are `async`. The base URL is `{api_url}/api/v2`.

### Users — `/users`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `authenticate()` | `POST /users/auth` | Log in and store JWT |
| `signup(dto)` | `POST /users/signup` | Create a new user account |
| `get_current_user()` | `GET /users/me` | Get the authenticated user's profile |
| `get_user_settings(user_id)` | `GET /users/{id}/settings` | Get user preferences |
| `update_user_settings(user_id, prefs)` | `PUT /users/{id}/settings` | Replace user preferences |

### Catalogs — `/catalogs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `create_catalog(dto)` | `POST /catalogs` | Create a catalog with nested items and hierarchy |
| `create_catalog_from_json(...)` | `POST /catalogs` | Create a catalog from a file, JSON string, or dict |
| `create_bulk_catalogs_from_json(...)` | `POST /catalogs/bulk` | Create multiple catalogs at once |
| `list_catalogs()` | `GET /catalogs` | List all catalogs (summary) |
| `get_catalog(catalog_id)` | `GET /catalogs/{id}` | Get a full catalog with items and aliases |

### Catalog items — `/catalog-items`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `create_catalog_item(dto)` | `POST /catalog-items` | Create a standalone item in an existing catalog |
| `list_catalog_items(limit)` | `GET /catalog-items` | List catalog items (paginated) |
| `get_catalog_item(id)` | `GET /catalog-items/{id}` | Get a single item |
| `update_catalog_item(id, dto)` | `PUT /catalog-items/{id}` | Update mutable fields |
| `delete_catalog_item(id)` | `DELETE /catalog-items/{id}` | Delete item and its relationships |
| `list_catalog_item_aliases(id)` | `GET /catalog-items/{id}/aliases` | List aliases |
| `add_catalog_item_alias(id, dto)` | `POST /catalog-items/{id}/aliases` | Add an alias |
| `delete_catalog_item_alias(id, alias_id)` | `DELETE /catalog-items/{id}/aliases/{alias_id}` | Remove an alias |
| `list_catalog_item_children(id)` | `GET /catalog-items/{id}/children` | List child items |
| `link_catalog_item_child(id, dto)` | `POST /catalog-items/{id}/children` | Link a child item |
| `unlink_catalog_item_child(id, child_id)` | `DELETE /catalog-items/{id}/children/{child_id}` | Unlink a child |
| `list_catalogs_for_item(id)` | `GET /catalog-items/{id}/catalogs` | List catalogs containing this item |
| `link_item_to_catalog(id, dto)` | `POST /catalog-items/{id}/catalogs` | Link item to a catalog |
| `unlink_item_from_catalog(id, catalog_id)` | `DELETE /catalog-items/{id}/catalogs/{catalog_id}` | Unlink from catalog |
| `list_products_for_item(id)` | `GET /catalog-items/{id}/products` | List product IDs tagged with this item |

### Observatories — `/observatories`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `create_observatory(dto)` | `POST /observatories` | Create an immediately-enabled observatory |
| `setup_observatory(dto)` | `POST /observatories/setup` | Create a disabled observatory and queue a setup task |
| `list_observatories(page_index, limit)` | `GET /observatories` | List observatories (paginated) |
| `get_observatory(id)` | `GET /observatories/{id}` | Get a single observatory |
| `update_observatory(id, dto)` | `PUT /observatories/{id}` | Update mutable fields |
| `delete_observatory(id)` | `DELETE /observatories/{id}` | Delete observatory and relationships |
| `link_catalog_to_observatory(id, dto)` | `POST /observatories/{id}/catalogs` | Link an existing catalog |
| `list_observatory_catalogs(id)` | `GET /observatories/{id}/catalogs` | List linked catalogs |
| `unlink_catalog_from_observatory(id, cid)` | `DELETE /observatories/{id}/catalogs/{cid}` | Unlink a catalog |
| `bulk_assign_catalogs(id, dto)` | `POST /observatories/{id}/catalogs/bulk` | Create and link multiple catalogs |
| `list_observatory_products(id)` | `GET /observatories/{id}/products` | List linked products |
| `link_product_to_observatory(id, dto)` | `POST /observatories/{id}/products` | Link an existing product |
| `unlink_product_from_observatory(id, pid)` | `DELETE /observatories/{id}/products/{pid}` | Unlink a product |
| `bulk_assign_products(id, dto)` | `POST /observatories/{id}/products/bulk` | Create and link multiple products |

### Products — `/products`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `create_product(dto)` | `POST /products` | Create a product linked to an observatory |
| `list_products(limit)` | `GET /products` | List products (paginated) |
| `get_product(id)` | `GET /products/{id}` | Get a single product |
| `update_product(id, dto)` | `PUT /products/{id}` | Update mutable fields |
| `delete_product(id)` | `DELETE /products/{id}` | Delete product and relationships |
| `get_product_tags(id)` | `GET /products/{id}/tags` | Get associated catalog item IDs |
| `add_product_tags(id, dto)` | `POST /products/{id}/tags` | Associate catalog items with a product |
| `remove_product_tag(id, catalog_item_id)` | `DELETE /products/{id}/tags/{cid}` | Remove a tag |
| `get_product_tag_details(id)` | `GET /products/{id}/tags/details` | Get full catalog items for each tag |
| `upload_product(id, file_path)` | `POST /products/{id}/upload` | Queue a file for background ingestion |
| `download_product(id)` | `GET /products/{id}/download` | Download the product file as bytes |

### Data sources — `/datasources`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `register_data_source(dto)` | `POST /datasources` | Register a data source |
| `register_data_source_from_json(...)` | `POST /datasources` | Register from a file, JSON string, or dict |
| `list_data_sources()` | `GET /datasources` | List all data sources |
| `get_data_source(id)` | `GET /datasources/{id}` | Get a single data source |
| `delete_data_source(id)` | `DELETE /datasources/{id}` | Delete source and all its records |
| `ingest_records(source_id, records)` | `POST /datasources/{id}/records` | Ingest a batch of records |
| `ingest_records_from_json(source_id, ...)` | `POST /datasources/{id}/records` | Ingest records from a file, JSON string, or dict |
| `query_records(source_id, dto)` | `POST /datasources/{id}/query` | Query records with the JUB DSL |

### Search — `/search`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `search(dto)` | `POST /search` | DSL search returning hydrated products |
| `search_records(dto)` | `POST /search/records` | DSL query returning raw data records |
| `generate_plot(dto)` | `POST /search/plot` | DSL aggregation returning ECharts JSON |
| `search_observatories(dto)` | `POST /search/observatories` | DSL search scoped to observatories |
| `search_services(dto)` | `POST /search/services` | DSL search scoped to services |

### Tasks — `/tasks`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_task_stats()` | `GET /tasks/stats` | Task counts by status |
| `list_my_tasks(limit)` | `GET /tasks` | Recent tasks for the authenticated user |
| `get_task(task_id)` | `GET /tasks/{id}` | Details of a single task |
| `complete_task(task_id, dto)` | `POST /tasks/{id}/complete` | Mark a task done (enables its observatory) |
| `retry_task(task_id)` | `PUT /tasks/{id}/retry` | Retry a failed task |

### YAML seed — `/code`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `create_from_code(file_path, yaml_string)` | `POST /code` | Upload a YAML file to seed catalogs, observatories, and products |

### Notifications — `/notifications`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `list_notifications(unread_only, limit)` | `GET /notifications` | List the current user's notifications |
| `mark_notification_read(id)` | `PUT /notifications/{id}/read` | Mark a notification as read |
| `mark_all_notifications_read()` | `PUT /notifications/read-all` | Mark all notifications as read |
| `clear_read_notifications()` | `DELETE /notifications/clear-read` | Delete all read notifications |

### Building blocks, Patterns, Stages, Workflows, Services

| Group | Methods | Endpoint prefix |
|-------|---------|-----------------|
| Building blocks | `create`, `list`, `get`, `update`, `delete` | `/building-blocks` |
| Patterns | `create`, `list`, `get`, `update`, `delete` | `/patterns` |
| Stages | `create`, `list`, `get`, `update`, `delete` | `/stages` |
| Workflows | `create`, `list`, `get`, `update`, `delete` | `/workflows` |
| Services | `create`, `index`, `list`, `get`, `update`, `delete` | `/services` |

`index_service()` is a one-shot endpoint that creates a full **Service → Workflow → Stages → Patterns → Building Blocks** tree in a single request.

---

## JUB query language

The JUB DSL is used in `search`, `search_records`, `query_records`, `generate_plot`, `search_observatories`, and `search_services`.

Variables are prefixed by dimension:

```
jub.v1.VS(MX).VT(>= 2020).VI(C_MAMA AND SEX_FEMALE)
```

| Prefix | Dimension | Example |
|--------|-----------|---------|
| `VS(…)` | Spatial | `VS(MX)` — scope to Mexico |
| `VT(…)` | Temporal | `VT(>= 2020)` — from 2020 onward |
| `VI(…)` | Interest | `VI(C_MAMA OR C_CERVIX)` — categorical filter |
| `VO(…)` | Observable | `VO(AVG(TASA_100K))` — numeric aggregation |
| `BY(…)` | Group by | `BY(CIE10_CANCER)` — aggregation dimension |
| `SVC(…)` | Service | `SVC(name=cancer,public=true)` — service search |

**Examples:**

```python
# Search products — breast or ovarian cancer in Mexico since 2020
await client.search(DTO.SearchQueryDTO(
    query = "jub.v1.VS(MX).VT(>= 2020).VI(C_MAMA OR C_OVARIO)",
))

# Generate a bar chart of average cancer rates by diagnosis group
await client.generate_plot(DTO.PlotQueryDTO(
    query      = "jub.v1.VS(MX).VI(C_MAMA OR C_OVARIO).VO(AVG(TASA_100K)).BY(CIE10_CANCER)",
    chart_type = "bar",
))

# Search public services containing "cancer"
await client.search_services(DTO.ServiceQueryDTO(
    query = "jub.v1.SVC(name=cancer,public=true)",
))
```

---

## Observatory provisioning workflow

`setup_observatory()` follows a two-step provisioning pattern that keeps the observatory hidden from users until all content is indexed:

```
1. setup_observatory(dto)   →  disabled observatory created, task_id returned
2. bulk_assign_catalogs(…)  →  catalogs created and linked
3. bulk_assign_products(…)  →  products created and linked
4. upload_product(…)        →  files queued for ingestion
5. complete_task(task_id)   →  observatory enabled and made visible
```

```python
# Step 1
setup = (await client.setup_observatory(DTO.ObservatorySetupDTO(
    observatory_id = "obs_cancer_mx_2024",
    title          = "Cancer Epidemiology — Mexico 2024",
))).unwrap()

# ... index content ...

# Step 5 — enable the observatory
await client.complete_task(setup.task_id, DTO.TaskCompleteDTO(success=True))
```

Use `create_observatory()` for immediate creation without background processing.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JUB_API_URL` | `http://localhost:5000` | Base URL of the JUB API |
| `JUB_USERNAME` | — | Login username |
| `JUB_PASSWORD` | — | Login password |
| `JUB_CLIENT_LOG_PATH` | `/log` | Directory for JSON log files |
| `JUB_CLIENT_OBSERVATORY_ID_SIZE` | `12` | Length of generated observatory IDs |

Copy `.env.dev` to `.env` and fill in your values before running.

---

## Development setup

```bash
# Clone
git clone https://github.com/jub-ecosystem/jub-client
cd jub-client

# Install dependencies
poetry install

# Activate virtual environment
poetry self add poetry-plugin-shell
poetry shell

# Deploy the API and database
chmod +x deploy.sh
./deploy.sh
```

The API lives in a sibling repository at `~/Programming/Python/jub_api`.

---

## Running tests

```bash
coverage run -m pytest tests/
coverage report
```

Make sure the JUB API is running before executing the test suite.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a pull request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards, license header requirements, and the development workflow before sending a PR.

---

## License

Distributed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

---

## Contact

Ignacio Castillo — [@nachocodexx](https://github.com/nachocodexx) — jesus.castillo.b@cinvestav.mx
