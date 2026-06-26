"""Tests for black-box code_locations stripping in the reporting tool."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from strix.tools.reporting.tool import _do_create


def _valid_cvss() -> dict[str, str]:
    return {
        "attack_vector": "N",
        "attack_complexity": "L",
        "privileges_required": "N",
        "user_interaction": "N",
        "scope": "U",
        "confidentiality": "H",
        "integrity": "H",
        "availability": "H",
    }


def _code_locations() -> list[dict[str, Any]]:
    return [{"file": "src/controllers/auth.js", "start_line": 15, "end_line": 18}]


def _base_kwargs() -> dict[str, Any]:
    return {
        "title": "SQL Injection in login",
        "description": "Found via fuzzing the login endpoint.",
        "impact": "Full database read access.",
        "target": "http://localhost:3000",
        "technical_analysis": "User input concatenated into SQL.",
        "poc_description": "Send a crafted payload.",
        "poc_script_code": "import requests; requests.post(...)",
        "remediation_steps": "Use parameterized queries.",
        "cvss_breakdown": _valid_cvss(),
        "endpoint": "/rest/user/login",
        "method": "POST",
        "cve": None,
        "cwe": None,
        "code_locations": _code_locations(),
    }


def _patch_report_state(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    report_state = MagicMock()
    report_state.get_existing_vulnerabilities.return_value = []
    report_state.add_vulnerability_report.return_value = "vuln-0001"
    monkeypatch.setattr(
        "strix.report.state.get_global_report_state",
        lambda: report_state,
    )
    monkeypatch.setattr(
        "strix.report.dedupe.check_duplicate",
        AsyncMock(return_value={"is_duplicate": False}),
    )
    return report_state


@pytest.mark.asyncio
async def test_blackbox_strips_code_locations(monkeypatch: pytest.MonkeyPatch) -> None:
    report_state = _patch_report_state(monkeypatch)

    result = await _do_create(**_base_kwargs(), is_whitebox=False)

    assert result["success"] is True
    report_state.add_vulnerability_report.assert_called_once()
    assert report_state.add_vulnerability_report.call_args.kwargs["code_locations"] is None


@pytest.mark.asyncio
async def test_whitebox_preserves_code_locations(monkeypatch: pytest.MonkeyPatch) -> None:
    report_state = _patch_report_state(monkeypatch)

    result = await _do_create(**_base_kwargs(), is_whitebox=True)

    assert result["success"] is True
    report_state.add_vulnerability_report.assert_called_once()
    locations = report_state.add_vulnerability_report.call_args.kwargs["code_locations"]
    assert locations is not None
    assert locations[0]["file"] == "src/controllers/auth.js"


@pytest.mark.asyncio
async def test_blackbox_strip_still_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_report_state(monkeypatch)

    result = await _do_create(**_base_kwargs(), is_whitebox=False)

    assert result["success"] is True
    assert result["report_id"] == "vuln-0001"
