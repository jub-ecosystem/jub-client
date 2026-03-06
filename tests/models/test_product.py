

from jub.dto import Level, Product


def test_verify_default_values():
    product = Product()
    assert product.pid == ""
    assert product.description == ""
    assert product.levels == []
    assert product.product_type == ""
    assert product.level_path == ""
    assert product.profile == ""
    assert product.product_name == ""
    assert product.tags == []
    assert product.url  == ""

def test_mutable_fields():
    p1 = Product()
    p2 = Product()
    p1.levels.append(
        Level(
            index = 1,
            cid = "12345",
            value = "value",
            kind = "spatial"    
        )
    )
    p1.tags.extend(["tag1","tag2","tag3"])

    assert p1.levels is not p2.levels
    assert p1.tags is not p2.tags

    assert len(p1.levels) == 1 and len(p2.levels) == 0
    assert len(p1.tags) == 3 and len(p2.tags) == 0