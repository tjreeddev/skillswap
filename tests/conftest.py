"""Shared fixtures. Every test uses a temporary data file, never the real data.json.

Application modules are imported inside fixtures so that, before the app exists,
each test fails individually instead of the whole file failing to collect.
"""

import pytest


@pytest.fixture
def data_path(tmp_path):
    return tmp_path / "data.json"


@pytest.fixture
def store(data_path):
    from skillswap.core import Store

    return Store(data_path)


@pytest.fixture
def app(data_path):
    from skillswap.app import create_app

    app = create_app(data_path=data_path)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def reload_store(data_path):
    """Open a fresh Store on the same file (simulates reading saved state)."""
    from skillswap.core import Store

    return Store(data_path)
