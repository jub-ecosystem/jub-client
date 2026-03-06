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
import jub.config as CX
from nanoid import generate as nanoid
from jub.client import JubClient
from jub.dto import Catalog, KindEnum, Level, LevelCatalog, Observatory, Product

@pytest.fixture
def client():
    return JubClient(hostname="localhost",port=5000)

@pytest.fixture
def pid():
    return nanoid(alphabet=CX.JUB_CLIENT_OBSERVATORY_ID_ALPHABET,
                  size = CX.JUB_CLIENT_OBSERVATORY_ID_SIZE)

def test_create_product(client,pid):
    
    product =  Product(
            pid=pid,
        )
    res = client.create_products([product])
    assert res.is_ok

    client.delete_product(pid)

def test_get_products(client):
    res = client.get_products()
    assert res.is_ok
    assert isinstance(res.unwrap(),list)

def test_query_products(client):
    products = [
        Product
    ]


def test_delete_product(client,pid):
    res_create = client.create_products([
        Product(
            pid = pid
        )
    ])
    assert res_create.is_ok
    res_delete = client.delete_product(pid)
    assert res_delete.is_ok
    assert res_delete.unwrap() == pid