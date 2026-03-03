import streamlit as st
import pandas as pd
import plotly.express as px

st.title("💰 Donation Dashboard")

uploaded_file = st.file_uploader("Upload your donation CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is None:
    st.info("Please upload a file to get started.")st.stop()

# Load the file
if uploaded_file.name.endswith(".xlsx"):
    df = pd.read_excel(uploaded_file)
else:
    df = pd.read_csv(uploaded_file)

# Clean up column names
df.columns = df.columns.str.strip()

# Clean the Amount column
df['Amount'] = df['Amount'].astype(str).str.replace('[$,]', '', regex=True).str.strip()
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

# Clean the date column
df['Paid At'] = pd.to_datetime(df['Paid At'], errors='coerce')

st.markdown("---")

# ── KEY NUMBERS ──
st.subheader("📊 Summary")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Raised", f"${df['Amount'].sum():,.2f}")
col2.metric("Total Donations", f"{len(df):,}")
col3.metric("Unique Donors", f"{df['Full Name'].nunique():,}")
col4.metric("Average Donation", f"${df['Amount'].mean():,.2f}")

st.markdown("---")

# ── TOP DONORS ──
st.subheader("🏆 Top 10 Donors")

top_donors = (
    df.groupby('Full Name')['Amount']
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)
top_donors.columns = ['Name', 'Total Donated']

st.dataframe(top_donors, use_container_width=True)

st.markdown("---")

# ── DONATIONS OVER TIME ──
st.subheader("📅 Donations Over Time")

df['Month'] = df['Paid At'].dt.to_period('M').astype(str)
monthly = df.groupby('Month')['Amount'].sum().reset_index()
monthly.columns = ['Month', 'Total']

fig = px.bar(monthly, x='Month', y='Total', title='Monthly Donations')
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── RAW DATA ──
st.subheader("📋 Raw Data")
st.dataframe(df, use_container_width=True)
