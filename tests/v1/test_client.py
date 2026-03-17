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

from jub.client.v1 import JubClient
from nanoid import generate as nanoid
from jub.dto.v1 import Catalog, KindEnum,Observatory, LevelCatalog, Product, ProductFilter
import pytest
import jub.config as CX

@pytest.fixture()
def client():
    return JubClient(api_url="http://localhost:5000")

@pytest.fixture
def cid():
    return nanoid(alphabet=CX.JUB_CLIENT_OBSERVATORY_ID_ALPHABET,size=CX.JUB_CLIENT_OBSERVATORY_ID_SIZE)

@pytest.fixture
def catalog(client,cid):
    catalog = Catalog(
        cid = cid,
        display_name = "Catalog test",
        kind  = KindEnum.spatial
    )
    res = client.create_catalog(catalog)
    assert res.is_ok
    assert res.unwrap() == cid

    yield catalog
    client.delete_catalog(cid)
    
def test_create_catalog(client,cid):
    catalog = Catalog(
        cid = cid,
        display_name = "Catalog    test",
        kind = KindEnum.spatial
    )
    res_create = client.create_catalog(catalog)
    assert res_create.is_ok

    res_get = client.get_catalog(cid)
    assert res_get.is_ok
    assert res_get.unwrap().cid == cid
    
    client.delete_catalog(cid)

def test_get_catalogs(client):
    res = client.get_catalogs()
    assert res.is_ok
    catalogs = res.unwrap()
    assert isinstance(catalogs,list)

def test_get_catalog(client,catalog):
    res = client.get_catalog(catalog.cid)
    assert res.is_ok
    assert res.unwrap().cid == catalog.cid

def test_delete_catalog(client,cid):
    res_create = client.create_catalog(Catalog(
        cid = cid
    ))
    assert res_create.is_ok
    assert res_create.unwrap() == cid

    res_delete = client.delete_catalog(cid)

    assert res_delete.is_ok
    assert res_delete.unwrap() == cid


@pytest.fixture
def obid(client):
    local_obs = Observatory(
        title       = "Test Observatory",
        description = "This is a test observatory",
        catalogs    = [],
        obid=nanoid(alphabet=CX.JUB_CLIENT_OBSERVATORY_ID_ALPHABET,size=CX.JUB_CLIENT_OBSERVATORY_ID_SIZE)
    )
    
    result = client.create_observatory(
        observatory =local_obs
    )

    assert result.is_ok
    obid = result.unwrap()
    yield obid
    # Cleanup after test
    client.delete_observatory(obid=obid)

@pytest.fixture()
def observatory(client,obid):
    obs = Observatory(obid=obid)
    res = client.create_observatory(obs)
    assert res.is_ok
    
    yield obs
    client.delete_observatory(obid)

def test_create_observatory(client):
    obid       = nanoid(alphabet=CX.JUB_CLIENT_OBSERVATORY_ID_ALPHABET,size=CX.JUB_CLIENT_OBSERVATORY_ID_SIZE)

    res_create = client.create_observatory(Observatory(
        obid        = obid,
        description = "This is a test observatory",
        title       = "Test Observatory"
    ))
    assert res_create.is_ok
    assert res_create.unwrap() == obid
    
    res_get_observatory = client.get_observatory(obid)
    assert res_get_observatory.is_ok
    assert res_get_observatory.unwrap().obid == obid
    
    client.delete_observatory(obid)
    
def test_get_observatory(client,obid):
    res = client.get_observatory(obid)
    assert res.is_ok
    
    obs = res.unwrap()
    assert obs.obid == obid
    
def test_get_observatories(client):
    res = client.get_observatories(limit = 5)
    
    assert res.is_ok
    assert isinstance(res.unwrap(),list)

def test_update_observatory_catalogs(client,obid):
    catalogs = [
        LevelCatalog(
            cid="12345",
            level=1
        ),
        LevelCatalog(
            cid = "23456",
            level = 1
        ),
        LevelCatalog(
            cid = "34567",
            level = 1
        )
    ]
    res = client.update_observatory_catalogs(
                obid = obid,
                catalogs = catalogs
                )
    
    assert res.is_ok
    assert res.unwrap() == obid
    
    res_obs = client.get_observatory(obid = res.unwrap())
    assert res_obs.is_ok
    obs = res_obs.unwrap()
    assert obs.obid == obid
    assert isinstance(obs.catalogs,list)
    assert len(obs.catalogs) == 3

def test_delete_observatory(client):
    obid = nanoid(alphabet=CX.JUB_CLIENT_OBSERVATORY_ID_ALPHABET,size=CX.JUB_CLIENT_OBSERVATORY_ID_SIZE)
    res_create = client.create_observatory(Observatory(
        obid = obid
    ))
    assert res_create.is_ok
    assert res_create.unwrap() == obid
    
    
    res_delete = client.delete_observatory(obid=obid)
    assert res_delete.is_ok
    assert res_delete.unwrap() == obid

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
    res_observatory = client.create_observatory(Observatory())
    assert res_observatory.is_ok
    obid = res_observatory.unwrap()
    res_catalog = client.create_catalog(Catalog())
    assert res_catalog.is_ok
    cid = res_catalog.unwrap()
    
    res_update_observatory_catalogs = client.update_observatory_catalogs(obid,[
        LevelCatalog(
            level = 1,
            cid = cid
        )
    ])
    assert res_update_observatory_catalogs.is_ok
    
    p1_id = nanoid(alphabet=CX.JUB_CLIENT_OBSERVATORY_ID_ALPHABET,
                  size = CX.JUB_CLIENT_OBSERVATORY_ID_SIZE)
    
    p2_id = nanoid(alphabet=CX.JUB_CLIENT_OBSERVATORY_ID_ALPHABET,
                  size = CX.JUB_CLIENT_OBSERVATORY_ID_SIZE)

    products = [
        Product(
            pid = p1_id,
            cid = cid
        ),
        Product(
            pid = p2_id,
            cid = cid
        )
    ]
    
    res_create_products = client.create_products(products)
    assert res_create_products.is_ok
    
    res_query = client.query_products(obid,ProductFilter())
    assert res_query.is_ok

    list_products = res_query.unwrap() 
    assert isinstance(list_products,list)
    assert len(list_products)>= 2
    
    
    client.delete_product(p1_id)
    client.delete_product(p2_id)
    client.delete_observatory(obid)
    client.delete_catalog(cid)
    

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