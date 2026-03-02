
# Copyright 2026 MADTEC-2025-M-478 Project Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import json as J
from typing import List,Dict,Optional
from pydantic import BaseModel,field_validator

class LevelCatalog(BaseModel):
    """
    This model represents a reference to a catalog associated with a specefic level.

    Attributes:
        level (int):
             The level of the catalog.
        cid (str): 
            Unique identifier of the catalog.
    """
    level: int
    cid: str

class Observatory(BaseModel):
    """
    An observatory is an object that contains N catalogs.
    Represents a space from which products and their characteristics are observed
    and queried.
    
    Attributes:
        obid (str): 
            Unique identifier of the observatory.
        title (str):
             Display name used for the observatory.
        image_url (str):
            URL of an image to represent the observatory.
        description (str):
            Textual description providing context.
        catalogs (List[LevelCatalog]): 
            Collection of instances from the LevelCatalog model that references the catalogs and theirs levels.
        disabled (bool): 
            Indicates whether the observatory is inactive.
    """
    obid:str=""
    title: str="Observatory"
    image_url:str=""
    description:str=""
    catalogs:List[LevelCatalog]=[]
    disabled:bool = False

class CatalogItem(BaseModel):
    """
    Represents a single entry withing a Catalog.
    
    Attributes :
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
    """
    value:str
    display_name:str
    code:int
    description:str
    metadata:Dict[str,str]

class Catalog(BaseModel):
    """
    Catalogs represents a dynamic collection of Xvars, used for organizing 
    and validating attributes across specific categories.
 
    Attributes :
        cid (str): 
            Unique identifier of the catalog.
        display_name (str): 
            Human-readable name of the catalog.
        items (str): 
            Collection of items that belong to this catalog.
        kind (str): 
            Type of the catalog (e.g. 'TEMPORAL','SPATIAL','INTEREST')
    
    Validators :
        -`display_name` is normalized by a field validator.
        -`items` ensures type consistency and whitespace normalization.
    """
    cid:str = ""
    display_name:str = ""
    items: List[CatalogItem] = []
    kind:str = ""
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
    @field_validator("items")
    def remove_double_spaces_in_items(cls,items):
        """
        Ensures that all the items are dict types and normalize their `display_name` fields.
        
        Args:
            items (List[CatalogItem]): 
                Raw items list.
            
        Returns:
            xs (List[CatalogItem]): 
                Normalized collection of CatalogItem instances.
        """
        xs = []
        for item in items:
            if type(item) ==dict:
                item = CatalogItem(**item)
            item.display_name = " ".join(item.display_name.split())
            xs.append(item)
        return xs
    
    @staticmethod
    def from_json( path:str)->'Catalog':
        """
        Creates a Catalog instance from a JSON file.
        
        Args:
            path (str):
                Path string to the JSON file that contains the catalog data.
        
        Returns:
            catalog (Catalog): 
                A validated Catalog instance.
        """
        with open(path,"rb") as f:
            data = J.loads(f.read())
            catalog = Catalog(**data)
            return catalog

class InequalityFilter(BaseModel):
    """
    Helps to filter the products by comparison operations

    Attributes:
        gt (int | None):
            Represents a 'greater than' comparison.
        lt (int | None):
            Represents a 'less than' comparison.
        eq (int | None):
            Represents a 'equal to' comparison.
    """
    gt: Optional[int] = None 
    lt: Optional[int] = None
    eq: Optional[int] = None

    @field_validator('*')
    def empty_str_to_none(cls, v):
        """
        Converts empty strings to None.

        Args:
            v (int | str | None): 
                If the value is an empty string, it is converted to None.
        Returns:
            v (int | None):
                The original value, except that empty strings are converted to None.
        """
        return v if v != "" else None

class InterestFilter(BaseModel):
    """
    Represents a filter over a product interest attribute.

    An interest can be filtered either by an exact value (e.g. sex = "male")
    or by an inequality filter (e.g. age > 20), but not both
    
    Attributes:
        value (str | None):
            The exact value of the filter.
        inequality (InequalityFilter | None):
            Inequality-based filter.
    """
    value: Optional[str] = None
    inequality: Optional[InequalityFilter] = None

    @field_validator('inequality')
    def check_exclusivity(cls, v, values):
        """
        Validates mutual exclusivity between `value`and `inequality`

        Args:
            v (InequalityFilter | None):
                The value provided for the `inequality` field.
            values (dict):
                Dictionary containing previously validaded field values.
        Returns:
            InequalityFilter | None:
                The original inequality value if validation succeeds.
        Raises:
            ValueError:
                If both `value` and `inequality` are provided,
                or if neither is provided.
        """
        if v and values.get('value'):
            raise ValueError('Provide either a value or an inequality, not both')
        if not v and not values.get('value'):
            raise ValueError('Provide at least a value or an inequality')
        return v
    
class  TemporalFilter(BaseModel):
    """
    Helps to filter products by time-based variables. 
    
    Attributes:
        low (int):
        high (int):
    """
    low: int
    high: int

class SpatialFilter(BaseModel):
    """
    Represents a spatial filter composed of country,state,
    and municipality.

    Attributes:
        country (str):
            Name of the country where the product is based on.
        state (str):
            Name of the state where the product is based on.
        municipality (str):
            Name of the municipality where the product is based on.
        
    """
    country: str
    state: str
    municipality: str
    def make_regex(self):
        """
        Builds a regular expression pattern from the model attributes.
        
        Returns
            pattern (str):
                An uppercase regular expression pattern representing
                the spatial filter.
        """
        pattern = "^"
        pattern += re.escape(self.country) if self.country != "*" else ".*"
        pattern += r"\."
        pattern += re.escape(self.state) if self.state != "*" else ".*"
        pattern += r"\."
        pattern += re.escape(self.municipality) if self.municipality != "*" else ".*"
        return pattern.upper()

class ProductFilter(BaseModel):
    """
    Unify all the other filter models.
    This model can be used as a body for a
    request to the Jub Api.
    
    Attributes:
        temporal (TemporalFilter | None):
            Represents the temporal filters (e.g. date range).
        spatial (SpatialFilter | None):
            Represents the spatial filters
            (e.g. country, state , municipality).
        interest (List[InterestFilter]):
            Represents a collection of a product interest attributes
            (e.g. demographic attributes such as age or sex).

    """
    temporal: Optional[TemporalFilter] = None
    spatial: Optional[SpatialFilter] = None
    interest: List[InterestFilter]=[]

class Level(BaseModel):
    """
    Represents a single level within a catalog structure.

    Attributes:
        index (int):
            Position in the user interface.
        cid (str): 
            Catalog unique identifier for this level.
        value (str): 
            The value in the catalog
        kind (str): 
            The kind of the level spatial, temporal, and so on.
    """
    index:int
    cid:str
    value:str
    kind:str =""

class Product(BaseModel):
    """
    Products are the visual representation of combinations of values from catalogs.
    Each product can be visualized as a dataview, chart, or item in the UI. 

    Attributes:
        pid (str): 
            Product unique identifier.
        description (str): 
            Textual description of the product.
        levels (List[Level]):
            List of catalog levels that defines the product's position.
        product_type (str): 
            Category of the product.
        level_path (str):
            The name of the levels.
        profile (str):
            The value of the levels. 
        product_name (str): 
            Display name of the product.
        tags (List[str]): 
            Tags for advancing permission control.
        url (str):
            Path to the product in the application.
    """
    pid:str=""
    description:str=""
    levels:List[Level]=[]
    product_type: str=""
    level_path:str=""
    profile:str=""
    product_name: str=""
    tags:List[str]=[]
    url:str =""
