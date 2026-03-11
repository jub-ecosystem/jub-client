from pydantic import BaseModel,Field, field_validator
from typing import Dict, List

from jub.dto import LevelCatalog
"""
Client Adjustment Notes for V2 DTOs

With the introduction of the V2 domain models, the client must align
with the stricter data contracts defined by the updated Pydantic models.

Key considerations:

Removed Embedded Relationships
Since embedded collections (e.g., catalogs inside Observatory)
were removed, client methods that previously expected nested data
must be updated to either ignore legacy fields returned by the API
or adapt to the new link-based relationship models.

Methods that will be affected:
    
    update_observatory_catalogs()
        Will be no longer working with a list of LevelCatalog model instances,
        instead will be working with the new `ObservatoryCatalogLink` model.

    get_observatory()
        The method will need to remove the `catalogs` field that is returned
        in the `Observatory` model instance.

"""

class Observatory(BaseModel):
    """
    Unlike the V1 models, this Observatory model
    does not contain direct references to catalogs.
    Relationships between observatories and catalogs must be 
    represented through the `ObservatoryCatalogLink` model.

    Attributes:
        obid (str):
            Unique identifier of the observatory.
        
        title (str):
            Display name used for the observatory.
            Defaults to 'Observatory'
        
        image_url (str):
            URL of an image to represent the observatory.

        description (str):
            Textual description providing context.
     
        disabled (bool): 
            Indicates whether the observatory is inactive.
    """
    obid : str = ""
    title : str = "Observatory"
    image_url : str = ""
    description : str = ""
    disabled : bool = False

class Catalog(BaseModel):
    """
    This version removes the embedded `items` collection.
    Relationships between catalogs and items must be expressed
    thorugh the `CatalogItemLink` model.
    
    Attributes :
        cid (str): 
            Unique identifier of the catalog.
    
        display_name (str): 
            Human-readable name of the catalog.
        
        kind (str): 
            Type of the catalog (e.g. 'TEMPORAL','SPATIAL','INTEREST')
    
    Validators :
        -`display_name` is normalized by a field validator.
    """
    cid : str = ""
    display_name : str = ""
    kind : str = ""

    @field_validator("display_name")
    def remove_double_spaces(cls,value):
        """
        Normalizes `display_name` by collapsing consecutive whitespace into a single space.

        Args: 
            value (str): 
                A string with value of the attribute `display_name`
            
        Returns:
            x (str): 
                A new string of the `display_name` without double spaces.
        """
        x = " ".join(value.split())
        return x

class CatalogItem(BaseModel):
    """
    Represents an item within a catalog. This model is no
    longer attached to the `items` field of the Catalog model.
    Relationships between catalog items and catalogs are now
    represented through the `CatalogItemLink` model.
    
    Attributes :
        item_id (str):
            Unique identifier of the catalog item.
            
        value (str):
            Value for storage.
        
        display_name (str):
            A redeable name for the catalog item.
        
        code (str): 
            An unique code that identifies the catalog item.
        
        description (str): 
            Textual description providing context.
        
        metadata (Dict[str,str]): 
            A dictionary that contains extra data to provide context
            about the catalog item.
    
    Validators :
        -`display_name` is normalized by a field validator.
    """
    item_id : str
    value : str
    display_name : str
    code : int 
    description : str
    metadata : Dict[str,str]
    
    @field_validator("display_name")
    def remove_double_spaces(cls,value):
        """
        Normalizes `display_name` by collapsing consecutive whitespace into a single space.

        Args: 
            value (str): 
                A string with value of the attribute `display_name`
            
        Returns:
            x (str): 
                A new string of the `display_name` without double spaces.
        """
        x = " ".join(value.split())
        return x

class Product(BaseModel):
    """
    This new version of the model removes the `levels` field, which
    was previously used to reference relationships with different catalogs.
    
    Attributes:
        pid (str): 
            Product unique identifier.
        
        description (str): 
            Textual description of the product.
        
        product_type (str): 
            Category of the product.
        
        product_name (str): 
            Display name of the product.
      
        tags (List[str]): 
            Tags for advancing permission control.
        
        url (str):
            Path to the product in the application.
    """
    pid : str = ""
    description : str = ""
    product_type : str = ""
    product_name : str = ""
    tags : List[str] = Field(default_factory=List[str])
    url : str = ""

class ObservatoryCatalogLink(BaseModel):
    """
    Represents the relationship between an `Observatory` and
    a `Catalog` model.

    Attributes:
        obid (str):
            Unique identifier of the observatory.
        
        cid (str):
            Unique identifier of the catalog.
        
        level (LevelCatalog):
            It helps to represent the order for the UI.
    """
    obid : str
    cid : str
    level : LevelCatalog
    
class CatalogItemLink(BaseModel):
    """
    Represents the relationship between a `Catalog` and
    a `CatalogItem`. 
    
    Attributes:
        cid (str):
            Unique identifier of the catalog.
       
        item_id (str):
            Unique identifier of the catalog item.
    """
    cid : str
    item_id : str

class ProductObservatoryLink(BaseModel):
    """
    Represents the relationship between a `Product`
    and an `Observatory`.
    
    Attributes:
        pid (str):
            Unique identifer of the product.
        
        obid (str):
            Unique identifier of the observatory.
    """
    pid : str
    obid : str

class ProductCatalogItemLink(BaseModel):
    """
    Represents the relationship between a `Product` and 
    a `CatalogItem`.
    
    Attributes:
        pid (str):
            Unique identifier of the product.
        
        item_id (str):
            Unique identifier of the catalog item.
        
        level (LevelCatalog):
            Defines  the ordering level used in the UI.
            
        kind (str):
            The kind of the level spatial, temporal, and so on.
    """
    pid : str
    item_id : str
    level : LevelCatalog
    kind : str