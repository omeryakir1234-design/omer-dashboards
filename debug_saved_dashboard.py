from pathlib import Path
from streamlit.testing.v1 import AppTest
import app

csv_path = Path(__file__).resolve().parent / "debug_saved_dashboard.csv"
csv_path.write_text("value\n1\n2\n3\n", encoding="utf-8")

panel = {
    "id": "panel-1",
    "title": "Saved panel",
    "type": "Bar",
    "visualization_config": {
        "type": "bar",
        "title": "Saved panel",
        "x_field": "value",
        "y_field": "value",
        "group_field": "value",
        "aggregation": "Count",
        "filters": [],
        "styling": app.default_styling(),
    },
    "layout": {"x": 0, "y": 0, "width": 6, "height": 4},
}

at = AppTest.from_file(str(Path(__file__).resolve().parent / "app.py"), default_timeout=60)
at.session_state["current_saved_dashboard_id"] = "dash-1"
at.session_state["current_csv_path"] = str(csv_path)
at.session_state["current_csv_name"] = csv_path.name
at.session_state["dashboard_charts"] = [panel]
at.session_state["dashboard_appearance"] = app.default_dashboard_appearance()
at.session_state["dashboard_settings"] = app.default_dashboard_settings()
at.run()

report = {
    "exceptions": [repr(item) for item in at.exception],
    "session_state": {
        "current_saved_dashboard_id": at.session_state.get("current_saved_dashboard_id"),
        "current_csv_path": at.session_state.get("current_csv_path"),
        "current_csv_exists": Path(at.session_state.get("current_csv_path", "")).exists() if at.session_state.get("current_csv_path") else False,
        "dashboard_charts_length": len(at.session_state.get("dashboard_charts", [])),
        "dashboard_charts": at.session_state.get("dashboard_charts", []),
        "dashboard_layout": at.session_state.get("dashboard_layout"),
    },
    "dashboard_elements": len(at.markdown),
    "markdown": [item.value for item in at.markdown],
    "captions": [item.value for item in at.caption],
    "buttons": [item.label for item in at.button],
    "warnings": [item.value for item in at.warning],
    "infos": [item.value for item in at.info],
}
Path(__file__).resolve().with_name("saved_dashboard_runtime_debug.json").write_text(__import__("json").dumps(report, indent=2), encoding="utf-8")
