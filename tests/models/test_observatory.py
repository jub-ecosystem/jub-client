
from dataclasses import dataclass
from doctest import FAIL_FAST
from typing import List

from jub.dto import LevelCatalog, Observatory


def test_default_values_observatory():
    obs  = Observatory()
    
    assert obs.obid == ""
    assert obs.title == "Observatory"
    assert obs.image_url == ""
    assert obs.description == ""
    assert isinstance(obs.catalogs,list)
    assert obs.catalogs == []
    assert obs.disabled == False
