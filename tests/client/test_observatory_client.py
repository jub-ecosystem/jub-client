import pytest
import jub.config as CX
from nanoid import generate as nanoid
from jub.client import JubClient
from jub.dto import LevelCatalog, Observatory

@pytest.fixture
def client():
    return JubClient(hostname="Localhost",port=5000)

@pytest.fixture()
def obid():
    return nanoid(alphabet=CX.JUB_CLIENT_OBSERVATORY_ID_ALPHABET,
                  size=CX.JUB_CLIENT_OBSERVATORY_ID_SIZE
                )     

@pytest.fixture()
def observatory(client,obid):
    obs = Observatory(obid=obid)
    res = client.create_observatory(obs)
    assert res.is_ok
    
    yield obs
    client.delete_observatory(obid)

def test_create_observatory(client,obid):
    res_create = client.create_observatory(Observatory(
        obid = obid
    ))
    assert res_create.is_ok
    assert res_create.unwrap() == obid
    
    res_get_observatory = client.get_observatory(obid)
    assert res_get_observatory.is_ok
    assert res_get_observatory.unwrap().obid == obid
    
    client.delete_observatory(obid)
    
def test_get_observatory(client,observatory):
    res = client.get_observatory(observatory.obid)
    assert res.is_ok
    
    obs = res.unwrap()
    assert obs.obid == observatory.obid
    
def test_get_observatories(client):
    res = client.get_observatories(limit = 5)
    
    assert res.is_ok
    assert isinstance(res.unwrap(),list)

def test_update_observatory_catalogs(client,observatory):
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
                obid = observatory.obid,
                catalogs = catalogs
                )
    
    assert res.is_ok
    assert res.unwrap() == observatory.obid
    
    res_obs = client.get_observatory(obid = res.unwrap())
    assert res_obs.is_ok
    obs = res_obs.unwrap()
    assert obs.obid == observatory.obid
    assert isinstance(obs.catalogs,list)
    assert len(obs.catalogs) == 3

def test_delete_observatory(client,obid):
    res_create = client.create_observatory(observatory = Observatory(
        obid = obid
    ))
    assert res_create._is_ok
    assert res_create.unwrap() == obid
    
    
    res_delete = client.delete_observatory(obid=obid)
    assert res_delete.is_ok
    assert res_delete.unwrap() == obid

