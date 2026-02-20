import pytest
from jub import JubClient
from jub.dto import Observatory


@pytest.fixture
def client():
    return JubClient(hostname="localhost", port=5000)

def test_get_observatories(client):
    
    # GET /api/v4/observatories [Observatories]
    result   = client.get_observatories()
  
    assert result.is_ok

    observatories = result.unwrap()
    assert isinstance(observatories, list)
    
def test_get_catalogs(client):
    
    # GET /api/v4/catalogs [Catalogs]
    result   = client.get_catalogs()
  
    assert result.is_ok

    catalogs = result.unwrap()
    assert isinstance(catalogs, list)
    
def test_create_observatory(client):
    local_obs = Observatory(
            title       = "Test Observatory",
            description = "This is a test observatory",
            catalogs    = []
    )
    
    result = client.create_observatory(
        observatory =local_obs
    )

    assert result.is_ok
    obid = result.unwrap()
    observatory_result = client.get_observatory(obid=obid)
    assert observatory_result.is_ok
    remote_obs = observatory_result.unwrap()
    assert remote_obs.title == local_obs.title
    assert remote_obs.description == local_obs.description
    # assert remote_obs.name