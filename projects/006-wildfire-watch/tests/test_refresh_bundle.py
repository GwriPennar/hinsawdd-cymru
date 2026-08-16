"""Smoke test for the all-in-one refresh HTML bundle."""
from __future__ import annotations

import re
from pathlib import Path

import refresh_bundle as rb
import runs_index as ri


def test_write_refresh_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(rb, "REFRESH_ROOT", tmp_path / "refresh")
    monkeypatch.setattr(rb, "STABLE_POINTER", tmp_path / "run_all.html")
    monkeypatch.setattr(rb, "INDEX_PATH", tmp_path / "runs_index.json")

    index = ri.build_index()
    meta = rb.write_refresh_bundle(index, stamp="TESTSTAMP")
    latest = Path(meta["latest_html"])
    # meta paths are relative to project ROOT
    latest_abs = (ri.ROOT / latest).resolve() if not latest.is_absolute() else latest
    # In this test REFRESH_ROOT is tmp — rewrite expectation
    latest_abs = tmp_path / "refresh" / "latest" / "index.html"
    assert latest_abs.exists()
    html = latest_abs.read_text()
    assert "Project 006 — full refresh" in html
    assert "satellite thermal anomalies" in html
    assert html.count('<section class="card"') >= 1
    # Image links (if any) should resolve
    base = latest_abs.parent
    for src in re.findall(r'src="([^"]+)"', html):
        assert (base / src).resolve().exists(), src
    assert (tmp_path / "run_all.html").exists()
