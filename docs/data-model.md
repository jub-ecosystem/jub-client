# Data Model

The JUB data model follows the **STORI** schema — data is organised along five dimensions:

| Dimension | Prefix | Description |
|---|---|---|
| **S**patial | `VS` | Geographic scope (country, state, region) |
| **T**emporal | `VT` | Time range (year, date, period) |
| **O**bservable | `VO` | Numeric aggregation target (COUNT, AVG, SUM) |
| **R**eference | — | Metadata and structural context |
| **I**nterest | `VI` | Categorical filters (diagnoses, demographics, etc.) |

---

## Core entities

### Observatory

An Observatory is the top-level container. It groups related Catalogs and Products into a logical analytical space.

```python
class Observatory(BaseModel):
    obid: str = ""
    title: str = "Observatory"
    image_url: str = ""
    description: str = ""
    disabled: bool = False
```

| Field | Type | Description |
|---|---|---|
| `obid` | `str` | Unique identifier |
| `title` | `str` | Display name |
| `image_url` | `str` | URL of a representative image |
| `description` | `str` | Textual description |
| `disabled` | `bool` | `True` when the observatory is inactive |

---

### Catalog

A Catalog is a controlled vocabulary — an ordered set of items used to classify and filter data.

```python
class Catalog(BaseModel):
    cid: str = ""
    display_name: str = ""
    kind: str = ""
```

| Field | Type | Description |
|---|---|---|
| `cid` | `str` | Unique identifier |
| `display_name` | `str` | Human-readable name (whitespace is normalised automatically) |
| `kind` | `str` | Catalog type: `SPATIAL`, `TEMPORAL`, `INTEREST` |

---

### Catalog Item

A Catalog Item is a single entry within a catalog. Items can be nested hierarchically (e.g. Country → State → Municipality).

```python
class CatalogItem(BaseModel):
    item_id: str
    value: str
    display_name: str
    code: int
    description: str
    metadata: Dict[str, str]
```

| Field | Type | Description |
|---|---|---|
| `item_id` | `str` | Unique identifier |
| `value` | `str` | Stored value used in queries (e.g. `MX`, `C_MAMA`) |
| `display_name` | `str` | Human-readable label |
| `code` | `int` | Numeric code for the item |
| `description` | `str` | Contextual description |
| `metadata` | `Dict[str, str]` | Arbitrary key-value metadata |

---

### Product

A Product represents a data view — a chart, table, or dataset linked to an Observatory and tagged with Catalog Items.

```python
class Product(BaseModel):
    pid: str = ""
    description: str = ""
    product_type: str = ""
    product_name: str = ""
    tags: List[str] = []
    url: str = ""
```

| Field | Type | Description |
|---|---|---|
| `pid` | `str` | Unique identifier |
| `description` | `str` | Textual description |
| `product_type` | `str` | Category (e.g. `MAP`, `CHART`, `TABLE`) |
| `product_name` | `str` | Display name |
| `tags` | `List[str]` | Catalog item IDs used for filtering and permissions |
| `url` | `str` | Path to the product in the application |

---

## Relationships

Entities in v2 are **not embedded** — they are linked through explicit relationship objects.

| Relationship | Connects |
|---|---|
| `ObservatoryCatalogLink` | Observatory ↔ Catalog |
| `CatalogItemLink` | Catalog ↔ Catalog Item |
| `ProductObservatoryLink` | Product ↔ Observatory |
| `ProductCatalogItemLink` | Product ↔ Catalog Item (tag) |

!!! info "v2 vs v1"
    In v1 the Observatory embedded its catalogs and items directly. In v2 all relationships are expressed through link objects and managed via dedicated API endpoints. This decoupling allows items to belong to multiple catalogs and products to be tagged across multiple catalogs.

---

## Links and graph model

JUB entities are graph nodes. Links are directed edges managed via dedicated API endpoints. Linking is additive and non-destructive — removing a link never deletes either endpoint entity.

```
Observatory ──has_catalog──> Catalog ──has_item──> CatalogItem
     │                                                   │
     ├──has_product──> Product ─────tagged_with──> CatalogItem
     │                                                   ↕ child_of
     ├──has_datasource──> DataSource
     └──has_service──> Service
```

`CatalogItem` nodes also form a tree internally: a `CatalogItem` can be linked as a child of another `CatalogItem` via `link_catalog_item_child()`. This is the `child_of` self-link shown above — it lives on `CatalogItem` itself and is independent of `tagged_with` (the Product → CatalogItem edge above it).

### Edge reference

| Edge | Response object | Create | Delete |
|---|---|---|---|
| Observatory → Catalog | `ObservatoryCatalogLinkResponseDTO` | `link_catalog_to_observatory()` | `unlink_catalog_from_observatory()` |
| Catalog → CatalogItem | `CatalogItemCatalogLinkResponseDTO` | `link_item_to_catalog()` | `unlink_item_from_catalog()` |
| CatalogItem → CatalogItem (child) | `CatalogItemChildLinkResponseDTO` | `link_catalog_item_child()` | `unlink_catalog_item_child()` |
| Product → Observatory | `ObservatoryProductLinkResponseDTO` | `link_product_to_observatory()` | `unlink_product_from_observatory()` |
| Product → CatalogItem (tag) | `ProductTagsResponseDTO` | `add_product_tags()` | `remove_product_tag()` |
| Observatory → DataSource | *(source_id only)* | `link_datasource_to_observatory()` | `unlink_datasource_from_observatory()` |
| Observatory → Service | *(service_id only)* | `link_service_to_observatory()` | `unlink_service_from_observatory()` |

Bulk shortcuts — `bulk_assign_catalogs()` and `bulk_assign_products()` create entities and link them to an observatory in one call.

---

## Extended response models

These DTOs are returned by specific API methods and extend or compose the core entities above.

### `ObservatoryDetailDTO`

Returned by `get_observatory()`. Extends `ObservatoryXDTO` with aggregated relationship and rating data.

| Field | Type | Description |
|---|---|---|
| `observatory_id` | `str` | Unique identifier |
| `title` | `str` | Display name |
| `description` | `str` | Description |
| `image_url` | `str` | Image URL (optional) |
| `metadata` | `dict` | Arbitrary key-value metadata |
| `created_at` | `str` | ISO 8601 creation timestamp |
| `updated_at` | `str` | ISO 8601 last-update timestamp |
| `services` | `List[ServiceSnapshotDTO]` | Linked services |
| `data_sources` | `List[DataSourceSnapshotDTO]` | Linked data sources |
| `avg_rating` | `float` | Average user rating (0.0–5.0) |
| `review_count` | `int` | Total number of reviews |

### `ObservatoryStatsDTO`

Returned per-observatory by `get_observatories_stats()`.

| Field | Type | Description |
|---|---|---|
| `observatory_id` | `str` | Unique identifier |
| `avg_rating` | `float` | Average user rating (0.0–5.0) |
| `review_count` | `int` | Total number of reviews |
| `services` | `List[ServiceSnapshotDTO]` | Linked services |
| `data_sources` | `List[DataSourceSnapshotDTO]` | Linked data sources |

### `ServiceSnapshotDTO`

Lightweight service summary embedded in observatory responses.

| Field | Type | Description |
|---|---|---|
| `service_id` | `str` | Service identifier |
| `name` | `str` | Display name |
| `provider` | `str` | Provider name (optional) |

### `DataSourceSnapshotDTO`

Lightweight data source summary embedded in observatory responses.

| Field | Type | Description |
|---|---|---|
| `source_id` | `str` | Data source identifier |
| `name` | `str` | Display name |

---

## Update request DTOs

### `CatalogUpdateDTO`

Used by `update_catalog()`. All fields are optional — omit any you do not want to change.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | New human-readable name |
| `description` | `str` | New description |

### `DataSourceUpdateDTO`

Used by `update_data_source()`. All fields are optional.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | New human-readable name |
| `description` | `str` | New description |
| `connection_uri` | `str` | New database connection string |
| `bucket_id` | `str` | New MictlanX bucket identifier |

---

## External integrations — Nez Team *(experimental)*

> **Experimental.** These DTOs were contributed by the Nez Team. Contracts are subject to change and are not part of the stable STORI model. Use them in non-production contexts until they are promoted to stable.

The Nez Team integration introduces a compute layer on top of the JUB data model: **Building Blocks** (containerised units of work) are composed into **Patterns** (execution strategies), assembled into **Stages** (source → transform → sink), ordered into **Workflows**, and exposed as **Services** discoverable via the DSL `SVC()` operator.

### `ServiceProviderEnum`

Identifies the origin of a service. Used in `ServiceCreateDTO.provider` and `ServiceIndexDTO.provider`.

| Value | Meaning |
|---|---|
| `NEZ` | Nez Team managed service |
| `XELHUA` | Xelhua platform service |
| `EXTERNAL` | Third-party external service |
| `OTHER` | Unclassified |

---

### Building blocks

A containerised unit of work. Defines the image and entrypoint that a Pattern will run.

**`BuildingBlockCreateDTO`** — `POST /building-blocks`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Human-readable identifier |
| `command` | `str` | Container entrypoint command |
| `image` | `str` | Docker image reference (e.g. `python:3.11-slim`) |
| `description` | `str` | Optional description |

**`BuildingBlockUpdateDTO`** — `PATCH /building-blocks/{id}`

All fields optional.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | New identifier |
| `command` | `str` | New entrypoint command |
| `image` | `str` | New Docker image |
| `description` | `str` | New description |

**`BuildingBlockDTO`** — response

| Field | Type | Description |
|---|---|---|
| `building_block_id` | `str` | System-generated identifier |
| `name` | `str` | Human-readable identifier |
| `command` | `str` | Container entrypoint command |
| `image` | `str` | Docker image reference |
| `description` | `str` | Optional description |
| `created_at` | `str` | ISO 8601 creation timestamp |
| `updated_at` | `str` | ISO 8601 last-update timestamp |

---

### Patterns

An execution strategy that wraps a Building Block with parallelism and load-balancing config.

**`PatternCreateDTO`** — `POST /patterns`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Human-readable pattern name |
| `task` | `str` | Task category (e.g. `transform`, `ingest`) |
| `pattern` | `str` | Pattern type (e.g. `map-reduce`, `pipeline`) |
| `description` | `str` | Optional description |
| `workers` | `int` | Parallel worker instances (default `1`) |
| `loadbalancer` | `str` | Load-balancing strategy (default `round-robin`) |
| `building_block_id` | `str` | Optional ID of an existing Building Block |

**`PatternUpdateDTO`** — `PATCH /patterns/{id}` — all fields optional, same set as create.

**`PatternDTO`** — response — same fields as create plus `pattern_id`, `created_at`, `updated_at`.

---

### Stages

A processing unit: reads from a source, applies a transformation (Pattern), writes to a sink.

**`StageCreateDTO`** — `POST /stages`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Stage name |
| `source` | `str` | Input source identifier or URI |
| `sink` | `str` | Output sink identifier or URI |
| `endpoint` | `str` | HTTP or messaging endpoint exposed by this stage |
| `transformation_id` | `str` | Optional ID of an existing Pattern to apply |

**`StageUpdateDTO`** — `PATCH /stages/{id}` — all fields optional, same set as create.

**`StageDTO`** — response — same fields as create plus `stage_id`, `created_at`, `updated_at`.

---

### Workflows

An ordered list of Stages that forms a data pipeline.

**`WorkflowCreateDTO`** — `POST /workflows`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Workflow name |
| `stage_ids` | `List[str]` | Ordered list of Stage IDs |

**`WorkflowUpdateDTO`** — `PATCH /workflows/{id}` — all fields optional.

**`WorkflowDTO`** — response — same fields as create plus `workflow_id`, `created_at`, `updated_at`.

**`WorkflowDeleteResponseDTO`** — `DELETE /workflows/{id}`

| Field | Type | Description |
|---|---|---|
| `deleted` | `bool` | Whether the workflow was deleted |
| `cascade` | `dict` | Counts of cascade-deleted entities when `cascade=True` |

---

### Services

A named, discoverable unit that exposes a Workflow. Searchable via the `SVC()` DSL operator.

**`ServiceCreateDTO`** — `POST /services`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Service name (used in `SVC(name=…)` queries) |
| `owner_id` | `str` | User ID of the service owner |
| `description` | `str` | Optional description |
| `public` | `bool` | Whether discoverable via `SVC(*)` (default `False`) |
| `workflow_id` | `str` | Optional ID of an existing Workflow to attach |
| `provider` | `ServiceProviderEnum` | Provider classification (default `OTHER`) |

**`ServiceUpdateDTO`** — `PATCH /services/{id}` — all fields optional except IDs.

**`ServiceDTO`** — response

| Field | Type | Description |
|---|---|---|
| `service_id` | `str` | System-generated identifier |
| `name` | `str` | Service name |
| `description` | `str` | Optional description |
| `owner_id` | `str` | Owner user ID |
| `public` | `bool` | Public visibility flag |
| `workflow_id` | `str` | Attached workflow ID (optional) |
| `created_at` | `str` | ISO 8601 creation timestamp |
| `updated_at` | `str` | ISO 8601 last-update timestamp |

**`ServiceSimpleDTO`** — lightweight summary returned by observatory service lists.

| Field | Type | Description |
|---|---|---|
| `service_id` | `str` | Service identifier |
| `name` | `str` | Display name |
| `description` | `str` | Optional description |
| `provider` | `str` | Provider name (optional) |
| `public` | `bool` | Public visibility flag |

**`ServiceDeleteResponseDTO`** — `DELETE /services/{id}`

| Field | Type | Description |
|---|---|---|
| `deleted` | `bool` | Whether the service was deleted |
| `service_id` | `str` | ID of the deleted service |
| `cascade` | `dict` | Counts of cascade-deleted entities |

---

### One-shot indexing — `index_service()`

`POST /services/index` creates the full **Service → Workflow → Stages → Patterns → Building Blocks** tree in one call. At every level you can either define entities inline or reference existing IDs.

**`ServiceIndexDTO`** — request

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Service name |
| `owner_id` | `str` | Owner user ID |
| `description` | `str` | Optional description |
| `public` | `bool` | Public visibility (default `False`) |
| `provider` | `ServiceProviderEnum` | Provider classification (default `OTHER`) |
| `workflow` | `WorkflowInlineDTO` | Inline workflow to create (mutually exclusive with `workflow_id`) |
| `workflow_id` | `str` | ID of an existing workflow to attach |

**Inline DTOs** (nested inside `ServiceIndexDTO`):

`WorkflowInlineDTO` → `stages: List[StageInlineDTO]`  
`StageInlineDTO` → `transformation: PatternInlineDTO` or `transformation_id`  
`PatternInlineDTO` → `building_block: BuildingBlockInlineDTO` or `building_block_id`

```python
result = await client.index_service(DTO.ServiceIndexDTO(
    name        = "cancer-pipeline",
    owner_id    = user_id,
    public      = True,
    provider    = DTO.ServiceProviderEnum.NEZ,
    workflow    = DTO.WorkflowInlineDTO(
        name   = "ingest-workflow",
        stages = [
            DTO.StageInlineDTO(
                name     = "ingest-stage",
                source   = "s3://bucket/input",
                sink     = "mongodb://db/records",
                endpoint = "http://worker:8080/run",
                transformation = DTO.PatternInlineDTO(
                    name    = "map-pattern",
                    task    = "ingest",
                    pattern = "map-reduce",
                    building_block = DTO.BuildingBlockInlineDTO(
                        name    = "python-runner",
                        command = "python main.py",
                        image   = "python:3.11-slim",
                    ),
                ),
            ),
        ],
    ),
))
```

**`ServiceIndexResponseDTO`** — response

| Field | Type | Description |
|---|---|---|
| `service_id` | `str` | Created service ID |
| `workflow_id` | `str` | Created or referenced workflow ID |
| `stage_ids` | `List[str]` | IDs of all created stages |
| `pattern_ids` | `List[str]` | IDs of all created patterns |
| `building_block_ids` | `List[str]` | IDs of all created building blocks |
