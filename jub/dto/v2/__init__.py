from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, List, Optional, Union

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

    Attributes:
        obid: Unique identifier of the observatory.
        title: Display name of the observatory.
        image_url: URL of an image representing the observatory.
        description: Textual description providing context.
        disabled: Whether the observatory is inactive.
    """

    obid: str = ""
    title: str = "Observatory"
    image_url: str = ""
    description: str = ""
    disabled: bool = False


class Catalog(BaseModel):
    """
    Represents a catalog in the JUB domain.

    This version removes the embedded items collection.
    Relationships between catalogs and items are expressed via CatalogItemLink.

    Attributes:
        cid: Unique identifier of the catalog.
        display_name: Human-readable name of the catalog.
        kind: Type of the catalog (e.g. TEMPORAL, SPATIAL, INTEREST).
    """

    cid: str = ""
    display_name: str = ""
    kind: str = ""

    @field_validator("display_name")
    def remove_double_spaces(cls, value):
        """Normalizes display_name by collapsing consecutive whitespace into a single space."""
        return " ".join(value.split())


class CatalogItem(BaseModel):
    """
    Represents an item within a catalog.

    This model is no longer attached to the Catalog model directly.
    Relationships are now represented through CatalogItemLink.

    Attributes:
        item_id: Unique identifier of the catalog item.
        value: Value used for storage and querying.
        display_name: Human-readable name for the catalog item.
        code: Unique numeric code identifying the catalog item.
        description: Textual description providing context.
        metadata: Extra key-value data providing context about the item.
    """

    item_id: str
    value: str
    display_name: str
    code: int
    description: str
    metadata: Dict[str, str]

    @field_validator("display_name")
    def remove_double_spaces(cls, value):
        """Normalizes display_name by collapsing consecutive whitespace into a single space."""
        return " ".join(value.split())


class Product(BaseModel):
    """
    Represents a product in the JUB domain.

    This version removes the levels field used in V1 for catalog references.

    Attributes:
        pid: Product unique identifier.
        description: Textual description of the product.
        product_type: Category of the product.
        product_name: Display name of the product.
        tags: Tags for permission control and filtering.
        url: Path to the product in the application.
    """

    pid: str = ""
    description: str = ""
    product_type: str = ""
    product_name: str = ""
    tags: List[str] = Field(default_factory=list)
    url: str = ""


# ── Link models ────────────────────────────────────────────────


class ObservatoryCatalogLink(BaseModel):
    """
    Represents the relationship between an Observatory and a Catalog.

    Attributes:
        obid: Unique identifier of the observatory.
        cid: Unique identifier of the catalog.
    """

    obid: str
    cid: str


class CatalogItemLink(BaseModel):
    """
    Represents the relationship between a Catalog and a CatalogItem.

    Attributes:
        cid: Unique identifier of the catalog.
        item_id: Unique identifier of the catalog item.
    """

    cid: str
    item_id: str


class ProductObservatoryLink(BaseModel):
    """
    Represents the relationship between a Product and an Observatory.

    Attributes:
        pid: Unique identifier of the product.
        obid: Unique identifier of the observatory.
    """

    pid: str
    obid: str


class ProductCatalogItemLink(BaseModel):
    """
    Represents the relationship between a Product and a CatalogItem.

    Attributes:
        pid: Unique identifier of the product.
        item_id: Unique identifier of the catalog item.
        kind: The kind of the level (SPATIAL, TEMPORAL, INTEREST, etc.).
    """

    pid: str
    item_id: str
    kind: str


# ── User DTOs ──────────────────────────────────────────────────


class SignUpDTO(BaseModel):
    """
    Payload for creating a new user account.

    Attributes:
        username: Unique login handle.
        email: User email address.
        password: Plain-text password (transmitted over HTTPS only).
        first_name: Optional first name.
        last_name: Optional last name.
    """

    username: str
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""


class AuthAttemptDTO(BaseModel):
    """
    Payload for POST /users/auth.

    Attributes:
        username: Account login handle.
        password: Plain-text password.
    """

    username: str
    password: str


class AppearanceSettingsDTO(BaseModel):
    """
    User appearance preferences.

    Attributes:
        theme: UI theme (light, dark, system).
        font_size: Base font size in pixels.
        reduce_animations: Whether to disable UI animations.
    """

    theme: str = "light"
    font_size: int = 14
    reduce_animations: bool = False


class ExplorationSettingsDTO(BaseModel):
    """
    User exploration preferences.

    Attributes:
        enable_tutorial: Whether to show onboarding tutorials.
        default_view: Default layout view (list, grid).
        items_per_page: Number of items shown per page.
    """

    enable_tutorial: bool = True
    default_view: str = "list"
    items_per_page: int = 12


class ExportSettingsDTO(BaseModel):
    """
    User export preferences.

    Attributes:
        default_format: Default export format (json, yml).
        include_metadata: Whether to include metadata in exports.
    """

    default_format: str = "yml"
    include_metadata: bool = True


class UserPreferencesDTO(BaseModel):
    """
    Aggregated user preferences payload for PUT /users/{user_id}/settings.

    Attributes:
        appearance: Visual appearance settings.
        exploration: Data exploration settings.
        export: Data export settings.
    """

    appearance: AppearanceSettingsDTO = Field(default_factory=AppearanceSettingsDTO)
    exploration: ExplorationSettingsDTO = Field(default_factory=ExplorationSettingsDTO)
    export: ExportSettingsDTO = Field(default_factory=ExportSettingsDTO)


# ── Catalog DTOs ───────────────────────────────────────────────


class CatalogItemAliasCreateDTO(BaseModel):
    """
    Payload for creating an alias for a catalog item.

    Attributes:
        value: The alias value string.
        value_type: Type of the alias value (STRING, NUMBER, BOOLEAN, DATETIME).
        description: Optional description for the alias.
    """

    value: str
    value_type: str
    description: str = ""


class CatalogItemCreateDTO(BaseModel):
    """
    Payload for creating a catalog item within a new catalog.

    This model is recursive to support hierarchical catalog structures.

    Attributes:
        name: Human-readable display name.
        value: Stored value used in queries (typically UPPER_SNAKE_CASE).
        code: Numeric code uniquely identifying the item.
        value_type: Data type of the value (STRING, NUMBER, BOOLEAN, DATETIME).
        description: Optional description providing context.
        temporal_value: Optional ISO 8601 datetime string for temporal items.
        aliases: List of alternative names or codes for this item.
        children: Nested child items for hierarchical catalogs.
    """

    name: str
    value: str
    code: int
    value_type: str
    description: str = ""
    temporal_value: Optional[str] = None
    aliases: List[CatalogItemAliasCreateDTO] = Field(default_factory=list)
    children: List["CatalogItemCreateDTO"] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


CatalogItemCreateDTO.model_rebuild()


class CatalogCreateDTO(BaseModel):
    """
    Payload for POST /catalogs.

    Attributes:
        name: Human-readable name of the catalog.
        value: Stored value used in queries (UPPER_SNAKE_CASE).
        catalog_type: Classification of the catalog (SPATIAL, TEMPORAL, INTEREST, etc.).
        description: Optional description providing context.
        items: List of catalog items to create together with the catalog.
    """

    name: str
    value: str
    catalog_type: str
    description: str = ""
    items: List[CatalogItemCreateDTO] = Field(default_factory=list)


class CatalogItemStandaloneCreateDTO(BaseModel):
    """
    Payload for POST /catalog-items (standalone creation outside catalog bulk flow).

    Attributes:
        catalog_id: ID of the catalog this item belongs to.
        name: Human-readable display name.
        value: Stored value used in queries.
        code: Numeric code uniquely identifying the item.
        value_type: Data type of the value (STRING, NUMBER, BOOLEAN, DATETIME).
        description: Optional description providing context.
        temporal_value: Optional ISO 8601 datetime string for temporal items.
        parent_item_id: Optional ID of a parent item for hierarchical placement.
    """

    catalog_id: str
    name: str
    value: str
    code: int
    value_type: str
    description: str = ""
    temporal_value: Optional[str] = None
    parent_item_id: Optional[str] = None


class CatalogItemUpdateDTO(BaseModel):
    """
    Payload for PUT /catalog-items/{catalog_item_id}.

    All fields are optional; only provided fields are updated.

    Attributes:
        name: New display name.
        description: New description.
        temporal_value: New ISO 8601 datetime string.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    temporal_value: Optional[str] = None


# ── DataSource DTOs ────────────────────────────────────────────


class DataSourceCreateDTO(BaseModel):
    """
    Payload for POST /datasources.

    Attributes:
        name: Human-readable name for the data source.
        description: Optional description.
        format: Data format (csv, json, postgres, mysql, mongodb).
        bucket_id: Optional MictlanX bucket identifier.
        connection_uri: Optional connection string for database sources.
    """

    name: str
    description: str = Field("")
    format: str = Field("csv")
    bucket_id: Optional[str] = Field(None)
    connection_uri: Optional[str] = Field(None)


class DataSourceDTO(BaseModel):
    """
    Response model for a registered data source.

    Attributes:
        source_id: System-generated unique identifier.
        name: Human-readable name.
        description: Optional description.
        format: Data format type.
        bucket_id: Optional MictlanX bucket identifier.
        connection_uri: Optional connection string.
    """

    source_id: str
    name: str
    description: str = Field(default="")
    format: str
    bucket_id: Optional[str] = Field(default=None)
    connection_uri: Optional[str] = Field(default=None)


class DataRecordCreateDTO(BaseModel):
    """
    A single data record to ingest via POST /datasources/{source_id}/records.

    Attributes:
        record_id: Unique identifier for this record.
        spatial_id: Catalog item ID for the spatial dimension.
        temporal_id: ISO 8601 datetime string for the temporal dimension.
        interest_ids: List of catalog item IDs for interest dimensions.
        numerical_interest_ids: Map of catalog item IDs to numeric values.
        raw_payload: Arbitrary additional data stored with the record.
    """

    record_id: str
    spatial_id: str
    temporal_id: str
    interest_ids: List[str] = Field(default_factory=list)
    numerical_interest_ids: Dict[str, float] = Field(default_factory=dict)
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class DataSourceQueryDTO(BaseModel):
    """
    Payload for POST /datasources/{source_id}/query.

    Attributes:
        query: JUB DSL query string.
        limit: Maximum number of records to return.
        skip: Number of records to skip for pagination.
    """

    query: str
    limit: int = Field(100)
    skip: int = Field(0)


# ── Observatory DTOs ───────────────────────────────────────────


class ObservatoryCreateDTO(BaseModel):
    """
    Payload for POST /observatories (immediate creation, enabled by default).

    Attributes:
        title: Display name of the observatory.
        description: Optional description providing context.
        image_url: Optional URL of a representative image.
    """

    title: str
    description: str = ""
    image_url: str = ""


class ObservatoryUpdateDTO(BaseModel):
    """
    Payload for PUT /observatories/{observatory_id}.

    All fields are optional; only provided fields are updated.

    Attributes:
        title: New display name.
        description: New description.
        image_url: New image URL.
    """

    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class ObservatorySetupDTO(BaseModel):
    """
    Payload for POST /observatories/setup.

    Creates a disabled observatory and queues a background setup task.
    The observatory is enabled only when the task completes successfully
    via POST /tasks/{task_id}/complete.

    Attributes:
        title: Display name of the observatory.
        description: Optional description providing context.
        image_url: Optional URL of a representative image.
    """

    observatory_id: Optional[str] = Field(None, description="Optional pre-defined ID for the observatory. If not provided, a random UUID is generated.")
    title: str
    description: str = Field("",description="Optional description providing context about the observatory.")
    image_url: str = Field("",description="Optional URL of a representative image.")
    metadata:Dict[str,str] = Field(default_factory=dict, description="Optional metadata for the observatory.")
    # user_id: 


class LinkCatalogDTO(BaseModel):
    """
    Payload for POST /observatories/{observatory_id}/catalogs.

    Attributes:
        catalog_id: ID of the catalog to link.
        level: Display order level for the catalog in the UI.
    """

    catalog_id: str
    level: int = 0


class LinkProductDTO(BaseModel):
    """
    Payload for POST /observatories/{observatory_id}/products.

    Attributes:
        product_id: ID of the product to link.
    """

    product_id: str


class BulkCatalogsDTO(BaseModel):
    """
    Payload for POST /observatories/{observatory_id}/catalogs/bulk.

    Creates multiple catalogs and links each to the observatory in one request.

    Attributes:
        catalogs: List of catalog creation payloads.
    """

    catalogs: List[CatalogCreateDTO] = Field(default_factory=list)

class BulkCatalogsResponseDTO(BaseModel):
    observatory_id: str = Field(..., description="ID of the observatory the catalogs were assigned to.")
    catalog_ids: List[str] = Field(default_factory=list, description="List of catalog IDs that were assigned to the observatory.")

class BulkProductItemDTO(BaseModel):
    """Item inside a BulkProductsDTO request (no observatory_id — that comes from the URL)."""
    product_id: Optional[str] = None
    name: str
    description: str = ""
    catalog_item_ids: List[str] = Field(default_factory=list)

class BulkProductCreatedDTO(BaseModel):
    product_id: str
    name: str

class BulkProductsResponseDTO(BaseModel):
    observatory_id: str
    products: List[BulkProductCreatedDTO] = Field(default_factory=list)

# ── Product DTOs ───────────────────────────────────────────────


class ProductCreateDTO(BaseModel):
    """
    Payload for POST /products.

    Attributes:
        name: Display name of the product.
        description: Optional textual description.
        product_type: Category of the product.
        observatory_id: ID of the observatory this product belongs to.
        catalog_item_ids: List of catalog item IDs to tag this product with.
    """

    product_id: Optional[str] = Field(None, description="Optional pre-defined ID for the product. If not provided, a random UUID is generated.")
    name: str = Field(..., description="Display name of the product.")
    description: str = Field("", description="Optional textual description providing context about the product.")
    observatory_id: str = Field(..., description="ID of the observatory this product belongs to.")
    catalog_item_ids: List[str] = Field(default_factory=list, description="List of catalog item IDs to tag this product with.")


class ProductUpdateDTO(BaseModel):
    """
    Payload for PUT /products/{product_id}.

    All fields are optional; only provided fields are updated.

    Attributes:
        name: New display name.
        description: New description.
        product_type: New product type category.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    product_type: Optional[str] = None


class TagProductDTO(BaseModel):
    """
    Payload for POST /products/{product_id}/tags.

    Attributes:
        catalog_item_ids: List of catalog item IDs to associate with the product.
    """

    catalog_item_ids: List[str] = Field(default_factory=list)


class BulkProductsDTO(BaseModel):
    """Payload for POST /observatories/{observatory_id}/products/bulk."""

    products: List[Union[BulkProductItemDTO, ProductCreateDTO]] = Field(default_factory=list)


# ── Search DTOs ────────────────────────────────────────────────


class SearchQueryDTO(BaseModel):
    """
    Payload for POST /search, /search/records, and /search/observatories.

    The query field uses the JUB DSL (see Query Language section in CLAUDE.md).

    Attributes:
        query: JUB DSL query string (e.g. jub.v1.VS(MX).VT(>= 2020).VI(SEX_FEMALE)).
        observatory_id: Optional observatory ID to scope the search.
        limit: Maximum number of results to return.
        skip: Number of results to skip for pagination.
    """

    query: str
    observatory_id: Optional[str] = Field(None)
    limit: int = Field(10)
    skip: int = Field(0)


class PlotQueryDTO(BaseModel):
    """
    Payload for POST /search/plot.

    Generates an ECharts-compatible chart from a DSL aggregation query.
    Use VO operators (COUNT, AVG, SUM) and BY for grouping.

    Attributes:
        query: JUB DSL aggregation query string.
        observatory_id: Optional observatory ID to scope the query.
        chart_type: Chart type for the ECharts response (bar, line, pie, etc.).
    """

    query: str
    observatory_id: Optional[str] = Field(None)
    chart_type: str = Field("bar")


# ── Task DTOs ──────────────────────────────────────────────────


class TaskCompleteDTO(BaseModel):
    """
    Payload for POST /tasks/{task_id}/complete.

    Called by external indexers or workers when a background task finishes.
    On success, the associated observatory is enabled.

    Attributes:
        success: Whether the task completed successfully.
        message: Optional status or error message from the worker.
    """

    success: bool
    message: Optional[str] = None


class TasksStatsDTO(BaseModel):
    """
    Response for GET /tasks/stats.

    Attributes:
        pending: Number of tasks waiting to run.
        running: Number of tasks currently executing.
        success: Number of tasks that completed successfully.
        failed: Number of tasks that failed.
    """

    pending: int = 0
    running: int = 0
    success: int = 0
    failed: int = 0


class TaskXDTO(BaseModel):
    """Response model for a single background task."""

    task_id: str
    user_id: str = ""
    observatory_id: str = ""
    title: str = ""
    description: str = ""
    operation: str
    current_status: str
    progress_message: str = ""
    created_at: str = ""
    updated_at: str = ""


class TaskCompleteResponseDTO(BaseModel):
    """Response for POST /tasks/{id}/complete."""
    task_id: str
    status: str
    observatory_id: str
    observatory_enabled: bool


# ── Users ──────────────────────────────────────────────────────


class UserProfileDTO(BaseModel):
    """Response for GET /users/me."""
    user_id: str
    username: str
    fullname: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str
    is_disabled: bool = False
    created_at: str = ""
    updated_at: str = ""


# ── Catalogs (response) ────────────────────────────────────────


class ObservatoryXDTO(BaseModel):
    """Response for create / get / update / list observatories."""
    observatory_id: str
    title: str
    description: str = ""
    image_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ObservatorySetupResponseDTO(BaseModel):
    """Response for POST /observatories/setup."""
    observatory_id: str
    task_id: str
    status: str = "pending"
    message: str = ""


class ObservatoryDeleteResponseDTO(BaseModel):
    """Response for DELETE /observatories/{id}."""
    deleted: bool


class CatalogCreatedResponseDTO(BaseModel):
    """Response for POST /catalogs."""
    catalog_id: str


class CatalogCreatedBulkResponseDTO(BaseModel):
    """Response for POST /catalogs/bulk."""
    catalog_ids: List[str]


class CatalogSummaryDTO(BaseModel):
    """Lightweight catalog entry returned by GET /catalogs."""
    catalog_id: str
    name: str
    value: str
    catalog_type: str


class _CatalogItemAliasResp(BaseModel):
    catalog_item_alias_id: Optional[str] = None
    value: str
    value_type: str
    description: str = ""


class CatalogItemResponseDTO(BaseModel):
    """Item sub-object inside a full CatalogResponseDTO."""
    catalog_item_id: str
    name: str
    value: str
    code: int
    value_type: str
    temporal_value: Optional[str] = None
    description: str = ""
    aliases: List[_CatalogItemAliasResp] = Field(default_factory=list)
    children: List["CatalogItemResponseDTO"] = Field(default_factory=list)

CatalogItemResponseDTO.model_rebuild()


class CatalogResponseDTO(BaseModel):
    """Full catalog returned by GET /catalogs/{id}."""
    catalog_id: str
    name: str
    value: str
    catalog_type: str
    description: str = ""
    items: List[CatalogItemResponseDTO] = Field(default_factory=list)


class CatalogXDTO(BaseModel):
    """Catalog entry returned by GET /observatories/{id}/catalogs."""
    catalog_id: str
    name: str
    value: str
    catalog_type: str
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    level: int = 0
    created_at: str
    updated_at: str


class CatalogItemXResponseDTO(BaseModel):
    """Response for catalog-item CRUD endpoints."""
    catalog_item_id: str
    name: str
    value: str
    code: int
    value_type: str
    catalog_type: Optional[str] = None
    temporal_value: Optional[str] = None
    description: str = ""
    created_at: str
    updated_at: str


class CatalogItemDeleteResponseDTO(BaseModel):
    """Response for DELETE /catalog-items/{id}."""
    deleted: bool


class CatalogItemAliasXResponseDTO(BaseModel):
    """Response for alias CRUD endpoints."""
    catalog_item_alias_id: str
    value: str
    value_type: str
    catalog_type: Optional[str] = None
    description: str = ""
    created_at: str
    updated_at: str


class ProductSimpleDTO(BaseModel):
    """Response for product CRUD endpoints."""
    product_id: str
    name: str
    description: str = ""
    created_at: str
    updated_at: str


class ProductDeleteResponseDTO(BaseModel):
    """Response for DELETE /products/{id}."""
    deleted: bool


class DataSourceDeleteResponseDTO(BaseModel):
    """Response for DELETE /datasources/{id}."""
    deleted: bool
    records_removed: int


# ── Notifications ──────────────────────────────────────────────


class NotificationReadAllResponseDTO(BaseModel):
    """
    Response for PUT /notifications/read-all.

    Attributes:
        modified: Number of notifications marked as read.
    """

    modified: int


class NotificationClearReadResponseDTO(BaseModel):
    """
    Response for DELETE /notifications/clear-read.

    Attributes:
        deleted: Number of read notifications deleted.
    """

    deleted: int


# ── Building blocks ────────────────────────────────────────────


class BuildingBlockCreateDTO(BaseModel):
    """
    Payload for POST /building-blocks.

    Attributes:
        name: Human-readable identifier for this building block.
        command: Entrypoint command executed inside the container.
        image: Docker image reference (e.g. 'python:3.11-slim').
        description: Optional description providing context.
    """

    name: str
    command: str
    image: str
    description: str = ""


class BuildingBlockUpdateDTO(BaseModel):
    """
    Payload for PATCH /building-blocks/{building_block_id}.

    All fields are optional; only provided fields are updated.

    Attributes:
        name: New human-readable identifier.
        command: New entrypoint command.
        image: New Docker image reference.
        description: New description.
    """

    name: Optional[str] = None
    command: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None


class BuildingBlockDTO(BaseModel):
    """
    Response model for a building block.

    Attributes:
        building_block_id: System-generated unique identifier.
        name: Human-readable identifier.
        command: Container entrypoint command.
        image: Docker image reference.
        description: Optional description.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 last-update timestamp.
    """

    building_block_id: str
    name: str
    command: str
    image: str
    description: str = ""
    created_at: str = ""
    updated_at: str = ""


# ── Patterns ───────────────────────────────────────────────────


class PatternCreateDTO(BaseModel):
    """
    Payload for POST /patterns.

    Attributes:
        name: Human-readable pattern name.
        task: Task category (e.g. 'transform', 'ingest').
        pattern: Pattern type (e.g. 'map-reduce', 'pipeline').
        description: Optional description providing context.
        workers: Number of parallel worker instances (minimum 1).
        loadbalancer: Load-balancing strategy (default 'round-robin').
        building_block_id: Optional ID of an existing BuildingBlock to associate.
    """

    name: str
    task: str
    pattern: str
    description: str = ""
    workers: int = 1
    loadbalancer: str = "round-robin"
    building_block_id: Optional[str] = None


class PatternUpdateDTO(BaseModel):
    """
    Payload for PATCH /patterns/{pattern_id}.

    All fields are optional; only provided fields are updated.

    Attributes:
        name: New pattern name.
        task: New task category.
        pattern: New pattern type.
        description: New description.
        workers: New worker count (minimum 1).
        loadbalancer: New load-balancing strategy.
        building_block_id: New building block reference.
    """

    name: Optional[str] = None
    task: Optional[str] = None
    pattern: Optional[str] = None
    description: Optional[str] = None
    workers: Optional[int] = None
    loadbalancer: Optional[str] = None
    building_block_id: Optional[str] = None


class PatternDTO(BaseModel):
    """
    Response model for a pattern.

    Attributes:
        pattern_id: System-generated unique identifier.
        name: Human-readable pattern name.
        task: Task category.
        pattern: Pattern type.
        description: Optional description.
        workers: Number of parallel worker instances.
        loadbalancer: Load-balancing strategy.
        building_block_id: Associated building block ID, if any.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 last-update timestamp.
    """

    pattern_id: str
    name: str
    task: str
    pattern: str
    description: str = ""
    workers: int = 1
    loadbalancer: str = "round-robin"
    building_block_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


# ── Stages ─────────────────────────────────────────────────────


class StageCreateDTO(BaseModel):
    """
    Payload for POST /stages.

    Attributes:
        name: Stage name.
        source: Input source identifier or URI.
        sink: Output sink identifier or URI.
        endpoint: HTTP or messaging endpoint exposed by this stage.
        transformation_id: Optional ID of an existing Pattern to apply.
    """

    name: str
    source: str
    sink: str
    endpoint: str
    transformation_id: Optional[str] = None


class StageUpdateDTO(BaseModel):
    """
    Payload for PATCH /stages/{stage_id}.

    All fields are optional; only provided fields are updated.

    Attributes:
        name: New stage name.
        source: New input source.
        sink: New output sink.
        endpoint: New endpoint URI.
        transformation_id: New pattern reference.
    """

    name: Optional[str] = None
    source: Optional[str] = None
    sink: Optional[str] = None
    endpoint: Optional[str] = None
    transformation_id: Optional[str] = None


class StageDTO(BaseModel):
    """
    Response model for a stage.

    Attributes:
        stage_id: System-generated unique identifier.
        name: Stage name.
        source: Input source identifier or URI.
        sink: Output sink identifier or URI.
        endpoint: Endpoint exposed by this stage.
        transformation_id: Associated pattern ID, if any.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 last-update timestamp.
    """

    stage_id: str
    name: str
    source: str
    sink: str
    endpoint: str
    transformation_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


# ── Workflows ──────────────────────────────────────────────────


class WorkflowCreateDTO(BaseModel):
    """
    Payload for POST /workflows.

    Attributes:
        name: Workflow name.
        stage_ids: Ordered list of stage IDs that form the workflow pipeline.
    """

    name: str
    stage_ids: List[str] = Field(default_factory=list)


class WorkflowUpdateDTO(BaseModel):
    """
    Payload for PATCH /workflows/{workflow_id}.

    All fields are optional; only provided fields are updated.

    Attributes:
        name: New workflow name.
        stage_ids: New ordered list of stage IDs.
    """

    name: Optional[str] = None
    stage_ids: Optional[List[str]] = None


class WorkflowDTO(BaseModel):
    """
    Response model for a workflow.

    Attributes:
        workflow_id: System-generated unique identifier.
        name: Workflow name.
        stage_ids: Ordered list of stage IDs in the pipeline.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 last-update timestamp.
    """

    workflow_id: str
    name: str
    stage_ids: List[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


# ── Services ───────────────────────────────────────────────────


class ServiceCreateDTO(BaseModel):
    """
    Payload for POST /services.

    Attributes:
        name: Service name, searchable via the SVC() DSL operator.
        owner_id: User ID of the service owner.
        description: Optional description providing context.
        public: Whether this service is publicly discoverable via SVC(*) queries.
        workflow_id: Optional ID of an existing workflow to attach.
    """

    name: str
    owner_id: str
    description: str = ""
    public: bool = False
    workflow_id: Optional[str] = None


class ServiceUpdateDTO(BaseModel):
    """
    Payload for PATCH /services/{service_id}.

    All fields are optional; only provided fields are updated.

    Attributes:
        name: New service name.
        description: New description.
        public: New visibility flag.
        workflow_id: New workflow reference.
    """

    name: Optional[str] = None
    description: Optional[str] = None
    public: Optional[bool] = None
    workflow_id: Optional[str] = None


class ServiceDTO(BaseModel):
    """
    Response model for a service.

    Attributes:
        service_id: System-generated unique identifier.
        name: Service name.
        description: Optional description.
        owner_id: User ID of the service owner.
        public: Whether the service is publicly discoverable.
        workflow_id: Associated workflow ID, if any.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 last-update timestamp.
    """

    service_id: str
    name: str
    description: str = ""
    owner_id: str
    public: bool = False
    workflow_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class BuildingBlockInlineDTO(BaseModel):
    """
    Inline building block definition used inside ServiceIndexDTO.

    Attributes:
        name: Human-readable identifier.
        command: Container entrypoint command.
        image: Docker image reference.
        description: Optional description.
    """

    name: str
    command: str
    image: str
    description: str = ""


class PatternInlineDTO(BaseModel):
    """
    Inline pattern definition used inside ServiceIndexDTO.

    Provide either building_block (to create one inline) or building_block_id
    (to reference an existing one). Both are optional.

    Attributes:
        name: Human-readable pattern name.
        task: Task category.
        pattern: Pattern type.
        description: Optional description.
        workers: Number of parallel worker instances.
        loadbalancer: Load-balancing strategy.
        building_block: Inline building block to create together with this pattern.
        building_block_id: ID of an existing building block to reference.
    """

    name: str
    task: str
    pattern: str
    description: str = ""
    workers: int = 1
    loadbalancer: str = "round-robin"
    building_block: Optional[BuildingBlockInlineDTO] = None
    building_block_id: Optional[str] = None


class StageInlineDTO(BaseModel):
    """
    Inline stage definition used inside ServiceIndexDTO.

    Provide either transformation (to create a pattern inline) or
    transformation_id (to reference an existing one). Both are optional.

    Attributes:
        name: Stage name.
        source: Input source identifier or URI.
        sink: Output sink identifier or URI.
        endpoint: HTTP or messaging endpoint exposed by this stage.
        transformation: Inline pattern to create together with this stage.
        transformation_id: ID of an existing pattern to reference.
    """

    name: str
    source: str
    sink: str
    endpoint: str
    transformation: Optional[PatternInlineDTO] = None
    transformation_id: Optional[str] = None


class WorkflowInlineDTO(BaseModel):
    """
    Inline workflow definition used inside ServiceIndexDTO.

    Attributes:
        name: Workflow name.
        stages: Ordered list of inline stage definitions (minimum one stage required).
    """

    name: str
    stages: List[StageInlineDTO] = Field(default_factory=list)


class ServiceIndexDTO(BaseModel):
    """
    Payload for POST /services/index.

    One-shot request that creates the complete Service -> Workflow -> Stages ->
    Patterns -> BuildingBlocks tree in a single call. At every level you can
    either provide inline definitions or reference existing IDs.

    Attributes:
        name: Service name.
        owner_id: User ID of the service owner.
        description: Optional description.
        public: Whether this service is publicly discoverable.
        workflow: Inline workflow definition to create together with the service.
        workflow_id: ID of an existing workflow to attach instead.
    """

    name: str
    owner_id: str
    description: str = ""
    public: bool = False
    workflow: Optional[WorkflowInlineDTO] = None
    workflow_id: Optional[str] = None


class ServiceIndexResponseDTO(BaseModel):
    """
    Response for POST /services/index.

    Summary of every entity created or referenced during the bulk index call.

    Attributes:
        service_id: ID of the created service.
        workflow_id: ID of the created or referenced workflow, if any.
        stage_ids: IDs of all created stages.
        pattern_ids: IDs of all created patterns.
        building_block_ids: IDs of all created building blocks.
    """

    service_id: str
    workflow_id: Optional[str] = None
    stage_ids: List[str] = Field(default_factory=list)
    pattern_ids: List[str] = Field(default_factory=list)
    building_block_ids: List[str] = Field(default_factory=list)


class ServiceQueryDTO(BaseModel):
    """
    Payload for POST /services/search (Services DSL search).

    DSL query uses the SVC() operator:
        jub.v1.SVC(*)                       -- all services
        jub.v1.SVC(name=cancer)             -- name contains 'cancer'
        jub.v1.SVC(public=true)             -- public only
        jub.v1.SVC(owner=usr_abc)           -- by owner
        jub.v1.SVC(name=cancer,public=true) -- combined

    Attributes:
        query: Services DSL query string.
        limit: Maximum number of results to return (1-1000).
        skip: Number of results to skip for pagination.
    """

    query: str
    limit: int = 100
    skip: int = 0


class ServiceDeleteResponseDTO(BaseModel):
    """
    Response for DELETE /services/{service_id}.

    Attributes:
        deleted: Whether the service was deleted.
        service_id: ID of the deleted service.
        cascade: Counts of cascade-deleted entities (e.g. {'workflow': 1, 'stages': 3}).
    """

    deleted: bool
    service_id: str
    cascade: Dict[str, Any] = Field(default_factory=dict)
