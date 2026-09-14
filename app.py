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
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #bfe7ff 0%, #eaf6ff 100%);
    }

    [data-testid="stHeader"] {
        background: rgba(0, 0, 0, 0);
    }

    .stApp {
        color: #0b1f3a;
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
