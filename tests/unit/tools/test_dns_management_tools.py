"""Unit tests for dns_management tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import APIType
from src.tools import dns_management as dns


@pytest.fixture
def local_settings() -> MagicMock:
    s = MagicMock()
    s.api_type = APIType.LOCAL
    s.log_level = "INFO"
    return s


@pytest.fixture
def cloud_settings() -> MagicMock:
    s = MagicMock()
    s.api_type = APIType.CLOUD_EA
    s.log_level = "INFO"
    return s


def _make_client(get_return=None, put_return=None):
    client = MagicMock()
    client.is_authenticated = False
    client.authenticate = AsyncMock()
    client.get = AsyncMock(return_value=get_return or {})
    client.put = AsyncMock(return_value=put_return or {})
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


# ---------------------------------------------------------------------------
# _ensure_local_api guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_wan_dns_requires_local(cloud_settings):
    with pytest.raises(NotImplementedError, match="local"):
        await dns.list_wan_dns("default", cloud_settings)


@pytest.mark.asyncio
async def test_update_wan_dns_requires_local(cloud_settings):
    with pytest.raises(NotImplementedError, match="local"):
        await dns.update_wan_dns("wan-1", "default", cloud_settings, confirm=True)


@pytest.mark.asyncio
async def test_get_dns_filter_settings_requires_local(cloud_settings):
    with pytest.raises(NotImplementedError, match="local"):
        await dns.get_dns_filter_settings("default", cloud_settings)


@pytest.mark.asyncio
async def test_update_dns_filter_requires_local(cloud_settings):
    with pytest.raises(NotImplementedError, match="local"):
        await dns.update_dns_filter("default", cloud_settings, confirm=True)


# ---------------------------------------------------------------------------
# list_wan_dns
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_wan_dns_returns_only_wans(local_settings):
    response = [
        {"_id": "wan-1", "name": "WAN", "purpose": "wan", "wan_dns1": "8.8.8.8"},
        {"_id": "net-1", "name": "LAN", "purpose": "corporate"},
    ]
    client = _make_client(get_return=response)

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.list_wan_dns("default", local_settings)

    assert len(result) == 1
    assert result[0]["id"] == "wan-1"
    assert result[0]["wan_dns1"] == "8.8.8.8"


@pytest.mark.asyncio
async def test_list_wan_dns_empty_when_no_wans(local_settings):
    response = [{"_id": "net-1", "name": "LAN", "purpose": "corporate"}]
    client = _make_client(get_return=response)

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.list_wan_dns("default", local_settings)

    assert result == []


@pytest.mark.asyncio
async def test_list_wan_dns_dict_response(local_settings):
    response = {
        "data": [{"_id": "wan-1", "name": "WAN", "purpose": "wan", "wan_dns2": "8.8.4.4"}]
    }
    client = _make_client(get_return=response)

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.list_wan_dns("default", local_settings)

    assert result[0]["wan_dns2"] == "8.8.4.4"


# ---------------------------------------------------------------------------
# update_wan_dns
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_wan_dns_requires_confirm(local_settings):
    with pytest.raises(ValueError, match="confirm=True"):
        await dns.update_wan_dns("wan-1", "default", local_settings, confirm=False)


@pytest.mark.asyncio
async def test_update_wan_dns_dry_run(local_settings):
    result = await dns.update_wan_dns(
        "wan-1", "default", local_settings, dns1="1.1.1.1", dry_run=True
    )
    assert result["status"] == "dry_run"
    assert result["changes"]["wan_dns1"] == "1.1.1.1"
    assert result["changes"]["wan_dns_preference"] == "manual"


@pytest.mark.asyncio
async def test_update_wan_dns_dry_run_preference_auto(local_settings):
    result = await dns.update_wan_dns(
        "wan-1", "default", local_settings, dns_preference="auto", dry_run=True
    )
    assert result["changes"]["wan_dns_preference"] == "auto"
    assert "wan_dns1" not in result["changes"]


@pytest.mark.asyncio
async def test_update_wan_dns_invalid_preference(local_settings):
    with pytest.raises(ValueError, match="dns_preference must be"):
        await dns.update_wan_dns(
            "wan-1", "default", local_settings, dns_preference="invalid", dry_run=True
        )


@pytest.mark.asyncio
async def test_update_wan_dns_success(local_settings):
    put_response = [
        {"_id": "wan-1", "name": "WAN", "wan_dns1": "1.1.1.1", "wan_dns_preference": "manual"}
    ]
    client = _make_client(put_return=put_response)

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.update_wan_dns(
            "wan-1", "default", local_settings, dns1="1.1.1.1", confirm=True
        )

    assert result["wan_dns1"] == "1.1.1.1"
    client.put.assert_called_once()


@pytest.mark.asyncio
async def test_update_wan_dns_auto_sets_manual_preference(local_settings):
    """Providing dns1 without dns_preference should auto-set to manual."""
    client = _make_client(put_return=[{"_id": "wan-1"}])

    with patch.object(dns, "UniFiClient", return_value=client):
        await dns.update_wan_dns(
            "wan-1", "default", local_settings, dns1="8.8.8.8", confirm=True
        )

    call_kwargs = client.put.call_args[1]["json_data"]
    assert call_kwargs["wan_dns_preference"] == "manual"


# ---------------------------------------------------------------------------
# get_dns_filter_settings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_dns_filter_settings_success(local_settings):
    response = [
        {"_id": "ips-1", "dns_filtering": True, "dns_filters": [{"network_id": "net-1"}]}
    ]
    client = _make_client(get_return=response)

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.get_dns_filter_settings("default", local_settings)

    assert result["dns_filtering"] is True
    assert len(result["dns_filters"]) == 1


@pytest.mark.asyncio
async def test_get_dns_filter_settings_empty_response(local_settings):
    client = _make_client(get_return=[])

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.get_dns_filter_settings("default", local_settings)

    assert result == {"dns_filtering": False, "dns_filters": []}


@pytest.mark.asyncio
async def test_get_dns_filter_settings_dict_response(local_settings):
    response = {"data": {"_id": "ips-1", "dns_filtering": False, "dns_filters": []}}
    client = _make_client(get_return=response)

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.get_dns_filter_settings("default", local_settings)

    assert result["dns_filtering"] is False


# ---------------------------------------------------------------------------
# update_dns_filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_dns_filter_requires_confirm(local_settings):
    with pytest.raises(ValueError, match="confirm=True"):
        await dns.update_dns_filter("default", local_settings, confirm=False)


@pytest.mark.asyncio
async def test_update_dns_filter_dry_run_global_toggle(local_settings):
    ips = [{"_id": "ips-1", "dns_filtering": False, "dns_filters": []}]
    client = _make_client(get_return=ips)

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.update_dns_filter(
            "default", local_settings, dns_filtering=True, dry_run=True
        )

    assert result["status"] == "dry_run"
    assert result["changes"]["dns_filtering"] is True


@pytest.mark.asyncio
async def test_update_dns_filter_dry_run_per_network(local_settings):
    ips = [{"_id": "ips-1", "dns_filtering": True, "dns_filters": []}]
    client = _make_client(get_return=ips)

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.update_dns_filter(
            "default",
            local_settings,
            network_id="net-1",
            filter_level="family",
            dry_run=True,
        )

    assert result["status"] == "dry_run"
    filters = result["changes"]["dns_filters"]
    assert any(f.get("network_id") == "net-1" and f.get("filter") == "family" for f in filters)


@pytest.mark.asyncio
async def test_update_dns_filter_updates_existing_network_entry(local_settings):
    ips = [
        {
            "_id": "ips-1",
            "dns_filtering": True,
            "dns_filters": [{"network_id": "net-1", "filter": "none", "blocked_sites": []}],
        }
    ]
    client = _make_client(get_return=ips)

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.update_dns_filter(
            "default",
            local_settings,
            network_id="net-1",
            filter_level="work",
            dry_run=True,
        )

    filters = result["changes"]["dns_filters"]
    entry = next(f for f in filters if f.get("network_id") == "net-1")
    assert entry["filter"] == "work"


@pytest.mark.asyncio
async def test_update_dns_filter_success(local_settings):
    ips_get = [{"_id": "ips-1", "dns_filtering": False, "dns_filters": []}]
    ips_put = [{"_id": "ips-1", "dns_filtering": True, "dns_filters": []}]
    client = _make_client(get_return=ips_get, put_return=ips_put)

    with patch.object(dns, "UniFiClient", return_value=client):
        result = await dns.update_dns_filter(
            "default", local_settings, dns_filtering=True, confirm=True
        )

    assert result["dns_filtering"] is True
    client.put.assert_called_once()
