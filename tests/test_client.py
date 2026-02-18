import pytest
from jub import JubClient
from jub.dto import Observatory


@pytest.fixture
def client():
    return JubClient(hostname="localhost", port=5000)

def test_create_observatory(client):
    local_obs = Observatory(
            title="Test Observatory",
            description="This is a test observatory"
    )
    result = client.create_observatory(
        observatory=local_obs
    )
    assert result.is_ok
    obid = result.unwrap()
    observatory_result = client.get_observatory(obid=obid)
    assert observatory_result.is_ok
    remote_obs = observatory_result.unwrap()
    assert remote_obs.title == local_obs.title
    assert remote_obs.description == local_obs.description
    # assert remote_obs.name