import pandas as pd
import streamlit as st
import altair as alt
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


st.set_page_config(
    page_title="Omer's Dashboards",
    page_icon="📊",
    layout="wide"
)

st.markdown(
    """
    <style>
    :root {
        --text: #e8edf2;
        --text-soft: #aab7c4;
        --muted: #71808e;
        --line: #2d3b47;
        --glass: rgba(25, 35, 43, 0.92);
        --panel: #202c35;
        --panel-soft: #263640;
        --blue: #54b8d5;
        --blue-deep: #2789aa;
        --blue-dark: #f0f4f7;
        --aqua: #80d8d1;
        --shadow: rgba(0, 0, 0, 0.28);
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 76% 6%, rgba(183, 226, 250, 0.95), transparent 15%),
            radial-gradient(circle at 16% 92%, rgba(155, 220, 232, 0.60), transparent 14%),
            linear-gradient(135deg, #eaf9ff 0%, #d9edf9 52%, #c8dde8 100%);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: transparent;
        box-shadow: none;
    }

    .stApp {
        color: var(--text);
    }

    .block-container {
        padding-top: 1.35rem;
        padding-bottom: 3rem;
        max-width: min(1440px, calc(100vw - 3rem));
    }

    h1 {
        font-size: clamp(2.2rem, 3vw, 3.2rem) !important;
        font-weight: 700 !important;
        color: var(--blue-dark) !important;
        letter-spacing: 0 !important;
        margin-bottom: 0.4rem !important;
    }

    h2, h3 {
        color: var(--blue-dark) !important;
        font-weight: 700 !important;
        letter-spacing: -0.035em !important;
    }

    p, .stMarkdown {
        color: var(--text-soft);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        box-shadow: 0 8px 24px var(--shadow);
    }

    div[data-testid="stFileUploader"] {
        border-radius: 6px;
        border: 1px solid var(--line);
        background: var(--glass);
        box-shadow: 0 8px 24px var(--shadow);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 6px;
        border: 1px solid var(--line);
        background: var(--panel);
        box-shadow: 0 8px 24px var(--shadow);
        overflow: hidden;
    }

    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stNumberInput > div > div,
    .stTextInput > div > div {
        border-radius: 14px;
        border: 1px solid var(--line);
        background: #18232b;
        box-shadow: 0 2px 8px var(--shadow);
    }

    div.stButton > button {
        height: 38px;
        border: 1px solid var(--blue);
        border-radius: 4px;
        background: var(--blue);
        color: #07151d;
        font-weight: 900;
        font-size: 0.88rem;
        letter-spacing: 0.03em;
        padding: 0.7rem 1.45rem;
        box-shadow: 0 5px 14px var(--shadow);
        transition: transform 220ms ease, box-shadow 220ms ease, filter 220ms ease, background 220ms ease;
        font-family: "Inter", "Segoe UI", Arial, sans-serif;
    }

    div.stButton > button:hover {
        background: var(--blue-deep);
        color: #ffffff;
        transform: translateY(-1px);
        box-shadow: 0 8px 18px var(--shadow);
        filter: saturate(1.12);
    }

    div.stButton > button:focus {
        outline: 3px solid rgba(150, 220, 232, 0.75);
        outline-offset: 3px;
    }

    div.stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 7px 16px var(--shadow);
    }

    section[data-testid="stSidebar"] {
        background: #17232b;
        border-right: 1px solid var(--line);
        box-shadow: 0 12px 36px var(--shadow);
    }

    div[data-testid="stAlert"] {
        border-radius: 14px;
    }

    .stCaption {
        color: var(--aqua);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    div[data-testid="stDownloadButton"] > button {
        height: 38px;
        border-radius: 4px;
        border: 1px solid #496171;
        background: #263640;
        color: var(--text);
        font-weight: 700;
    }

    div[data-testid="stDownloadButton"] > button:hover {
        border-color: var(--blue);
        color: #ffffff;
        background: #304755;
    }

    [data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 0.7rem 0.9rem;
    }

    .css-1v0mbdj, .css-1n7v2u7 {
        padding: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def add_chart_to_dashboard(dashboard, chart, chart_type):
    dashboard.append({
        "type": chart_type,
        "chart": chart,
    })
    return dashboard


def delete_chart_from_dashboard(dashboard, index):
    if 0 <= index < len(dashboard):
        del dashboard[index]
    return dashboard


def build_dashboard_image(dashboard):
    """Create a simple PNG dashboard preview image from the saved charts in session state."""
    width = 1024
    height = 700 + max(0, len(dashboard) - 1) * 120
    image = Image.new("RGB", (width, height), color=(239, 247, 252))
    draw = ImageDraw.Draw(image)

    try:
        font_header = ImageFont.truetype("arial.ttf", 36)
        font_body = ImageFont.truetype("arial.ttf", 22)
        font_small = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font_header = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_small = ImageFont.load_default()

    title = "Omer's Dashboard"
    draw.rectangle((0, 0, width, height), fill=(239, 247, 252))
    draw.rectangle((40, 30, width - 40, 110), fill=(30, 76, 110))
    draw.text((70, 50), title, fill=(250, 251, 252), font=font_header)

    y = 140
    for idx, item in enumerate(dashboard):
        chart_type = item.get("type", "Chart")
        x0 = 60
        y0 = y
        x1 = width - 60
        y1 = y + 90
        draw.rounded_rectangle((x0, y0, x1, y1), radius=14, fill=(255, 255, 255))
        draw.rounded_rectangle((x0 + 8, y0 + 8, x0 + 30, y0 + 30), radius=6, fill=(120, 197, 235))
        draw.text((x0 + 44, y0 + 15), f"{idx + 1}. {chart_type}", fill=(30, 76, 110), font=font_body)
        draw.text((x0 + 44, y0 + 50), "Visualization", fill=(84, 108, 126), font=font_small)
        y += 120

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def build_chart(df, chart_type, selected_col, numeric_columns, categorical_columns, x_col=None, y_col=None, category_col=None):
    """Return an Altair chart object for the selected chart style."""
    if chart_type == "Line Chart":
        plot_df = df.reset_index(drop=True).reset_index().rename(columns={"index": "row"})
        return alt.Chart(plot_df).mark_line(point=True).encode(
            x=alt.X("row:O", title="Row"),
            y=alt.Y(f"{selected_col}:Q", title=selected_col)
        ).properties(
            title=f"Line chart of {selected_col}",
            height=350
        )

    if chart_type == "Bar Chart":
        plot_df = df.reset_index(drop=True).reset_index().rename(columns={"index": "row"})
        return alt.Chart(plot_df).mark_bar().encode(
            x=alt.X("row:O", title="Row"),
            y=alt.Y(f"{selected_col}:Q", title=selected_col)
        ).properties(
            title=f"Bar chart of {selected_col}",
            height=350
        )

    if chart_type == "Area Chart":
        plot_df = df.reset_index(drop=True).reset_index().rename(columns={"index": "row"})
        return alt.Chart(plot_df).mark_area().encode(
            x=alt.X("row:O", title="Row"),
            y=alt.Y(f"{selected_col}:Q", title=selected_col)
        ).properties(
            title=f"Area chart of {selected_col}",
            height=350
        )

    if chart_type == "Histogram":
        return alt.Chart(df).mark_bar().encode(
            alt.X(f"{selected_col}:Q", bin=alt.Bin(maxbins=30), title=selected_col),
            y=alt.Y("count():Q", title="Count")
        ).properties(
            title=f"Histogram of {selected_col}",
            height=350
        )

    if chart_type == "Scatter Plot":
        if len(numeric_columns) < 2:
            return None
        x_col = x_col or numeric_columns[0]
        y_col = y_col or numeric_columns[1]
        return alt.Chart(df.dropna(subset=[x_col, y_col])).mark_circle(size=80, opacity=0.7).encode(
            x=alt.X(f"{x_col}:Q", title=x_col),
            y=alt.Y(f"{y_col}:Q", title=y_col),
            tooltip=[x_col, y_col]
        ).properties(
            title=f"{y_col} vs {x_col}",
            height=350
        )

    if chart_type == "Box Plot":
        if len(categorical_columns) == 0:
            return None
        category_col = category_col or categorical_columns[0]
        return alt.Chart(df.dropna(subset=[selected_col, category_col])).mark_boxplot(extent="min-max").encode(
            x=alt.X(f"{category_col}:N", title=category_col),
            y=alt.Y(f"{selected_col}:Q", title=selected_col)
        ).properties(
            title=f"Box plot of {selected_col} by {category_col}",
            height=350
        )

    return None


st.title("Omer's CSV Dashboard Generator")
st.write("Upload a CSV file to analyze your data and create charts.")

if "dashboard_charts" not in st.session_state:
    st.session_state.dashboard_charts = []

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Data Preview")
    st.dataframe(df.head())

    st.subheader("Dataset Summary")
    st.dataframe(df.describe(include="all"))

    st.subheader("Columns")
    st.write("Total rows:", df.shape[0])
    st.write("Total columns:", df.shape[1])
    st.write(df.dtypes)

    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = df.select_dtypes(exclude=["number"]).columns.tolist()

    if len(numeric_columns) > 0:
        st.subheader("Create a Chart")

        chart_type = st.selectbox(
            "Choose a chart type:",
            ["Line Chart", "Bar Chart", "Area Chart", "Histogram", "Scatter Plot", "Box Plot"]
        )

        selected_col = st.selectbox(
            "Choose a numeric column to visualize:",
            numeric_columns
        )

        x_col = None
        y_col = None
        category_col = None

        if chart_type == "Scatter Plot":
            if len(numeric_columns) < 2:
                st.warning("Please upload a CSV with at least two numeric columns to create a scatter plot.")
            else:
                x_col = st.selectbox("Choose X-axis numeric column:", numeric_columns)
                y_col = st.selectbox("Choose Y-axis numeric column:", numeric_columns, index=1 if len(numeric_columns) > 1 else 0)

        elif chart_type == "Box Plot":
            if len(categorical_columns) == 0:
                st.warning("Please upload a CSV with a categorical column to create a box plot.")
            else:
                category_col = st.selectbox("Choose a category column:", categorical_columns)

        chart = build_chart(
            df=df,
            chart_type=chart_type,
            selected_col=selected_col,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            x_col=x_col,
            y_col=y_col,
            category_col=category_col,
        )

        if chart is not None:
            st.altair_chart(chart, use_container_width=True)

            if st.button("Add Current Visualization to Dashboard"):
                st.session_state.dashboard_charts = add_chart_to_dashboard(
                    st.session_state.dashboard_charts,
                    chart,
                    chart_type,
                )
                st.success("Visualization added to the dashboard.")

    else:
        st.warning("The file does not contain numeric columns for charting.")

if st.session_state.dashboard_charts:
    st.subheader("Dashboard")

    dashboard_header_col, dashboard_stats_col, dashboard_actions_col = st.columns([5, 2, 3])
    with dashboard_header_col:
        st.markdown("**Analytics workspace**")
        st.caption("Saved visualizations")

    with dashboard_stats_col:
        st.metric("Panels", len(st.session_state.dashboard_charts))

    with dashboard_actions_col:
        st.download_button(
            label="Download dashboard",
            data=build_dashboard_image(st.session_state.dashboard_charts),
            file_name="dashboard.png",
            mime="image/png",
        )

    chart_columns = st.columns(2)

    for idx, chart_item in enumerate(st.session_state.dashboard_charts):
        with chart_columns[idx % 2]:
            with st.container(border=True):
                panel_title_col, panel_meta_col = st.columns([5, 1])
                with panel_title_col:
                    st.caption(f"{chart_item['type']}")
                with panel_meta_col:
                    st.caption(f"P{idx + 1:02d}")
                st.altair_chart(chart_item["chart"], use_container_width=True)

    download_col, delete_col = st.columns([4, 1])
    with delete_col:
        if st.button("×", key="delete_dashboard_visualization", help="Delete last visualization"):
            if st.session_state.dashboard_charts:
                st.session_state.dashboard_charts = delete_chart_from_dashboard(
                    st.session_state.dashboard_charts,
                    len(st.session_state.dashboard_charts) - 1,
                )
