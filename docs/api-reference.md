# API Reference

Full reference for all methods on `JubClient`. The base URL for every endpoint is `{api_url}/api/v2`.

Every method is `async` and returns `Result[T, Exception]` from the [`option`](https://pypi.org/project/option/) library — never raises.

```python
from jub.client.v2 import JubClient
import jub.dto.v2 as DTO

client = JubClient("http://localhost:5000", "username", "password")
await client.authenticate()
```

---

## JubClient constructor

```python
JubClient(
    api_url: str,
    username: str,
    password: str,
    scope: Optional[str] = None,
    token_expiration: Optional[str] = None,
    renew_token: bool = True,
    write_timeout: int = 120,
    read_timeout: int = 10,
    timeout: int = 30,
    upload_registry_path: Optional[str] = None,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_url` | `str` | — | Base URL of the JUB API (e.g. `http://localhost:5000`) |
| `username` | `str` | — | Account login handle |
| `password` | `str` | — | Account password |
| `scope` | `str` | `"jub"` | JWT scope sent during login |
| `token_expiration` | `str` | `"1h"` | Requested JWT lifetime (e.g. `"2h"`, `"30m"`) |
| `renew_token` | `bool` | `True` | Automatically re-authenticate when the token expires |
| `write_timeout` | `int` | `120` | Seconds before a write (upload) request times out; increase for large files |
| `read_timeout` | `int` | `10` | Seconds before a read response times out |
| `timeout` | `int` | `30` | Default connect/pool timeout in seconds |
| `upload_registry_path` | `str \| None` | `None` | Path to the upload registry JSON file; `None` disables persistence entirely — see [Upload registry](#upload-registry) |

---

## JubClientBuilder

A fluent builder that constructs a `JubClient` and fully authenticates it before returning the result. Use it instead of calling `JubClient()` directly when you want to chain configuration in one expression and have authentication failures surfaced as `Err` rather than a silent uninitialized state.

```python
result = await (
    JubClientBuilder()
    .with_api_url("http://localhost:5000")
    .with_credentials("admin", "secret")
    .with_timeouts(timeout=30, write_timeout=180, read_timeout=15)
    .with_upload_registry("/data/jobs/uploads.json")
    .build()
)

if result.is_ok:
    client = result.unwrap()
else:
    print("Auth failed:", result.unwrap_err())
```

| Method | Returns | Description |
|---|---|---|
| `with_api_url(url)` | `JubClientBuilder` | Sets the API base URL |
| `with_credentials(username, password)` | `JubClientBuilder` | Sets the login credentials |
| `with_timeouts(timeout, write_timeout, read_timeout)` | `JubClientBuilder` | Overrides the three HTTP timeout values |
| `with_upload_registry(path)` | `JubClientBuilder` | Enables the upload registry at the given file path; the file is created automatically if it does not exist — see [Upload registry](#upload-registry) |
| `build()` | `Result[JubClient, Exception]` | Authenticates and returns a ready-to-use client; returns `Err` if authentication fails |

---

## Users

### `authenticate`

```python
async def authenticate() -> Result[bool, Exception]
```

`POST /users/auth` — Logs in with the credentials provided at construction and stores the JWT for all subsequent requests.

**Returns:** `Ok(True)` on success.

```python
result = await client.authenticate()
assert result.is_ok
```

---

### `signup`

```python
async def signup(dto: SignUpDTO) -> Result[AuthResponseDTO, Exception]
```

`POST /users/signup` — Creates a new user account.

| Parameter | Type | Description |
|---|---|---|
| `dto` | `SignUpDTO` | Registration payload |

**`SignUpDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `username` | `str` | Yes | Unique login handle |
| `email` | `str` | Yes | User email address |
| `password` | `str` | Yes | Plain-text password |
| `first_name` | `str` | No | First name |
| `last_name` | `str` | No | Last name |

**Returns:** `Ok(AuthResponseDTO)` — contains `access_token` and `user_profile`.

```python
result = await client.signup(DTO.SignUpDTO(
    username   = "jdoe",
    email      = "jdoe@example.com",
    password   = "s3cr3t",
    first_name = "John",
    last_name  = "Doe",
))
```

---

### `get_current_user`

```python
async def get_current_user() -> Result[UserProfileDTO, Exception]
```

`GET /users/me` — Returns the profile of the currently authenticated user.

**Returns:** `Ok(UserProfileDTO)`.

```python
result = await client.get_current_user()
profile = result.unwrap()
print(profile.username, profile.email)
```

---

### `get_user_settings`

```python
async def get_user_settings(user_id: str) -> Result[UserPreferencesDTO, Exception]
```

`GET /users/{user_id}/settings` — Returns preferences for a specific user.

| Parameter | Type | Description |
|---|---|---|
| `user_id` | `str` | Target user identifier |

**Returns:** `Ok(UserPreferencesDTO)`.

---

### `update_user_settings`

```python
async def update_user_settings(
    user_id: str,
    prefs: UserPreferencesDTO,
) -> Result[UserPreferencesDTO, Exception]
```

`PUT /users/{user_id}/settings` — Replaces all preferences for the given user.

| Parameter | Type | Description |
|---|---|---|
| `user_id` | `str` | Target user identifier |
| `prefs` | `UserPreferencesDTO` | New preferences payload |

**`UserPreferencesDTO` fields:**

| Field | Type | Description |
|---|---|---|
| `appearance` | `AppearanceSettingsDTO` | Theme and font settings |
| `exploration` | `ExplorationSettingsDTO` | Default view and pagination |
| `export` | `ExportSettingsDTO` | Default export format and metadata flag |

**Returns:** `Ok(UserPreferencesDTO)` — the saved preferences.

---

## Catalogs

### `create_catalog`

```python
async def create_catalog(
    dto: Union[CatalogCreateDTO, Dict],
) -> Result[CatalogCreatedResponseDTO, Exception]
```

`POST /catalogs` — Creates a catalog with its items, aliases, and hierarchy in one request.

| Parameter | Type | Description |
|---|---|---|
| `dto` | `CatalogCreateDTO` or `dict` | Catalog creation payload |

**`CatalogCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Human-readable name |
| `value` | `str` | Yes | Stored query value (UPPER_SNAKE_CASE) |
| `catalog_type` | `str` | Yes | `SPATIAL`, `TEMPORAL`, or `INTEREST` |
| `description` | `str` | No | Contextual description |
| `items` | `List[CatalogItemCreateDTO]` | No | Items to create inline |

**`CatalogItemCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Display name |
| `value` | `str` | Yes | Query value |
| `code` | `int` | Yes | Unique numeric code |
| `value_type` | `str` | Yes | `STRING`, `NUMBER`, `BOOLEAN`, or `DATETIME` |
| `description` | `str` | No | Contextual description |
| `temporal_value` | `str` | No | ISO 8601 datetime (temporal items only) |
| `aliases` | `List[CatalogItemAliasCreateDTO]` | No | Alternative values |
| `children` | `List[CatalogItemCreateDTO]` | No | Nested child items |

**Returns:** `Ok(CatalogCreatedResponseDTO)` — contains `catalog_id`.

```python
result = await client.create_catalog(DTO.CatalogCreateDTO(
    name         = "Geographic Dimension",
    value        = "SPATIAL_MX",
    catalog_type = "SPATIAL",
    items=[
        DTO.CatalogItemCreateDTO(
            name="Mexico", value="MX", code=0, value_type="STRING",
        )
    ],
))
catalog_id = result.unwrap().catalog_id
```

---

### `create_catalog_from_json`

```python
async def create_catalog_from_json(
    json_path: Optional[str] = None,
    json_string: Optional[str] = None,
    data: Optional[Dict] = None,
) -> Result[CatalogCreatedResponseDTO, Exception]
```

`POST /catalogs` — Convenience wrapper to load a catalog payload from a file, JSON string, or dict. Provide exactly one of the three parameters.

| Parameter | Type | Description |
|---|---|---|
| `json_path` | `str` | Path to a JSON file |
| `json_string` | `str` | Raw JSON string |
| `data` | `dict` | Already-parsed dict matching `CatalogCreateDTO` |

**Returns:** `Ok(CatalogCreatedResponseDTO)`.

```python
result = await client.create_catalog_from_json(json_path="catalogs/spatial.json")
```

---

### `create_bulk_catalogs_from_json`

```python
async def create_bulk_catalogs_from_json(
    json_path: Optional[str] = None,
    json_string: Optional[str] = None,
    data: Optional[List[Dict]] = None,
) -> Result[CatalogCreatedBulkResponseDTO, Exception]
```

`POST /catalogs/bulk` — Creates multiple catalogs at once. The source must be a JSON array of `CatalogCreateDTO` payloads.

| Parameter | Type | Description |
|---|---|---|
| `json_path` | `str` | Path to a JSON file containing a list |
| `json_string` | `str` | Raw JSON string containing a list |
| `data` | `List[dict]` | Already-parsed list of dicts |

**Returns:** `Ok(CatalogCreatedBulkResponseDTO)` — contains `catalog_ids: List[str]`.

---

### `update_catalog`

```python
async def update_catalog(
    catalog_id: str,
    payload: CatalogUpdateDTO,
) -> Result[CatalogSummaryDTO, Exception]
```

`PUT /catalogs/{catalog_id}` — Updates mutable fields on an existing catalog. Does not touch nested items or aliases.

| Parameter | Type | Description |
|---|---|---|
| `catalog_id` | `str` | Target catalog identifier |
| `payload` | `CatalogUpdateDTO` | Fields to update |

**`CatalogUpdateDTO` fields** (all optional):

| Field | Type | Description |
|---|---|---|
| `name` | `str` | New human-readable name |
| `description` | `str` | New description |

**Returns:** `Ok(CatalogSummaryDTO)`.

```python
result = await client.update_catalog(
    "cat_abc",
    DTO.CatalogUpdateDTO(name="Renamed Catalog"),
)
```

---

### `delete_catalog`

```python
async def delete_catalog(catalog_id: str) -> Result[CatalogSummaryDTO, Exception]
```

`DELETE /catalogs/{catalog_id}` — Deletes a catalog and all its linked relationships.

| Parameter | Type | Description |
|---|---|---|
| `catalog_id` | `str` | Target catalog identifier |

**Returns:** `Ok(CatalogSummaryDTO)` — the deleted catalog's summary.

```python
result = await client.delete_catalog("cat_abc")
```

---

### `list_catalogs`

```python
async def list_catalogs() -> Result[List[CatalogSummaryDTO], Exception]
```

`GET /catalogs` — Returns a lightweight summary list of all catalogs.

**Returns:** `Ok(List[CatalogSummaryDTO])` — each item has `catalog_id`, `name`, `value`, `catalog_type`.

```python
catalogs = (await client.list_catalogs()).unwrap()
```

---

### `get_catalog`

```python
async def get_catalog(catalog_id: str) -> Result[CatalogResponseDTO, Exception]
```

`GET /catalogs/{catalog_id}` — Returns the full catalog including all items and their aliases.

| Parameter | Type | Description |
|---|---|---|
| `catalog_id` | `str` | Unique identifier of the catalog |

**Returns:** `Ok(CatalogResponseDTO)` — contains `catalog_id`, `name`, `value`, `catalog_type`, `description`, `items`.

---

## Catalog Items

### `create_catalog_item`

```python
async def create_catalog_item(
    dto: Union[CatalogItemStandaloneCreateDTO, Dict],
) -> Result[CatalogItemXResponseDTO, Exception]
```

`POST /catalog-items` — Creates a standalone catalog item in an existing catalog.

**`CatalogItemStandaloneCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `catalog_id` | `str` | Yes | ID of the parent catalog |
| `name` | `str` | Yes | Display name |
| `value` | `str` | Yes | Query value |
| `code` | `int` | Yes | Unique numeric code |
| `value_type` | `str` | Yes | `STRING`, `NUMBER`, `BOOLEAN`, or `DATETIME` |
| `description` | `str` | No | Contextual description |
| `temporal_value` | `str` | No | ISO 8601 datetime |
| `parent_item_id` | `str` | No | ID of a parent item for hierarchy placement |

**Returns:** `Ok(CatalogItemXResponseDTO)`.

---

### `list_catalog_items`

```python
async def list_catalog_items(limit: int = 100) -> Result[List[CatalogItemXResponseDTO], Exception]
```

`GET /catalog-items` — Returns a paginated list of catalog items.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | `int` | `100` | Maximum number of items to return |

**Returns:** `Ok(List[CatalogItemXResponseDTO])`.

---

### `get_catalog_item`

```python
async def get_catalog_item(catalog_item_id: str) -> Result[CatalogItemXResponseDTO, Exception]
```

`GET /catalog-items/{id}` — Returns a single catalog item.

| Parameter | Type | Description |
|---|---|---|
| `catalog_item_id` | `str` | Unique identifier of the item |

**Returns:** `Ok(CatalogItemXResponseDTO)`.

---

### `update_catalog_item`

```python
async def update_catalog_item(
    catalog_item_id: str,
    dto: Union[CatalogItemUpdateDTO, Dict],
) -> Result[CatalogItemXResponseDTO, Exception]
```

`PUT /catalog-items/{id}` — Updates mutable fields on a catalog item.

| Parameter | Type | Description |
|---|---|---|
| `catalog_item_id` | `str` | Unique identifier of the item |
| `dto` | `CatalogItemUpdateDTO` or `dict` | Fields to update |

**`CatalogItemUpdateDTO` fields** (all optional):

| Field | Type | Description |
|---|---|---|
| `name` | `str` | New display name |
| `description` | `str` | New description |
| `temporal_value` | `str` | New ISO 8601 datetime |

**Returns:** `Ok(CatalogItemXResponseDTO)`.

---

### `delete_catalog_item`

```python
async def delete_catalog_item(catalog_item_id: str) -> Result[CatalogItemDeleteResponseDTO, Exception]
```

`DELETE /catalog-items/{id}` — Deletes a catalog item and all its relationships.

| Parameter | Type | Description |
|---|---|---|
| `catalog_item_id` | `str` | Unique identifier of the item |

**Returns:** `Ok(CatalogItemDeleteResponseDTO)` — contains `deleted: bool`.

---

### `list_catalog_item_aliases`

```python
async def list_catalog_item_aliases(catalog_item_id: str) -> Result[List[CatalogItemAliasXResponseDTO], Exception]
```

`GET /catalog-items/{id}/aliases` — Returns all aliases for an item.

**Returns:** `Ok(List[CatalogItemAliasXResponseDTO])`.

---

### `add_catalog_item_alias`

```python
async def add_catalog_item_alias(
    catalog_item_id: str,
    dto: Union[CatalogItemAliasCreateDTO, Dict],
) -> Result[CatalogItemAliasXResponseDTO, Exception]
```

`POST /catalog-items/{id}/aliases` — Adds an alias to an item.

| Parameter | Type | Description |
|---|---|---|
| `catalog_item_id` | `str` | Unique identifier of the item |
| `dto` | `CatalogItemAliasCreateDTO` or `dict` | Alias payload |

**`CatalogItemAliasCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `value` | `str` | Yes | The alias string |
| `value_type` | `str` | Yes | `STRING`, `NUMBER`, `BOOLEAN`, or `DATETIME` |
| `description` | `str` | No | Contextual description |

**Returns:** `Ok(CatalogItemAliasXResponseDTO)`.

---

### `delete_catalog_item_alias`

```python
async def delete_catalog_item_alias(
    catalog_item_id: str,
    alias_id: str,
) -> Result[bool, Exception]
```

`DELETE /catalog-items/{id}/aliases/{alias_id}` — Removes an alias (204 No Content).

**Returns:** `Ok(True)` on success.

---

### `list_catalog_item_children`

```python
async def list_catalog_item_children(catalog_item_id: str) -> Result[List[CatalogItemXResponseDTO], Exception]
```

`GET /catalog-items/{id}/children` — Returns direct child items in the hierarchy.

**Returns:** `Ok(List[CatalogItemXResponseDTO])`.

---

### `link_catalog_item_child`

```python
async def link_catalog_item_child(
    catalog_item_id: str,
    dto: Union[CatalogItemChildLinkCreateDTO, Dict],
) -> Result[CatalogItemChildLinkResponseDTO, Exception]
```

`POST /catalog-items/{id}/children` — Links a child item to this item.

| Parameter | Type | Description |
|---|---|---|
| `catalog_item_id` | `str` | Parent item ID |
| `dto` | `CatalogItemChildLinkCreateDTO` | Must contain `child_item_id: str` |

**Returns:** `Ok(CatalogItemChildLinkResponseDTO)` — contains `parent_item_id` and `child_item_id`.

---

### `unlink_catalog_item_child`

```python
async def unlink_catalog_item_child(
    catalog_item_id: str,
    child_item_id: str,
) -> Result[bool, Exception]
```

`DELETE /catalog-items/{id}/children/{child_id}` — Removes a child relationship (204 No Content).

**Returns:** `Ok(True)` on success.

---

### `list_catalogs_for_item`

```python
async def list_catalogs_for_item(catalog_item_id: str) -> Result[List[CatalogXDTO], Exception]
```

`GET /catalog-items/{id}/catalogs` — Returns all catalogs that contain this item.

**Returns:** `Ok(List[CatalogXDTO])`.

---

### `link_item_to_catalog`

```python
async def link_item_to_catalog(
    catalog_item_id: str,
    dto: Union[CatalogItemCatalogLinkCreateDTO, Dict],
) -> Result[CatalogItemCatalogLinkResponseDTO, Exception]
```

`POST /catalog-items/{id}/catalogs` — Links this item to an existing catalog.

| Parameter | Type | Description |
|---|---|---|
| `catalog_item_id` | `str` | Item to link |
| `dto` | `CatalogItemCatalogLinkCreateDTO` | Must contain `catalog_id: str` |

**Returns:** `Ok(CatalogItemCatalogLinkResponseDTO)`.

---

### `unlink_item_from_catalog`

```python
async def unlink_item_from_catalog(
    catalog_item_id: str,
    catalog_id: str,
) -> Result[bool, Exception]
```

`DELETE /catalog-items/{id}/catalogs/{catalog_id}` — Removes an item from a catalog (204 No Content).

**Returns:** `Ok(True)` on success.

---

### `list_products_for_item`

```python
async def list_products_for_item(catalog_item_id: str) -> Result[ItemProductsDTO, Exception]
```

`GET /catalog-items/{id}/products` — Returns the product IDs tagged with this item.

**Returns:** `Ok(ItemProductsDTO)` — contains `catalog_item_id` and `product_ids: List[str]`.

---

## Observatories

### `create_observatory`

```python
async def create_observatory(
    dto: Union[ObservatoryCreateDTO, Dict],
) -> Result[ObservatoryXDTO, Exception]
```

`POST /observatories` — Creates an immediately-enabled observatory.

**`ObservatoryCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `str` | Yes | Display name |
| `description` | `str` | No | Contextual description |
| `image_url` | `str` | No | URL of a representative image |

**Returns:** `Ok(ObservatoryXDTO)`.

```python
result = await client.create_observatory(DTO.ObservatoryCreateDTO(
    title       = "Cancer Epidemiology",
    description = "National cancer surveillance.",
))
obs = result.unwrap()
```

---

### `setup_observatory`

```python
async def setup_observatory(
    dto: Union[ObservatorySetupDTO, Dict],
) -> Result[ObservatorySetupResponseDTO, Exception]
```

`POST /observatories/setup` — Creates a **disabled** observatory and queues a background setup task. The observatory is enabled only after `complete_task()` is called with `success=True`.

!!! info "Two-step provisioning"
    Use `setup_observatory` when you need to index catalogs and products before the observatory becomes visible to users. Use `create_observatory` for immediate, empty observatories.

**`ObservatorySetupDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `str` | Yes | Display name |
| `observatory_id` | `str` | No | Pre-defined ID (random UUID generated if omitted) |
| `description` | `str` | No | Contextual description |
| `image_url` | `str` | No | URL of a representative image |
| `metadata` | `Dict[str, str]` | No | Arbitrary key-value metadata |

**Returns:** `Ok(ObservatorySetupResponseDTO)` — contains `observatory_id` and `task_id`.

```python
result = await client.setup_observatory(DTO.ObservatorySetupDTO(
    observatory_id = "obs_cancer_mx_2024",
    title          = "Cancer Epidemiology — Mexico 2024",
))
setup = result.unwrap()
task_id = setup.task_id  # needed for complete_task()
```

---

### `list_observatories`

```python
async def list_observatories(
    page_index: int = 0,
    limit: int = 10,
) -> Result[List[ObservatoryXDTO], Exception]
```

`GET /observatories` — Returns a paginated list of observatories.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page_index` | `int` | `0` | Page offset (0-based) |
| `limit` | `int` | `10` | Page size |

**Returns:** `Ok(List[ObservatoryXDTO])`.

---

### `get_observatory`

```python
async def get_observatory(observatory_id: str) -> Result[ObservatoryDetailDTO, Exception]
```

`GET /observatories/{id}` — Returns a single observatory enriched with linked services, data sources, and rating stats.

**Returns:** `Ok(ObservatoryDetailDTO)` — extends `ObservatoryXDTO` with `services`, `data_sources`, `avg_rating`, and `review_count`.

```python
obs = (await client.get_observatory("obs_abc")).unwrap()
print(obs.avg_rating, len(obs.services))
```

---

### `get_observatories_stats`

```python
async def get_observatories_stats(
    obs_ids: List[str],
) -> Result[List[ObservatoryStatsDTO], Exception]
```

`POST /observatories/details` — Returns rating and relationship stats for a batch of observatory IDs.

| Parameter | Type | Description |
|---|---|---|
| `obs_ids` | `List[str]` | Observatory identifiers to query |

**Returns:** `Ok(List[ObservatoryStatsDTO])`.

**`ObservatoryStatsDTO` fields:**

| Field | Type | Description |
|---|---|---|
| `observatory_id` | `str` | Observatory identifier |
| `avg_rating` | `float` | Average user rating (0.0–5.0) |
| `review_count` | `int` | Total number of reviews |
| `services` | `List[ServiceSnapshotDTO]` | Linked services (id, name, provider) |
| `data_sources` | `List[DataSourceSnapshotDTO]` | Linked data sources (id, name) |

```python
stats = (await client.get_observatories_stats(["obs_1", "obs_2"])).unwrap()
for s in stats:
    print(s.observatory_id, s.avg_rating, s.review_count)
```

---

### `update_observatory`

```python
async def update_observatory(
    observatory_id: str,
    dto: Union[ObservatoryUpdateDTO, Dict],
) -> Result[ObservatoryXDTO, Exception]
```

`PUT /observatories/{id}` — Updates mutable fields on an observatory.

**`ObservatoryUpdateDTO` fields** (all optional):

| Field | Type | Description |
|---|---|---|
| `title` | `str` | New display name |
| `description` | `str` | New description |
| `image_url` | `str` | New image URL |

**Returns:** `Ok(ObservatoryXDTO)`.

---

### `delete_observatory`

```python
async def delete_observatory(observatory_id: str) -> Result[ObservatoryDeleteResponseDTO, Exception]
```

`DELETE /observatories/{id}` — Deletes an observatory and its linked relationships.

**Returns:** `Ok(ObservatoryDeleteResponseDTO)` — contains `deleted: bool`.

---

### `link_catalog_to_observatory`

```python
async def link_catalog_to_observatory(
    observatory_id: str,
    dto: Union[LinkCatalogDTO, Dict],
) -> Result[ObservatoryCatalogLinkResponseDTO, Exception]
```

`POST /observatories/{id}/catalogs` — Links an existing catalog to an observatory.

| Parameter | Type | Description |
|---|---|---|
| `observatory_id` | `str` | Target observatory |
| `dto` | `LinkCatalogDTO` | Contains `catalog_id: str` and optional `level: int` |

**Returns:** `Ok(ObservatoryCatalogLinkResponseDTO)`.

---

### `list_observatory_catalogs`

```python
async def list_observatory_catalogs(observatory_id: str) -> Result[List[CatalogXDTO], Exception]
```

`GET /observatories/{id}/catalogs` — Lists all catalogs linked to an observatory.

**Returns:** `Ok(List[CatalogXDTO])`.

---

### `unlink_catalog_from_observatory`

```python
async def unlink_catalog_from_observatory(
    observatory_id: str,
    catalog_id: str,
) -> Result[bool, Exception]
```

`DELETE /observatories/{id}/catalogs/{catalog_id}` — Removes a catalog link (204 No Content).

**Returns:** `Ok(True)` on success.

---

### `bulk_assign_catalogs`

```python
async def bulk_assign_catalogs(
    observatory_id: str,
    dto: Union[BulkCatalogsDTO, Dict],
) -> Result[BulkCatalogsResponseDTO, Exception]
```

`POST /observatories/{id}/catalogs/bulk` — Creates multiple catalogs and links each to the observatory in one request.

| Parameter | Type | Description |
|---|---|---|
| `observatory_id` | `str` | Target observatory |
| `dto` | `BulkCatalogsDTO` | Contains `catalogs: List[CatalogCreateDTO]` |

**Returns:** `Ok(BulkCatalogsResponseDTO)` — contains `observatory_id` and `catalog_ids: List[str]`.

---

### `list_observatory_products`

```python
async def list_observatory_products(observatory_id: str) -> Result[List[ProductSimpleDTO], Exception]
```

`GET /observatories/{id}/products` — Lists all products linked to an observatory.

**Returns:** `Ok(List[ProductSimpleDTO])`.

---

### `link_product_to_observatory`

```python
async def link_product_to_observatory(
    observatory_id: str,
    dto: Union[LinkProductDTO, Dict],
) -> Result[ObservatoryProductLinkResponseDTO, Exception]
```

`POST /observatories/{id}/products` — Links an existing product to an observatory.

| Parameter | Type | Description |
|---|---|---|
| `observatory_id` | `str` | Target observatory |
| `dto` | `LinkProductDTO` | Contains `product_id: str` |

**Returns:** `Ok(ObservatoryProductLinkResponseDTO)`.

---

### `unlink_product_from_observatory`

```python
async def unlink_product_from_observatory(
    observatory_id: str,
    product_id: str,
) -> Result[bool, Exception]
```

`DELETE /observatories/{id}/products/{product_id}` — Removes a product link (204 No Content).

**Returns:** `Ok(True)` on success.

---

### `bulk_assign_products`

```python
async def bulk_assign_products(
    observatory_id: str,
    dto: Union[BulkProductsDTO, Dict],
) -> Result[BulkProductsResponseDTO, Exception]
```

`POST /observatories/{id}/products/bulk` — Creates multiple products and links each to the observatory in one request.

| Parameter | Type | Description |
|---|---|---|
| `observatory_id` | `str` | Target observatory |
| `dto` | `BulkProductsDTO` | Contains `products: List[BulkProductItemDTO]` |

**`BulkProductItemDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Display name |
| `product_id` | `str` | No | Pre-defined ID |
| `description` | `str` | No | Contextual description |
| `catalog_item_ids` | `List[str]` | No | Tags to apply |

**Returns:** `Ok(BulkProductsResponseDTO)` — contains `observatory_id` and `products: List[BulkProductCreatedDTO]`.

---

### `link_service_to_observatory`

```python
async def link_service_to_observatory(
    observatory_id: str,
    service_id: str,
) -> Result[bool, Exception]
```

`POST /observatories/{id}/services` — Links an existing service to an observatory.

| Parameter | Type | Description |
|---|---|---|
| `observatory_id` | `str` | Target observatory |
| `service_id` | `str` | Service to link |

**Returns:** `Ok(True)` on success.

---

### `list_observatory_services`

```python
async def list_observatory_services(
    observatory_id: str,
) -> Result[List[ServiceSimpleDTO], Exception]
```

`GET /observatories/{id}/services` — Lists all services linked to an observatory.

**`ServiceSimpleDTO` fields:**

| Field | Type | Description |
|---|---|---|
| `service_id` | `str` | Service identifier |
| `name` | `str` | Display name |
| `description` | `str` | Description |
| `provider` | `str` | Provider name (optional) |
| `public` | `bool` | Whether the service is publicly visible |

**Returns:** `Ok(List[ServiceSimpleDTO])`.

---

### `unlink_service_from_observatory`

```python
async def unlink_service_from_observatory(
    observatory_id: str,
    service_id: str,
) -> Result[bool, Exception]
```

`DELETE /observatories/{id}/services/{service_id}` — Removes the link between a service and an observatory (204 No Content).

**Returns:** `Ok(True)` on success.

---

### `link_datasource_to_observatory`

```python
async def link_datasource_to_observatory(
    observatory_id: str,
    datasource_id: str,
) -> Result[bool, Exception]
```

`POST /observatories/{id}/datasources` — Links an existing data source to an observatory.

| Parameter | Type | Description |
|---|---|---|
| `observatory_id` | `str` | Target observatory |
| `datasource_id` | `str` | Data source to link |

**Returns:** `Ok(True)` on success.

---

### `list_observatory_datasources`

```python
async def list_observatory_datasources(
    observatory_id: str,
) -> Result[List[DataSourceDTO], Exception]
```

`GET /observatories/{id}/datasources` — Lists all data sources linked to an observatory.

**Returns:** `Ok(List[DataSourceDTO])`.

---

### `unlink_datasource_from_observatory`

```python
async def unlink_datasource_from_observatory(
    observatory_id: str,
    datasource_id: str,
) -> Result[bool, Exception]
```

`DELETE /observatories/{id}/datasources/{datasource_id}` — Removes the link between a data source and an observatory (204 No Content).

**Returns:** `Ok(True)` on success.

---

## Products

### `create_product`

```python
async def create_product(
    dto: Union[ProductCreateDTO, Dict],
) -> Result[ProductSimpleDTO, Exception]
```

`POST /products` — Creates a product linked to an observatory.

**`ProductCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Display name |
| `observatory_id` | `str` | Yes | Observatory to link this product to |
| `product_id` | `str` | No | Pre-defined ID (random UUID generated if omitted) |
| `description` | `str` | No | Contextual description |
| `catalog_item_ids` | `List[str]` | No | Initial tags |

**Returns:** `Ok(ProductSimpleDTO)`.

---

### `list_products`

```python
async def list_products(limit: int = 100) -> Result[List[ProductSimpleDTO], Exception]
```

`GET /products` — Returns a paginated list of products.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | `int` | `100` | Maximum number of products to return |

**Returns:** `Ok(List[ProductSimpleDTO])`.

---

### `get_product`

```python
async def get_product(product_id: str) -> Result[ProductSimpleDTO, Exception]
```

`GET /products/{id}` — Returns a single product.

**Returns:** `Ok(ProductSimpleDTO)`.

---

### `update_product`

```python
async def update_product(
    product_id: str,
    dto: Union[ProductUpdateDTO, Dict],
) -> Result[ProductSimpleDTO, Exception]
```

`PUT /products/{id}` — Updates mutable fields on a product.

**`ProductUpdateDTO` fields** (all optional):

| Field | Type | Description |
|---|---|---|
| `name` | `str` | New display name |
| `description` | `str` | New description |
| `product_type` | `str` | New product type category |

**Returns:** `Ok(ProductSimpleDTO)`.

---

### `delete_product`

```python
async def delete_product(product_id: str) -> Result[ProductDeleteResponseDTO, Exception]
```

`DELETE /products/{id}` — Deletes a product and its relationships.

**Returns:** `Ok(ProductDeleteResponseDTO)` — contains `deleted: bool`.

---

### `get_product_tags`

```python
async def get_product_tags(product_id: str) -> Result[ProductTagsResponseDTO, Exception]
```

`GET /products/{id}/tags` — Returns the catalog item IDs associated with a product.

**Returns:** `Ok(ProductTagsResponseDTO)` — contains `product_id` and `catalog_item_ids: List[str]`.

---

### `add_product_tags`

```python
async def add_product_tags(
    product_id: str,
    dto: Union[TagProductDTO, Dict],
) -> Result[ProductTagsResponseDTO, Exception]
```

`POST /products/{id}/tags` — Associates catalog items with a product for search and filtering.

| Parameter | Type | Description |
|---|---|---|
| `product_id` | `str` | Target product |
| `dto` | `TagProductDTO` | Contains `catalog_item_ids: List[str]` |

**Returns:** `Ok(ProductTagsResponseDTO)`.

---

### `remove_product_tag`

```python
async def remove_product_tag(
    product_id: str,
    catalog_item_id: str,
) -> Result[bool, Exception]
```

`DELETE /products/{id}/tags/{catalog_item_id}` — Removes a catalog item tag from a product (204 No Content).

**Returns:** `Ok(True)` on success.

---

### `get_product_tag_details`

```python
async def get_product_tag_details(product_id: str) -> Result[List[CatalogItemXResponseDTO], Exception]
```

`GET /products/{id}/tags/details` — Returns the full `CatalogItemXResponseDTO` for each tag instead of just IDs.

**Returns:** `Ok(List[CatalogItemXResponseDTO])`.

---

### `upload_product`

```python
async def upload_product(
    product_id: str,
    file_path: Union[str, bytes],
) -> Result[ProductUploadResponseDTO, Exception]
```

`POST /products/{id}/upload` — Queues a file for background ingestion linked to the product.

| Parameter | Type | Description |
|---|---|---|
| `product_id` | `str` | Target product |
| `file_path` | `str` or `bytes` | Path to a file on disk, or raw bytes |

**Returns:** `Ok(ProductUploadResponseDTO)` — contains `job_id`, `product_id`, and `status`.

**Error cases:**

| Error | Condition |
|---|---|
| `Err(IsADirectoryError)` | `file_path` is a string pointing to a directory instead of a file |
| `Err(OSError)` | Any other IO failure: file not found, permission denied, etc. |

```python
result = await client.upload_product("prod_123", "charts/mortality.html")
upload = result.unwrap()
print(f"Job {upload.job_id} queued with status {upload.status}")
```

---

### `download_product`

```python
async def download_product(product_id: str) -> Result[bytes, Exception]
```

`GET /products/{id}/download` — Downloads the product file as raw bytes.

**Returns:** `Ok(bytes)`.

```python
data = (await client.download_product("prod_123")).unwrap()
with open("output.html", "wb") as f:
    f.write(data)
```

---

## Bulk uploads

`JubClient` includes a queue-based bulk upload system for ingesting many product files concurrently without blocking. The workflow is:

1. Call `register_upload()` for each file (sync, returns immediately).
2. Call `wait_uploads()` to drain the queue with configurable concurrency.

Or use `bulk_upload_products()` as a single-call convenience wrapper.

### Result types

```python
@dataclass
class FailedUploadEntry:
    product_id: str   # Product that failed
    attempts: int     # Total attempts made
    last_error: str   # Error message from the last attempt

@dataclass
class BulkUploadResult:
    succeeded: List[ProductUploadResponseDTO]  # Successful job responses
    failed:    List[FailedUploadEntry]         # Permanent failures
    skipped:   List[str]                       # product_ids skipped because the registry recorded them as already succeeded
```

---

### `register_upload`

```python
def register_upload(
    product_id: str,
    payload: Union[str, bytes],
) -> Result[int, Exception]
```

Enqueues a product upload job without executing it. This method is synchronous.

If an `UploadRegistry` is active and the product already has a `succeeded` entry from a prior session, the job is **skipped** — it is never added to the queue and the `product_id` is recorded in `BulkUploadResult.skipped` instead. A `job_skipped_already_uploaded` log event is emitted immediately at INFO level.

| Parameter | Type | Description |
|---|---|---|
| `product_id` | `str` | Product to upload to |
| `payload` | `str` or `bytes` | File path on disk (`str`) or raw file bytes |

**Returns:** `Ok(pending_count)` — number of jobs currently in the queue.

**Error cases:**

| Error | Condition |
|---|---|
| `Err(TypeError)` | `payload` is not `str` or `bytes` |
| `Err(IsADirectoryError)` | `payload` is a string pointing to a directory instead of a file |

```python
client.register_upload("prod_1", "/data/file1.csv")
client.register_upload("prod_2", b"raw,csv,bytes")
```

---

### `wait_uploads`

```python
async def wait_uploads(
    workers: int = 1,
    max_retries: int = 1,
) -> Result[BulkUploadResult, Exception]
```

Processes all jobs registered via `register_upload()`. Drains and clears the queue on each call.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `workers` | `int` | `1` | Number of concurrent upload coroutines |
| `max_retries` | `int` | `1` | Maximum attempts per job (1 = no retry) |

**Returns:** `Ok(BulkUploadResult)` — failed jobs are in `result.failed`, not wrapped in `Err`. Only returns `Err` if another `wait_uploads()` call is already running.

```python
client.register_upload("prod_1", "/data/report.csv")
client.register_upload("prod_2", "/data/summary.json")

result = (await client.wait_uploads(workers=4, max_retries=3)).unwrap()
print(f"Done: {len(result.succeeded)} ok, {len(result.failed)} failed")
for f in result.failed:
    print(f.product_id, f.last_error)
```

---

### `bulk_upload_products`

```python
async def bulk_upload_products(
    uploads: List[Tuple[str, Union[str, bytes]]],
    workers: int = 1,
    max_retries: int = 1,
) -> Result[BulkUploadResult, Exception]
```

Convenience wrapper that calls `register_upload()` for every entry and then calls `wait_uploads()`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `uploads` | `List[Tuple[str, str or bytes]]` | — | List of `(product_id, file_path_or_bytes)` pairs |
| `workers` | `int` | `1` | Concurrent upload coroutines |
| `max_retries` | `int` | `1` | Attempts per job before permanent failure |

**Returns:** `Ok(BulkUploadResult)` or `Err` if any payload type is invalid.

```python
result = (await client.bulk_upload_products(
    uploads=[
        ("prod_1", "/data/report.csv"),
        ("prod_2", "/data/summary.json"),
        ("prod_3", b"inline,bytes,data"),
    ],
    workers=4,
    max_retries=2,
)).unwrap()
```

---

### `clear_upload_registry`

```python
def clear_upload_registry() -> Result[None, Exception]
```

Wipes every entry from the upload registry file. The next run will treat every product as new, even those that previously succeeded.

**Returns:** `Ok(None)` on success. `Err(Exception)` if no `upload_registry_path` was given to this client.

```python
client.clear_upload_registry().unwrap()
```

---

### `reset_failed_uploads`

```python
def reset_failed_uploads() -> Result[int, Exception]
```

Removes only the `failed` entries from the registry so they can be re-registered and retried on the next run. `succeeded` entries are left untouched, so products that already completed will still be skipped.

| Returns | Condition |
|---|---|
| `Ok(count)` | Number of failed entries removed |
| `Err(Exception)` | No `upload_registry_path` was given to this client |

```python
removed = client.reset_failed_uploads().unwrap()
print(f"Cleared {removed} failed entries — they will be retried on next run")
```

---

## Upload registry

The upload registry is an opt-in, file-backed mechanism that persists the outcome of every product upload across Python sessions. Enable it by passing `upload_registry_path` to the constructor or calling `.with_upload_registry(path)` on the builder.

### Purpose

| Goal | How it works |
|---|---|
| **Idempotency** | `register_upload()` checks the registry before queuing — if the product already `succeeded`, the job is skipped |
| **Resumability** | Re-running the same script continues from where it left off; only products that never succeeded are attempted again |
| **Crash safety** | The registry file is written atomically (`os.replace`) so a crash mid-write never corrupts it |

### Registry file format

The registry is a plain JSON object. Each key is a `product_id`:

```json
{
  "prod-abc123": {
    "status": "succeeded",
    "job_id": "job-xyz",
    "attempts": 1,
    "last_error": null,
    "timestamp": "2026-05-07T14:32:10.123456+00:00"
  },
  "prod-def456": {
    "status": "failed",
    "job_id": null,
    "attempts": 3,
    "last_error": "500 Internal Server Error",
    "timestamp": "2026-05-07T14:35:02.654321+00:00"
  },
  "prod-ghi789": {
    "status": "pending",
    "job_id": null,
    "attempts": 0,
    "last_error": null,
    "timestamp": "2026-05-07T14:34:58.000000+00:00"
  }
}
```

| Field | Values | Meaning |
|---|---|---|
| `status` | `pending` / `succeeded` / `failed` | Current lifecycle state |
| `job_id` | string or `null` | Background job ID returned by the API on success |
| `attempts` | integer | Total upload attempts so far |
| `last_error` | string or `null` | Error message from the last failed attempt |
| `timestamp` | ISO-8601 UTC | When this entry was last written |

!!! note "Pending entries on restart"
    A `pending` entry means the worker picked up the job but the process was killed before a final outcome was recorded. On the next run these entries are **not** skipped — they are retried, which is the safe behaviour since it is unknown whether the upload completed on the server side.

### Log events

All events are emitted through the `jub-uploads` logger as structured JSON.

| Event | Level | When emitted |
|---|---|---|
| `job_registered` | DEBUG | Job successfully added to the queue |
| `job_skipped_already_uploaded` | INFO | Registry has a `succeeded` entry — job skipped |
| `bulk_start` | INFO | `wait_uploads()` starts; includes `total_jobs`, `skipped_count`, `workers`, `max_retries` |
| `job_started` | DEBUG | Worker picked up a job; includes current attempt number |
| `job_succeeded` | INFO | Upload completed; includes attempt, progress %, and durations |
| `job_failed_retry` | INFO | Upload failed, retries remain; includes `retries_left` |
| `job_failed_permanent` | INFO | All retries exhausted; job recorded as permanently failed |
| `bulk_complete` | INFO | All jobs finished; includes `succeeded_count`, `failed_count`, `skipped_count`, duration |
| `registry_cleared` | INFO | `clear_upload_registry()` was called |
| `registry_failed_reset` | INFO | `reset_failed_uploads()` was called; includes `removed_count` |

---

## Data Sources

### `register_data_source`

```python
async def register_data_source(
    dto: Union[DataSourceCreateDTO, Dict],
) -> Result[DataSourceDTO, Exception]
```

`POST /datasources` — Registers a new data source.

**`DataSourceCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Human-readable name |
| `format` | `str` | No | `csv`, `json`, `postgres`, `mysql`, `mongodb` (default `csv`) |
| `description` | `str` | No | Contextual description |
| `bucket_id` | `str` | No | MictlanX bucket identifier |
| `connection_uri` | `str` | No | Connection string for database sources |

**Returns:** `Ok(DataSourceDTO)` — contains the system-generated `source_id`.

---

### `register_data_source_from_json`

```python
async def register_data_source_from_json(
    json_path: Optional[str] = None,
    json_string: Optional[str] = None,
    data: Optional[Dict] = None,
) -> Result[DataSourceDTO, Exception]
```

`POST /datasources` — Convenience wrapper to load the payload from a file, JSON string, or dict.

**Returns:** `Ok(DataSourceDTO)`.

---

### `list_data_sources`

```python
async def list_data_sources() -> Result[List[DataSourceDTO], Exception]
```

`GET /datasources` — Returns all registered data sources.

**Returns:** `Ok(List[DataSourceDTO])`.

---

### `get_data_source`

```python
async def get_data_source(source_id: str) -> Result[DataSourceDTO, Exception]
```

`GET /datasources/{id}` — Returns a single data source.

**Returns:** `Ok(DataSourceDTO)`.

---

### `update_data_source`

```python
async def update_data_source(
    source_id: str,
    dto: Union[DataSourceUpdateDTO, Dict],
) -> Result[DataSourceDTO, Exception]
```

`PUT /datasources/{id}` — Updates mutable fields on a data source. All fields are optional; omit any you do not want to change.

| Parameter | Type | Description |
|---|---|---|
| `source_id` | `str` | Target data source identifier |
| `dto` | `DataSourceUpdateDTO` or `dict` | Fields to update |

**`DataSourceUpdateDTO` fields** (all optional):

| Field | Type | Description |
|---|---|---|
| `name` | `str` | New human-readable name |
| `description` | `str` | New description |
| `connection_uri` | `str` | New database connection string |
| `bucket_id` | `str` | New MictlanX bucket identifier |

**Returns:** `Ok(DataSourceDTO)` — the updated data source.

```python
result = await client.update_data_source(
    "ds_abc",
    DTO.DataSourceUpdateDTO(name="Renamed Source"),
)
```

---

### `delete_data_source`

```python
async def delete_data_source(source_id: str) -> Result[DataSourceDeleteResponseDTO, Exception]
```

`DELETE /datasources/{id}` — Deletes a data source and all its records.

**Returns:** `Ok(DataSourceDeleteResponseDTO)` — contains `deleted: bool` and `records_removed: int`.

---

### `ingest_records`

```python
async def ingest_records(
    source_id: str,
    records: List[Union[DataRecordCreateDTO, Dict]],
) -> Result[IngestResponseDTO, Exception]
```

`POST /datasources/{id}/records` — Ingests a batch of data records.

| Parameter | Type | Description |
|---|---|---|
| `source_id` | `str` | Target data source |
| `records` | `List[DataRecordCreateDTO]` or `List[dict]` | Records to ingest |

**`DataRecordCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `record_id` | `str` | Yes | Unique identifier for this record |
| `spatial_id` | `str` | Yes | Catalog item ID for the spatial dimension |
| `temporal_id` | `str` | Yes | ISO 8601 datetime string for the temporal dimension |
| `interest_ids` | `List[str]` | No | Catalog item IDs for categorical dimensions |
| `numerical_interest_ids` | `Dict[str, float]` | No | Catalog item IDs mapped to numeric values |
| `raw_payload` | `Dict[str, Any]` | No | Arbitrary additional data |

**Returns:** `Ok(IngestResponseDTO)` — contains `inserted: int`.

---

### `ingest_records_from_json`

```python
async def ingest_records_from_json(
    source_id: str,
    json_path: Optional[str] = None,
    json_string: Optional[str] = None,
    data: Optional[List[Dict]] = None,
) -> Result[IngestResponseDTO, Exception]
```

`POST /datasources/{id}/records` — Loads records from a file, JSON string, or list of dicts and ingests them.

**Returns:** `Ok(IngestResponseDTO)`.

---

### `query_records`

```python
async def query_records(
    source_id: str,
    dto: DataSourceQueryDTO,
) -> Result[Any, Exception]
```

`POST /datasources/{id}/query` — Runs a JUB DSL query against the records of a data source.

| Parameter | Type | Description |
|---|---|---|
| `source_id` | `str` | Target data source |
| `dto` | `DataSourceQueryDTO` | Query payload |

**`DataSourceQueryDTO` fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | — | JUB DSL query string |
| `limit` | `int` | `100` | Maximum records to return |
| `skip` | `int` | `0` | Records to skip (pagination) |

**Returns:** `Ok(list of matching record dicts)`.

---

## Search

!!! info "JUB DSL"
    The search methods use the JUB Domain-Specific Language. Variables are prefixed by dimension:

    | Prefix | Dimension | Example |
    |---|---|---|
    | `VS` | Spatial | `VS(MX)` |
    | `VT` | Temporal | `VT(>= 2020)` |
    | `VI` | Interest | `VI(C_MAMA AND SEX_FEMALE)` |
    | `VO` | Observable | `VO(AVG(TASA_100K))` |
    | `BY` | Group by | `BY(CIE10_CANCER)` |

    Full example: `jub.v1.VS(MX).VT(>= 2020).VI(C_MAMA OR C_OVARIO)`

### `search`

```python
async def search(dto: SearchQueryDTO) -> Result[Any, Exception]
```

`POST /search` — Runs a JUB DSL query and returns hydrated product results.

**`SearchQueryDTO` fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | — | JUB DSL query string |
| `observatory_id` | `str` | `None` | Scope the search to a specific observatory |
| `limit` | `int` | `10` | Maximum results |
| `skip` | `int` | `0` | Pagination offset |

**Returns:** `Ok(list of product dicts)`.

```python
result = await client.search(DTO.SearchQueryDTO(
    query          = "jub.v1.VS(MX).VT(>= 2020).VI(C_MAMA)",
    observatory_id = "obs_cancer_mx_2024",
    limit          = 20,
))
```

---

### `search_records`

```python
async def search_records(dto: SearchQueryDTO) -> Result[Any, Exception]
```

`POST /search/records` — Runs a JUB DSL query and returns raw data records.

**Returns:** `Ok(list of data record dicts)`.

---

### `generate_plot`

```python
async def generate_plot(dto: PlotQueryDTO) -> Result[Any, Exception]
```

`POST /search/plot` — Runs a JUB DSL aggregation query and returns an ECharts-compatible JSON object.

**`PlotQueryDTO` fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | — | JUB DSL aggregation query (use `VO` and `BY`) |
| `observatory_id` | `str` | `None` | Optional observatory scope |
| `chart_type` | `str` | `"bar"` | ECharts chart type (`bar`, `line`, `pie`, etc.) |

**Returns:** `Ok(echarts_config_dict)`.

```python
result = await client.generate_plot(DTO.PlotQueryDTO(
    query      = "jub.v1.VS(MX).VI(C_MAMA OR C_OVARIO).VO(AVG(TASA_100K)).BY(CIE10_CANCER)",
    chart_type = "bar",
))
```

---

### `search_observatories`

```python
async def search_observatories(dto: SearchQueryDTO) -> Result[Any, Exception]
```

`POST /search/observatories` — Runs a JUB DSL query scoped to the observatory dimension.

**Returns:** `Ok(list of observatory dicts)`.

---

### `search_services`

```python
async def search_services(dto: ServiceQueryDTO) -> Result[List[ServiceDTO], Exception]
```

`POST /search/services` — Searches services using the JUB `SVC()` DSL operator.

**`ServiceQueryDTO` fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | — | Services DSL query (e.g. `jub.v1.SVC(name=cancer)`) |
| `limit` | `int` | `100` | Maximum results |
| `skip` | `int` | `0` | Pagination offset |

**SVC() examples:**

| Query | Meaning |
|---|---|
| `jub.v1.SVC(*)` | All services |
| `jub.v1.SVC(name=cancer)` | Name contains "cancer" |
| `jub.v1.SVC(public=true)` | Public services only |
| `jub.v1.SVC(owner=usr_abc)` | Services owned by user |

**Returns:** `Ok(List[ServiceDTO])`.

---

## Tasks

### `get_task_stats`

```python
async def get_task_stats() -> Result[TasksStatsDTO, Exception]
```

`GET /tasks/stats` — Returns background task counts grouped by status.

**Returns:** `Ok(TasksStatsDTO)` — contains `pending`, `running`, `success`, `failed` counts.

---

### `list_my_tasks`

```python
async def list_my_tasks(limit: int = 50) -> Result[List[TaskXDTO], Exception]
```

`GET /tasks` — Returns recent background tasks for the authenticated user.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | `int` | `50` | Maximum number of tasks to return |

**Returns:** `Ok(List[TaskXDTO])`.

---

### `get_task`

```python
async def get_task(task_id: str) -> Result[TaskXDTO, Exception]
```

`GET /tasks/{id}` — Returns details of a single background task.

**Returns:** `Ok(TaskXDTO)` — contains `task_id`, `operation`, `current_status`, `progress_message`, timestamps.

---

### `complete_task`

```python
async def complete_task(
    task_id: str,
    dto: Union[TaskCompleteDTO, Dict],
) -> Result[TaskCompleteResponseDTO, Exception]
```

`POST /tasks/{id}/complete` — Marks a background task as done. When `success=True`, the associated observatory is enabled.

| Parameter | Type | Description |
|---|---|---|
| `task_id` | `str` | Task to complete |
| `dto` | `TaskCompleteDTO` | Completion payload |

**`TaskCompleteDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `success` | `bool` | Yes | Whether the task completed successfully |
| `message` | `str` | No | Status or error message from the worker |

**Returns:** `Ok(TaskCompleteResponseDTO)` — contains `task_id`, `status`, `observatory_id`, `observatory_enabled`.

```python
result = await client.complete_task(task_id, DTO.TaskCompleteDTO(
    success = True,
    message = "Indexing complete.",
))
done = result.unwrap()
print("Observatory enabled:", done.observatory_enabled)
```

---

### `retry_task`

```python
async def retry_task(task_id: str) -> Result[bool, Exception]
```

`PUT /tasks/{id}/retry` — Retries a failed task (204 No Content).

**Returns:** `Ok(True)` on success.

---

## YAML Seed

### `create_from_code`

```python
async def create_from_code(
    file_path: Optional[str] = None,
    yaml_string: Optional[str] = None,
) -> Result[bool, Exception]
```

`POST /code` — Uploads a YAML file to seed the database with catalogs, observatories, and products in a single request. The YAML is validated against the `JubFile` Pydantic schema on the server.

| Parameter | Type | Description |
|---|---|---|
| `file_path` | `str` | Path to a `.yml` or `.yaml` file on disk |
| `yaml_string` | `str` | Raw YAML string to upload directly |

Provide exactly one of the two parameters.

**Returns:** `Ok(True)` on success.

```python
result = await client.create_from_code(file_path="xolo.yml")
```

---

## Notifications

### `list_notifications`

```python
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
) -> Result[List[NotificationDTO], Exception]
```

`GET /notifications` — Returns the current user's notifications.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `unread_only` | `bool` | `False` | When `True`, returns only unread notifications |
| `limit` | `int` | `50` | Maximum notifications to return |

**Returns:** `Ok(List[NotificationDTO])`.

---

### `mark_notification_read`

```python
async def mark_notification_read(notification_id: str) -> Result[bool, Exception]
```

`PUT /notifications/{id}/read` — Marks a single notification as read (204 No Content).

**Returns:** `Ok(True)` on success.

---

### `mark_all_notifications_read`

```python
async def mark_all_notifications_read() -> Result[NotificationReadAllResponseDTO, Exception]
```

`PUT /notifications/read-all` — Marks all unread notifications as read.

**Returns:** `Ok(NotificationReadAllResponseDTO)` — contains `modified: int`.

---

### `clear_read_notifications`

```python
async def clear_read_notifications() -> Result[NotificationClearReadResponseDTO, Exception]
```

`DELETE /notifications/clear-read` — Deletes all previously read notifications.

**Returns:** `Ok(NotificationClearReadResponseDTO)` — contains `deleted: int`.

---

## Building Blocks

### `create_building_block`

```python
async def create_building_block(
    dto: Union[BuildingBlockCreateDTO, Dict],
) -> Result[BuildingBlockDTO, Exception]
```

`POST /building-blocks` — Creates a containerised unit of work.

**`BuildingBlockCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Human-readable identifier |
| `command` | `str` | Yes | Entrypoint command executed inside the container |
| `image` | `str` | Yes | Docker image reference (e.g. `python:3.11-slim`) |
| `description` | `str` | No | Contextual description |

**Returns:** `Ok(BuildingBlockDTO)`.

---

### `list_building_blocks`

```python
async def list_building_blocks(skip: int = 0, limit: int = 100) -> Result[List[BuildingBlockDTO], Exception]
```

`GET /building-blocks` — Returns a paginated list of building blocks.

**Returns:** `Ok(List[BuildingBlockDTO])`.

---

### `get_building_block`

```python
async def get_building_block(building_block_id: str) -> Result[BuildingBlockDTO, Exception]
```

`GET /building-blocks/{id}` — Returns a single building block.

**Returns:** `Ok(BuildingBlockDTO)`.

---

### `update_building_block`

```python
async def update_building_block(
    building_block_id: str,
    dto: Union[BuildingBlockUpdateDTO, Dict],
) -> Result[BuildingBlockDTO, Exception]
```

`PATCH /building-blocks/{id}` — Updates mutable fields on a building block.

**`BuildingBlockUpdateDTO` fields** (all optional):

| Field | Type | Description |
|---|---|---|
| `name` | `str` | New identifier |
| `command` | `str` | New entrypoint command |
| `image` | `str` | New Docker image |
| `description` | `str` | New description |

**Returns:** `Ok(BuildingBlockDTO)`.

---

### `delete_building_block`

```python
async def delete_building_block(building_block_id: str) -> Result[bool, Exception]
```

`DELETE /building-blocks/{id}` — Deletes a building block (204 No Content).

**Returns:** `Ok(True)` on success.

---

## Patterns

### `create_pattern`

```python
async def create_pattern(
    dto: Union[PatternCreateDTO, Dict],
) -> Result[PatternDTO, Exception]
```

`POST /patterns` — Creates an execution pattern for a building block.

**`PatternCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Human-readable pattern name |
| `task` | `str` | Yes | Task category (e.g. `transform`, `ingest`) |
| `pattern` | `str` | Yes | Pattern type (e.g. `map-reduce`, `pipeline`) |
| `description` | `str` | No | Contextual description |
| `workers` | `int` | No | Number of parallel worker instances (default `1`) |
| `loadbalancer` | `str` | No | Load-balancing strategy (default `round-robin`) |
| `building_block_id` | `str` | No | ID of an existing building block to associate |

**Returns:** `Ok(PatternDTO)`.

---

### `list_patterns`

```python
async def list_patterns(skip: int = 0, limit: int = 100) -> Result[List[PatternDTO], Exception]
```

`GET /patterns` — Returns a paginated list of patterns.

**Returns:** `Ok(List[PatternDTO])`.

---

### `get_pattern`

```python
async def get_pattern(pattern_id: str) -> Result[PatternDTO, Exception]
```

`GET /patterns/{id}` — Returns a single pattern.

**Returns:** `Ok(PatternDTO)`.

---

### `update_pattern`

```python
async def update_pattern(
    pattern_id: str,
    dto: Union[PatternUpdateDTO, Dict],
) -> Result[PatternDTO, Exception]
```

`PATCH /patterns/{id}` — Updates mutable fields on a pattern. All `PatternUpdateDTO` fields are optional.

**Returns:** `Ok(PatternDTO)`.

---

### `delete_pattern`

```python
async def delete_pattern(pattern_id: str) -> Result[bool, Exception]
```

`DELETE /patterns/{id}` — Deletes a pattern (204 No Content).

**Returns:** `Ok(True)` on success.

---

## Stages

### `create_stage`

```python
async def create_stage(
    dto: Union[StageCreateDTO, Dict],
) -> Result[StageDTO, Exception]
```

`POST /stages` — Creates a processing step (source → transformation → sink).

**`StageCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Stage name |
| `source` | `str` | Yes | Input source identifier or URI |
| `sink` | `str` | Yes | Output sink identifier or URI |
| `endpoint` | `str` | Yes | HTTP or messaging endpoint exposed by this stage |
| `transformation_id` | `str` | No | ID of an existing Pattern to apply |

**Returns:** `Ok(StageDTO)`.

---

### `list_stages`

```python
async def list_stages(skip: int = 0, limit: int = 100) -> Result[List[StageDTO], Exception]
```

`GET /stages` — Returns a paginated list of stages.

**Returns:** `Ok(List[StageDTO])`.

---

### `get_stage`

```python
async def get_stage(stage_id: str) -> Result[StageDTO, Exception]
```

`GET /stages/{id}` — Returns a single stage.

**Returns:** `Ok(StageDTO)`.

---

### `update_stage`

```python
async def update_stage(
    stage_id: str,
    dto: Union[StageUpdateDTO, Dict],
) -> Result[StageDTO, Exception]
```

`PATCH /stages/{id}` — Updates mutable fields on a stage. All `StageUpdateDTO` fields are optional.

**Returns:** `Ok(StageDTO)`.

---

### `delete_stage`

```python
async def delete_stage(stage_id: str) -> Result[bool, Exception]
```

`DELETE /stages/{id}` — Deletes a stage (204 No Content).

**Returns:** `Ok(True)` on success.

---

## Workflows

### `create_workflow`

```python
async def create_workflow(
    dto: Union[WorkflowCreateDTO, Dict],
) -> Result[WorkflowDTO, Exception]
```

`POST /workflows` — Creates a workflow from an ordered list of stages.

**`WorkflowCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Workflow name |
| `stage_ids` | `List[str]` | No | Ordered list of stage IDs |

**Returns:** `Ok(WorkflowDTO)`.

---

### `list_workflows`

```python
async def list_workflows(skip: int = 0, limit: int = 100) -> Result[List[WorkflowDTO], Exception]
```

`GET /workflows` — Returns a paginated list of workflows.

**Returns:** `Ok(List[WorkflowDTO])`.

---

### `get_workflow`

```python
async def get_workflow(workflow_id: str) -> Result[WorkflowDTO, Exception]
```

`GET /workflows/{id}` — Returns a single workflow.

**Returns:** `Ok(WorkflowDTO)`.

---

### `update_workflow`

```python
async def update_workflow(
    workflow_id: str,
    dto: Union[WorkflowUpdateDTO, Dict],
) -> Result[WorkflowDTO, Exception]
```

`PATCH /workflows/{id}` — Updates mutable fields on a workflow. All `WorkflowUpdateDTO` fields are optional.

**Returns:** `Ok(WorkflowDTO)`.

---

### `delete_workflow`

```python
async def delete_workflow(
    workflow_id: str,
    cascade: bool = False,
) -> Result[WorkflowDeleteResponseDTO, Exception]
```

`DELETE /workflows/{id}` — Deletes a workflow. When `cascade=True`, also deletes all linked stages.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `workflow_id` | `str` | — | Target workflow |
| `cascade` | `bool` | `False` | Also delete linked stages when `True` |

**Returns:** `Ok(WorkflowDeleteResponseDTO)` — contains `deleted: bool` and `cascade: Dict`.

---

## Services

### `create_service`

```python
async def create_service(
    dto: Union[ServiceCreateDTO, Dict],
) -> Result[ServiceDTO, Exception]
```

`POST /services` — Creates a service with an optional workflow reference.

**`ServiceCreateDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Service name (searchable via `SVC()`) |
| `owner_id` | `str` | Yes | User ID of the service owner |
| `description` | `str` | No | Contextual description |
| `public` | `bool` | No | Whether the service is publicly discoverable (default `False`) |
| `workflow_id` | `str` | No | ID of an existing workflow to attach |
| `provider` | `ServiceProviderEnum` | No | Provider classification |

**Returns:** `Ok(ServiceDTO)`.

---

### `index_service`

```python
async def index_service(
    dto: Union[ServiceIndexDTO, Dict],
) -> Result[ServiceIndexResponseDTO, Exception]
```

`POST /services/index` — One-shot endpoint that creates the full **Service → Workflow → Stages → Patterns → Building Blocks** tree in a single request.

**`ServiceIndexDTO` fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Service name |
| `owner_id` | `str` | Yes | User ID of the service owner |
| `description` | `str` | No | Contextual description |
| `public` | `bool` | No | Publicly discoverable (default `False`) |
| `workflow` | `WorkflowInlineDTO` | No | Inline workflow to create (mutually exclusive with `workflow_id`) |
| `workflow_id` | `str` | No | Existing workflow to attach |
| `provider` | `ServiceProviderEnum` | No | Provider classification |

**Inline DTO hierarchy:**

```
ServiceIndexDTO
└── WorkflowInlineDTO
    └── List[StageInlineDTO]
        └── PatternInlineDTO (optional)
            └── BuildingBlockInlineDTO (optional)
```

At each level you can provide inline definitions or reference existing IDs.

**Returns:** `Ok(ServiceIndexResponseDTO)` — contains `service_id`, `workflow_id`, `stage_ids`, `pattern_ids`, `building_block_ids`.

---

### `list_services`

```python
async def list_services(skip: int = 0, limit: int = 100) -> Result[List[ServiceDTO], Exception]
```

`GET /services` — Returns a paginated list of services.

**Returns:** `Ok(List[ServiceDTO])`.

---

### `get_service`

```python
async def get_service(service_id: str) -> Result[ServiceDTO, Exception]
```

`GET /services/{id}` — Returns a single service.

**Returns:** `Ok(ServiceDTO)`.

---

### `update_service`

```python
async def update_service(
    service_id: str,
    dto: Union[ServiceUpdateDTO, Dict],
) -> Result[ServiceDTO, Exception]
```

`PATCH /services/{id}` — Updates mutable fields on a service. All `ServiceUpdateDTO` fields are optional.

**Returns:** `Ok(ServiceDTO)`.

---

### `delete_service`

```python
async def delete_service(service_id: str) -> Result[ServiceDeleteResponseDTO, Exception]
```

`DELETE /services/{id}` — Deletes a service and returns a cascade summary.

**Returns:** `Ok(ServiceDeleteResponseDTO)` — contains `deleted: bool`, `service_id`, and `cascade: Dict`.

---

## Response models reference

| Model | Returned by |
|---|---|
| `AuthResponseDTO` | `signup()` |
| `UserProfileDTO` | `get_current_user()` |
| `UserPreferencesDTO` | `get_user_settings()`, `update_user_settings()` |
| `CatalogCreatedResponseDTO` | `create_catalog()`, `create_catalog_from_json()` |
| `CatalogCreatedBulkResponseDTO` | `create_bulk_catalogs_from_json()` |
| `CatalogSummaryDTO` | `list_catalogs()` |
| `CatalogResponseDTO` | `get_catalog()` |
| `CatalogXDTO` | `list_observatory_catalogs()`, `list_catalogs_for_item()` |
| `CatalogItemXResponseDTO` | `create_catalog_item()`, `get_catalog_item()`, `list_catalog_items()`, `update_catalog_item()`, `get_product_tag_details()` |
| `CatalogItemDeleteResponseDTO` | `delete_catalog_item()` |
| `CatalogItemAliasXResponseDTO` | `list_catalog_item_aliases()`, `add_catalog_item_alias()` |
| `CatalogItemChildLinkResponseDTO` | `link_catalog_item_child()` |
| `CatalogItemCatalogLinkResponseDTO` | `link_item_to_catalog()` |
| `ItemProductsDTO` | `list_products_for_item()` |
| `ObservatoryXDTO` | `create_observatory()`, `get_observatory()`, `list_observatories()`, `update_observatory()` |
| `ObservatorySetupResponseDTO` | `setup_observatory()` |
| `ObservatoryDeleteResponseDTO` | `delete_observatory()` |
| `ObservatoryCatalogLinkResponseDTO` | `link_catalog_to_observatory()` |
| `ObservatoryProductLinkResponseDTO` | `link_product_to_observatory()` |
| `BulkCatalogsResponseDTO` | `bulk_assign_catalogs()` |
| `BulkProductsResponseDTO` | `bulk_assign_products()` |
| `ProductSimpleDTO` | `create_product()`, `get_product()`, `list_products()`, `update_product()`, `list_observatory_products()` |
| `ProductDeleteResponseDTO` | `delete_product()` |
| `ProductTagsResponseDTO` | `get_product_tags()`, `add_product_tags()` |
| `ProductUploadResponseDTO` | `upload_product()` |
| `DataSourceDTO` | `register_data_source()`, `get_data_source()`, `list_data_sources()` |
| `DataSourceDeleteResponseDTO` | `delete_data_source()` |
| `IngestResponseDTO` | `ingest_records()`, `ingest_records_from_json()` |
| `TasksStatsDTO` | `get_task_stats()` |
| `TaskXDTO` | `get_task()`, `list_my_tasks()` |
| `TaskCompleteResponseDTO` | `complete_task()` |
| `NotificationDTO` | `list_notifications()` |
| `NotificationReadAllResponseDTO` | `mark_all_notifications_read()` |
| `NotificationClearReadResponseDTO` | `clear_read_notifications()` |
| `BuildingBlockDTO` | `create_building_block()`, `get_building_block()`, `list_building_blocks()`, `update_building_block()` |
| `PatternDTO` | `create_pattern()`, `get_pattern()`, `list_patterns()`, `update_pattern()` |
| `StageDTO` | `create_stage()`, `get_stage()`, `list_stages()`, `update_stage()` |
| `WorkflowDTO` | `create_workflow()`, `get_workflow()`, `list_workflows()`, `update_workflow()` |
| `WorkflowDeleteResponseDTO` | `delete_workflow()` |
| `ServiceDTO` | `create_service()`, `get_service()`, `list_services()`, `update_service()`, `search_services()` |
| `ServiceIndexResponseDTO` | `index_service()` |
| `ServiceDeleteResponseDTO` | `delete_service()` |

---

## Legacy client (v1)

!!! warning "Deprecated"
    The v1 client is **unmaintained**. All new development should use `jub.client.v2`.

The v1 client lives at `jub/client/v1/__init__.py` and uses the synchronous `requests` library. It targets an older API that embeds catalogs and products directly inside the Observatory model.

```python
from jub.client.v1 import JubClient  # legacy

client = JubClient(api_url="http://localhost:5000")
result = client.create_observatory(observatory=obs)
```

Key differences from v2:

| Area | v1 | v2 |
|---|---|---|
| I/O model | Synchronous (`requests`) | Async (`httpx`) |
| Authentication | Not built-in | JWT stored on `authenticate()` |
| Relationships | Embedded in Observatory | Separate link endpoints |
| Return type | `Result[T, Exception]` | `Result[T, Exception]` |
| API version | `/api/v1` | `/api/v2` |

Migrate to v2 by replacing `from jub.client.v1 import JubClient` with `from jub.client.v2 import JubClient` and converting all call sites to `async/await`.
