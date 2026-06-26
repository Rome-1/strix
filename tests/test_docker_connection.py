"""Tests for macOS Docker socket fallback in check_docker_connection."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from docker.errors import DockerException

from strix.interface.utils import check_docker_connection


def test_returns_from_env_client(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = object()
    monkeypatch.setattr("strix.interface.utils.docker.from_env", lambda: sentinel)

    assert check_docker_connection() is sentinel


def test_falls_back_to_macos_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_docker_exception() -> object:
        raise DockerException("no default socket")

    monkeypatch.setattr("strix.interface.utils.docker.from_env", raise_docker_exception)
    monkeypatch.setattr("strix.interface.utils.sys.platform", "darwin")
    # Pretend every candidate socket exists.
    monkeypatch.setattr("strix.interface.utils.Path.exists", lambda *_: True)

    fallback_client = MagicMock()
    fallback_client.ping.return_value = True
    monkeypatch.setattr("strix.interface.utils.docker.DockerClient", lambda **_: fallback_client)

    result = check_docker_connection()

    assert result is fallback_client
    fallback_client.ping.assert_called_once()


def test_raises_runtime_error_on_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_docker_exception() -> object:
        raise DockerException("no daemon")

    monkeypatch.setattr("strix.interface.utils.docker.from_env", raise_docker_exception)
    monkeypatch.setattr("strix.interface.utils.sys.platform", "linux")

    with pytest.raises(RuntimeError, match="Docker not available"):
        check_docker_connection()
