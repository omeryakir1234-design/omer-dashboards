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
