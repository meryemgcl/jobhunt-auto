import json

from services import tracker


def test_update_career_dashboard_writes_state_files(tmp_path, monkeypatch):
    applications_path = tmp_path / "applications.json"
    dashboard_path = tmp_path / "DASHBOARD.md"

    monkeypatch.setattr(tracker, "APPLICATIONS_PATH", applications_path)
    monkeypatch.setattr(tracker, "DASHBOARD_PATH", dashboard_path)

    updated = tracker.update_career_dashboard(
        total_analyzed=12,
        matched_count=4,
        skill_gap_data={"top_market_demands": [{"tech": "FASTAPI", "demand_count": 3}]},
    )

    assert updated is True
    assert json.loads(applications_path.read_text(encoding="utf-8"))["matched_jobs_count"] == 4
    assert "FASTAPI" in dashboard_path.read_text(encoding="utf-8")
