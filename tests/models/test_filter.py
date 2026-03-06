import pytest
from jub.client import JubClient
from jub.dto import InequalityFilter, InterestFilter, ProductFilter, SpatialFilter, TemporalFilter


@pytest.fixture
def client():
    return JubClient(hostname="localhost",port=5000)

def test_filters_defaults():
    inequality_filter = InequalityFilter(
    )
    interest_filter = InterestFilter(
    )
    temporal_filter = TemporalFilter(
    )
    spatial_filter = SpatialFilter(
    )
    product_filter = ProductFilter(
    )