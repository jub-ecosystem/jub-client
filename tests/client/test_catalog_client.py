from jub.client import JubClient
from nanoid import generate as nanoid
from jub.dto import Catalog, KindEnum
import pytest
import jub.config as CX

@pytest.fixture()
def client():
    return JubClient(hostname="Localhost",port=5000)

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
    