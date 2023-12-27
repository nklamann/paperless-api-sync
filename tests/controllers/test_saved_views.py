"""Test saved_views."""

from unittest.mock import patch

import pytest

from pypaperless import Paperless
from pypaperless.controllers import SavedViewsController
from pypaperless.controllers.base import CreateMixin, DeleteMixin, ResultPage, UpdateMixin
from pypaperless.models import SavedView, SavedViewFilterRule


@pytest.fixture(scope="module")
def dataset(data):
    """Represent current data."""
    return data["saved_views"]


async def test_endpoint(paperless: Paperless) -> None:
    """Test endpoint."""
    assert isinstance(paperless.saved_views, SavedViewsController)
    assert not isinstance(paperless.saved_views, CreateMixin | UpdateMixin | DeleteMixin)


async def test_list_and_get(paperless: Paperless, dataset):
    """Test list."""
    with patch.object(paperless, "request_json", return_value=dataset):
        result = await paperless.saved_views.list()

        assert isinstance(result, list)
        assert len(result) > 0
        for item in result:
            assert isinstance(item, int)

        page = await paperless.saved_views.get()

        assert isinstance(page, ResultPage)
        assert len(page.items) > 0
        assert isinstance(page.items.pop(), SavedView)


async def test_iterate(paperless: Paperless, dataset):
    """Test iterate."""
    with patch.object(paperless, "request_json", return_value=dataset):
        async for item in paperless.saved_views.iterate():
            assert isinstance(item, SavedView)


async def test_one(paperless: Paperless, dataset):
    """Test one."""
    with patch.object(paperless, "request_json", return_value=dataset["results"][0]):
        item = await paperless.saved_views.one(72)

        assert isinstance(item, SavedView)

        if isinstance(item.filter_rules, list):
            if len(item.filter_rules) > 0:
                assert isinstance(item.filter_rules.pop(), SavedViewFilterRule)
        else:
            assert False
