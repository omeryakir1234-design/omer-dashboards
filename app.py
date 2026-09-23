from io import BytesIO
from uuid import uuid4

import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont


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
    .stSelectbox label,.stMultiSelect label,.stNumberInput label,.stTextInput label { color:#d8e7ee !important; }
    [data-baseweb="select"] { background:#d9edf9 !important; color:#10222c !important; }
    div.stButton > button { height:38px; border:1px solid var(--blue); border-radius:4px; background:var(--blue); color:#07151d; font-weight:800; }
    div.stButton > button:hover { background:var(--deep); color:white; }
    section[data-testid="stSidebar"] { background:#17232b; border-right:1px solid var(--line); }
    [data-testid="stMetric"] { background:var(--panel); border:1px solid var(--line); border-radius:6px; }
    .lens-kicker { color:#2789aa; font-size:.76rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
    .empty-canvas { min-height:360px; display:flex; align-items:center; justify-content:center; border:1px dashed #7caabc; border-radius:6px; color:#58717d; background:rgba(234,249,255,.35); }
    </style>
    """,
    unsafe_allow_html=True,
)


PALETTE = ["#2789aa", "#54b8d5", "#80d8d1", "#17647f", "#9adfe5", "#3b9ab8", "#b8eef0"]
VIS_TYPES = ["Bar", "Line", "Area", "KPI / Metric", "Pie", "Heat Map", "Waffle", "Map", "Treemap", "Word Cloud"]
AGGREGATIONS = ["Count", "Unique count", "Sum", "Average", "Min", "Max", "Median"]
DATE_GROUPS = ["None", "Minute", "Hour", "Day", "Week", "Month", "Year"]


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
    return {"type": chart_type.lower().replace(" / ", "_"), "title": chart_type, "x_field": dimension, "y_field": metric,
            "group_field": dimension, "breakdown": None, "aggregation": "Average" if numeric else "Count", "date_group": "None",
            "sort": "Metric", "sort_direction": "Descending", "top_n": 20, "orientation": "Vertical", "legend": True,
            "labels": False, "points": True, "stacked": False, "donut": False, "donut_hole": 0.45, "target": None,
            "subtitle": "", "precision": 2, "prefix": "", "suffix": "", "percentage": False, "cells": 100,
            "min_frequency": 1, "max_words": 30, "stop_words": "the, a, an, and, or, to, of", "font_min": 12, "font_max": 44,
            "filters": []}


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
    if config.get("breakdown"): enc["color"] = alt.Color(f"{config['breakdown']}:N", scale=alt.Scale(range=PALETTE), legend=alt.Legend() if config.get("legend", True) else None)
    if config.get("labels"): enc["text"] = alt.Text("value:Q", format=".2f")
    return alt.Chart(grouped).mark_bar().encode(**enc).properties(title=config.get("title"), height=360)


def build_line_chart(df, config, mark="line"):
    _, grouped = chart_frame(df, config)
    if grouped.empty: return None
    x_type = "T" if config.get("date_group") != "None" else "N"
    enc = {"x": alt.X(f"{config.get('x_field')}:{x_type}", title=config.get("x_field")), "y": alt.Y("value:Q", title=config.get("aggregation"))}
    if config.get("breakdown"): enc["color"] = alt.Color(f"{config['breakdown']}:N", scale=alt.Scale(range=PALETTE), legend=alt.Legend() if config.get("legend", True) else None)
    chart = alt.Chart(grouped).mark_area(opacity=.55) if mark == "area" else alt.Chart(grouped).mark_line(interpolate="monotone", point=config.get("points", True))
    return chart.encode(**enc).properties(title=config.get("title"), height=360)


def build_metric(df, config):
    value = aggregate_series(apply_filters(df, config.get("filters", [])), config.get("y_field"), config.get("aggregation", "Count"))
    formatted = f"{config.get('prefix', '')}{value:,.{int(config.get('precision', 2))}f}{config.get('suffix', '')}" if isinstance(value, (float, int)) else str(value)
    if config.get("percentage"): formatted = f"{float(value) * 100:,.{int(config.get('precision', 2))}f}%"
    return {"value": formatted, "title": config.get("title", "Metric"), "subtitle": config.get("subtitle", "")}


def build_pie_chart(df, config):
    _, grouped = chart_frame(df, {**config, "x_field": config.get("group_field")})
    if grouped.empty: return None
    grouped = grouped.nlargest(int(config.get("top_n", 10)), "value")
    return alt.Chart(grouped).mark_arc(innerRadius=70 if config.get("donut") else 0).encode(theta=alt.Theta("value:Q"), color=alt.Color(f"{config.get('group_field')}:N", scale=alt.Scale(range=PALETTE), legend=alt.Legend() if config.get("legend", True) else None), tooltip=[config.get("group_field"), alt.Tooltip("value:Q", format=",.2f")]).properties(title=config.get("title"), height=360)


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
    chart = alt.Chart(grouped).mark_rect().encode(x=alt.X(f"{x}:N"), y=alt.Y(f"{y}:N"), color=alt.Color("value:Q", scale=alt.Scale(range=["#d9edf9", "#2789aa"])), tooltip=list(grouped.columns))
    return chart.properties(title=config.get("title"), height=360)


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
    return alt.Chart(pd.DataFrame(rows)).mark_rect(stroke="#d9edf9", strokeWidth=1).encode(x=alt.X("column:O", axis=None), y=alt.Y("row:O", sort="descending", axis=None), color=alt.Color("category:N", scale=alt.Scale(range=PALETTE), legend=alt.Legend() if config.get("legend", True) else None), tooltip=["category"]).properties(title=config.get("title"), width=360, height=360)


def build_map(df, config):
    lat, lon = config.get("latitude"), config.get("longitude")
    if not lat or not lon or lat not in df.columns or lon not in df.columns: return None
    work = df.copy(); work[lat] = pd.to_numeric(work[lat], errors="coerce"); work[lon] = pd.to_numeric(work[lon], errors="coerce"); work = work.dropna(subset=[lat, lon])
    if work.empty: return None
    enc = {"latitude": alt.Latitude(f"{lat}:Q"), "longitude": alt.Longitude(f"{lon}:Q"), "tooltip": [lat, lon]}
    return alt.Chart(work).mark_circle(opacity=.7, color=PALETTE[0]).encode(**enc).properties(title=config.get("title"), height=380)


def build_treemap(df, config):
    group = config.get("group_field")
    _, grouped = chart_frame(df, {**config, "x_field": group})
    if grouped.empty: return None
    grouped = grouped.nlargest(int(config.get("top_n", 20)), "value")
    return alt.Chart(grouped).mark_bar().encode(x=alt.X(f"{group}:N", axis=None), y=alt.Y("value:Q", axis=None), color=alt.Color(f"{group}:N", scale=alt.Scale(range=PALETTE), legend=None), tooltip=[group, "value:Q"]).properties(title=config.get("title"), height=360)


def build_wordcloud(df, config):
    field = config.get("text_field")
    if not field or field not in df.columns: return None
    work = apply_filters(df, config.get("filters", [])); words = work[field].dropna().astype(str).str.lower().str.split().explode()
    stops = {word.strip() for word in config.get("stop_words", "").split(",") if word.strip()}; words = words[~words.isin(stops) & (words.str.len() > 1)]
    counts = words.value_counts().rename_axis("word").reset_index(name="value"); counts = counts[counts.value >= int(config.get("min_frequency", 1))].head(int(config.get("max_words", 30)))
    if counts.empty: return None
    return alt.Chart(counts).mark_text().encode(text="word:N", size=alt.Size("value:Q", scale=alt.Scale(range=[int(config.get("font_min", 12)), int(config.get("font_max", 44))]), legend=None), color=alt.Color("value:Q", scale=alt.Scale(range=PALETTE), legend=None), tooltip=["word", "value"]).properties(title=config.get("title"), height=360)


def render_visualization(df, config):
    chart_type = config.get("type", "bar")
    builders = {"bar": build_bar_chart, "line": lambda data, settings: build_line_chart(data, settings), "area": lambda data, settings: build_line_chart(data, settings, "area"), "pie": build_pie_chart, "heat_map": build_heatmap, "waffle": build_waffle, "map": build_map, "treemap": build_treemap, "word_cloud": build_wordcloud}
    if chart_type == "kpi_metric": return build_metric(df, config)
    builder = builders.get(chart_type)
    return builder(df, config) if builder else None


def add_chart_to_dashboard(dashboard, chart, chart_type, config=None, title=None):
    if config is None: return dashboard + [{"type": chart_type, "chart": chart}]
    return dashboard + [{"id": uuid4().hex, "type": config.get("type", chart_type), "title": title or config.get("title", chart_type), "config": dict(config)}]


def delete_chart_from_dashboard(dashboard, index):
    if 0 <= index < len(dashboard): del dashboard[index]
    return dashboard


def build_dashboard_image(dashboard):
    image = Image.new("RGB", (1024, 700 + max(0, len(dashboard) - 1) * 120), color=(239, 247, 252)); draw = ImageDraw.Draw(image)
    try: font_header = ImageFont.truetype("arial.ttf", 36); font_body = ImageFont.truetype("arial.ttf", 22); font_small = ImageFont.truetype("arial.ttf", 16)
    except Exception: font_header = font_body = font_small = ImageFont.load_default()
    draw.rectangle((0, 0, image.width, image.height), fill=(239, 247, 252)); draw.rectangle((40, 30, image.width - 40, 110), fill=(30, 76, 110)); draw.text((70, 50), "Omer's Dashboard", fill=(250, 251, 252), font=font_header)
    for idx, item in enumerate(dashboard):
        y = 140 + idx * 120; draw.rounded_rectangle((60, y, 964, y + 90), radius=14, fill=(255, 255, 255)); draw.text((104, y + 15), f"{idx + 1}. {item.get('title', item.get('type', 'Chart'))}", fill=(30, 76, 110), font=font_body); draw.text((104, y + 50), str(item.get("type", "Visualization")), fill=(84, 108, 126), font=font_small)
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


def editor_controls(df, field_types, config):
    types = field_types; all_fields = types["all"]; numeric = types["numeric"]; categorical = types["categorical"] + types["boolean"]; key = f"editor_{st.session_state.get('editor_revision', 0)}"
    label_for_type = {"kpi_metric": "KPI / Metric", "heat_map": "Heat Map", "word_cloud": "Word Cloud"}
    current_label = label_for_type.get(config["type"], config["type"].title())
    chart_label = st.selectbox("Visualization", VIS_TYPES, index=VIS_TYPES.index(current_label) if current_label in VIS_TYPES else 0, key=f"type_{key}")
    config["type"] = chart_label.lower().replace(" / ", "_").replace(" ", "_")
    config["title"] = st.text_input("Title", config.get("title", chart_label), key=f"title_{key}")
    config["aggregation"] = st.selectbox("Aggregation", AGGREGATIONS, index=AGGREGATIONS.index(config.get("aggregation", "Count")) if config.get("aggregation") in AGGREGATIONS else 0, key=f"agg_{key}")
    compatible = compatible_fields(types, config["aggregation"]) or all_fields
    def choose(label, name, options, fallback=None):
        options = list(options); current = config.get(name) if config.get(name) in options else (fallback or (options[0] if options else None)); config[name] = st.selectbox(label, options or ["No compatible field"], index=options.index(current) if current in options else 0, key=f"{name}_{key}") if options else None
    if config["type"] in {"bar", "line", "area"}:
        choose("X-axis / Dimension", "x_field", all_fields); choose("Metric field", "y_field", compatible); choose("Breakdown", "breakdown", [None] + categorical, None); config["date_group"] = st.selectbox("Datetime grouping", DATE_GROUPS, index=DATE_GROUPS.index(config.get("date_group", "None")), key=f"date_{key}"); config["orientation"] = st.selectbox("Orientation", ["Vertical", "Horizontal"], key=f"orientation_{key}") if config["type"] == "bar" else "Vertical"; config["points"] = st.checkbox("Data points", value=config.get("points", True), key=f"points_{key}"); config["stacked"] = st.checkbox("Stacked", value=config.get("stacked", False), key=f"stacked_{key}") if config["type"] == "area" else False
    elif config["type"] == "kpi_metric":
        choose("Metric field", "y_field", compatible); config["subtitle"] = st.text_input("Subtitle", config.get("subtitle", ""), key=f"subtitle_{key}"); config["precision"] = st.number_input("Decimal precision", 0, 6, int(config.get("precision", 2)), key=f"precision_{key}"); config["prefix"] = st.text_input("Prefix", config.get("prefix", ""), key=f"prefix_{key}"); config["suffix"] = st.text_input("Suffix", config.get("suffix", ""), key=f"suffix_{key}"); config["percentage"] = st.checkbox("Percentage format", value=config.get("percentage", False), key=f"percentage_{key}")
    elif config["type"] in {"pie", "waffle", "treemap"}:
        choose("Group by", "group_field", categorical or all_fields); choose("Metric field", "y_field", compatible); config["top_n"] = st.number_input("Top N", 1, 100, int(config.get("top_n", 10)), key=f"top_{key}"); config["legend"] = st.checkbox("Legend", value=config.get("legend", True), key=f"legend_{key}"); config["donut"] = st.checkbox("Donut mode", value=config.get("donut", False), key=f"donut_{key}") if config["type"] == "pie" else False; config["cells"] = st.number_input("Number of cells", 25, 400, int(config.get("cells", 100)), key=f"cells_{key}") if config["type"] == "waffle" else 100
    elif config["type"] == "heat_map":
        choose("X-axis", "x_field", all_fields); choose("Y-axis", "group_field", categorical or all_fields); choose("Cell metric", "y_field", compatible)
    elif config["type"] == "map":
        choose("Latitude", "latitude", types["latitude"]); choose("Longitude", "longitude", types["longitude"]); choose("Metric", "y_field", numeric, None)
    elif config["type"] == "word_cloud":
        choose("Text field", "text_field", categorical or all_fields); config["max_words"] = st.number_input("Maximum words", 5, 200, int(config.get("max_words", 30)), key=f"words_{key}"); config["min_frequency"] = st.number_input("Minimum frequency", 1, 100, int(config.get("min_frequency", 1)), key=f"frequency_{key}"); config["stop_words"] = st.text_input("Stop words", config.get("stop_words", ""), key=f"stops_{key}")
    return config


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
    left, right = st.columns([2.2, 1], gap="large")
    with right:
        with st.container(border=True):
            st.markdown("**Configure visualization**")
            config = editor_controls(df, field_types, base)
            config["filters"] = filter_controls(df, field_types)
            if st.button("Add to Dashboard", type="primary", use_container_width=True):
                st.session_state.dashboard_charts = add_chart_to_dashboard(st.session_state.dashboard_charts, None, config["type"], config, config.get("title")); st.success("Visualization added.")
    with left:
        st.markdown("**Live preview**")
        preview = render_visualization(df, config)
        if isinstance(preview, dict): st.markdown(f"<div style='background:#d9edf9;border:1px solid #9bbdce;border-radius:6px;padding:4rem 1rem;text-align:center'><div style='font-size:3rem;font-weight:800;color:#2789aa'>{preview['value']}</div><div style='font-size:1.2rem;color:#10222c'>{preview['title']}</div><div style='color:#5d7180'>{preview['subtitle']}</div></div>", unsafe_allow_html=True)
        elif preview is not None: st.altair_chart(preview, use_container_width=True)
        else: st.info("This visualization needs compatible fields or contains no matching data.")
    st.divider(); st.subheader("Dashboard")
    if not st.session_state.dashboard_charts: st.caption("Your saved visualizations will appear here.")
    else:
        top = st.columns([4, 1, 2]); top[0].markdown("**Saved panels**"); top[1].metric("Panels", len(st.session_state.dashboard_charts)); top[2].download_button("Download dashboard", build_dashboard_image(st.session_state.dashboard_charts), "dashboard.png", "image/png")
        panel_columns = st.columns(2)
        for index, panel in enumerate(st.session_state.dashboard_charts):
            with panel_columns[index % 2]:
                with st.container(border=True):
                    st.caption(f"{panel.get('type', 'Chart').replace('_', ' ').title()} · P{index + 1:02d}"); st.markdown(f"**{panel.get('title', 'Visualization')}**")
                    if "config" in panel:
                        output = render_visualization(df, panel["config"])
                        if isinstance(output, dict): st.metric(output["title"], output["value"], help=output["subtitle"])
                        elif output is not None: st.altair_chart(output, use_container_width=True)
                        else: st.warning("This panel cannot render with the current dataset.")
                    else: st.info("Legacy panel. Create a new visualization to edit it.")
                    actions = st.columns(3)
                    if actions[0].button("Edit", key=f"edit_{index}") and "config" in panel: st.session_state.editor_config = dict(panel["config"]); st.session_state.editor_revision = st.session_state.get("editor_revision", 0) + 1; st.rerun()
                    if actions[1].button("Duplicate", key=f"duplicate_{index}") and "config" in panel: st.session_state.dashboard_charts.insert(index + 1, {**panel, "id": uuid4().hex, "title": panel.get("title", "Visualization") + " copy", "config": dict(panel["config"])}); st.rerun()
                    if actions[2].button("Delete", key=f"delete_{index}"): st.session_state.dashboard_charts = delete_chart_from_dashboard(st.session_state.dashboard_charts, index); st.rerun()


if __name__ == "__main__":
    main()
