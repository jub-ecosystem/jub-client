from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from jub.enums import ServiceProviderEnum

"""
DTOs for the JUB API v2.

These models mirror the request/response contracts defined in the JUB API.
Domain models (Observatory, Catalog, etc.) represent response data.
DTO classes (ObservatoryCreateDTO, etc.) represent request payloads.
"""


# ── Domain models ──────────────────────────────────────────────


class Observatory(BaseModel):
    """
    Represents an observatory in the JUB domain.

    Unlike the V1 model, this does not contain direct references to catalogs.
    Relationships are represented through ObservatoryCatalogLink.
    """

    obid: str = Field("", description="Unique identifier of the observatory.")
    title: str = Field("Observatory", description="Display name of the observatory.")
    image_url: str = Field("", description="URL of an image representing the observatory.")
    description: str = Field("", description="Textual description providing context.")
    disabled: bool = Field(False, description="Whether the observatory is inactive.")


class Catalog(BaseModel):
    """
    Represents a catalog in the JUB domain.

    This version removes the embedded items collection.
    Relationships between catalogs and items are expressed via CatalogItemLink.
    """

    cid: str = Field("", description="Unique identifier of the catalog.")
    display_name: str = Field("", description="Human-readable name of the catalog.")
    kind: str = Field("", description="Type of the catalog (e.g. TEMPORAL, SPATIAL, INTEREST).")

    @field_validator("display_name")
    def remove_double_spaces(cls, value):
        """Normalizes display_name by collapsing consecutive whitespace into a single space."""
        return " ".join(value.split())


class CatalogItem(BaseModel):
    """
    Represents an item within a catalog.

    This model is no longer attached to the Catalog model directly.
    Relationships are now represented through CatalogItemLink.
    """

    item_id: str = Field(..., description="Unique identifier of the catalog item.")
    value: str = Field(..., description="Value used for storage and querying.")
    display_name: str = Field(..., description="Human-readable name for the catalog item.")
    code: int = Field(..., description="Unique numeric code identifying the catalog item.")
    description: str = Field(..., description="Textual description providing context.")
    metadata: Dict[str, str] = Field(..., description="Extra key-value data providing context about the item.")

    @field_validator("display_name")
    def remove_double_spaces(cls, value):
        """Normalizes display_name by collapsing consecutive whitespace into a single space."""
        return " ".join(value.split())


class Product(BaseModel):
    """
    Represents a product in the JUB domain.

    This version removes the levels field used in V1 for catalog references.
    """

    pid: str = Field("", description="Product unique identifier.")
    description: str = Field("", description="Textual description of the product.")
    product_type: str = Field("", description="Category of the product.")
    product_name: str = Field("", description="Display name of the product.")
    tags: List[str] = Field(default_factory=list, description="Tags for permission control and filtering.")
    url: str = Field("", description="Path to the product in the application.")


# ── Link models ────────────────────────────────────────────────


class ObservatoryCatalogLink(BaseModel):
    """Represents the relationship between an Observatory and a Catalog."""

    obid: str = Field(..., description="Unique identifier of the observatory.")
    cid: str = Field(..., description="Unique identifier of the catalog.")


class CatalogItemLink(BaseModel):
    """Represents the relationship between a Catalog and a CatalogItem."""

    cid: str = Field(..., description="Unique identifier of the catalog.")
    item_id: str = Field(..., description="Unique identifier of the catalog item.")


class ProductObservatoryLink(BaseModel):
    """Represents the relationship between a Product and an Observatory."""

    pid: str = Field(..., description="Unique identifier of the product.")
    obid: str = Field(..., description="Unique identifier of the observatory.")


class ProductCatalogItemLink(BaseModel):
    """Represents the relationship between a Product and a CatalogItem."""

    pid: str = Field(..., description="Unique identifier of the product.")
    item_id: str = Field(..., description="Unique identifier of the catalog item.")
    kind: str = Field(..., description="The kind of the level (SPATIAL, TEMPORAL, INTEREST, etc.).")


# ── User DTOs ──────────────────────────────────────────────────


class SignUpDTO(BaseModel):
    """Payload for creating a new user account."""

    username: str = Field(..., description="Unique login handle.")
    first_name: str = Field("", description="Optional first name of the user.")  # Example of using Field for description
    last_name: str = Field("", description="Optional last name of the user.")  # Example of using Field for description
    email: str = Field(..., description="User email address.")
    password: str = Field(..., description="Plain-text password (transmitted over HTTPS only).")
    profile_photo:str = Field("", description="Optional URL of the user's profile photo.")
    scope: Optional[str] = Field("jub", description="Optional scope of the user's access (e.g. 'admin', 'analyst').")
    expiration: Optional[str] = Field("1y", description="Optional ISO 8601 datetime string indicating when the user's access expires.")


class AuthAttemptDTO(BaseModel):
    """Payload for POST /users/auth."""

    username: str = Field(..., description="Account login handle.")
    password: str = Field(..., description="Plain-text password.")
    scope: str = Field("jub", description="JWT token scope.")
    expiration: Optional[str] = Field("1h", description="Requested token lifetime (e.g. 1h, 30m).")
    renew_token: Optional[bool] = Field(False, description="Whether the server should issue a renewable token.")


class AppearanceSettingsDTO(BaseModel):
    """User appearance preferences."""

    theme: str = Field("light", description="UI theme (light, dark, system).")
    font_size: int = Field(14, description="Base font size in pixels.")
    reduce_animations: bool = Field(False, description="Whether to disable UI animations.")


class ExplorationSettingsDTO(BaseModel):
    """User exploration preferences."""

    enable_tutorial: bool = Field(True, description="Whether to show onboarding tutorials.")
    default_view: str = Field("list", description="Default layout view (list, grid).")
    items_per_page: int = Field(12, description="Number of items shown per page.")


class ExportSettingsDTO(BaseModel):
    """User export preferences."""

    default_format: str = Field("yml", description="Default export format (json, yml).")
    include_metadata: bool = Field(True, description="Whether to include metadata in exports.")


class UserPreferencesDTO(BaseModel):
    """Aggregated user preferences payload for PUT /users/{user_id}/settings."""

    appearance: AppearanceSettingsDTO = Field(default_factory=AppearanceSettingsDTO, description="Visual appearance settings.")
    exploration: ExplorationSettingsDTO = Field(default_factory=ExplorationSettingsDTO, description="Data exploration settings.")
    export: ExportSettingsDTO = Field(default_factory=ExportSettingsDTO, description="Data export settings.")


# ── Catalog DTOs ───────────────────────────────────────────────

class CatalogUpdateDTO(BaseModel):
    """
    Payload for PUT /catalogs/{catalog_id}.

    All fields are optional; only provided fields are updated.
    """
    name: Optional[str] = Field(default=None, description="Updated catalog name")
    description: Optional[str] = Field(default=None, description="Updated description")

class CatalogItemAliasCreateDTO(BaseModel):
    """Payload for creating an alias for a catalog item."""
    alias_id: Optional[str] = Field(None, description="Optional pre-defined ID for the catalog item alias. If not provided, a random UUID is generated.")
    value: str = Field(..., description="The alias value string.")
    value_type: str = Field(..., description="Type of the alias value (STRING, NUMBER, BOOLEAN, DATETIME).")
    description: str = Field("", description="Optional description for the alias.")

class CatalogItemCreateDTO(BaseModel):
    """
    Payload for creating a catalog item within a new catalog.

    This model is recursive to support hierarchical catalog structures.
    """

    catalog_item_id:Optional[str] = Field(None, description="Optional pre-defined ID for the catalog item. If not provided, a random UUID is generated.")
    name: str = Field(..., description="Human-readable display name.")
    value: str = Field(..., description="Stored value used in queries (typically UPPER_SNAKE_CASE).")
    code: int = Field(..., description="Numeric code uniquely identifying the item.")
    value_type: str = Field(..., description="Data type of the value (STRING, NUMBER, BOOLEAN, DATETIME).")
    description: Optional[str] = Field("", description="Optional description providing context about the catalog item.")
    temporal_value: Optional[str] = Field(None, description="Optional ISO 8601 datetime string for temporal items.")
    aliases: List[CatalogItemAliasCreateDTO] = Field(default_factory=list, description="List of alternative names or codes for this item.")
    children: List["CatalogItemCreateDTO"] = Field(default_factory=list, description="Nested child items for hierarchical catalogs.")

    model_config = {"populate_by_name": True}


CatalogItemCreateDTO.model_rebuild()


class CatalogCreateDTO(BaseModel):
    """Payload for POST /catalogs."""

    catalog_id:Optional[str] = Field(None, description="Optional pre-defined ID for the catalog. If not provided, a random UUID is generated.")
    name: str = Field(..., description="Human-readable name of the catalog.")
    value: str = Field(..., description="Stored value used in queries (UPPER_SNAKE_CASE).")
    catalog_type: str = Field(..., description="Classification of the catalog (SPATIAL, TEMPORAL, INTEREST, etc.).")
    description: str = Field("", description="Optional description providing context.")
    items: List[CatalogItemCreateDTO] = Field(default_factory=list, description="List of catalog items to create together with the catalog.")


class CatalogItemStandaloneCreateDTO(BaseModel):
    """Payload for POST /catalog-items (standalone creation outside catalog bulk flow)."""

    catalog_item_id: Optional[str] = Field(None, description="Optional pre-defined ID for the catalog item. If not provided, a random UUID is generated.")
    catalog_id: str = Field(..., description="ID of the catalog this item belongs to.")
    name: str = Field(..., description="Human-readable display name.")
    value: str = Field(..., description="Stored value used in queries.")
    code: int = Field(..., description="Numeric code uniquely identifying the item.")
    value_type: str = Field(..., description="Data type of the value (STRING, NUMBER, BOOLEAN, DATETIME).")
    description: str = Field("", description="Optional description providing context about the catalog item.")
    temporal_value: Optional[str] = Field(None, description="Optional ISO 8601 datetime string for temporal items.")
    parent_item_id: Optional[str] = Field(None, description="Optional ID of a parent item for hierarchical placement. If provided, this item will be linked as a child to the specified parent item.")
    catalog_type: Optional[str] = Field(None, description="Optional catalog type of the item (INTEREST, TEMPORAL, SPATIAL, OBSERVABLE, REFERENCE).")
    metadata: Optional[Dict[str, str]] = Field(None, description="Optional string key-value metadata.")


class CatalogItemUpdateDTO(BaseModel):
    """
    Payload for PUT /catalog-items/{catalog_item_id}.

    All fields are optional; only provided fields are updated.
    """

    name: Optional[str] = Field(None, description="New display name.")
    description: Optional[str] = Field(None, description="New description.")
    temporal_value: Optional[str] = Field(None, description="New ISO 8601 datetime string.")


class CatalogItemChildLinkCreateDTO(BaseModel):
    """Payload for POST /catalog-items/{id}/children."""
    child_item_id: str = Field(..., description="ID of the catalog item to link as a child of the item in the URL.")


class CatalogItemCatalogLinkCreateDTO(BaseModel):
    """Payload for POST /catalog-items/{id}/catalogs."""
    catalog_id: str = Field(..., description="ID of the catalog the item in the URL is linked into.")


# ── DataSource DTOs ────────────────────────────────────────────


class DataSourceCreateDTO(BaseModel):
    """Payload for POST /datasources."""

    source_id: Optional[str] = Field(None, description="Optional pre-defined ID for the data source. If not provided, one is generated.")
    name: str = Field(..., description="Human-readable name for the data source.")
    description: str = Field("", description="Optional description.")
    format: str = Field("csv", description="Data format (csv, json, postgres, mysql, mongodb).")
    bucket_id: Optional[str] = Field(None, description="Optional MictlanX bucket identifier.")
    connection_uri: Optional[str] = Field(None, description="Optional connection string for database sources.")


class DataSourceDTO(BaseModel):
    """Response model for a registered data source."""

    source_id: Optional[str] = Field(None, description="System-generated unique identifier.")
    name: str = Field(..., description="Human-readable name.")
    description: str = Field(default="", description="Optional description.")
    format: str = Field(..., description="Data format type.")
    bucket_id: Optional[str] = Field(default=None, description="Optional MictlanX bucket identifier.")
    connection_uri: Optional[str] = Field(default=None, description="Optional connection string.")


class DataRecordCreateDTO(BaseModel):
    """A single data record to ingest via POST /datasources/{source_id}/records."""

    record_id: str = Field(..., description="Unique identifier for this record.")
    spatial_id: str = Field(..., description="Catalog item ID for the spatial dimension.")
    temporal_id: str = Field(..., description="ISO 8601 datetime string for the temporal dimension.")
    interest_ids: List[str] = Field(default_factory=list, description="List of catalog item IDs for interest dimensions.")
    numerical_interest_ids: Dict[str, float] = Field(default_factory=dict, description="Map of catalog item IDs to numeric values.")
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary additional data stored with the record.")


class DataSourceQueryDTO(BaseModel):
    """Payload for POST /datasources/{source_id}/query."""

    query: str = Field(..., description="JUB DSL query string.")
    limit: int = Field(100, description="Maximum number of records to return.")
    skip: int = Field(0, description="Number of records to skip for pagination.")


# ── Observatory DTOs ───────────────────────────────────────────
class ServiceSnapshotDTO(BaseModel):
    """Lightweight service summary embedded in observatory responses."""
    service_id: str = Field(..., description="Unique identifier of the service.")
    name: str = Field(..., description="Display name of the service.")
    provider: Optional[str] = Field(None, description="Provider classification (see ServiceProviderEnum), if any.")
class DataSourceSnapshotDTO(BaseModel):
    """Lightweight data source summary embedded in observatory responses."""
    source_id: str = Field(..., description="Unique identifier of the data source.")
    name: str = Field(..., description="Display name of the data source.")
class ObservatoryStatsDTO(BaseModel):
    """Per-observatory stats returned by POST /observatories/details."""
    observatory_id: str = Field(..., description="ID of the observatory these stats belong to.")
    avg_rating: float = Field(default=0.0, description="Average user rating, from 0.0 to 5.0.")
    review_count: int = Field(default=0, description="Total number of user reviews.")
    services: List[ServiceSnapshotDTO] = Field(default_factory=list, description="Services linked to the observatory.")
    data_sources: List[DataSourceSnapshotDTO] = Field(default_factory=list, description="Data sources linked to the observatory.")

class ObservatoryXDTO(BaseModel):
    """Response for create / get / update / list observatories."""
    observatory_id: str = Field(..., description="Unique identifier of the observatory.")
    title: str = Field(..., description="Display name of the observatory.")
    description: str = Field("", description="Textual description providing context.")
    image_url: Optional[str] = Field(None, description="URL of a representative image, if any.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary key-value metadata.")
    is_disabled: bool = Field(False, description="Whether the observatory is disabled (hidden from regular users).")
    view_count: int = Field(0, description="Number of times the observatory has been viewed.")
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")
    updated_at: str = Field(..., description="ISO 8601 last-update timestamp.")
    
class ObservatoryDetailDTO(ObservatoryXDTO):
    """
    Response for GET /observatories/{id}.

    Adds linked services, data sources and rating data to the base observatory fields.
    """
    services: List[ServiceSnapshotDTO] = Field(default_factory=list, description="Services linked to the observatory.")
    data_sources: List[DataSourceSnapshotDTO] = Field(default_factory=list, description="Data sources linked to the observatory.")
    avg_rating: float = Field(default=0.0, description="Average user rating for this observatory, from 0.0 to 5.0")
    review_count: int = Field(default=0, description="Total number of user reviews for this observatory")


class ObservatoryCreateDTO(BaseModel):
    """Payload for POST /observatories (immediate creation, enabled by default)."""

    observatory_id:Optional[str] = Field(None, description="Optional pre-defined ID for the observatory. If not provided, a random UUID is generated.")
    title: str = Field(..., description="Display name of the observatory.")
    description: str = Field("", description="Optional description providing context.")
    image_url: str = Field("", description="Optional URL of a representative image.")
    metadata: Optional[Dict[str, str]] = Field(None, description="Optional string key-value metadata.")


class ObservatoryUpdateDTO(BaseModel):
    """
    Payload for PUT /observatories/{observatory_id}.

    All fields are optional; only provided fields are updated.
    """

    title: Optional[str] = Field(None, description="New display name.")
    description: Optional[str] = Field(None, description="New description.")
    image_url: Optional[str] = Field(None, description="New image URL.")
    metadata: Optional[Dict[str, str]] = Field(None, description="New string key-value metadata.")


class ObservatorySetupDTO(BaseModel):
    """
    Payload for POST /observatories/setup.

    Creates a disabled observatory and queues a background setup task.
    The observatory is enabled only when the task completes successfully
    via POST /tasks/{task_id}/complete.
    """

    observatory_id: Optional[str] = Field(None, description="Optional pre-defined ID for the observatory. If not provided, a random UUID is generated.")
    title: str = Field(..., description="Display name of the observatory.")
    description: str = Field("",description="Optional description providing context about the observatory.")
    image_url: str = Field("",description="Optional URL of a representative image.")
    metadata:Dict[str,str] = Field(default_factory=dict, description="Optional metadata for the observatory.")
    # user_id: 


class LinkCatalogDTO(BaseModel):
    """Payload for POST /observatories/{observatory_id}/catalogs."""

    catalog_id: str = Field(..., description="ID of the catalog to link.")
    level: int = Field(0, description="Display order level for the catalog in the UI.")


class LinkProductDTO(BaseModel):
    """Payload for POST /observatories/{observatory_id}/products."""

    product_id: str = Field(..., description="ID of the product to link.")


class BulkCatalogsDTO(BaseModel):
    """
    Payload for POST /observatories/{observatory_id}/catalogs/bulk.

    Creates multiple catalogs and links each to the observatory in one request.
    """

    catalogs: List[CatalogCreateDTO] = Field(default_factory=list, description="List of catalog creation payloads.")

class BulkCatalogsResponseDTO(BaseModel):
    """Response for POST /observatories/{id}/catalogs/bulk and POST /catalogs/bulk/{id}/link."""
    observatory_id: str = Field(..., description="ID of the observatory the catalogs were assigned to.")
    catalog_ids: List[str] = Field(default_factory=list, description="List of catalog IDs that were assigned to the observatory.")

class BulkProductItemDTO(BaseModel):
    """
    Item inside a BulkProductsDTO request.

    The observatory is taken from the URL, so no observatory_id is needed.
    """
    product_id: Optional[str] = Field(None, description="Optional pre-defined ID (A-Z a-z 0-9 _ . -); generated when omitted.")
    name: str = Field(..., description="Display name of the product.")
    description: str = Field("", description="Optional textual description.")
    catalog_item_ids: List[str] = Field(default_factory=list, description="Catalog item IDs to tag the product with.")

class BulkProductCreatedDTO(BaseModel):
    """A product created by a bulk product request."""
    product_id: str = Field(..., description="ID of the created product.")
    name: str = Field(..., description="Display name of the created product.")

class BulkProductsResponseDTO(BaseModel):
    """Response for POST /observatories/{id}/products/bulk."""
    observatory_id: str = Field(..., description="ID of the observatory the products were linked to.")
    products: List[BulkProductCreatedDTO] = Field(default_factory=list, description="The products that were created.")

# ── Product DTOs ───────────────────────────────────────────────


class ProductCreateDTO(BaseModel):
    """Payload for POST /products."""

    product_id: Optional[str] = Field(None, description="Optional pre-defined ID for the product. If not provided, a random UUID is generated.")
    name: str = Field(..., description="Display name of the product.")
    description: str = Field("", description="Optional textual description providing context about the product.")
    observatory_id: str = Field(..., description="ID of the observatory this product belongs to.")
    catalog_item_ids: List[str] = Field(default_factory=list, description="List of catalog item IDs to tag this product with.")
    metadata: Optional[Dict[str, str]] = Field(None, description="Optional string key-value metadata.")


class ProductUpdateDTO(BaseModel):
    """
    Payload for PUT /products/{product_id}.

    All fields are optional; only provided fields are updated.
    """

    name: Optional[str] = Field(None, description="New display name.")
    description: Optional[str] = Field(None, description="New description.")
    metadata: Optional[Dict[str, str]] = Field(None, description="New string key-value metadata.")


class TagProductDTO(BaseModel):
    """Payload for POST /products/{product_id}/tags."""

    catalog_item_ids: List[str] = Field(default_factory=list, description="List of catalog item IDs to associate with the product.")


class BulkProductsDTO(BaseModel):
    """Payload for POST /observatories/{observatory_id}/products/bulk."""

    products: List[Union[BulkProductItemDTO, ProductCreateDTO]] = Field(default_factory=list, description="Products to create and link to the observatory. Each entry may be a BulkProductItemDTO or a full ProductCreateDTO.")


# ── Search DTOs ────────────────────────────────────────────────


class SearchQueryDTO(BaseModel):
    """
    Payload for POST /search, /search/records, and /search/observatories.

    The query field uses the JUB DSL (see Query Language section in CLAUDE.md).
    """

    query: str = Field(..., description="JUB DSL query string (e.g. jub.v1.VS(MX).VT(>= 2020).VI(SEX_FEMALE)).")
    observatory_id: Optional[str] = Field(None, description="Optional observatory ID to scope the search.")
    limit: int = Field(10, description="Maximum number of results to return.")
    skip: int = Field(0, description="Number of results to skip for pagination.")
    strict: bool = Field(True, description="Reject queries that reference unknown catalog values instead of ignoring them.")
    no_cache: bool = Field(False, description="Bypass the server-side result cache.")


class PlotQueryDTO(BaseModel):
    """
    Payload for POST /search/plot.

    Generates an ECharts-compatible chart from a DSL aggregation query.
    Use VO operators (COUNT, AVG, SUM) and BY for grouping.
    """

    query: str = Field(..., description="JUB DSL aggregation query string.")
    observatory_id: Optional[str] = Field(None, description="Optional observatory ID to scope the query.")
    chart_type: str = Field("bar", description="Chart type for the ECharts response (bar, line, pie, etc.).")
    source_id: Optional[str] = Field(None, description="Optional data source ID to aggregate over.")
    strict: bool = Field(True, description="Reject queries that reference unknown catalog values instead of ignoring them.")


# ── Task DTOs ──────────────────────────────────────────────────


class TaskCompleteDTO(BaseModel):
    """
    Payload for POST /tasks/{task_id}/complete.

    Called by external indexers or workers when a background task finishes.
    On success, the associated observatory is enabled.
    """

    success: bool = Field(..., description="Whether the task completed successfully.")
    message: Optional[str] = Field(None, description="Optional status or error message from the worker.")


class TasksStatsDTO(BaseModel):
    """Response for GET /tasks/stats."""

    pending: int = Field(0, description="Number of tasks waiting to run.")
    running: int = Field(0, description="Number of tasks currently executing.")
    success: int = Field(0, description="Number of tasks that completed successfully.")
    failed: int = Field(0, description="Number of tasks that failed.")


class TaskXDTO(BaseModel):
    """Response model for a single background task."""

    task_id: str = Field(..., description="Unique identifier of the task.")
    user_id: str = Field("", description="ID of the user who owns the task.")
    observatory_id: str = Field("", description="ID of the observatory the task relates to, if any.")
    title: str = Field("", description="Short human-readable title.")
    description: str = Field("", description="Longer description of the task.")
    operation: str = Field(..., description="Kind of work (create, update, delete, sync, setup, index).")
    current_status: str = Field(..., description="Lifecycle state (pending, running, success, failed).")
    progress_message: str = Field("", description="Latest progress or error message reported by the worker.")
    created_at: str = Field("", description="ISO 8601 creation timestamp.")
    updated_at: str = Field("", description="ISO 8601 last-update timestamp.")


class TaskCompleteResponseDTO(BaseModel):
    """Response for POST /tasks/{id}/complete."""
    task_id: str = Field(..., description="ID of the completed task.")
    status: str = Field(..., description="Final status recorded for the task.")
    observatory_id: str = Field(..., description="ID of the observatory the task provisioned.")
    observatory_enabled: bool = Field(..., description="Whether the observatory was enabled as a result.")


# ── Users ──────────────────────────────────────────────────────


class UserProfileDTO(BaseModel):
    """Response for GET /users/me."""
    user_id: str = Field(..., description="Unique identifier of the user.")
    username: str = Field(..., description="Login handle.")
    fullname: str = Field("", description="Full name of the user, combining first and last name if available.")
    first_name: str = Field("", description="Optional first name of the user.")
    last_name: str = Field("", description="Optional last name of the user.")
    email: str = Field(..., description="User email address.")
    settings: UserPreferencesDTO = Field(default_factory=UserPreferencesDTO, description="The user's saved preferences.")
    created_at: str = Field("", description="ISO 8601 datetime string indicating when the user account was created.")
    updated_at: str = Field("", description="ISO 8601 datetime string indicating when the user account was last updated.")
    is_disabled: bool = Field(False, description="Whether the user account is disabled.")


class AuthResponseDTO(BaseModel):
    """Response for POST /users/auth and POST /users/signup."""
    access_token: str = Field(..., description="JWT sent as a Bearer token on subsequent requests.")
    temporal_secret_key: Optional[str] = Field(None, description="Secret for internal service-to-service authentication, if issued.")
    user_profile: UserProfileDTO = Field(..., description="Profile of the authenticated user.")


# ── Catalogs (response) ────────────────────────────────────────




class ObservatorySetupResponseDTO(BaseModel):
    """Response for POST /observatories/setup."""
    observatory_id: str = Field(..., description="ID of the created (disabled) observatory.")
    task_id: str = Field(..., description="ID of the setup task; pass it to complete_task() when done.")
    status: str = Field("pending", description="Initial status of the setup task.")
    message: str = Field("", description="Informational message from the API.")


class ObservatoryDeleteResponseDTO(BaseModel):
    """Response for DELETE /observatories/{id}."""
    deleted: bool = Field(..., description="Whether the observatory was deleted.")


class ObservatoryCatalogLinkResponseDTO(BaseModel):
    """Response for POST /observatories/{id}/catalogs."""
    observatory_id: str = Field(..., description="ID of the observatory.")
    catalog_id: str = Field(..., description="ID of the linked catalog.")
    level: int = Field(0, description="Display order level of the catalog in the observatory.")


class ObservatoryProductLinkResponseDTO(BaseModel):
    """Response for POST /observatories/{id}/products."""
    observatory_id: str = Field(..., description="ID of the observatory.")
    product_id: str = Field(..., description="ID of the linked product.")


class CatalogCreatedResponseDTO(BaseModel):
    """Response for POST /catalogs."""
    catalog_id: str = Field(..., description="ID of the created catalog.")


class CatalogCreatedBulkResponseDTO(BaseModel):
    """Response for POST /catalogs/bulk."""
    catalog_ids: List[str] = Field(..., description="IDs of the created catalogs, in request order.")


class CatalogSummaryDTO(BaseModel):
    """Lightweight catalog entry returned by GET /catalogs."""
    catalog_id: str = Field(..., description="Unique identifier of the catalog.")
    name: str = Field(..., description="Human-readable name.")
    value: str = Field(..., description="Stored value used in queries (UPPER_SNAKE_CASE).")
    catalog_type: str = Field(..., description="Classification (SPATIAL, TEMPORAL, INTEREST, OBSERVABLE, REFERENCE).")


T = TypeVar("T")


class PageDTO(BaseModel, Generic[T]):
    """Generic paginated response envelope."""
    items: List[T] = Field(default_factory=list, description="Items in the current page.")
    total: int = Field(..., description="Total number of items matching the filters (across all pages).")
    skip: int = Field(..., description="Number of items skipped before this page.")
    limit: int = Field(..., description="Maximum number of items in a page.")


class _CatalogItemAliasResp(BaseModel):
    """Alias sub-object inside a CatalogItemResponseDTO."""
    catalog_item_alias_id: Optional[str] = Field(None, description="ID of the alias, if stored as a separate entity.")
    value: str = Field(..., description="The alias value string.")
    value_type: str = Field(..., description="Type of the alias value (STRING, NUMBER, BOOLEAN, DATETIME).")
    description: str = Field("", description="Optional description of the alias.")


class CatalogItemResponseDTO(BaseModel):
    """Item sub-object inside a full CatalogResponseDTO."""
    catalog_item_id: str = Field(..., description="Unique identifier of the item.")
    name: str = Field(..., description="Human-readable display name.")
    value: str = Field(..., description="Stored value used in queries.")
    code: int = Field(..., description="Numeric code uniquely identifying the item.")
    value_type: str = Field(..., description="Data type of the value (STRING, NUMBER, BOOLEAN, DATETIME).")
    temporal_value: Optional[str] = Field(None, description="ISO 8601 datetime string for temporal items.")
    description: str = Field("", description="Optional description.")
    aliases: List[_CatalogItemAliasResp] = Field(default_factory=list, description="Alternative names or codes for this item.")
    children: List["CatalogItemResponseDTO"] = Field(default_factory=list, description="Nested child items in the hierarchy.")

CatalogItemResponseDTO.model_rebuild()


class CatalogResponseDTO(BaseModel):
    """Full catalog returned by GET /catalogs/{id}."""
    catalog_id: str = Field(..., description="Unique identifier of the catalog.")
    name: str = Field(..., description="Human-readable name.")
    value: str = Field(..., description="Stored value used in queries.")
    catalog_type: str = Field(..., description="Classification (SPATIAL, TEMPORAL, INTEREST, OBSERVABLE, REFERENCE).")
    description: str = Field("", description="Optional description.")
    items: List[CatalogItemResponseDTO] = Field(default_factory=list, description="Items in the catalog, with aliases and children populated.")


class CatalogXDTO(BaseModel):
    """Catalog entry returned by GET /observatories/{id}/catalogs."""
    catalog_id: str = Field(..., description="Unique identifier of the catalog.")
    name: str = Field(..., description="Human-readable name.")
    value: str = Field(..., description="Stored value used in queries.")
    catalog_type: str = Field(..., description="Classification (SPATIAL, TEMPORAL, INTEREST, OBSERVABLE, REFERENCE).")
    description: str = Field("", description="Optional description.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary key-value metadata.")
    level: int = Field(0, description="Display order level of the catalog in the observatory.")
    parent_catalog_id: Optional[str] = Field(None, description="ID of the parent catalog, if this catalog is nested.")
    root_group_id: Optional[str] = Field(None, description="ID of the root catalog of the group this catalog belongs to.")
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")
    updated_at: str = Field(..., description="ISO 8601 last-update timestamp.")


class CatalogItemXResponseDTO(BaseModel):
    """Response for catalog-item CRUD endpoints."""
    catalog_item_id: str = Field(..., description="Unique identifier of the item.")
    name: str = Field(..., description="Human-readable display name.")
    value: str = Field(..., description="Stored value used in queries.")
    code: int = Field(..., description="Numeric code uniquely identifying the item.")
    value_type: str = Field(..., description="Data type of the value (STRING, NUMBER, BOOLEAN, DATETIME).")
    catalog_type: Optional[str] = Field(None, description="Type of the catalog the item belongs to, if known.")
    temporal_value: Optional[str] = Field(None, description="ISO 8601 datetime string for temporal items.")
    description: str = Field("", description="Optional description.")
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")
    updated_at: str = Field(..., description="ISO 8601 last-update timestamp.")


class CatalogItemDeleteResponseDTO(BaseModel):
    """Response for DELETE /catalog-items/{id}."""
    deleted: bool = Field(..., description="Whether the item was deleted.")


class CatalogItemAliasXResponseDTO(BaseModel):
    """Response for alias CRUD endpoints."""
    catalog_item_alias_id: str = Field(..., description="Unique identifier of the alias.")
    value: str = Field(..., description="The alias value string.")
    value_type: str = Field(..., description="Type of the alias value (STRING, NUMBER, BOOLEAN, DATETIME).")
    catalog_type: Optional[str] = Field(None, description="Type of the catalog the aliased item belongs to, if known.")
    description: str = Field("", description="Optional description.")
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")
    updated_at: str = Field(..., description="ISO 8601 last-update timestamp.")


class CatalogItemChildLinkResponseDTO(BaseModel):
    """Response for POST /catalog-items/{id}/children."""
    parent_item_id: str = Field(..., description="ID of the parent item.")
    child_item_id: str = Field(..., description="ID of the linked child item.")


class CatalogItemCatalogLinkResponseDTO(BaseModel):
    """Response for POST /catalog-items/{id}/catalogs."""
    catalog_item_id: str = Field(..., description="ID of the catalog item.")
    catalog_id: str = Field(..., description="ID of the catalog it was linked into.")


class ItemProductsDTO(BaseModel):
    """Response for GET /catalog-items/{id}/products."""
    catalog_item_id: str = Field(..., description="ID of the catalog item.")
    product_ids: List[str] = Field(default_factory=list, description="IDs of the products tagged with this item.")


class ProductSimpleDTO(BaseModel):
    """Response for product CRUD endpoints."""
    product_id: str = Field(..., description="Unique identifier of the product.")
    name: str = Field(..., description="Display name of the product.")
    description: str = Field("", description="Optional textual description.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary key-value metadata.")
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")
    updated_at: str = Field(..., description="ISO 8601 last-update timestamp.")


class ProductDeleteResponseDTO(BaseModel):
    """Response for DELETE /products/{id}."""
    deleted: bool = Field(..., description="Whether the product was deleted.")


class ProductTagsResponseDTO(BaseModel):
    """Response for GET /products/{id}/tags and POST /products/{id}/tags."""
    product_id: str = Field(..., description="ID of the product.")
    catalog_item_ids: List[str] = Field(default_factory=list, description="IDs of the catalog items the product is tagged with.")


class ProductUploadResponseDTO(BaseModel):
    """Response for POST /products/{id}/upload."""
    job_id: str = Field(..., description="ID of the background ingestion job.")
    product_id: str = Field(..., description="ID of the product the file was uploaded to.")
    status: str = Field("queued", description="Initial job status.")


class DataSourceUpdateDTO(BaseModel):
    """
    Payload for PUT /datasources/{source_id}.

    All fields are optional; only provided fields are updated.
    """
    name: Optional[str] = Field(None, description="New human-readable name.")
    description: Optional[str] = Field(None, description="New description.")
    connection_uri: Optional[str] = Field(None, description="New connection string for database sources.")
    bucket_id: Optional[str] = Field(None, description="New MictlanX bucket identifier.")


class DataSourceDeleteResponseDTO(BaseModel):
    """Response for DELETE /datasources/{id}."""
    deleted: bool = Field(..., description="Whether the data source was deleted.")
    records_removed: int = Field(..., description="Number of data records deleted with it.")


class IngestResponseDTO(BaseModel):
    """Response for POST /datasources/{id}/records."""
    inserted: int = Field(0, description="Number of records inserted.")


# ── Notifications ──────────────────────────────────────────────


class NotificationReadAllResponseDTO(BaseModel):
    """Response for PUT /notifications/read-all."""

    modified: int = Field(..., description="Number of notifications marked as read.")


class NotificationClearReadResponseDTO(BaseModel):
    """Response for DELETE /notifications/clear-read."""

    deleted: int = Field(..., description="Number of read notifications deleted.")


class NotificationDTO(BaseModel):
    """Response item for GET /notifications."""
    notification_id: str = Field(..., description="Unique identifier of the notification.")
    user_id: str = Field("", description="ID of the user the notification belongs to.")
    status: str = Field("", description="Severity (info, warning, error, success).")
    operation: str = Field("", description="Operation that triggered it (create, update, delete, read, other).")
    entity: str = Field("", description="Kind of entity involved (product, observatory, catalog, task, ...).")
    entity_id: Optional[str] = Field(None, description="ID of the entity involved, if any.")
    title: str = Field("", description="Short title.")
    message: str = Field("", description="Full notification message.")
    is_read: bool = Field(False, description="Whether the notification has been marked as read.")
    created_at: str = Field("", description="ISO 8601 creation timestamp.")


# ── Building blocks ────────────────────────────────────────────


class BuildingBlockCreateDTO(BaseModel):
    """Payload for POST /building-blocks."""

    name: str = Field(..., description="Human-readable identifier for this building block.")
    command: str = Field(..., description="Entrypoint command executed inside the container.")
    image: str = Field(..., description="Docker image reference (e.g. 'python:3.11-slim').")
    description: str = Field("", description="Optional description providing context.")


class BuildingBlockUpdateDTO(BaseModel):
    """
    Payload for PATCH /building-blocks/{building_block_id}.

    All fields are optional; only provided fields are updated.
    """

    name: Optional[str] = Field(None, description="New human-readable identifier.")
    command: Optional[str] = Field(None, description="New entrypoint command.")
    image: Optional[str] = Field(None, description="New Docker image reference.")
    description: Optional[str] = Field(None, description="New description.")


class BuildingBlockDTO(BaseModel):
    """Response model for a building block."""

    building_block_id: str = Field(..., description="System-generated unique identifier.")
    name: str = Field(..., description="Human-readable identifier.")
    command: str = Field(..., description="Container entrypoint command.")
    image: str = Field(..., description="Docker image reference.")
    description: str = Field("", description="Optional description.")
    created_at: str = Field("", description="ISO 8601 creation timestamp.")
    updated_at: str = Field("", description="ISO 8601 last-update timestamp.")


# ── Patterns ───────────────────────────────────────────────────


class PatternCreateDTO(BaseModel):
    """Payload for POST /patterns."""

    name: str = Field(..., description="Human-readable pattern name.")
    task: str = Field(..., description="Task category (e.g. 'transform', 'ingest').")
    pattern: str = Field(..., description="Pattern type (e.g. 'map-reduce', 'pipeline').")
    description: str = Field("", description="Optional description providing context.")
    workers: int = Field(1, description="Number of parallel worker instances (minimum 1).")
    loadbalancer: str = Field("round-robin", description="Load-balancing strategy (default 'round-robin').")
    building_block_id: Optional[str] = Field(None, description="Optional ID of an existing BuildingBlock to associate.")


class PatternUpdateDTO(BaseModel):
    """
    Payload for PATCH /patterns/{pattern_id}.

    All fields are optional; only provided fields are updated.
    """

    name: Optional[str] = Field(None, description="New pattern name.")
    task: Optional[str] = Field(None, description="New task category.")
    pattern: Optional[str] = Field(None, description="New pattern type.")
    description: Optional[str] = Field(None, description="New description.")
    workers: Optional[int] = Field(None, description="New worker count (minimum 1).")
    loadbalancer: Optional[str] = Field(None, description="New load-balancing strategy.")
    building_block_id: Optional[str] = Field(None, description="New building block reference.")


class PatternDTO(BaseModel):
    """Response model for a pattern."""

    pattern_id: str = Field(..., description="System-generated unique identifier.")
    name: str = Field(..., description="Human-readable pattern name.")
    task: str = Field(..., description="Task category.")
    pattern: str = Field(..., description="Pattern type.")
    description: str = Field("", description="Optional description.")
    workers: int = Field(1, description="Number of parallel worker instances.")
    loadbalancer: str = Field("round-robin", description="Load-balancing strategy.")
    building_block_id: Optional[str] = Field(None, description="Associated building block ID, if any.")
    created_at: str = Field("", description="ISO 8601 creation timestamp.")
    updated_at: str = Field("", description="ISO 8601 last-update timestamp.")


# ── Stages ─────────────────────────────────────────────────────


class StageCreateDTO(BaseModel):
    """Payload for POST /stages."""

    name: str = Field(..., description="Stage name.")
    source: str = Field(..., description="Input source identifier or URI.")
    sink: str = Field(..., description="Output sink identifier or URI.")
    endpoint: str = Field(..., description="HTTP or messaging endpoint exposed by this stage.")
    transformation_id: Optional[str] = Field(None, description="Optional ID of an existing Pattern to apply.")


class StageUpdateDTO(BaseModel):
    """
    Payload for PATCH /stages/{stage_id}.

    All fields are optional; only provided fields are updated.
    """

    name: Optional[str] = Field(None, description="New stage name.")
    source: Optional[str] = Field(None, description="New input source.")
    sink: Optional[str] = Field(None, description="New output sink.")
    endpoint: Optional[str] = Field(None, description="New endpoint URI.")
    transformation_id: Optional[str] = Field(None, description="New pattern reference.")


class StageDTO(BaseModel):
    """Response model for a stage."""

    stage_id: str = Field(..., description="System-generated unique identifier.")
    name: str = Field(..., description="Stage name.")
    source: str = Field(..., description="Input source identifier or URI.")
    sink: str = Field(..., description="Output sink identifier or URI.")
    endpoint: str = Field(..., description="Endpoint exposed by this stage.")
    transformation_id: Optional[str] = Field(None, description="Associated pattern ID, if any.")
    created_at: str = Field("", description="ISO 8601 creation timestamp.")
    updated_at: str = Field("", description="ISO 8601 last-update timestamp.")


# ── Workflows ──────────────────────────────────────────────────


class WorkflowCreateDTO(BaseModel):
    """Payload for POST /workflows."""

    name: str = Field(..., description="Workflow name.")
    stage_ids: List[str] = Field(default_factory=list, description="Ordered list of stage IDs that form the workflow pipeline.")


class WorkflowUpdateDTO(BaseModel):
    """
    Payload for PATCH /workflows/{workflow_id}.

    All fields are optional; only provided fields are updated.
    """

    name: Optional[str] = Field(None, description="New workflow name.")
    stage_ids: Optional[List[str]] = Field(None, description="New ordered list of stage IDs.")


class WorkflowDTO(BaseModel):
    """Response model for a workflow."""

    workflow_id: str = Field(..., description="System-generated unique identifier.")
    name: str = Field(..., description="Workflow name.")
    stage_ids: List[str] = Field(default_factory=list, description="Ordered list of stage IDs in the pipeline.")
    created_at: str = Field("", description="ISO 8601 creation timestamp.")
    updated_at: str = Field("", description="ISO 8601 last-update timestamp.")


class WorkflowDeleteResponseDTO(BaseModel):
    """Response for DELETE /workflows/{id}."""
    deleted: bool = Field(..., description="Whether the workflow was deleted.")
    cascade: Dict[str, Any] = Field(default_factory=dict, description="Counts of cascade-deleted entities when cascade=True.")


# ── Services ───────────────────────────────────────────────────


class ServiceCreateDTO(BaseModel):
    """Payload for POST /services."""

    name: str = Field(..., description="Service name, searchable via the SVC() DSL operator.")
    owner_id: str = Field(..., description="User ID of the service owner.")
    description: str = Field("", description="Optional description providing context.")
    public: bool = Field(False, description="Whether this service is publicly discoverable via SVC(*) queries.")
    workflow_id: Optional[str] = Field(None, description="Optional ID of an existing workflow to attach.")
    provider: Optional[ServiceProviderEnum] = Field(ServiceProviderEnum.OTHER, description="Optional service provider classification (e.g. NEZ, XELHUA, EXTERNAL).")


class ServiceUpdateDTO(BaseModel):
    """
    Payload for PATCH /services/{service_id}.

    All fields are optional; only provided fields are updated.
    """

    name: Optional[str] = Field(None, description="New service name.")
    description: Optional[str] = Field(None, description="New description.")
    public: Optional[bool] = Field(None, description="New visibility flag.")
    provider: Optional[ServiceProviderEnum] = Field(None, description="New provider of the service (XELHUA, NEZ, EXTERNAL, OTHER).")
    workflow_id: Optional[str] = Field(None, description="New workflow reference.")


class ServiceDTO(BaseModel):
    """Response model for a service."""

    service_id: str = Field(..., description="System-generated unique identifier.")
    name: str = Field(..., description="Service name.")
    description: str = Field("", description="Optional description.")
    owner_id: str = Field(..., description="User ID of the service owner.")
    public: bool = Field(False, description="Whether the service is publicly discoverable.")
    provider: str = Field("", description="Provider of the service (XELHUA, NEZ, EXTERNAL, OTHER).")
    workflow_id: Optional[str] = Field(None, description="Associated workflow ID, if any.")
    created_at: str = Field("", description="ISO 8601 creation timestamp.")
    updated_at: str = Field("", description="ISO 8601 last-update timestamp.")


class BuildingBlockInlineDTO(BaseModel):
    """Inline building block definition used inside ServiceIndexDTO."""

    name: str = Field(..., description="Human-readable identifier.")
    command: str = Field(..., description="Container entrypoint command.")
    image: str = Field(..., description="Docker image reference.")
    description: str = Field("", description="Optional description.")


class PatternInlineDTO(BaseModel):
    """
    Inline pattern definition used inside ServiceIndexDTO.

    Provide either building_block (to create one inline) or building_block_id
    (to reference an existing one). Both are optional.
    """

    name: str = Field(..., description="Human-readable pattern name.")
    task: str = Field(..., description="Task category.")
    pattern: str = Field(..., description="Pattern type.")
    description: str = Field("", description="Optional description.")
    workers: int = Field(1, description="Number of parallel worker instances.")
    loadbalancer: str = Field("round-robin", description="Load-balancing strategy.")
    building_block: Optional[BuildingBlockInlineDTO] = Field(None, description="Inline building block to create together with this pattern.")
    building_block_id: Optional[str] = Field(None, description="ID of an existing building block to reference.")


class StageInlineDTO(BaseModel):
    """
    Inline stage definition used inside ServiceIndexDTO.

    Provide either transformation (to create a pattern inline) or
    transformation_id (to reference an existing one). Both are optional.
    """

    name: str = Field(..., description="Stage name.")
    source: str = Field(..., description="Input source identifier or URI.")
    sink: str = Field(..., description="Output sink identifier or URI.")
    endpoint: str = Field(..., description="HTTP or messaging endpoint exposed by this stage.")
    transformation: Optional[PatternInlineDTO] = Field(None, description="Inline pattern to create together with this stage.")
    transformation_id: Optional[str] = Field(None, description="ID of an existing pattern to reference.")


class WorkflowInlineDTO(BaseModel):
    """Inline workflow definition used inside ServiceIndexDTO."""

    name: str = Field(..., description="Workflow name.")
    stages: List[StageInlineDTO] = Field(default_factory=list, description="Ordered list of inline stage definitions (minimum one stage required).")



class ServiceIndexDTO(BaseModel):
    """
    Payload for POST /services/index.

    One-shot request that creates the complete Service -> Workflow -> Stages ->
    Patterns -> BuildingBlocks tree in a single call. At every level you can
    either provide inline definitions or reference existing IDs.
    """

    name: str = Field(..., description="Service name.")
    owner_id: str = Field(..., description="User ID of the service owner.")
    description: str = Field("", description="Optional description providing context about the service.")
    public: bool = Field(False, description="Whether this service is publicly discoverable via SVC() DSL queries.")
    workflow: Optional[WorkflowInlineDTO] = Field(None, description="Inline workflow definition to create together with the service. If provided, workflow_id must be null.")
    workflow_id: Optional[str] = Field(None, description="ID of an existing workflow to attach instead of creating one inline.")
    provider: Optional[ServiceProviderEnum ] =Field(ServiceProviderEnum.OTHER, description="Optional service provider classification (e.g. NEZ, XELHUA, EXTERNAL).")


class ServiceIndexResponseDTO(BaseModel):
    """
    Response for POST /services/index.

    Summary of every entity created or referenced during the bulk index call.
    """

    service_id: str = Field(..., description="ID of the created service.")
    workflow_id: Optional[str] = Field(None, description="ID of the created or referenced workflow, if any.")
    stage_ids: List[str] = Field(default_factory=list, description="IDs of all created stages.")
    pattern_ids: List[str] = Field(default_factory=list, description="IDs of all created patterns.")
    building_block_ids: List[str] = Field(default_factory=list, description="IDs of all created building blocks.")


class ServiceQueryDTO(BaseModel):
    """
    Payload for POST /services/search (Services DSL search).

    DSL query uses the SVC() operator:
        jub.v1.SVC(*)                       -- all services
        jub.v1.SVC(name=cancer)             -- name contains 'cancer'
        jub.v1.SVC(public=true)             -- public only
        jub.v1.SVC(owner=usr_abc)           -- by owner
        jub.v1.SVC(name=cancer,public=true) -- combined
    """

    query: str = Field(..., description="Services DSL query string.")
    limit: int = Field(100, description="Maximum number of results to return (1-1000).")
    skip: int = Field(0, description="Number of results to skip for pagination.")


class ServiceDeleteResponseDTO(BaseModel):
    """Response for DELETE /services/{service_id}."""

    deleted: bool = Field(..., description="Whether the service was deleted.")
    service_id: str = Field(..., description="ID of the deleted service.")
    cascade: Dict[str, Any] = Field(default_factory=dict, description="Counts of cascade-deleted entities (e.g. {'workflow': 1, 'stages': 3}).")


class ServiceSimpleDTO(BaseModel):
    """Lightweight service entry returned by GET /observatories/{id}/services."""
    service_id: str = Field(..., description="Unique identifier of the service.")
    name: str = Field(..., description="Service name.")
    description: str = Field("", description="Optional description.")
    provider: Optional[str] = Field(None, description="Provider classification (see ServiceProviderEnum), if any.")
    public: bool = Field(False, description="Whether the service is publicly discoverable.")


# ── Observatory status, views, and reviews ─────────────────────

class ObservatoryStatusUpdateDTO(BaseModel):
    """Payload for PATCH /observatories/{observatory_id}/status."""
    is_disabled: bool = Field(..., description="True to disable (hide) the observatory, False to enable it.")


class ObservatoryViewResponseDTO(BaseModel):
    """Response for POST /observatories/{observatory_id}/view."""
    observatory_id: str = Field(..., description="ID of the viewed observatory.")
    view_count: int = Field(..., description="View count after the increment.")


class CreateReviewDTO(BaseModel):
    """Payload for POST /observatories/{observatory_id}/reviews."""
    content: str = Field(..., description="Review text.")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5.")


class UpdateReviewDTO(BaseModel):
    """
    Payload for PUT /observatories/{observatory_id}/reviews/{review_id}.

    All fields are optional; only provided fields are updated.
    """
    content: Optional[str] = Field(None, description="New review text.")
    rating: Optional[int] = Field(None, ge=1, le=5, description="New rating from 1 to 5.")


class ReviewDTO(BaseModel):
    """Response model for an observatory review."""
    review_id: str = Field(..., description="Unique identifier of the review.")
    observatory_id: str = Field(..., description="ID of the reviewed observatory.")
    user_id: str = Field(..., description="ID of the user who wrote the review.")
    content: str = Field(..., description="Review text.")
    rating: int = Field(..., description="Rating from 1 to 5.")
    created_at: str = Field(..., description="ISO 8601 creation timestamp.")
    updated_at: str = Field(..., description="ISO 8601 last-update timestamp.")


# ── Product relations and bulk tagging ─────────────────────────

class RelateProductDTO(BaseModel):
    """Payload for POST /products/{product_id}/related."""
    related_product_id: str = Field(..., description="ID of the product to relate to this one.")


class RelatedProductLinkResponseDTO(BaseModel):
    """Response for POST /products/{product_id}/related."""
    product_id: str = Field(..., description="ID of the source product.")
    related_product_id: str = Field(..., description="ID of the related product.")


class BulkTagFromCatalogResponseDTO(BaseModel):
    """Response for POST /products/{product_id}/tags/catalog/{catalog_id}."""
    product_id: str = Field(..., description="ID of the tagged product.")
    catalog_id: str = Field(..., description="ID of the catalog whose items were assigned.")
    linked_items: int = Field(..., description="Number of catalog items linked to the product.")


# ── Search suggestions ─────────────────────────────────────────

class SearchSuggestionItemDTO(BaseModel):
    """A single suggested query with its number of hits."""
    query: str = Field(..., description="Suggested JUB DSL query string.")
    hit_count: int = Field(..., description="Number of results the query returns.")


class SearchSuggestionsResponseDTO(BaseModel):
    """Response for GET /search/products/suggestions."""
    observatory_id: str = Field(..., description="Observatory the suggestions are scoped to.")
    suggestions: List[SearchSuggestionItemDTO] = Field(default_factory=list, description="Suggested queries.")


class ObservatorySearchSuggestionsResponseDTO(BaseModel):
    """Response for GET /search/observatories/suggestions."""
    suggestions: List[SearchSuggestionItemDTO] = Field(default_factory=list, description="Suggested queries.")
