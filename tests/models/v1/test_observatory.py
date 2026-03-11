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

from dataclasses import dataclass
from doctest import FAIL_FAST
from typing import List

from jub.dto.v1 import LevelCatalog, Observatory


def test_default_values_observatory():
    obs  = Observatory()
    
    assert obs.obid == ""
    assert obs.title == "Observatory"
    assert obs.image_url == ""
    assert obs.description == ""
    assert isinstance(obs.catalogs,list)
    assert obs.catalogs == []
    assert obs.disabled == False
