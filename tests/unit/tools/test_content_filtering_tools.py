"""Unit tests for content_filtering tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import APIType
from src.tools import content_filtering as cf
from src.utils.exceptions import ResourceNotFoundError


@pytest.fixture
def local_settings() -> MagicMock:
    s = MagicMock()
    s.api_type = APIType.LOCAL
    s.log_level = "INFO"
    s.get_v2_api_path = MagicMock(return_value="/proxy/network/v2/api/site/default")
    return s


@pytest.fixture
def cloud_settings() -> MagicMock:
    s = MagicMock()
    s.api_type = APIType.CLOUD_EA
    s.log_level = "INFO"
    return s


def _make_client(get_return=None, put_return=None, delete_return=None):
    client = MagicMock()
    client.is_authenticated = False
    client.authenticate = AsyncMock()
    client.get = AsyncMock(return_value=get_return if get_return is not None else [])
    client.put = AsyncMock(return_value=put_return or {})
    client.delete = AsyncMock(return_value=delete_return or {})
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


SAMPLE_FILTER = {
    "_id": "cf-1",
    "name": "Kids Profile",
    "enabled": True,
    "categories": ["ADULT", "GAMBLING"],
    "network_ids": ["net-1"],
    "client_macs": [],
    "allow_list": [],
    "block_list": [],
    "safe_search": [],
    "schedule": None,
}


# ---------------------------------------------------------------------------
# _ensure_local_api guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_content_filters_requires_local(cloud_settings):
    with pytest.raises(NotImplementedError, match="local"):
        await cf.list_content_filters("default", cloud_settings)


@pytest.mark.asyncio
async def test_list_content_filter_categories_requires_local(cloud_settings):
    with pytest.raises(NotImplementedError, match="local"):
        await cf.list_content_filter_categories("default", cloud_settings)


@pytest.mark.asyncio
async def test_update_content_filter_requires_local(cloud_settings):
    with pytest.raises(NotImplementedError, match="local"):
        await cf.update_content_filter("cf-1", "default", cloud_settings, confirm=True)


@pytest.mark.asyncio
async def test_delete_content_filter_requires_local(cloud_settings):
    with pytest.raises(NotImplementedError, match="local"):
        await cf.delete_content_filter("cf-1", "default", cloud_settings, confirm=True)


# ---------------------------------------------------------------------------
# list_content_filters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_content_filters_success(local_settings):
    client = _make_client(get_return=[SAMPLE_FILTER])

    with patch.object(cf, "UniFiClient", return_value=client):
        result = await cf.list_content_filters("default", local_settings)

    assert len(result) == 1
    assert result[0]["id"] == "cf-1"
    assert result[0]["name"] == "Kids Profile"
    assert result[0]["enabled"] is True
    assert "ADULT" in result[0]["categories"]


@pytest.mark.asyncio
async def test_list_content_filters_empty(local_settings):
    client = _make_client(get_return=[])

    with patch.object(cf, "UniFiClient", return_value=client):
        result = await cf.list_content_filters("default", local_settings)

    assert result == []


@pytest.mark.asyncio
async def test_list_content_filters_dict_response(local_settings):
    client = _make_client(get_return={"data": [SAMPLE_FILTER]})

    with patch.object(cf, "UniFiClient", return_value=client):
        result = await cf.list_content_filters("default", local_settings)

    assert len(result) == 1
    assert result[0]["id"] == "cf-1"


# ---------------------------------------------------------------------------
# list_content_filter_categories
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_content_filter_categories_success(local_settings):
    client = _make_client(get_return=["ADULT", "GAMBLING", "ADVERTISEMENT"])

    with patch.object(cf, "UniFiClient", return_value=client):
        result = await cf.list_content_filter_categories("default", local_settings)

    assert "ADULT" in result
    assert "GAMBLING" in result


@pytest.mark.asyncio
async def test_list_content_filter_categories_empty(local_settings):
    client = _make_client(get_return=[])

    with patch.object(cf, "UniFiClient", return_value=client):
        result = await cf.list_content_filter_categories("default", local_settings)

    assert result == []


@pytest.mark.asyncio
async def test_list_content_filter_categories_non_list_response(local_settings):
    client = _make_client(get_return={"error": "unexpected"})

    with patch.object(cf, "UniFiClient", return_value=client):
        result = await cf.list_content_filter_categories("default", local_settings)

    assert result == []


# ---------------------------------------------------------------------------
# update_content_filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_content_filter_requires_confirm(local_settings):
    with pytest.raises(ValueError, match="confirm=True"):
        await cf.update_content_filter("cf-1", "default", local_settings, confirm=False)


@pytest.mark.asyncio
async def test_update_content_filter_dry_run(local_settings):
    client = _make_client(get_return=[SAMPLE_FILTER])

    with patch.object(cf, "UniFiClient", return_value=client):
        result = await cf.update_content_filter(
            "cf-1",
            "default",
            local_settings,
            name="Updated",
            enabled=False,
            dry_run=True,
        )

    assert result["status"] == "dry_run"
    assert result["filter_id"] == "cf-1"
    assert result["changes"]["name"] == "Updated"
    assert result["changes"]["enabled"] is False


@pytest.mark.asyncio
async def test_update_content_filter_not_found(local_settings):
    client = _make_client(get_return=[SAMPLE_FILTER])

    with patch.object(cf, "UniFiClient", return_value=client):
        with pytest.raises(ResourceNotFoundError):
            await cf.update_content_filter(
                "nonexistent", "default", local_settings, enabled=True, confirm=True
            )


@pytest.mark.asyncio
async def test_update_content_filter_success(local_settings):
    updated = {**SAMPLE_FILTER, "enabled": False}
    client = _make_client(get_return=[SAMPLE_FILTER], put_return=updated)

    with patch.object(cf, "UniFiClient", return_value=client):
        result = await cf.update_content_filter(
            "cf-1", "default", local_settings, enabled=False, confirm=True
        )

    assert result["id"] == "cf-1"
    client.put.assert_called_once()
    # _id should be stripped from PUT payload
    put_payload = client.put.call_args[1]["json_data"]
    assert "_id" not in put_payload


@pytest.mark.asyncio
async def test_update_content_filter_categories(local_settings):
    client = _make_client(get_return=[SAMPLE_FILTER], put_return=SAMPLE_FILTER)

    with patch.object(cf, "UniFiClient", return_value=client):
        await cf.update_content_filter(
            "cf-1",
            "default",
            local_settings,
            categories=["HACKING"],
            confirm=True,
        )

    put_payload = client.put.call_args[1]["json_data"]
    assert put_payload["categories"] == ["HACKING"]


@pytest.mark.asyncio
async def test_update_content_filter_dry_run_all_fields(local_settings):
    client = _make_client(get_return=[SAMPLE_FILTER])

    with patch.object(cf, "UniFiClient", return_value=client):
        result = await cf.update_content_filter(
            "cf-1",
            "default",
            local_settings,
            network_ids=["net-2"],
            client_macs=["aa:bb:cc:dd:ee:ff"],
            allow_list=["example.com"],
            block_list=["bad.com"],
            safe_search=["google"],
            dry_run=True,
        )

    changes = result["changes"]
    assert changes["network_ids"] == ["net-2"]
    assert changes["client_macs"] == ["aa:bb:cc:dd:ee:ff"]
    assert changes["allow_list"] == ["example.com"]
    assert changes["block_list"] == ["bad.com"]
    assert changes["safe_search"] == ["google"]


# ---------------------------------------------------------------------------
# delete_content_filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_content_filter_requires_confirm(local_settings):
    with pytest.raises(ValueError, match="confirm=True"):
        await cf.delete_content_filter("cf-1", "default", local_settings, confirm=False)


@pytest.mark.asyncio
async def test_delete_content_filter_dry_run(local_settings):
    result = await cf.delete_content_filter("cf-1", "default", local_settings, dry_run=True)

    assert result["status"] == "dry_run"
    assert result["filter_id"] == "cf-1"
    assert result["action"] == "would_delete"


@pytest.mark.asyncio
async def test_delete_content_filter_success(local_settings):
    client = _make_client()

    with patch.object(cf, "UniFiClient", return_value=client):
        result = await cf.delete_content_filter("cf-1", "default", local_settings, confirm=True)

    assert result["status"] == "success"
    assert result["filter_id"] == "cf-1"
    assert result["action"] == "deleted"
    client.delete.assert_called_once()


# ---------------------------------------------------------------------------
# _normalize helper
# ---------------------------------------------------------------------------


def test_normalize_full_object():
    item = {
        "_id": "cf-1",
        "name": "Test",
        "enabled": True,
        "categories": ["ADULT"],
        "network_ids": ["net-1"],
        "client_macs": ["aa:bb:cc:dd:ee:ff"],
        "allow_list": ["ok.com"],
        "block_list": ["bad.com"],
        "safe_search": ["google"],
        "schedule": {"enabled": False},
        "extra_field": "ignored_in_normalize_but_present",
    }
    result = cf._normalize(item)
    assert result["id"] == "cf-1"
    assert result["name"] == "Test"
    assert result["enabled"] is True
    assert result["categories"] == ["ADULT"]
    assert result["schedule"] == {"enabled": False}


def test_normalize_missing_fields():
    result = cf._normalize({})
    assert result["id"] is None
    assert result["enabled"] is False
    assert result["categories"] == []
