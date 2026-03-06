from pathlib import Path
from jub.dto import Catalog, CatalogItem

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
    JSON_PATH = (Path(__file__).parent).parent.joinpath("data/catalog.json")
    catalog = Catalog.from_json(JSON_PATH)

    assert isinstance(catalog,Catalog)
    assert catalog.cid == "7jz0ygosp3oe"
    assert catalog.kind == "SPATIAL"

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
