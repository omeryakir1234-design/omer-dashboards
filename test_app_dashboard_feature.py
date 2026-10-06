import pandas as pd
import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app


def test_add_visualization_to_dashboard_list():
    df = pd.DataFrame({"value": [1, 2, 3, 4]})
    chart = app.build_chart(
        df=df,
        chart_type="Line Chart",
        selected_col="value",
        numeric_columns=["value"],
        categorical_columns=[],
        x_col="value",
        y_col="value",
        category_col="value",
    )

    dashboard = app.add_chart_to_dashboard([], chart, "Line Chart")

    assert len(dashboard) == 1
    assert dashboard[0]["type"] == "Line Chart"
    assert dashboard[0]["chart"] is chart
    assert "df" not in dashboard[0]
    assert "view" not in dashboard[0]


def test_delete_chart_from_dashboard_only():
    dashboard = [
        {"type": "Line Chart", "chart": object()},
        {"type": "Bar Chart", "chart": object()},
    ]

    dashboard = app.delete_chart_from_dashboard(dashboard, 0)
    assert len(dashboard) == 1
    assert dashboard[0]["type"] == "Bar Chart"


def test_build_dashboard_image_returns_png_bytes():
    dashboard = [{"type": "Line Chart", "chart": None}]
    png = app.build_dashboard_image(dashboard)

    assert png.startswith(b"\x89PNG")


def test_dashboard_visualization_html_uses_a_responsive_vega_container():
    df = pd.DataFrame({"category": ["A", "B"], "value": [1, 2]})
    config = app.default_config("Bar", app.detect_fields(df))
    original_config = deepcopy(config)
    panel = {"visualization_config": config}

    rendered = app.visualization_html(df, panel)

    assert '"width": "container"' in rendered
    assert '"height": "container"' in rendered
    assert '"autosize": {"type": "fit", "contains": "padding", "resize": true}' in rendered
    assert "ResizeObserver" in rendered
    assert "padding:0 12px 12px 0" in rendered
    assert config == original_config


def test_dashboard_appearance_is_separate_from_panel_configuration():
    appearance = app.default_dashboard_appearance()
    appearance["background_mode"] = "Pattern"
    appearance["decoration"] = "Grid"

    workspace = app.dashboard_workspace_style(appearance)
    panel = app.dashboard_panel_style(appearance)

    assert "linear-gradient" in workspace["backgroundImage"]
    assert workspace["backgroundColor"] == appearance["background_color"]
    assert "boxShadow" in panel
    assert "visualization_config" not in appearance


def test_dashboard_image_appearance_uses_the_requested_fit_and_overlay():
    appearance = app.default_dashboard_appearance()
    appearance.update({"background_mode": "Image", "image_data": "data:image/png;base64,abc", "image_fit": "Contain", "overlay_enabled": True})

    workspace = app.dashboard_workspace_style(appearance)

    assert "url(data:image/png;base64,abc)" in workspace["backgroundImage"]
    assert workspace["backgroundSize"].endswith("contain")


def test_contextual_panel_actions_target_only_the_selected_panel():
    config = {"type": "bar", "styling": {"main_color": "#2789aa"}}
    dashboard = [
        {"id": "first", "title": "First", "visualization_config": deepcopy(config), "layout": {"x": 1, "y": 2, "width": 9, "height": 7}},
        {"id": "second", "title": "Second", "visualization_config": deepcopy(config), "layout": {"x": 4, "y": 8, "width": 3, "height": 3}},
    ]

    app.apply_dashboard_panel_action(dashboard, "first", "Duplicate")
    duplicate = dashboard[1]
    app.apply_dashboard_panel_action(dashboard, "second", "Reset Size")
    app.apply_dashboard_panel_action(dashboard, "second", "Reset Position")
    app.apply_dashboard_panel_action(dashboard, duplicate["id"], "Delete")

    assert len(dashboard) == 2
    assert duplicate["id"] != "first"
    assert duplicate["visualization_config"] == config
    assert duplicate["visualization_config"] is not dashboard[0]["visualization_config"]
    assert dashboard[1]["layout"] == {"x": 0, "y": 4, "width": app.DEFAULT_PANEL_WIDTH, "height": app.DEFAULT_PANEL_HEIGHT}


def test_dashboard_title_settings_are_independent_and_styleable():
    settings = app.default_dashboard_settings()
    settings.update({"title": "Operations", "title_size": 36, "title_weight": "Medium", "title_alignment": "Center"})

    style = app.dashboard_title_style(settings)
    png = app.build_dashboard_image([], dashboard_settings=settings)

    assert style["fontSize"] == "36px"
    assert style["fontWeight"] == 500
    assert style["textAlign"] == "center"
    assert "visualization_config" not in settings
    assert png.startswith(b"\x89PNG")


def test_persisted_dashboard_record_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(app, "saved_dashboards_file_path", lambda: tmp_path / "saved_dashboards.json")
    dashboard = [{"id": "panel-1", "title": "Chart", "visualization_config": {"type": "bar", "title": "Chart"}, "layout": {"x": 0, "y": 0, "width": 6, "height": 4}}]
    record = app.build_saved_dashboard_record(
        dashboard_id="dash-123",
        name="Dashboard A",
        source_csv_path="/tmp/source.csv",
        source_csv_name="source.csv",
        dashboard_charts=dashboard,
        appearance=app.default_dashboard_appearance(),
        settings=app.default_dashboard_settings(),
    )

    app.persist_saved_dashboard(record)
    saved = app.load_saved_dashboards()

    assert saved["dash-123"]["name"] == "Dashboard A"
    assert saved["dash-123"]["source_csv_path"] == "/tmp/source.csv"
    assert saved["dash-123"]["dashboard"]["charts"][0]["id"] == "panel-1"


def test_missing_csv_dashboard_refuses_to_open(tmp_path):
    missing_csv = tmp_path / "missing.csv"
    record = {
        "id": "dash-404",
        "name": "Missing CSV Dashboard",
        "source_csv_path": str(missing_csv),
        "source_csv_name": "missing.csv",
    }

    assert app.saved_dashboard_can_open(record) is False
    assert "missing" in app.saved_dashboard_error_message(record).lower()


def test_saved_dashboard_save_widget_key_is_unique():
    app_source = Path(app.__file__).read_text(encoding="utf-8")

    assert app_source.count('key="save_dashboard_button"') == 1
    assert app_source.count('st.button("Save"') == 1
