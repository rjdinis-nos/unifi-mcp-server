"""Unit tests for zbf_matrix tools (deprecated — all raise NotImplementedError)."""

from unittest.mock import MagicMock

import pytest

from src.config import APIType
from src.tools import zbf_matrix as zbf


@pytest.fixture
def settings() -> MagicMock:
    s = MagicMock()
    s.api_type = APIType.LOCAL
    s.log_level = "INFO"
    return s


@pytest.mark.asyncio
async def test_get_zbf_matrix_raises(settings):
    with pytest.raises(NotImplementedError):
        await zbf.get_zbf_matrix("default", settings)


@pytest.mark.asyncio
async def test_get_zone_policies_raises(settings):
    with pytest.raises(NotImplementedError):
        await zbf.get_zone_policies("default", "zone-1", settings)


@pytest.mark.asyncio
async def test_update_zbf_policy_raises(settings):
    with pytest.raises(NotImplementedError):
        await zbf.update_zbf_policy(
            site_id="default",
            source_zone_id="zone-1",
            destination_zone_id="zone-2",
            action="allow",
            settings=settings,
            confirm=True,
        )


@pytest.mark.asyncio
async def test_block_application_by_zone_raises(settings):
    with pytest.raises(NotImplementedError):
        await zbf.block_application_by_zone(
            site_id="default",
            zone_id="zone-1",
            application_id="app-1",
            settings=settings,
            confirm=True,
        )


@pytest.mark.asyncio
async def test_list_blocked_applications_raises(settings):
    with pytest.raises(NotImplementedError):
        await zbf.list_blocked_applications("default", settings=settings)


@pytest.mark.asyncio
async def test_list_blocked_applications_with_zone_raises(settings):
    with pytest.raises(NotImplementedError):
        await zbf.list_blocked_applications("default", zone_id="zone-1", settings=settings)


@pytest.mark.asyncio
async def test_get_zone_matrix_policy_raises(settings):
    with pytest.raises(NotImplementedError):
        await zbf.get_zone_matrix_policy("default", "zone-1", "zone-2", settings)


@pytest.mark.asyncio
async def test_delete_zbf_policy_raises(settings):
    with pytest.raises(NotImplementedError):
        await zbf.delete_zbf_policy(
            site_id="default",
            source_zone_id="zone-1",
            destination_zone_id="zone-2",
            settings=settings,
            confirm=True,
        )
