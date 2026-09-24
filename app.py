from io import BytesIO
from copy import deepcopy
import json
from uuid import uuid4

import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from streamlit_elements import dashboard as elements_dashboard
from streamlit_elements import elements, html, mui, sync
import vl_convert as vlc


st.set_page_config(page_title="Omer's Lens", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    :root { --ink:#10222c; --muted:#5d7180; --line:#2d3b47; --panel:#202c35;
      --panel-soft:#263640; --blue:#54b8d5; --deep:#2789aa; --aqua:#80d8d1; }
    [data-testid="stAppViewContainer"] { background:linear-gradient(135deg,#eaf9ff 0%,#d9edf9 52%,#c8dde8 100%); color:var(--ink); }
    [data-testid="stHeader"] { background:transparent; }
    .block-container { max-width:min(1480px,calc(100vw - 3rem)); padding-top:1.2rem; padding-bottom:3rem; }
    h1,h2,h3 { color:#10222c !important; letter-spacing:0 !important; }
    h1 { font-size:2.5rem !important; }
    p,.stMarkdown { color:var(--muted); }
    div[data-testid="stVerticalBlockBorderWrapper"] { background:var(--panel); border:1px solid var(--line); border-radius:6px; box-shadow:0 8px 24px rgba(0,0,0,.2); }
    div[data-testid="stFileUploader"],div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:6px; background:rgba(25,35,43,.92); }
    .stSelectbox > div > div,.stMultiSelect > div > div,.stNumberInput > div > div,.stTextInput > div > div { border-radius:6px; border:1px solid var(--line); background:#18232b; }
    .stSelectbox label,.stMultiSelect label,.stNumberInput label,.stTextInput label,.stSlider label { color:#ffffff !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"], [data-testid="stMultiSelect"] [data-baseweb="select"], [data-baseweb="select"] > div, [data-baseweb="select"] [data-baseweb="input"] { background:#18232b !important; color:#ffffff !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] *, [data-testid="stMultiSelect"] [data-baseweb="select"] *, [data-baseweb="select"] span, [data-baseweb="select"] input, [data-baseweb="select"] svg { color:#ffffff !important; fill:#ffffff !important; -webkit-text-fill-color:#ffffff !important; }
    [data-testid="stSelectbox"] [data-baseweb="select"] input::placeholder, [data-testid="stMultiSelect"] [data-baseweb="select"] input::placeholder { color:#aab7c4 !important; -webkit-text-fill-color:#aab7c4 !important; opacity:1 !important; }
    [role="listbox"], [role="listbox"] [role="option"], [role="listbox"] [role="option"] * { background:#18232b !important; color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; }
    [role="listbox"] [role="option"]:hover, [role="listbox"] [aria-selected="true"], [role="listbox"] [role="option"]:hover * { background:#2789aa !important; color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; }
    .stTextInput input,.stNumberInput input { background:#18232b !important; color:#ffffff !important; -webkit-text-fill-color:#ffffff !important; caret-color:#80d8d1; }
    .stTextInput input::placeholder,.stNumberInput input::placeholder { color:#aab7c4 !important; -webkit-text-fill-color:#aab7c4 !important; opacity:1 !important; }
    div.stButton > button { height:38px; border:1px solid var(--blue); border-radius:4px; background:var(--blue); color:#ffffff !important; font-weight:800; }
    div.stButton > button:hover { background:var(--deep); color:#ffffff !important; }
    div.stButton > button p, div.stButton > button span { color:#ffffff !important; }
    section[data-testid="stSidebar"] { background:#17232b; border-right:1px solid var(--line); }
    [data-testid="stMetric"] { background:var(--panel); border:1px solid var(--line); border-radius:6px; }
    .lens-kicker { color:#2789aa; font-size:.76rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
    .empty-canvas { min-height:360px; display:flex; align-items:center; justify-content:center; border:1px dashed #7caabc; border-radius:6px; color:#58717d; background:rgba(234,249,255,.35); }
    .builder-section { margin:1rem 0 .55rem; padding-bottom:.35rem; border-bottom:1px solid #496171; color:#80d8d1; font-size:.78rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
    .preview-shell { padding:.25rem .5rem .8rem; background:rgba(234,249,255,.35); border:1px solid #9bbdce; border-radius:6px; }
    </style>
    """,
    unsafe_allow_html=True,
)


PALETTE = ["#2789aa", "#54b8d5", "#80d8d1", "#17647f", "#9adfe5", "#3b9ab8", "#b8eef0"]
DEFAULT_BACKGROUND = "#d9edf9"
DEFAULT_STYLING = {
    "background_color": DEFAULT_BACKGROUND,
    "main_color": "#54b8d5",
    "color_mode": "Categorical palette",
    "palette": PALETTE.copy(),
    "category_colors": {},
    "heatmap_scale": "Blue → Aqua",
    "heatmap_min": "#eaf9ff",
    "heatmap_mid": "#54b8d5",
    "heatmap_max": "#2789aa",
    "reverse_heatmap": False,
    "marker_opacity": 0.7,
    "marker_border": "#17647f",
    "marker_size": 80,
    "kpi_mode": "Static",
    "kpi_apply_to": "KPI number",
    "kpi_thresholds": [],
}
VIS_TYPES = ["Bar", "Line", "Area", "KPI / Metric", "Pie", "Heat Map", "Waffle", "Map", "Treemap", "Word Cloud"]
AGGREGATIONS = ["Count", "Unique count", "Sum", "Average", "Min", "Max", "Median"]
DATE_GROUPS = ["None", "Minute", "Hour", "Day", "Week", "Month", "Year"]
DASHBOARD_COLUMNS = 12
DEFAULT_PANEL_WIDTH = 6
DEFAULT_PANEL_HEIGHT = 4


def default_styling():
    return {key: (value.copy() if isinstance(value, (list, dict)) else value) for key, value in DEFAULT_STYLING.items()}


def ensure_styling(config):
    styling = default_styling()
    styling.update(config.get("styling") or {})
    styling["palette"] = list(styling.get("palette") or PALETTE)
    styling["category_colors"] = dict(styling.get("category_colors") or {})
    config["styling"] = styling
    return styling


def valid_color(value, fallback):
    value = str(value or "").strip()
    if len(value) == 7 and value.startswith("#"):
        try:
            int(value[1:], 16)
            return value.lower()
        except ValueError:
            pass
    return fallback


def readable_text_color(background):
    background = valid_color(background, DEFAULT_BACKGROUND).lstrip("#")
    channels = [int(background[index:index + 2], 16) for index in (0, 2, 4)]
    luminance = (0.299 * channels[0]) + (0.587 * channels[1]) + (0.114 * channels[2])
    return "#f4fbfd" if luminance < 145 else "#10222c"


def styling_palette(config, categories=None):
    styling = ensure_styling(config)
    categories = [str(category) for category in (categories or [])]
    if styling.get("color_mode") in {"Single color", "Static"}:
        return [styling["main_color"] for _ in categories] or [styling["main_color"]]
    palette = [valid_color(color, PALETTE[index % len(PALETTE)]) for index, color in enumerate(styling["palette"])] or PALETTE
    if styling.get("color_mode") == "Custom colors":
        return [valid_color(styling["category_colors"].get(category), palette[index % len(palette)]) for index, category in enumerate(categories)] or palette
    return [palette[index % len(palette)] for index, _ in enumerate(categories)] or palette


def visualization_properties(chart, config):
    styling = ensure_styling(config)
    text_color = readable_text_color(styling["background_color"])
    return chart.properties(background=styling["background_color"]).configure_axis(labelColor=text_color, titleColor=text_color, domainColor=text_color, tickColor=text_color).configure_legend(labelColor=text_color, titleColor=text_color)


def dashboard_chart_theme():
    return {"config": {"background": "#d9edf9", "view": {"fill": "#d9edf9", "stroke": "#9bbdce"}, "axis": {"labelColor": "#10222c", "titleColor": "#10222c", "gridColor": "#a9c9d8"}, "legend": {"labelColor": "#10222c", "titleColor": "#10222c"}, "title": {"color": "#10222c"}}}


alt.themes.register("dashboard_light_blue", dashboard_chart_theme)
alt.themes.enable("dashboard_light_blue")


def detect_fields(df):
    result = {"numeric": [], "categorical": [], "boolean": [], "datetime": [], "latitude": [], "longitude": [], "all": list(df.columns)}
    for column in df.columns:
        series = df[column]
        name = str(column).lower().replace("-", "_").replace(" ", "_")
        if pd.api.types.is_bool_dtype(series):
            result["boolean"].append(column)
        elif pd.api.types.is_numeric_dtype(series):
            result["numeric"].append(column)
        else:
            parsed = pd.to_datetime(series, errors="coerce")
            if parsed.notna().mean() >= 0.8 and series.nunique(dropna=True) > 1:
                result["datetime"].append(column)
            else:
                result["categorical"].append(column)
        if name in {"lat", "latitude", "y", "geo_lat", "decimal_latitude"} or "latitude" in name:
            result["latitude"].append(column)
        if name in {"lon", "lng", "longitude", "x", "geo_lon", "decimal_longitude"} or "longitude" in name:
            result["longitude"].append(column)
    return result


def compatible_fields(field_types, aggregation):
    if aggregation in {"Sum", "Average", "Min", "Max", "Median"}:
        return field_types["numeric"]
    return field_types["all"]


def default_config(chart_type, field_types):
    numeric = field_types["numeric"]
    categorical = field_types["categorical"] or field_types["boolean"] or field_types["datetime"]
    all_fields = field_types["all"]
    metric = numeric[0] if numeric else (all_fields[0] if all_fields else None)
    dimension = categorical[0] if categorical else metric
    return {"type": chart_type.lower().replace(" / ", "_").replace(" ", "_"), "title": chart_type, "x_field": dimension, "y_field": metric,
            "group_field": dimension, "breakdown": None, "aggregation": "Average" if numeric else "Count", "date_group": "None",
            "sort": "Metric", "sort_direction": "Descending", "top_n": 20, "orientation": "Vertical", "legend": True,
            "labels": False, "points": True, "stacked": False, "donut": False, "donut_hole": 0.45, "target": None,
            "subtitle": "", "precision": 2, "prefix": "", "suffix": "", "percentage": False, "cells": 100,
            "min_frequency": 1, "max_words": 30, "stop_words": "the, a, an, and, or, to, of", "font_min": 12, "font_max": 44,
            "filters": [], "styling": default_styling()}


def apply_filters(df, filters):
    filtered = df.copy()
    for item in filters or []:
        field, operator, value = item.get("field"), item.get("operator"), item.get("value", "")
        if field not in filtered.columns:
            continue
        series = filtered[field]
        text = str(value)
        numeric_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if operator == "Equals": mask = series.astype(str) == text
        elif operator == "Not equals": mask = series.astype(str) != text
        elif operator == "Contains": mask = series.astype(str).str.contains(text, case=False, na=False)
        elif operator == "Does not contain": mask = ~series.astype(str).str.contains(text, case=False, na=False)
        elif operator in {"Greater than", "Less than", "Greater than or equal", "Less than or equal"}:
            comparable = pd.to_numeric(series, errors="coerce")
            if pd.isna(numeric_value):
                continue
            mask = {"Greater than": comparable > numeric_value, "Less than": comparable < numeric_value,
                    "Greater than or equal": comparable >= numeric_value, "Less than or equal": comparable <= numeric_value}[operator]
        elif operator == "Is empty": mask = series.isna() | (series.astype(str).str.strip() == "")
        elif operator == "Is not empty": mask = series.notna() & (series.astype(str).str.strip() != "")
        else: continue
        filtered = filtered.loc[mask]
    return filtered


def aggregate_series(df, field, aggregation):
    if aggregation == "Count": return len(df)
    if field not in df.columns: return 0
    series = df[field]
    if aggregation == "Unique count": return series.nunique(dropna=True)
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty: return 0
    return {"Sum": numeric.sum(), "Average": numeric.mean(), "Min": numeric.min(), "Max": numeric.max(), "Median": numeric.median()}.get(aggregation, numeric.mean())


def prepare_grouped(df, dimension, metric, aggregation, breakdown=None, date_group="None"):
    if dimension not in df.columns:
        return pd.DataFrame()
    work = df.copy()
    if date_group != "None" and dimension in df.columns:
        dates = pd.to_datetime(work[dimension], errors="coerce")
        periods = {"Minute": dates.dt.floor("min"), "Hour": dates.dt.floor("h"), "Day": dates.dt.floor("D"), "Week": dates.dt.to_period("W").dt.start_time, "Month": dates.dt.to_period("M").dt.start_time, "Year": dates.dt.to_period("Y").dt.start_time}
        work[dimension] = periods.get(date_group, dates)
    keys = [dimension] + ([breakdown] if breakdown and breakdown in work.columns and breakdown != dimension else [])
    if aggregation == "Count": grouped = work.groupby(keys, dropna=False).size().reset_index(name="value")
    elif aggregation == "Unique count": grouped = work.groupby(keys, dropna=False)[metric].nunique().reset_index(name="value")
    else:
        aggregation_name = {"Average": "mean", "Min": "min", "Max": "max", "Median": "median", "Sum": "sum"}.get(aggregation, "mean")
        grouped = work.assign(__metric=pd.to_numeric(work[metric], errors="coerce")).groupby(keys, dropna=False, as_index=False)["__metric"].agg(aggregation_name).rename(columns={"__metric": "value"})
    return grouped.dropna(subset=[dimension])


def chart_frame(df, config):
    filtered = apply_filters(df, config.get("filters", []))
    dimension = config.get("x_field") or config.get("group_field")
    metric = config.get("y_field") or dimension
    return filtered, prepare_grouped(filtered, dimension, metric, config.get("aggregation", "Count"), config.get("breakdown"), config.get("date_group", "None"))


def build_bar_chart(df, config):
    _, grouped = chart_frame(df, config)
    if grouped.empty: return None
    x = config.get("x_field")
    if config.get("sort") == "Metric": grouped = grouped.sort_values("value", ascending=config.get("sort_direction") == "Ascending")
    grouped = grouped.tail(int(config.get("top_n", 20))) if config.get("sort_direction") == "Ascending" else grouped.head(int(config.get("top_n", 20)))
    if config.get("orientation") == "Horizontal":
        enc = {"y": alt.Y(f"{x}:N", sort="-x", title=x), "x": alt.X("value:Q", title=config.get("aggregation"))}
    else:
        enc = {"x": alt.X(f"{x}:N", sort="-y", title=x), "y": alt.Y("value:Q", title=config.get("aggregation"))}
    styling = ensure_styling(config)
    if config.get("breakdown"):
        categories = grouped[config["breakdown"]].dropna().astype(str).unique().tolist()
        enc["color"] = alt.Color(f"{config['breakdown']}:N", scale=alt.Scale(range=styling_palette(config, categories)), legend=alt.Legend() if config.get("legend", True) else None)
    if config.get("labels"): enc["text"] = alt.Text("value:Q", format=".2f")
    mark = alt.Chart(grouped).mark_bar(color=styling["main_color"] if not config.get("breakdown") else None).encode(**enc).properties(title=config.get("title"), height=360)
    return visualization_properties(mark, config)


def build_line_chart(df, config, mark="line"):
    _, grouped = chart_frame(df, config)
    if grouped.empty: return None
    x_type = "T" if config.get("date_group") != "None" else "N"
    enc = {"x": alt.X(f"{config.get('x_field')}:{x_type}", title=config.get("x_field")), "y": alt.Y("value:Q", title=config.get("aggregation"))}
    styling = ensure_styling(config)
    if config.get("breakdown"):
        categories = grouped[config["breakdown"]].dropna().astype(str).unique().tolist()
        enc["color"] = alt.Color(f"{config['breakdown']}:N", scale=alt.Scale(range=styling_palette(config, categories)), legend=alt.Legend() if config.get("legend", True) else None)
    if mark == "area":
        chart = alt.Chart(grouped).mark_area(opacity=.55, color=styling["main_color"] if not config.get("breakdown") else None)
    else:
        chart = alt.Chart(grouped).mark_line(interpolate="monotone", point=config.get("points", True), color=styling["main_color"] if not config.get("breakdown") else None)
    return visualization_properties(chart.encode(**enc).properties(title=config.get("title"), height=360), config)


def build_metric(df, config):
    styling = ensure_styling(config)
    value = aggregate_series(apply_filters(df, config.get("filters", [])), config.get("y_field"), config.get("aggregation", "Count"))
    formatted = f"{config.get('prefix', '')}{value:,.{int(config.get('precision', 2))}f}{config.get('suffix', '')}" if isinstance(value, (float, int)) else str(value)
    if config.get("percentage"): formatted = f"{float(value) * 100:,.{int(config.get('precision', 2))}f}%"
    number_color = styling["main_color"]
    if styling.get("kpi_mode") == "Dynamic":
        for threshold in styling.get("kpi_thresholds", []):
            minimum = threshold.get("minimum", float("-inf")); maximum = threshold.get("maximum", float("inf"))
            if minimum <= float(value) <= maximum:
                number_color = valid_color(threshold.get("color"), number_color)
                break
    return {"value": formatted, "title": config.get("title", "Metric"), "subtitle": config.get("subtitle", ""), "color": number_color, "background": styling["background_color"], "apply_to": styling.get("kpi_apply_to", "KPI number")}


def build_pie_chart(df, config):
    _, grouped = chart_frame(df, {**config, "x_field": config.get("group_field")})
    if grouped.empty: return None
    grouped = grouped.nlargest(int(config.get("top_n", 10)), "value")
    categories = grouped[config["group_field"]].dropna().astype(str).tolist()
    chart = alt.Chart(grouped).mark_arc(innerRadius=70 if config.get("donut") else 0).encode(theta=alt.Theta("value:Q"), color=alt.Color(f"{config.get('group_field')}:N", scale=alt.Scale(range=styling_palette(config, categories)), legend=alt.Legend() if config.get("legend", True) else None), tooltip=[config.get("group_field"), alt.Tooltip("value:Q", format=",.2f")]).properties(title=config.get("title"), height=360)
    return visualization_properties(chart, config)


def build_heatmap(df, config):
    x, y = config.get("x_field"), config.get("group_field") or config.get("breakdown")
    if not x: return None
    if y and y in df.columns:
        grouped = prepare_grouped(apply_filters(df, config.get("filters", [])), x, config.get("y_field"), config.get("aggregation", "Count"), y, config.get("date_group", "None"))
    else:
        _, grouped = chart_frame(df, {**config, "x_field": x, "breakdown": None})
        grouped["row"] = "All"
        y = "row"
    if grouped.empty: return None
    styling = ensure_styling(config)
    scale_colors = {"Blue": ["#eaf9ff", "#2789aa"], "Aqua": ["#eaf9ff", "#80d8d1"], "Blue → Aqua": ["#eaf9ff", "#2789aa", "#80d8d1"], "Light → Dark": ["#eaf9ff", "#17647f"]}.get(styling.get("heatmap_scale"), [styling["heatmap_min"], styling["heatmap_mid"], styling["heatmap_max"]])
    if styling.get("reverse_heatmap"): scale_colors = list(reversed(scale_colors))
    chart = alt.Chart(grouped).mark_rect().encode(x=alt.X(f"{x}:N"), y=alt.Y(f"{y}:N"), color=alt.Color("value:Q", scale=alt.Scale(range=scale_colors)), tooltip=list(grouped.columns))
    return visualization_properties(chart.properties(title=config.get("title"), height=360), config)


def build_waffle(df, config):
    group = config.get("group_field")
    _, grouped = chart_frame(df, {**config, "x_field": group})
    if grouped.empty: return None
    grouped = grouped.nlargest(int(config.get("top_n", 10)), "value")
    total, cells = grouped["value"].sum(), int(config.get("cells", 100)); rows = []; cursor = 0
    for _, item in grouped.iterrows():
        count = round((item["value"] / total) * cells) if total else 0
        for _ in range(count): rows.append({"column": cursor % 10, "row": cursor // 10, "category": str(item[group])}); cursor += 1
    if not rows: return None
    chart = alt.Chart(pd.DataFrame(rows)).mark_rect(stroke="#d9edf9", strokeWidth=1).encode(x=alt.X("column:O", axis=None), y=alt.Y("row:O", sort="descending", axis=None), color=alt.Color("category:N", scale=alt.Scale(range=styling_palette(config, grouped[group].astype(str).tolist())), legend=alt.Legend() if config.get("legend", True) else None), tooltip=["category"]).properties(title=config.get("title"), width=360, height=360)
    return visualization_properties(chart, config)


def build_map(df, config):
    lat, lon = config.get("latitude"), config.get("longitude")
    if not lat or not lon or lat not in df.columns or lon not in df.columns: return None
    work = df.copy(); work[lat] = pd.to_numeric(work[lat], errors="coerce"); work[lon] = pd.to_numeric(work[lon], errors="coerce"); work = work.dropna(subset=[lat, lon])
    if work.empty: return None
    styling = ensure_styling(config)
    enc = {"latitude": alt.Latitude(f"{lat}:Q"), "longitude": alt.Longitude(f"{lon}:Q"), "tooltip": [lat, lon]}
    if config.get("breakdown") and config["breakdown"] in work.columns:
        categories = work[config["breakdown"]].dropna().astype(str).unique().tolist()
        enc["color"] = alt.Color(f"{config['breakdown']}:N", scale=alt.Scale(range=styling_palette(config, categories)))
    marker = alt.Chart(work).mark_circle(opacity=styling["marker_opacity"], color=None if config.get("breakdown") else styling["main_color"], stroke=styling["marker_border"], size=styling["marker_size"])
    return visualization_properties(marker.encode(**enc).properties(title=config.get("title"), height=380), config)


def build_treemap(df, config):
    group = config.get("group_field")
    _, grouped = chart_frame(df, {**config, "x_field": group})
    if grouped.empty: return None
    grouped = grouped.nlargest(int(config.get("top_n", 20)), "value")
    categories = grouped[group].dropna().astype(str).tolist()
    chart = alt.Chart(grouped).mark_bar().encode(x=alt.X(f"{group}:N", axis=None), y=alt.Y("value:Q", axis=None), color=alt.Color(f"{group}:N", scale=alt.Scale(range=styling_palette(config, categories)), legend=None), tooltip=[group, "value:Q"]).properties(title=config.get("title"), height=360)
    return visualization_properties(chart, config)


def build_wordcloud(df, config):
    field = config.get("text_field")
    if not field or field not in df.columns: return None
    work = apply_filters(df, config.get("filters", [])); words = work[field].dropna().astype(str).str.lower().str.split().explode()
    stops = {word.strip() for word in config.get("stop_words", "").split(",") if word.strip()}; words = words[~words.isin(stops) & (words.str.len() > 1)]
    counts = words.value_counts().rename_axis("word").reset_index(name="value"); counts = counts[counts.value >= int(config.get("min_frequency", 1))].head(int(config.get("max_words", 30)))
    if counts.empty: return None
    styling = ensure_styling(config)
    color_encoding = alt.value(styling["main_color"])
    if styling.get("color_mode") != "Single color":
        color_encoding = alt.Color("word:N", scale=alt.Scale(range=styling_palette(config, counts["word"].tolist())), legend=None)
    chart = alt.Chart(counts).mark_text().encode(text="word:N", size=alt.Size("value:Q", scale=alt.Scale(range=[int(config.get("font_min", 12)), int(config.get("font_max", 44))]), legend=None), color=color_encoding, tooltip=["word", "value"]).properties(title=config.get("title"), height=360)
    return visualization_properties(chart, config)


def render_visualization(df, config):
    chart_type = config.get("type", "bar")
    builders = {"bar": build_bar_chart, "line": lambda data, settings: build_line_chart(data, settings), "area": lambda data, settings: build_line_chart(data, settings, "area"), "pie": build_pie_chart, "heat_map": build_heatmap, "waffle": build_waffle, "map": build_map, "treemap": build_treemap, "word_cloud": build_wordcloud}
    if chart_type == "kpi_metric": return build_metric(df, config)
    builder = builders.get(chart_type)
    return builder(df, config) if builder else None


def add_chart_to_dashboard(dashboard, chart, chart_type, config=None, title=None):
    if config is None: return dashboard + [{"type": chart_type, "chart": chart}]
    panel_id = uuid4().hex
    return dashboard + [{"id": panel_id, "type": config.get("type", chart_type), "title": title or config.get("title", chart_type), "config": deepcopy(config), "layout": {"x": 0, "y": next_panel_y(dashboard), "width": DEFAULT_PANEL_WIDTH, "height": DEFAULT_PANEL_HEIGHT}}]


def next_panel_y(dashboard):
    if not dashboard:
        return 0
    return max(int(panel.get("layout", {}).get("y", 0)) + int(panel.get("layout", {}).get("height", DEFAULT_PANEL_HEIGHT)) for panel in dashboard)


def panel_layout(panel, index=0):
    layout = panel.setdefault("layout", {})
    if not layout:
        layout.update({"x": (index % 2) * DEFAULT_PANEL_WIDTH, "y": (index // 2) * DEFAULT_PANEL_HEIGHT, "width": DEFAULT_PANEL_WIDTH, "height": DEFAULT_PANEL_HEIGHT})
    layout["x"] = max(0, min(DASHBOARD_COLUMNS - 1, int(layout.get("x", 0))))
    layout["y"] = max(0, int(layout.get("y", 0)))
    layout["width"] = max(2, min(DASHBOARD_COLUMNS, int(layout.get("width", DEFAULT_PANEL_WIDTH))))
    layout["height"] = max(3, int(layout.get("height", DEFAULT_PANEL_HEIGHT)))
    if layout["x"] + layout["width"] > DASHBOARD_COLUMNS:
        layout["x"] = DASHBOARD_COLUMNS - layout["width"]
    return layout


def reset_dashboard_layout(dashboard):
    for index, panel in enumerate(dashboard):
        layout = panel_layout(panel, index)
        layout.update({"x": (index % 2) * DEFAULT_PANEL_WIDTH, "y": (index // 2) * DEFAULT_PANEL_HEIGHT, "width": DEFAULT_PANEL_WIDTH, "height": DEFAULT_PANEL_HEIGHT})
    return dashboard


def update_dashboard_layout(dashboard, layout_items):
    by_id = {str(item.get("i")): item for item in layout_items or []}
    for index, panel in enumerate(dashboard):
        item = by_id.get(str(panel.get("id")))
        if item:
            panel["layout"] = {"x": item.get("x", 0), "y": item.get("y", 0), "width": item.get("w", DEFAULT_PANEL_WIDTH), "height": item.get("h", DEFAULT_PANEL_HEIGHT)}
        panel_layout(panel, index)
    return dashboard


def delete_chart_from_dashboard(dashboard, index):
    if 0 <= index < len(dashboard): del dashboard[index]
    return dashboard


def chart_png(chart):
    if chart is None:
        return None
    try:
        return vlc.vegalite_to_png(json.dumps(chart.to_dict()))
    except Exception:
        return None


def build_dashboard_image(dashboard, df=None):
    """Compose the configured panels, at their saved grid positions, into a real PNG."""
    scale = 140
    margin = 28
    row_height = 145
    max_row = max((panel_layout(panel).get("y", 0) + panel_layout(panel).get("height", DEFAULT_PANEL_HEIGHT) for panel in dashboard), default=DEFAULT_PANEL_HEIGHT)
    image = Image.new("RGB", (DASHBOARD_COLUMNS * scale + margin * 2, max_row * row_height + 125), color=(234, 249, 255))
    draw = ImageDraw.Draw(image)
    try:
        font_header = ImageFont.truetype("arial.ttf", 30); font_title = ImageFont.truetype("arial.ttf", 16); font_small = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        font_header = font_title = font_small = ImageFont.load_default()
    draw.text((margin, 28), "Omer's Dashboard", fill=(16, 34, 44), font=font_header)
    for index, panel in enumerate(dashboard):
        layout = panel_layout(panel, index)
        x0 = margin + layout["x"] * scale; y0 = 90 + layout["y"] * row_height
        width = max(220, layout["width"] * scale - 12); height = max(170, layout["height"] * row_height - 12)
        config = panel.get("config", {}); styling = ensure_styling(config)
        draw.rounded_rectangle((x0, y0, x0 + width, y0 + height), radius=6, fill=tuple(int(styling["background_color"][i:i + 2], 16) for i in (1, 3, 5)), outline=(45, 59, 71), width=2)
        draw.text((x0 + 12, y0 + 10), panel.get("title", panel.get("type", "Visualization")), fill=readable_text_color(styling["background_color"]), font=font_title)
        output = render_visualization(df, config) if df is not None and config else None
        if isinstance(output, dict):
            color = output.get("color", styling["main_color"]); draw.text((x0 + 24, y0 + height // 2 - 20), output["value"], fill=tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)), font=font_header); draw.text((x0 + 24, y0 + height // 2 + 22), output.get("subtitle", ""), fill=readable_text_color(styling["background_color"]), font=font_small)
        else:
            png = chart_png(output)
            if png:
                chart_image = Image.open(BytesIO(png)).convert("RGB"); chart_image.thumbnail((width - 24, height - 48)); image.paste(chart_image, (x0 + 12, y0 + 36))
            else:
                draw.text((x0 + 16, y0 + height // 2), "Visualization unavailable", fill=readable_text_color(styling["background_color"]), font=font_small)
    buffer = BytesIO(); image.save(buffer, format="PNG"); return buffer.getvalue()


def build_chart(df, chart_type, selected_col, numeric_columns, categorical_columns, x_col=None, y_col=None, category_col=None):
    legacy_map = {"Line Chart": "line", "Bar Chart": "bar", "Area Chart": "area"}
    if chart_type in legacy_map:
        config = default_config(chart_type, detect_fields(df)); config.update({"type": legacy_map[chart_type], "x_field": x_col or selected_col, "y_field": y_col or selected_col, "title": f"{chart_type} of {selected_col}", "aggregation": "Average"})
        return render_visualization(df, config)
    if chart_type == "Histogram": return alt.Chart(df).mark_bar().encode(x=alt.X(f"{selected_col}:Q", bin=alt.Bin(maxbins=30)), y="count()").properties(title=f"Histogram of {selected_col}", height=350)
    if chart_type == "Scatter Plot" and x_col and y_col: return alt.Chart(df).mark_circle(size=80).encode(x=f"{x_col}:Q", y=f"{y_col}:Q").properties(title=f"{y_col} vs {x_col}", height=350)
    if chart_type == "Box Plot" and category_col: return alt.Chart(df).mark_boxplot().encode(x=f"{category_col}:N", y=f"{selected_col}:Q").properties(title=f"Box plot of {selected_col}", height=350)
    return None


def _sync_picker_to_hex(picker_key, hex_key):
    color = valid_color(st.session_state.get(picker_key), DEFAULT_BACKGROUND)
    st.session_state[hex_key] = color


def _sync_hex_to_picker(picker_key, hex_key):
    color = valid_color(st.session_state.get(hex_key), st.session_state.get(picker_key, DEFAULT_BACKGROUND))
    st.session_state[picker_key] = color
    st.session_state[hex_key] = color


def color_input(label, value, key):
    picker_key = f"picker_{key}"
    hex_key = f"hex_{key}"
    initial = valid_color(value, DEFAULT_BACKGROUND)
    if picker_key not in st.session_state:
        st.session_state[picker_key] = initial
    if hex_key not in st.session_state:
        st.session_state[hex_key] = initial
    columns = st.columns([1, 2])
    columns[0].color_picker(label, key=picker_key, on_change=_sync_picker_to_hex, args=(picker_key, hex_key))
    columns[1].text_input("HEX", key=hex_key, on_change=_sync_hex_to_picker, args=(picker_key, hex_key))
    return valid_color(st.session_state.get(hex_key), st.session_state.get(picker_key, initial))


def color_controls(df, field_types, config):
    styling = ensure_styling(config)
    widget_key = f"{st.session_state.get('editor_revision', 0)}"
    with st.expander("Colors", expanded=False):
        background = color_input("Background", styling["background_color"], f"{widget_key}_background")
        styling["background_color"] = background
        styling["main_color"] = color_input("Visualization / series color", styling["main_color"], f"{widget_key}_main")
        relevant_type = config.get("type")
        if relevant_type != "kpi_metric":
            color_modes = ["Static", "Categorical palette", "Custom colors"]
            saved_mode = "Static" if styling.get("color_mode") == "Single color" else styling.get("color_mode", "Categorical palette")
            styling["color_mode"] = st.selectbox("Color mode", color_modes, index=color_modes.index(saved_mode), key=f"{widget_key}_color_mode")
        if relevant_type in {"bar", "line", "area", "pie", "waffle", "treemap", "word_cloud", "map"}:
            color_field = config.get("breakdown") or config.get("group_field") or config.get("text_field")
            categories = []
            if color_field in df.columns:
                categories = df[color_field].dropna().astype(str).drop_duplicates().head(30).tolist()
            if styling["color_mode"] == "Categorical palette":
                st.caption("Default blue / aqua palette")
                st.markdown(" ".join(f"<span style='display:inline-block;width:28px;height:14px;background:{color};border:1px solid #9bbdce'></span>" for color in styling["palette"]), unsafe_allow_html=True)
            if styling["color_mode"] == "Custom colors" and categories:
                st.caption("Category colors")
                for index, category in enumerate(categories):
                    styling["category_colors"][category] = color_input(category, styling["category_colors"].get(category, styling["palette"][index % len(styling["palette"])]), f"{widget_key}_category_{index}")
            if relevant_type in {"pie", "waffle", "treemap"} and st.button("Apply palette", key="apply_palette"):
                styling["category_colors"] = {category: styling["palette"][index % len(styling["palette"])] for index, category in enumerate(categories)}
            if relevant_type in {"pie", "waffle", "treemap"} and st.button("Reset colors", key="reset_partition_colors"):
                styling["category_colors"] = {}; styling["color_mode"] = "Categorical palette"
        if relevant_type == "heat_map":
            styling["heatmap_scale"] = st.selectbox("Color scale", ["Blue", "Aqua", "Blue → Aqua", "Light → Dark", "Custom gradient"], key="heatmap_scale")
            if styling["heatmap_scale"] == "Custom gradient":
                styling["heatmap_min"] = color_input("Minimum", styling["heatmap_min"], f"{widget_key}_heat_min")
                styling["heatmap_mid"] = color_input("Midpoint", styling["heatmap_mid"], f"{widget_key}_heat_mid")
                styling["heatmap_max"] = color_input("Maximum", styling["heatmap_max"], f"{widget_key}_heat_max")
            styling["reverse_heatmap"] = st.checkbox("Reverse color scale", styling.get("reverse_heatmap", False), key=f"{widget_key}_reverse_heatmap")
        if relevant_type == "map":
            styling["marker_opacity"] = st.slider("Marker opacity", 0.1, 1.0, float(styling.get("marker_opacity", 0.7)), 0.05, key=f"{widget_key}_marker_opacity")
            styling["marker_border"] = color_input("Marker border", styling["marker_border"], f"{widget_key}_marker_border")
            styling["marker_size"] = st.slider("Marker size", 20, 400, int(styling.get("marker_size", 80)), 10, key=f"{widget_key}_marker_size")
        if relevant_type == "kpi_metric":
            styling["kpi_mode"] = st.selectbox("Color mode", ["Static", "Dynamic"], index=["Static", "Dynamic"].index(styling.get("kpi_mode", "Static")), key=f"{widget_key}_kpi_mode")
            apply_targets = ["KPI number", "KPI background", "Accent", "Both"]
            styling["kpi_apply_to"] = st.selectbox("Apply color to", apply_targets, index=apply_targets.index(styling.get("kpi_apply_to", "KPI number")), key=f"{widget_key}_kpi_apply_to")
            if styling["kpi_mode"] == "Dynamic":
                st.caption("Threshold ranges are inclusive")
                thresholds = styling.get("kpi_thresholds") or [{"minimum": 0, "maximum": 50, "color": "#d65c5c"}, {"minimum": 50, "maximum": 80, "color": "#d6ad45"}, {"minimum": 80, "maximum": 1000000000, "color": "#2c9b7a"}]
                styling["kpi_thresholds"] = thresholds
                for index, threshold in enumerate(thresholds):
                    columns = st.columns([1, 1, 2])
                    threshold["minimum"] = columns[0].number_input(f"Min {index + 1}", value=float(threshold.get("minimum", 0)), key=f"{widget_key}_threshold_min_{index}")
                    threshold["maximum"] = columns[1].number_input(f"Max {index + 1}", value=float(threshold.get("maximum", 100)), key=f"{widget_key}_threshold_max_{index}")
                    threshold["color"] = columns[2].color_picker(f"Color {index + 1}", threshold.get("color", styling["main_color"]), key=f"{widget_key}_threshold_color_{index}")
        reset_columns = st.columns(2)
        if reset_columns[0].button("Reset colors", key="reset_all_colors"):
            config["styling"] = default_styling(); st.rerun()
        if reset_columns[1].button("Reset all styling", key="reset_all_styling"):
            config["styling"] = default_styling(); st.rerun()
    return config


def editor_controls(df, field_types, config):
    types = field_types; all_fields = types["all"]; numeric = types["numeric"]; categorical = types["categorical"] + types["boolean"]; key = f"editor_{st.session_state.get('editor_revision', 0)}"
    label_for_type = {"kpi_metric": "KPI / Metric", "heat_map": "Heat Map", "word_cloud": "Word Cloud"}
    current_label = label_for_type.get(config["type"], config["type"].title())
    st.markdown('<div class="builder-section">General</div>', unsafe_allow_html=True)
    general = st.columns(3, gap="medium")
    with general[0]:
        chart_label = st.selectbox("Visualization", VIS_TYPES, index=VIS_TYPES.index(current_label) if current_label in VIS_TYPES else 0, key=f"type_{key}")
    with general[1]:
        config["title"] = st.text_input("Title", config.get("title", chart_label if "chart_label" in locals() else current_label), key=f"title_{key}")
    with general[2]:
        config["aggregation"] = st.selectbox("Aggregation", AGGREGATIONS, index=AGGREGATIONS.index(config.get("aggregation", "Count")) if config.get("aggregation") in AGGREGATIONS else 0, key=f"agg_{key}")
    config["type"] = chart_label.lower().replace(" / ", "_").replace(" ", "_")
    compatible = compatible_fields(types, config["aggregation"]) or all_fields
    def choose(label, name, options, fallback=None):
        options = list(options); current = config.get(name) if config.get(name) in options else (fallback or (options[0] if options else None)); config[name] = st.selectbox(label, options or ["No compatible field"], index=options.index(current) if current in options else 0, key=f"{name}_{key}") if options else None
    st.markdown('<div class="builder-section">Axes &amp; Dimensions</div>', unsafe_allow_html=True)
    if config["type"] in {"bar", "line", "area"}:
        axes = st.columns(3, gap="medium")
        with axes[0]: choose("X-axis / Dimension", "x_field", all_fields)
        with axes[1]: choose("Metric field", "y_field", compatible)
        with axes[2]: choose("Breakdown", "breakdown", [None] + categorical, None)
        details = st.columns(3, gap="medium")
        with details[0]: config["date_group"] = st.selectbox("Datetime grouping", DATE_GROUPS, index=DATE_GROUPS.index(config.get("date_group", "None")), key=f"date_{key}")
        with details[1]: config["orientation"] = st.selectbox("Orientation", ["Vertical", "Horizontal"], key=f"orientation_{key}") if config["type"] == "bar" else "Vertical"
        with details[2]:
            config["labels"] = st.checkbox("Data labels", value=config.get("labels", False), key=f"labels_{key}")
            config["points"] = st.checkbox("Data points", value=config.get("points", True), key=f"points_{key}")
            if config["type"] == "area": config["stacked"] = st.checkbox("Stacked", value=config.get("stacked", False), key=f"stacked_{key}")
    elif config["type"] == "kpi_metric":
        axes = st.columns(3, gap="medium")
        with axes[0]: choose("Metric field", "y_field", compatible)
        with axes[1]: config["subtitle"] = st.text_input("Subtitle", config.get("subtitle", ""), key=f"subtitle_{key}")
        with axes[2]: config["precision"] = st.number_input("Decimal precision", 0, 6, int(config.get("precision", 2)), key=f"precision_{key}")
        details = st.columns(3, gap="medium")
        with details[0]: config["prefix"] = st.text_input("Prefix", config.get("prefix", ""), key=f"prefix_{key}")
        with details[1]: config["suffix"] = st.text_input("Suffix", config.get("suffix", ""), key=f"suffix_{key}")
        with details[2]: config["percentage"] = st.checkbox("Percentage format", value=config.get("percentage", False), key=f"percentage_{key}")
    elif config["type"] in {"pie", "waffle", "treemap"}:
        axes = st.columns(3, gap="medium")
        with axes[0]: choose("Group by", "group_field", categorical or all_fields)
        with axes[1]: choose("Metric field", "y_field", compatible)
        with axes[2]: config["top_n"] = st.number_input("Top N", 1, 100, int(config.get("top_n", 10)), key=f"top_{key}")
        details = st.columns(3, gap="medium")
        with details[0]: config["legend"] = st.checkbox("Legend", value=config.get("legend", True), key=f"legend_{key}")
        with details[1]: config["donut"] = st.checkbox("Donut mode", value=config.get("donut", False), key=f"donut_{key}") if config["type"] == "pie" else False
        with details[2]: config["cells"] = st.number_input("Number of cells", 25, 400, int(config.get("cells", 100)), key=f"cells_{key}") if config["type"] == "waffle" else 100
    elif config["type"] == "heat_map":
        axes = st.columns(3, gap="medium")
        with axes[0]: choose("X-axis", "x_field", all_fields)
        with axes[1]: choose("Y-axis", "group_field", categorical or all_fields)
        with axes[2]: choose("Cell metric", "y_field", compatible)
    elif config["type"] == "map":
        axes = st.columns(4, gap="medium")
        with axes[0]: choose("Latitude", "latitude", types["latitude"])
        with axes[1]: choose("Longitude", "longitude", types["longitude"])
        with axes[2]: choose("Metric", "y_field", numeric, None)
        with axes[3]: choose("Breakdown", "breakdown", [None] + categorical, None)
    elif config["type"] == "word_cloud":
        axes = st.columns(4, gap="medium")
        with axes[0]: choose("Text field", "text_field", categorical or all_fields)
        with axes[1]: config["max_words"] = st.number_input("Maximum words", 5, 200, int(config.get("max_words", 30)), key=f"words_{key}")
        with axes[2]: config["min_frequency"] = st.number_input("Minimum frequency", 1, 100, int(config.get("min_frequency", 1)), key=f"frequency_{key}")
        with axes[3]: config["stop_words"] = st.text_input("Stop words", config.get("stop_words", ""), key=f"stops_{key}")
    return color_controls(df, field_types, config)


def filter_controls(df, field_types):
    st.markdown("**Filters**")
    if "draft_filters" not in st.session_state: st.session_state.draft_filters = []
    for index, item in enumerate(st.session_state.draft_filters):
        cols = st.columns([2, 2, 3, .5]); fields = field_types["all"]
        item["field"] = cols[0].selectbox("Field", fields, index=fields.index(item.get("field")) if item.get("field") in fields else 0, key=f"filter_field_{index}")
        item["operator"] = cols[1].selectbox("Operator", ["Equals", "Not equals", "Contains", "Does not contain", "Greater than", "Less than", "Greater than or equal", "Less than or equal", "Is empty", "Is not empty"], key=f"filter_op_{index}")
        item["value"] = cols[2].text_input("Value", item.get("value", ""), key=f"filter_value_{index}")
        if cols[3].button("×", key=f"remove_filter_{index}"): st.session_state.draft_filters.pop(index); st.rerun()
    if st.button("+ Add filter", key="add_filter"): st.session_state.draft_filters.append({"field": field_types["all"][0], "operator": "Equals", "value": ""}); st.rerun()
    return st.session_state.draft_filters


def visualization_html(df, panel):
    output = render_visualization(df, panel.get("config", {}))
    if isinstance(output, dict):
        background = output.get("background", DEFAULT_BACKGROUND); color = output.get("color", "#54b8d5")
        return f"<div style='height:100%;padding:30px 12px;text-align:center;background:{background};color:{readable_text_color(background)}'><div style='font-size:42px;font-weight:800;color:{color}'>{output['value']}</div><div>{output['title']}</div><small>{output.get('subtitle', '')}</small></div>"
    if output is None:
        return "<div style='padding:40px;text-align:center;color:#5d7180'>Visualization unavailable</div>"
    return output.to_html(embed_options={"renderer": "svg"})


def render_dashboard_workspace(df, panels):
    for index, panel in enumerate(panels):
        panel_layout(panel, index)
    layout = [
        elements_dashboard.Item(str(panel["id"]), panel["layout"]["x"], panel["layout"]["y"], panel["layout"]["width"], panel["layout"]["height"])
        for panel in panels
    ]
    with elements("dashboard_workspace"):
        with elements_dashboard.Grid(layout, cols=DASHBOARD_COLUMNS, rowHeight=120, width="100%", draggableHandle=".panel-drag-handle", onLayoutChange=sync("dashboard_layout")):
            for panel in panels:
                styling = ensure_styling(panel.get("config", {}))
                with html.div(key=str(panel["id"]), style={"background": styling["background_color"], "border": "1px solid #2d3b47", "borderRadius": "6px", "overflow": "hidden", "height": "100%"}):
                    html.div(panel.get("title", "Visualization"), className="panel-drag-handle", style={"height": "30px", "padding": "7px 10px", "fontWeight": "700", "color": readable_text_color(styling["background_color"])})
                    html.iframe(srcDoc=visualization_html(df, panel), style={"width": "100%", "height": "calc(100% - 30px)", "border": "0"})
    if st.session_state.get("dashboard_layout"):
        update_dashboard_layout(panels, st.session_state.pop("dashboard_layout"))


def main():
    st.markdown('<div class="lens-kicker">CSV analytics workspace</div>', unsafe_allow_html=True)
    st.title("Omer's Lens")
    if "dashboard_charts" not in st.session_state: st.session_state.dashboard_charts = []
    if "editor_config" not in st.session_state: st.session_state.editor_config = None
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded_file is None:
        st.markdown('<div class="empty-canvas">Upload a CSV to begin building visualizations.</div>', unsafe_allow_html=True)
        return
    try: df = pd.read_csv(uploaded_file)
    except Exception as error: st.error(f"Could not read this CSV: {error}"); return
    if df.empty: st.warning("This dataset is empty."); return
    field_types = detect_fields(df)
    with st.expander("Dataset and fields", expanded=True):
        stats = st.columns(4); stats[0].metric("Rows", f"{len(df):,}"); stats[1].metric("Columns", len(df.columns)); stats[2].metric("Numeric", len(field_types["numeric"])); stats[3].metric("Datetime", len(field_types["datetime"]))
        st.dataframe(df.head(10), use_container_width=True); st.caption("Fields: " + ", ".join(f"{field} ({'numeric' if field in field_types['numeric'] else 'datetime' if field in field_types['datetime'] else 'categorical'})" for field in df.columns))
    base = st.session_state.editor_config or default_config("Bar", field_types)
    st.markdown("**Live preview**")
    preview_slot = st.empty()
    with preview_slot.container(border=True):
        st.info("Preview updates as you configure the visualization below.")
    st.markdown('<div class="builder-section">Configure Visualization</div>', unsafe_allow_html=True)
    with st.container(border=True):
        config = editor_controls(df, field_types, base)
        st.markdown('<div class="builder-section">Filters</div>', unsafe_allow_html=True)
        config["filters"] = filter_controls(df, field_types)
        if st.button("Add to Dashboard", type="primary", use_container_width=True):
            st.session_state.dashboard_charts = add_chart_to_dashboard(st.session_state.dashboard_charts, None, config["type"], config, config.get("title")); st.success("Visualization added.")
    with preview_slot.container(border=True):
        preview = render_visualization(df, config)
        if isinstance(preview, dict):
            number_color = preview["color"] if preview.get("apply_to") in {"KPI number", "Both"} else readable_text_color(preview["background"])
            card_background = preview["color"] if preview.get("apply_to") in {"KPI background", "Both"} else preview["background"]
            text_color = readable_text_color(card_background)
            st.markdown(f"<div style='background:{card_background};border:1px solid #9bbdce;border-radius:6px;padding:4rem 1rem;text-align:center;color:{text_color}'><div style='font-size:3rem;font-weight:800;color:{number_color}'>{preview['value']}</div><div style='font-size:1.2rem;color:{text_color}'>{preview['title']}</div><div style='color:{text_color};opacity:.78'>{preview['subtitle']}</div></div>", unsafe_allow_html=True)
        elif preview is not None:
            st.altair_chart(preview, use_container_width=True)
        else:
            st.info("This visualization needs compatible fields or contains no matching data.")
    st.divider(); st.subheader("Dashboard")
    panels = st.session_state.dashboard_charts
    for index, panel in enumerate(panels):
        panel_layout(panel, index)
    toolbar = st.columns([4, 1, 1, 1, 2])
    toolbar[0].markdown(f"**Analytics workspace** · {len(panels)} panels")
    if toolbar[1].button("+ Add visualization", key="dashboard_add_visualization"):
        st.session_state.editor_config = default_config("Bar", field_types); st.session_state.editor_revision = st.session_state.get("editor_revision", 0) + 1; st.rerun()
    if toolbar[2].button("Reset layout", key="dashboard_reset_layout"):
        reset_dashboard_layout(panels); st.rerun()
    if toolbar[3].button("Download PNG", key="dashboard_download_png"):
        st.session_state.dashboard_export_ready = True
    if toolbar[4].button("Clear dashboard", key="dashboard_clear"):
        st.session_state.dashboard_charts = []; st.rerun()
    if panels:
        render_dashboard_workspace(df, panels)
        st.caption("Drag panel headers to move panels. Drag panel edges or corners to resize.")
        for index, panel in enumerate(panels):
            actions = st.columns([3, 1, 1, 1, 1, 1])
            actions[0].caption(f"P{index + 1:02d} · {panel.get('title', 'Visualization')} · {panel['layout']['width']}×{panel['layout']['height']}")
            if actions[1].button("Edit", key=f"edit_{index}") and "config" in panel:
                st.session_state.editor_config = deepcopy(panel["config"]); st.session_state.editor_revision = st.session_state.get("editor_revision", 0) + 1; st.rerun()
            if actions[2].button("Duplicate", key=f"duplicate_{index}") and "config" in panel:
                copy_panel = {**panel, "id": uuid4().hex, "title": panel.get("title", "Visualization") + " copy", "config": deepcopy(panel["config"]), "layout": deepcopy(panel["layout"])}
                copy_panel["layout"]["x"] = min(DASHBOARD_COLUMNS - copy_panel["layout"]["width"], copy_panel["layout"]["x"] + 1); copy_panel["layout"]["y"] += 1
                st.session_state.dashboard_charts.insert(index + 1, copy_panel); st.rerun()
            if actions[3].button("Delete", key=f"delete_{index}"):
                st.session_state.dashboard_charts = delete_chart_from_dashboard(st.session_state.dashboard_charts, index); st.rerun()
            if actions[4].button("Reset size", key=f"reset_size_{index}"):
                panel["layout"].update({"width": DEFAULT_PANEL_WIDTH, "height": DEFAULT_PANEL_HEIGHT}); st.rerun()
            if actions[5].button("Reset position", key=f"reset_position_{index}"):
                panel["layout"].update({"x": (index % 2) * DEFAULT_PANEL_WIDTH, "y": (index // 2) * DEFAULT_PANEL_HEIGHT}); st.rerun()
        if st.session_state.get("dashboard_export_ready"):
            st.download_button("Download Dashboard as PNG", build_dashboard_image(panels, df), "omer-dashboard.png", "image/png", key="dashboard_export_download")
            st.session_state.dashboard_export_ready = False
    else:
        st.info("Add a visualization to start arranging your dashboard workspace.")


if __name__ == "__main__":
    main()
