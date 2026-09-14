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

st.title("Omer's CSV Dashboard Generator")
st.write("Upload a CSV file to analyze your data and create charts.")

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

        if chart_type == "Line Chart":
            st.line_chart(df[selected_col])
        elif chart_type == "Bar Chart":
            st.bar_chart(df[selected_col])
        elif chart_type == "Area Chart":
            st.area_chart(df[selected_col])
        elif chart_type == "Histogram":
            hist_chart = alt.Chart(df).mark_bar().encode(
                alt.X(f"{selected_col}:Q", bin=alt.Bin(maxbins=30)),
                y="count()"
            ).properties(
                title=f"Histogram of {selected_col}",
                height=350
            )
            st.altair_chart(hist_chart, use_container_width=True)
        elif chart_type == "Scatter Plot":
            if len(numeric_columns) < 2:
                st.warning("Please upload a CSV with at least two numeric columns to create a scatter plot.")
            else:
                x_col = st.selectbox("Choose X-axis numeric column:", numeric_columns)
                y_col = st.selectbox("Choose Y-axis numeric column:", numeric_columns, index=1 if len(numeric_columns) > 1 else 0)
                scatter_chart = alt.Chart(df.dropna(subset=[x_col, y_col])).mark_circle(size=80, opacity=0.7).encode(
                    x=alt.X(f"{x_col}:Q", title=x_col),
                    y=alt.Y(f"{y_col}:Q", title=y_col),
                    tooltip=[x_col, y_col]
                ).properties(
                    title=f"{y_col} vs {x_col}",
                    height=350
                )
                st.altair_chart(scatter_chart, use_container_width=True)
        elif chart_type == "Box Plot":
            if len(categorical_columns) == 0:
                st.warning("Please upload a CSV with a categorical column to create a box plot.")
            else:
                category_col = st.selectbox("Choose a category column:", categorical_columns)
                box_chart = alt.Chart(df.dropna(subset=[selected_col, category_col])).mark_boxplot(extent="min-max").encode(
                    x=alt.X(f"{category_col}:N", title=category_col),
                    y=alt.Y(f"{selected_col}:Q", title=selected_col)
                ).properties(
                    title=f"Box plot of {selected_col} by {category_col}",
                    height=350
                )
                st.altair_chart(box_chart, use_container_width=True)
    else:
        st.warning("The file does not contain numeric columns for charting.")
