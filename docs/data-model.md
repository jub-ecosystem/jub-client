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
