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

import pytest
from jub.dto.v1 import InequalityFilter, InterestFilter, ProductFilter, SpatialFilter, TemporalFilter


def test_inequality_filter_defaults():
    inequality_filter = InequalityFilter()
    assert inequality_filter.eq == None
    assert inequality_filter.gt == None
    assert inequality_filter.lt == None
    
def test_inequality_filter_empty_string_validator():
    inequality_filter = InequalityFilter(
        gt="",
        eq="",
        lt=""
    )
    assert inequality_filter.gt == None
    assert inequality_filter.eq == None
    assert inequality_filter.lt == None

def test_interest_filter_defaults():
    interest_filter = InterestFilter()
    assert interest_filter.inequality == None
    assert interest_filter.value == None

def test_interest_filter_rejects_both():
    with pytest.raises(ValueError):
        InterestFilter(value="male",inequality=InequalityFilter(gt=20))
    

def test_spatial_filter_regex_method():
    sf1 = SpatialFilter(
        country="Mexico",
        state="San Luis Potosi",
        municipality="Ciudad Valles"
    )
    assert sf1.make_regex() == "^MEXICO\.SAN\ LUIS\ POTOSI\.CIUDAD\ VALLES"

    sf2 = SpatialFilter(
        country="*",
        state="San Luis Potosi",
        municipality="*"
    )
    assert sf2.make_regex() == "^.*\.SAN\ LUIS\ POTOSI\..*"

    sf3 = SpatialFilter(
        country="*",
        state="*",
        municipality="*"
    )
    assert sf3.make_regex() == "^.*\..*\..*"


def test_product_filter_defaults():
    product_filter = ProductFilter()

    assert product_filter.temporal == None
    assert product_filter.spatial == None
    assert product_filter.interest == []