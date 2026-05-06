"""
Unit tests for bulk upload: register_upload, wait_uploads, bulk_upload_products.

upload_product is replaced on each client instance with a simple async function
so no live server is needed and no mock library is required.
"""

import pytest
from option import Ok, Err

from jub.client.v2 import JubClient, BulkUploadResult, FailedUploadEntry
import jub.dto.v2 as DTO


def _upload_response(product_id: str) -> DTO.ProductUploadResponseDTO:
    return DTO.ProductUploadResponseDTO(job_id=f"job-{product_id}", product_id=product_id, status="queued")


@pytest.fixture
def client():
    c = JubClient("http://localhost:5000", "admin", "secret")
    c._token = "test-token"
    c.user_id = "user-abc"
    return c


# ── register_upload ────────────────────────────────────────────


def test_register_upload_bytes_returns_pending_count(client):
    result = client.register_upload("prod-001", b"data")
    assert result.is_ok
    assert result.unwrap() == 1


def test_register_upload_str_path_accepted(client):
    result = client.register_upload("prod-001", "/some/file.csv")
    assert result.is_ok
    assert result.unwrap() == 1


def test_register_upload_invalid_type_returns_err(client):
    result = client.register_upload("prod-001", 12345)
    assert result.is_err
    assert isinstance(result.unwrap_err(), TypeError)


def test_register_upload_accumulates(client):
    client.register_upload("prod-001", b"a")
    r = client.register_upload("prod-002", b"b")
    assert r.unwrap() == 2
    assert len(client._upload_queue) == 2


# ── wait_uploads — empty queue ─────────────────────────────────


@pytest.mark.asyncio
async def test_wait_uploads_empty_queue(client):
    result = await client.wait_uploads()
    assert result.is_ok
    r = result.unwrap()
    assert isinstance(r, BulkUploadResult)
    assert r.succeeded == []
    assert r.failed == []


# ── wait_uploads — all succeed ─────────────────────────────────


@pytest.mark.asyncio
async def test_wait_uploads_all_succeed(client):
    async def _ok_upload(product_id, payload):
        return Ok(_upload_response(product_id))

    client.upload_product = _ok_upload
    client.register_upload("prod-001", b"file1")
    client.register_upload("prod-002", b"file2")

    result = await client.wait_uploads(workers=1)
    assert result.is_ok
    r = result.unwrap()
    assert len(r.succeeded) == 2
    assert len(r.failed) == 0
    ids = {d.product_id for d in r.succeeded}
    assert ids == {"prod-001", "prod-002"}


# ── wait_uploads — queue cleared after drain ───────────────────


@pytest.mark.asyncio
async def test_wait_uploads_clears_queue(client):
    async def _ok_upload(product_id, payload):
        return Ok(_upload_response(product_id))

    client.upload_product = _ok_upload
    client.register_upload("prod-001", b"data")
    await client.wait_uploads()
    assert client._upload_queue == []


# ── wait_uploads — retry on transient failure ──────────────────


@pytest.mark.asyncio
async def test_wait_uploads_retries_on_failure(client):
    call_count = {"n": 0}

    async def _flaky_upload(product_id, payload):
        call_count["n"] += 1
        if call_count["n"] < 2:
            return Err(Exception("transient error"))
        return Ok(_upload_response(product_id))

    client.upload_product = _flaky_upload
    client.register_upload("prod-001", b"data")

    result = await client.wait_uploads(workers=1, max_retries=2)
    assert result.is_ok
    r = result.unwrap()
    assert len(r.succeeded) == 1
    assert len(r.failed) == 0
    assert call_count["n"] == 2


# ── wait_uploads — permanent failure after exhausting retries ──


@pytest.mark.asyncio
async def test_wait_uploads_permanent_failure(client):
    async def _always_fail(product_id, payload):
        return Err(Exception("disk full"))

    client.upload_product = _always_fail
    client.register_upload("prod-001", b"data")

    result = await client.wait_uploads(workers=1, max_retries=1)
    assert result.is_ok
    r = result.unwrap()
    assert len(r.succeeded) == 0
    assert len(r.failed) == 1
    entry = r.failed[0]
    assert isinstance(entry, FailedUploadEntry)
    assert entry.product_id == "prod-001"
    assert entry.attempts == 1
    assert "disk full" in entry.last_error


# ── wait_uploads — mixed results ───────────────────────────────


@pytest.mark.asyncio
async def test_wait_uploads_mixed_success_and_failure(client):
    async def _mixed_upload(product_id, payload):
        if product_id == "prod-bad":
            return Err(Exception("bad file"))
        return Ok(_upload_response(product_id))

    client.upload_product = _mixed_upload
    client.register_upload("prod-ok", b"ok")
    client.register_upload("prod-bad", b"bad")

    result = await client.wait_uploads(workers=1, max_retries=1)
    assert result.is_ok
    r = result.unwrap()
    assert len(r.succeeded) == 1
    assert r.succeeded[0].product_id == "prod-ok"
    assert len(r.failed) == 1
    assert r.failed[0].product_id == "prod-bad"


# ── wait_uploads — unauthenticated client ──────────────────────


@pytest.mark.asyncio
async def test_wait_uploads_requires_auth():
    c = JubClient("http://localhost:5000", "admin", "secret")
    c.register_upload("prod-001", b"data")
    result = await c.wait_uploads()
    assert result.is_err
    assert "not authenticated" in str(result.unwrap_err()).lower()


# ── bulk_upload_products ───────────────────────────────────────


@pytest.mark.asyncio
async def test_bulk_upload_products_convenience_wrapper(client):
    async def _ok_upload(product_id, payload):
        return Ok(_upload_response(product_id))

    client.upload_product = _ok_upload

    result = await client.bulk_upload_products([
        ("prod-A", b"bytes-a"),
        ("prod-B", b"bytes-b"),
    ])
    assert result.is_ok
    r = result.unwrap()
    assert len(r.succeeded) == 2
    assert len(r.failed) == 0


@pytest.mark.asyncio
async def test_bulk_upload_products_invalid_payload_returns_err(client):
    result = await client.bulk_upload_products([("prod-001", 999)])
    assert result.is_err
    assert isinstance(result.unwrap_err(), TypeError)
