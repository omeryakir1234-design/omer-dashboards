import pandas as pd
import streamlit as st
import altair as alt


st.set_page_config(
    page_title="Omer's Dashboards",
    page_icon="📊",
    layout="wide"
)

st.markdown(
    """
    <style>
    :root {
        --page-text: #122b40;
        --page-soft: #eef7fb;
        --line: #dceaf4;
        --card: #ffffff;
        --muted: #667f94;
        --blue: #6cb9e8;
        --blue-deep: #155e8c;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 82% 8%, rgba(180, 226, 248, 0.9), transparent 16%),
            radial-gradient(circle at 10% 90%, rgba(214, 239, 251, 0.8), transparent 16%),
            linear-gradient(135deg, #eefaff 0%, #dcecfb 100%);
        color: var(--page-text);
    }

    [data-testid="stHeader"] {
        background: transparent;
        box-shadow: none;
    }

    .stApp {
        color: var(--page-text);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: min(1400px, calc(100vw - 2rem));
    }

    div[data-testid="stFileUploader"] {
        border-radius: 14px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.78);
        box-shadow: 0 14px 38px rgba(45, 77, 115, 0.08);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        border: 1px solid var(--line);
        background: var(--card);
        overflow: hidden;
    }

    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border-radius: 14px;
        border: 1px solid var(--line);
        background: var(--card);
    }

    .stButton > button {
        border: none;
        border-radius: 14px;
        background: var(--blue-deep);
        color: white;
        font-weight: 700;
        padding: 0.75rem 1.4rem;
        box-shadow: 0 12px 24px rgba(21, 94, 140, 0.16);
        transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease;
    }

    .stButton > button:hover {
        background: var(--blue);
        color: var(--page-text);
        transform: translateY(-2px);
        box-shadow: 0 16px 32px rgba(21, 94, 140, 0.22);
    }

    h1, h2, h3 {
        color: var(--page-text);
        letter-spacing: -0.04em;
        font-family: "Inter", "Segoe UI", Arial, sans-serif;
    }

    .stSubheader {
        color: var(--page-text);
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
    chart_columns = st.columns(2)

    for idx, chart_item in enumerate(st.session_state.dashboard_charts):
        with chart_columns[idx % 2]:
            st.caption(f"{chart_item['type']}")
            st.altair_chart(chart_item['chart'], use_container_width=True)
