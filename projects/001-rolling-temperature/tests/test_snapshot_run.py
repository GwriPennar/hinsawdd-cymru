from pathlib import Path
import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from snapshot_run import snapshot_run  # noqa: E402


def test_snapshot_run_creates_manifest_and_index(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "project"
    derived = project / "data" / "derived"
    figures = project / "figures"
    derived.mkdir(parents=True)
    figures.mkdir(parents=True)
    summary = {
        "last_published_month": "2026-08",
        "source_last_updated": "01-Sep-2026 11:56",
        "source_snapshot_sha256": "abc123",
        "source_path": "data/raw/example.txt",
        "current_window": {
            "period_label": "Sep 2025 to Aug 2026",
            "mean_temperature_c": 10.65,
            "rank_warmest": 3,
            "window_count": 1701,
        },
    }
    (derived / "summary.json").write_text(
        __import__("json").dumps(summary),
        encoding="utf-8",
    )
    (derived / "rolling_12_month_mean_temperature.csv").write_text("period_label,mean_temperature_c\n", encoding="utf-8")
    (derived / "wales_rolling_12_month_temperature_line_chart.csv").write_text("end_x,mean_temperature_c\n", encoding="utf-8")
    (figures / "wales_rolling_12_month_temperature_history.svg").write_text("<svg></svg>", encoding="utf-8")

    import snapshot_run as module

    monkeypatch.setattr(module, "PROJECT_DIR", project)
    monkeypatch.setattr(module, "DERIVED_DIR", derived)
    monkeypatch.setattr(module, "FIGURES_DIR", figures)
    monkeypatch.setattr(module, "RUNS_DIR", project / "runs")
    monkeypatch.setattr(module, "INDEX_PATH", project / "runs" / "index.json")

    run_dir = snapshot_run(run_id="2026-08", refreshed_at="2026-09-02T12:00:00Z")
    manifest = __import__("json").loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    index = __import__("json").loads((project / "runs" / "index.json").read_text(encoding="utf-8"))

    assert manifest["headline"]["mean_temperature_c"] == 10.65
    assert (run_dir / "RUN.md").exists()
    assert index["latest_run_id"] == "2026-08"
    assert index["runs"][0]["run_id"] == "2026-08"

    snapshot_run(run_id="2026-08", refreshed_at="2026-09-02T13:00:00Z")
    index_again = __import__("json").loads((project / "runs" / "index.json").read_text(encoding="utf-8"))
    assert len(index_again["runs"]) == 1
