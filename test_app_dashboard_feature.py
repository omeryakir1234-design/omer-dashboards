import pandas as pd
import sys
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
