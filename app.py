# app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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

    # Computing results
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
st.title("LLM-Powered CSV Analytics Assistant")
st.markdown("Ask questions about the Superstore dataset. Visualizations will appear when applicable.")

# Loading dataset
@st.cache_data
def load_data():
    df = pd.read_csv("Sample - Superstore.csv", parse_dates=["Order Date", "Ship Date"])
    return df

df = load_data()

# Users input
question = st.text_input("💬 Enter your question:")

if question:
    result, plot = ask_csv_llm(question, df)

    st.subheader("Answer:")
    # Displaying results
    if isinstance(result, pd.Series):
        result.index.name = None
        for idx, val in result.items():
            st.write(f"**{idx}**: {round(val,2) if isinstance(val,float) else val}")
    else:
        st.write(round(result,2) if isinstance(result,float) else result)

    # Displaying visualization if needed
    if plot and isinstance(result, pd.Series):
        st.subheader("Visualization:")

        # Auto-detecting chart type
        if group_by := interpret_question_llm(question)["group_by"]:
            fig = px.bar(
                x=result.index,
                y=result.values,
                labels={"x": group_by.capitalize(), "y": interpret_question_llm(question)["metric"].capitalize()},
                title=f"{interpret_question_llm(question)['metric'].capitalize()} by {group_by.capitalize()}",
                text=result.values
            )
            st.plotly_chart(fig, use_container_width=True)

# Optional footer
st.markdown("---")
st.markdown("Made with using Python, Pandas, and Streamlit")