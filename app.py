# app.py

import streamlit as st
import pandas as pd
import plotly.express as px


# LLM + Guardrails Functions
def interpret_question_llm(question):
    q = question.lower()

    # Hard-coded rules (guardrails)
    if "most profitable" in q:
        return {"metric": "profit", "group_by": "category", "plot": True}
    if "sold the most" in q or "most sold" in q:
        return {"metric": "quantity", "group_by": "product", "plot": True}
    if "sales per region" in q or "sales by region" in q:
        return {"metric": "sales", "group_by": "region", "plot": True}
    if "sales per year" in q or "sales by year" in q:
        return {"metric": "sales", "group_by": "year", "plot": True}
    if "total sales" in q:
        return {"metric": "sales", "group_by": "none", "plot": False}

    # Default fallback
    return {"metric": "sales", "group_by": "none", "plot": False}


def ask_csv_llm(question, df):
    intent = interpret_question_llm(question)
    metric = intent["metric"]
    group_by = intent["group_by"]
    plot = intent["plot"]

    # Compute results
    if metric == "sales" and group_by == "region":
        result = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
    elif metric == "sales" and group_by == "year":
        result = df.groupby(df["Order Date"].dt.year)["Sales"].sum()
    elif metric == "profit" and group_by == "category":
        result = df.groupby("Category")["Profit"].sum().sort_values(ascending=False)
    elif metric == "quantity" and group_by == "product":
        result = df.groupby("Product Name")["Quantity"].sum().sort_values(ascending=False).head(10)
    elif metric == "sales" and group_by == "none":
        result = df["Sales"].sum()
    else:
        result = "Intent understood, but analysis not implemented yet."

    return result, plot


# Streamlit App
st.set_page_config(page_title="CSV LLM Assistant", layout="wide")
st.title("📊 LLM-Powered CSV Analytics Assistant")
st.markdown("Interactive dashboard for the Superstore dataset with charts and metrics.")

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv("Sample - Superstore.csv", parse_dates=["Order Date", "Ship Date"])
    return df

df = load_data()


# Sidebar Controls
st.sidebar.header("Dashboard Controls")
metric_option = st.sidebar.selectbox("Select Metric", ["Sales", "Profit", "Quantity"])
group_option = st.sidebar.selectbox("Group By", ["None", "Region", "Year", "Category", "Product"])


# Tabs
tab1, tab2 = st.tabs(["Dashboard", "Ask a Question"])

# Tab 1: Dashboard
with tab1:
    st.subheader("Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sales", f"${df['Sales'].sum():,.2f}")
    col2.metric("Total Profit", f"${df['Profit'].sum():,.2f}")
    col3.metric("Total Quantity", f"{df['Quantity'].sum()}")

    st.subheader("Visualization")
    # Prepare data for chart
    group_col = None
    if group_option == "Region":
        group_col = "Region"
    elif group_option == "Year":
        group_col = df["Order Date"].dt.year
    elif group_option == "Category":
        group_col = "Category"
    elif group_option == "Product":
        group_col = "Product Name"

    if group_col is not None:
        metric_col = metric_option
        data = df.groupby(group_col)[metric_col].sum().sort_values(ascending=False)
        fig = px.bar(
            x=data.index,
            y=data.values,
            labels={"x": group_option, "y": metric_option},
            title=f"{metric_option} by {group_option}",
            text=data.values
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select a group to generate a chart.")

# Tab 2: Ask a Question
with tab2:
    question = st.text_input("Enter your question about the dataset:")

    if question:
        result, plot = ask_csv_llm(question, df)
        st.subheader("Answer:")
        if isinstance(result, pd.Series):
            for idx, val in result.items():
                st.write(f"**{idx}**: {round(val,2) if isinstance(val,float) else val}")
        else:
            st.write(round(result,2) if isinstance(result,float) else result)

        if plot and isinstance(result, pd.Series):
            st.subheader("Visualization:")
            fig = px.bar(
                x=result.index,
                y=result.values,
                labels={"x": interpret_question_llm(question)["group_by"].capitalize(),
                        "y": interpret_question_llm(question)["metric"].capitalize()},
                title=f"{interpret_question_llm(question)['metric'].capitalize()} by {interpret_question_llm(question)['group_by'].capitalize()}",
                text=result.values
            )
            st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Made using Python, Pandas, Plotly, and Streamlit")