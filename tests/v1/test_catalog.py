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

from pathlib import Path

from httpx import patch
from jub.dto.v1 import Catalog, CatalogItem

def test_default_values_catalog():
    catalog = Catalog()
    
    assert catalog.cid == ""
    assert catalog.display_name == ""
    assert isinstance(catalog.items,list) 
    assert catalog.items == []
    assert catalog.kind == "INTEREST"
def test_validators_catalog():
    catalog = Catalog(
        display_name= "Catalog      test    name",
        items = [
            CatalogItem(
                value = "value",
                display_name = "Catalog item 1      name           test",
                code = 1,
                description = "item description", 
                metadata = {
                }
            ),
            {
                "value" : "value",
                "display_name" : "Catalog item 2         name          test",
                "code" : 2,
                "description" : "item description", 
                "metadata" : {
                }
            }
        ]
    )
    
    assert catalog.display_name == "Catalog test name"
    assert isinstance(catalog.items[0],CatalogItem)
    assert catalog.items[0].display_name == "Catalog item 1 name test"
    assert catalog.items[1].display_name == "Catalog item 2 name test"
    

def test_create_catalog_from_json():
    # JSON_PATH = (Path(__file__).parent.parent).joinpath("./data/catalogs/sex.json")
    from unittest.mock import patch, mock_open
    mock_json_content = """
    {
        "cid": "sex3fb25a076cf021f2",
        "display_name": "Sexo",
        "items": [
            {"value": "HOMBRE", "display_name": "Hombre", "code": 0},
            {"value": "MUJER", "display_name": "Mujer", "code": 1}
        ],
        "kind": "INTEREST"
    }
    """
    with patch("builtins.open", mock_open(read_data=mock_json_content)):
        # The path here doesn't even need to exist!
        catalog = Catalog.from_json("fake_path.json")
    
    # 3. Assertions
    assert catalog.cid == "sex3fb25a076cf021f2"
    assert len(catalog.items) == 2
def test_default_mutables():
    """
    Verifies that each Catalog instance has an independent
    `items` list.

    Although the field is declared with a mutable default
    value, instances must not share state.
    """
    c1 = Catalog()
    c2 = Catalog()

    c1.items.append(
        CatalogItem(
            value =  "value",
            display_name = "Catalog item",
            code = "12345",
            description = "Catolog item description",
            metadata = {}
        )
    )
    assert c1.items is not c2.items
    assert len(c1.items) == 1
    assert len(c2.items) == 0   
    
def test_reject_empty_display_name():
    catalog = Catalog(display_name="     ")
    assert isinstance(catalog,Catalog)
    assert catalog.display_name == ""
