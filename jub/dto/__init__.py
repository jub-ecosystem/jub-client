
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

from typing import List,Dict,Optional
from pydantic import BaseModel,field_validator
import re
import json as J

class LevelCatalog(BaseModel):
    level: int
    cid: str

class Observatory(BaseModel):
    obid:str=""
    title: str="Observatory"
    image_url:str=""
    description:str=""
    catalogs:List[LevelCatalog]=[]
    disabled:bool = False

class CatalogItem(BaseModel):
    value:str
    display_name:str
    code:int
    description:str
    metadata:Dict[str,str]

class Catalog(BaseModel):
    cid:str = ""
    display_name:str = ""
    items: List[CatalogItem] = []
    kind:str = ""
    @field_validator("display_name")
    def remove_double_spaces(cls,value):
        x = " ".join(value.split())
        return x
    @field_validator("items")
    def remove_double_spaces_in_items(cls,items):
        xs = []
        for item in items:
            if type(item) ==dict:
                item = CatalogItem(**item)
            item.display_name = " ".join(item.display_name.split())
            xs.append(item)
        return xs
    
    @staticmethod
    def from_json( path:str)->'Catalog':
        with open(path,"rb") as f:
            data = J.loads(f.read())
            catalog = Catalog(**data)
            return catalog

class InequalityFilter(BaseModel):
    gt: Optional[int] = None  # Greater than
    lt: Optional[int] = None  # Less than
    eq: Optional[int] = None  # Equal to

    @field_validator('*')
    def empty_str_to_none(cls, v):
        return v if v != "" else None

class InterestFilter(BaseModel):
    # Allow either a simple value (str) or an inequality filter
    value: Optional[str] = None
    inequality: Optional[InequalityFilter] = None

    # Ensure either value or inequality is provided, but not both
    @field_validator('inequality')
    def check_exclusivity(cls, v, values):
        if v and values.get('value'):
            raise ValueError('Provide either a value or an inequality, not both')
        if not v and not values.get('value'):
            raise ValueError('Provide at least a value or an inequality')
        return v
    
class  TemporalFilter(BaseModel):
    low: int
    high: int

class SpatialFilter(BaseModel):
    country: str
    state: str
    municipality: str
    def make_regex(self):
        pattern = "^"
        pattern += re.escape(self.country) if self.country != "*" else ".*"
        pattern += r"\."
        pattern += re.escape(self.state) if self.state != "*" else ".*"
        pattern += r"\."
        pattern += re.escape(self.municipality) if self.municipality != "*" else ".*"
        return pattern.upper()


class ProductFilter(BaseModel):
    temporal: Optional[TemporalFilter] = None
    spatial: Optional[SpatialFilter] = None
    interest: List[InterestFilter]=[]

class Level(BaseModel):
    index:int
    cid:str
    value:str
    kind:str =""

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
