from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import src.api as api

import pytest
import psycopg2


def test_pool_created_at_startup_and_closed_at_shutdown(monkeypatch):
    database_pool = MagicMock()
    pool_factory = MagicMock(return_value=database_pool)
    monkeypatch.setattr(api, "create_db_pool", pool_factory)

    assert api.db_pool is None

    with TestClient(api.app):
        pool_factory.assert_called_once_with()
        assert api.db_pool is database_pool
        database_pool.closeall.assert_not_called()

    database_pool.closeall.assert_called_once_with()
    assert api.db_pool is None

def test_pool_closed_when_client_context_exits_with_error(monkeypatch):
    database_pool = MagicMock()
    pool_factory = MagicMock(return_value=database_pool)
    monkeypatch.setattr(api, "create_db_pool", pool_factory)

    with pytest.raises(RuntimeError, match="simulated test failure"):
        with TestClient(api.app):
            assert api.db_pool is database_pool
            raise RuntimeError("simulated test failure")

    pool_factory.assert_called_once_with()
    database_pool.closeall.assert_called_once_with()
    assert api.db_pool is None

def test_startup_fails_when_pool_creation_fails(monkeypatch):
    pool_factory = MagicMock(
        side_effect=psycopg2.OperationalError("database unavailable")
    )
    monkeypatch.setattr(api, "create_db_pool", pool_factory)

    with pytest.raises(
        psycopg2.OperationalError,
        match="database unavailable",
    ):
        with TestClient(api.app):
            pass

    pool_factory.assert_called_once_with()
    assert api.db_pool is None