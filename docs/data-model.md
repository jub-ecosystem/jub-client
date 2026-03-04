This section describes the data model used in the Jub Client. It includes the main entities, their attributes, and relationships.

<h2>Observatory</h2>

An `Observatory` is an object that contains N catalogs and products.

It represents a logical space where products and catalogs are organized and queried.

```python
class Observatory(BaseModel):
    obid:str=""
    title: str="Observatory"
    image_url:str=""
    description:str=""
    catalogs:List[LevelCatalog]=[]
    disabled:bool = False

```

**Attributes**

* `obid` : `str`
    Unique identifier of the observatory.

* `title` : `str`
    Display name used for the observatory.

* `image_url` : `str`
    URL of an image to represent the observatory.

* `description` : `str`
    Textual description providing context.

* `catalogs` : `List[LevelCatalog]`
    Collection of instances from the LevelCatalog model that references the catalogs and their levels.

* `disabled`: `bool`
    Indicates whether the observatory is inactive.

**Embedded Structure**
The `catalogs` attribute embeds catalog-level structures directly inside the observatory. This means that, in this V1 models, the observatory contains its catalog configuration as part of its structure.

<h2>Catalog</h2>

`Catalog` represents a dynamic collection of Xvars, used for organizing and validating attributes across specific categories.

```python
class Catalog(BaseModel):
    cid:str = ""
    display_name:str = ""
    items: List[CatalogItem] = []
    kind:str = ""
```

Attributes

* `cid` : `str`
    Unique identifier of the catalog.

* `display_name` : `str`
    Human-readable name of the catalog.

* `items` : `List[CatalogItem]`
    Collection of items that belong to this catalog.

* `kind` : `str`
    Type of the catalog (e.g. TEMPORAL, SPATIAL, INTEREST).

**Validators**

* `display_name` is normalized by collapsing consecutive whitespace into a single space.

* `items` ensures type consistency (dict → `CatalogItem`) and normalizes each item's `display_name`.

Embedded Structure

The `items` attribute embeds `CatalogItem` instances directly inside the catalog.
Catalog items are not referenced externally; they are stored as part of the catalog structure.

<h2>Product</h2>

`Product` represents the visual representation of combinations of values from catalogs.
Each product can be visualized as a dataview, chart, or item in the UI.

```python
class Product(BaseModel):
    pid:str=""
    description:str=""
    levels:List[Level]=[]
    product_type: str=""
    level_path:str=""
    profile:str=""
    product_name: str=""
    tags:List[str]=[]
    url:str =""
```

**Attributes**

* `pid`: `str`
    Product unique identifier.

* `description`: `str`
    Textual description of the product.

* `levels`: `List[Level]`
    List of catalog levels that defines the product's position.

* `product_type`: `str`
    Category of the product.

* `level_path`: `str`
    The name of the levels.

* `profile`: `str`
    The value of the levels.

* `product_name`: `str`
    Display name of the product.

* `tags` : `List[str]`
    Tags for advancing permission control.

* `url` : `str`
    Path to the product in the application.


**Embedded Relationship via Levels**

The `levels` attribute embeds `Level` instances inside the product.

Each `Level` corresponds to a value defined within a catalog.