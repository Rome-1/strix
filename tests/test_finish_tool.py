"""Tests for ``finish_scan``'s soft-fallback report persistence.

Regression coverage for usestrix/strix#294: empty narrative fields must not
discard the report. ``_do_finish`` substitutes a placeholder and still persists
the scan instead of returning a hard validation error.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from strix.tools.finish.tool import _MISSING_FIELD_PLACEHOLDER, _do_finish


def _finish(monkeypatch, **fields: str) -> tuple[dict, MagicMock]:
    report_state = MagicMock()
    report_state.vulnerability_reports = [{"id": "v1"}]
    monkeypatch.setattr(
        "strix.tools.finish.tool.get_global_report_state",
        lambda: report_state,
    )
    result = _do_finish(parent_id=None, **fields)
    return result, report_state


def test_all_fields_present_persists_report(monkeypatch) -> None:
    result, report_state = _finish(
        monkeypatch,
        executive_summary="Summary",
        methodology="Method",
        technical_analysis="Analysis",
        recommendations="Recs",
    )

    assert result["success"] is True
    assert result["scan_completed"] is True
    report_state.update_scan_final_fields.assert_called_once_with(
        executive_summary="Summary",
        methodology="Method",
        technical_analysis="Analysis",
        recommendations="Recs",
    )


def test_empty_fields_substitute_placeholder_and_persist(monkeypatch) -> None:
    result, report_state = _finish(
        monkeypatch,
        executive_summary="Summary",
        methodology="",
        technical_analysis="Analysis",
        recommendations="   ",
    )

    # The report is still persisted rather than discarded (issue #294).
    assert result["success"] is True
    assert result["scan_completed"] is True
    report_state.update_scan_final_fields.assert_called_once_with(
        executive_summary="Summary",
        methodology=_MISSING_FIELD_PLACEHOLDER,
        technical_analysis="Analysis",
        recommendations=_MISSING_FIELD_PLACEHOLDER,
    )


def test_subagent_call_rejected(monkeypatch) -> None:
    report_state = MagicMock()
    monkeypatch.setattr(
        "strix.tools.finish.tool.get_global_report_state",
        lambda: report_state,
    )

    result = _do_finish(
        parent_id="root-agent",
        executive_summary="Summary",
        methodology="Method",
        technical_analysis="Analysis",
        recommendations="Recs",
    )

    assert result["success"] is False
    report_state.update_scan_final_fields.assert_not_called()
