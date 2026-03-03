import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Donation Dashboard", page_icon="💰", layout="wide")
st.title("💰 Campaign Donation Dashboard")
st.markdown("---")

# ─────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────
uploaded_file = st.sidebar.file_uploader(
    "📁 Upload Donation CSV or Excel",
    type=["csv", "xlsx"]
)

if uploaded_file is None:
    st.info("👈 Upload your donation file in the sidebar to get started.")
    st.stop()

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
@st.cache_data
def load_data(file):
    if file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)

    df.columns = df.columns.str.strip()

    # Clean Amount
    df['Amount'] = (
        df['Amount']
        .astype(str)
        .str.replace('[$,]', '', regex=True)
        .str.strip()
    )
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

    # Clean Date
    df['Paid At'] = pd.to_datetime(df['Paid At'], errors='coerce')

    return df

df = load_data(uploaded_file)

# ─────────────────────────────────────────
# TABS
# ─────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Summary",
    "🏆 Top Donors",
    "📅 Timeline",
    "🎯 Donor Scoring"
])

# ══════════════════════════════════════════
# TAB 1 — SUMMARY
# ══════════════════════════════════════════
with tab1:
    st.subheader("📊 Summary Metrics")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Raised", f"${df['Amount'].sum():,.2f}")
    col2.metric("🔢 Total Donations", f"{len(df):,}")
    col3.metric("👥 Unique Donors", f"{df['Full Name'].nunique():,}")
    col4.metric("📈 Average Donation", f"${df['Amount'].mean():,.2f}")

    st.markdown("---")

    # In District breakdown
    if 'In District' in df.columns:
        st.subheader("🏘️ In-District Breakdown")
        district_counts = df['In District'].value_counts().reset_index()
        district_counts.columns = ['In District', 'Count']
        fig = px.pie(
            district_counts,
            names='In District',
            values='Count',
            title='In District vs Out of District',
            color_discrete_map={'Y': '#2ecc71', 'N': '#e74c3c'}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # State breakdown
    if 'Donor State' in df.columns:
        st.subheader("🗺️ Donations by State")
        state_totals = (
            df.groupby('Donor State')['Amount']
            .sum()
            .reset_index()
            .sort_values('Amount', ascending=False)
            .head(15)
        )
        fig2 = px.bar(
            state_totals,
            x='Donor State',
            y='Amount',
            title='Top States by Amount Raised',
            color='Amount',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # Raw data
    st.subheader("📋 Raw Data")
    st.dataframe(df, use_container_width=True)


# ══════════════════════════════════════════
# TAB 2 — TOP DONORS
# ══════════════════════════════════════════
with tab2:
    st.subheader("🏆 Top Donors")

    top_n = st.slider("Show Top N Donors", 5, 50, 10)

    top_donors = (
        df.groupby('Full Name')['Amount']
        .agg(['sum', 'count'])
        .reset_index()
        .rename(columns={'sum': 'Total Donated', 'count': 'Donations'})
        .sort_values('Total Donated', ascending=False)
        .head(top_n)
    )

    col_a, col_b = st.columns(2)

    with col_a:
        st.dataframe(
            top_donors.style.format({'Total Donated': '${:,.2f}'}),
            use_container_width=True
        )

    with col_b:
        fig3 = px.bar(
            top_donors.sort_values('Total Donated'),
            x='Total Donated',
            y='Full Name',
            orientation='h',
            title=f'Top {top_n} Donors by Total Amount',
            color='Total Donated',
            color_continuous_scale='Greens'
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # Repeat donors
    st.subheader("🔄 Repeat Donors")
    repeat = (
        df.groupby('Full Name')['Amount']
        .agg(['sum', 'count'])
        .reset_index()
        .rename(columns={'sum': 'Total Donated', 'count': 'Donations'})
        .query('Donations > 1')
        .sort_values('Donations', ascending=False)
    )
    st.dataframe(
        repeat.style.format({'Total Donated': '${:,.2f}'}),
        use_container_width=True
    )

    st.markdown("---")

    # Donation distribution
    st.subheader("📊 Donation Amount Distribution")
    fig4 = px.histogram(
        df,
        x='Amount',
        nbins=30,
        title='Distribution of Donation Amounts',
        labels={'Amount': 'Donation ($)', 'count': 'Frequency'}
    )
    st.plotly_chart(fig4, use_container_width=True)


# ══════════════════════════════════════════
# TAB 3 — TIMELINE
# ══════════════════════════════════════════
with tab3:
    st.subheader("📅 Donations Over Time")

    if df['Paid At'].notna().any():
        df['Month'] = df['Paid At'].dt.to_period('M').astype(str)
        monthly = df.groupby('Month')['Amount'].sum().reset_index()
        monthly.columns = ['Month', 'Total']

        fig5 = px.bar(
            monthly,
            x='Month',
            y='Total',
            title='💰 Total Raised Per Month',
            color='Total',
            color_continuous_scale='Blues'
        )
        fig5.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig5, use_container_width=True)

        # Donation count per month
        monthly_count = df.groupby('Month').size().reset_index(name='Count')
        fig6 = px.line(
            monthly_count,
            x='Month',
            y='Count',
            title='🔢 Number of Donations Per Month',
            markers=True
        )
        fig6.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig6, use_container_width=True)

        # Cumulative
        df_sorted = df.sort_values('Paid At')
        df_sorted['Cumulative'] = df_sorted['Amount'].cumsum()
        fig7 = px.area(
            df_sorted,
            x='Paid At',
            y='Cumulative',
            title='📈 Cumulative Fundraising Over Time',
            labels={'Cumulative': 'Total Raised ($)', 'Paid At': 'Date'}
        )
        st.plotly_chart(fig7, use_container_width=True)

    else:
        st.warning("No valid date data found.")


# ══════════════════════════════════════════
# TAB 4 — DONOR SCORING
# ══════════════════════════════════════════
with tab4:
    st.subheader("🎯 Donor Scoring & Prioritization")
    st.markdown("Uses **RFM Analysis** — Recency, Frequency, Monetary value")
    st.markdown("---")

    # ── SCORING SETTINGS ──
    st.markdown("### ⚙️ Scoring Weights")
    st.markdown("Adjust how much each factor influences the final score:")

    col_w1, col_w2, col_w3 = st.columns(3)
    recency_weight  = col_w1.slider("Recency Weight",  1, 5, 3)
    frequency_weight = col_w2.slider("Frequency Weight", 1, 5, 2)
    monetary_weight  = col_w3.slider("Monetary Weight",  1, 5, 5)

    st.markdown("---")

    # ── BUILD RFM TABLE ──
    df_scored = df.dropna(subset=['Full Name', 'Amount', 'Paid At'])
    today = pd.Timestamp(datetime.today().date())

    rfm = df_scored.groupby('Full Name').agg(
        Last_Donation=('Paid At', 'max'),
        Frequency=('Amount', 'count'),
        Total_Donated=('Amount', 'sum')
    ).reset_index()

    rfm['Recency_Days'] = (today - rfm['Last_Donation']).dt.days

    # ── SCORE EACH DIMENSION 1–5 ──
    def score_column(series, ascending=True):
        try:
            if ascending:
                return pd.qcut(
                    series, q=5,
                    labels=[5, 4, 3, 2, 1],
                    duplicates='drop'
                ).astype(float)
            else:
                return pd.qcut(
                    series, q=5,
                    labels=[1, 2, 3, 4, 5],
                    duplicates='drop'
                ).astype(float)
        except ValueError:
            return pd.cut(
                series, bins=5,
                labels=[1, 2, 3, 4, 5]
            ).astype(float)

    rfm['R_Score'] = score_column(rfm['Recency_Days'], ascending=True)
    rfm['F_Score'] = score_column(rfm['Frequency'],    ascending=False)
    rfm['M_Score'] = score_column(rfm['Total_Donated'],ascending=False)

    rfm[['R_Score', 'F_Score', 'M_Score']] = (
        rfm[['R_Score', 'F_Score', 'M_Score']].fillna(1)
    )

    # ── WEIGHTED FINAL SCORE (out of 100) ──
    total_weight = recency_weight + frequency_weight + monetary_weight
    rfm['Final_Score'] = (
        (rfm['R_Score'] * recency_weight) +
        (rfm['F_Score'] * frequency_weight) +
        (rfm['M_Score'] * monetary_weight)
    ) / (total_weight * 5) * 100
    rfm['Final_Score'] = rfm['Final_Score'].round(1)

    # ── DONOR TIERS ──
    def assign_tier(score):
        if score >= 80:
            return "🌟 Champion"
        elif score >= 60:
            return "💚 Loyal"
        elif score >= 40:
            return "🔄 Promising"
        elif score >= 20:
            return "⚠️ At Risk"
        else:
            return "❌ Lapsed"

    rfm['Tier'] = rfm['Final_Score'].apply(assign_tier)
    rfm = rfm.sort_values('Final_Score', ascending=False).reset_index(drop=True)
    rfm.index += 1

    # ── TIER METRICS ──
    st.markdown("### 📊 Tier Breakdown")

    col1, col2, col3, col4, col5 = st.columns(5)
    tier_cols = {
        "🌟 Champion": col1,
        "💚 Loyal":    col2,
        "🔄 Promising":col3,
        "⚠️ At Risk":  col4,
        "❌ Lapsed":   col5
    }
    for tier, col in tier_cols.items():
        count = rfm[rfm['Tier'] == tier].shape[0]
        col.metric(tier, count)

    st.markdown("---")

    # ── CHARTS ──
    col_a, col_b = st.columns(2)

    with col_a:
        tier_counts = rfm['Tier'].value_counts().reset_index()
        tier_counts.columns = ['Tier', 'Count']
        fig8 = px.pie(
            tier_counts,
            names='Tier',
            values='Count',
            title='Donor Distribution by Tier',
            color='Tier',
            color_discrete_map={
                "🌟 Champion": "#f1c40f",
                "💚 Loyal":    "#2ecc71",
                "🔄 Promising":"#3498db",
                "⚠️ At Risk":  "#e67e22",
                "❌ Lapsed":   "#e74c3c"
            }
        )
        st.plotly_chart(fig8, use_container_width=True)

    with col_b:
        fig9 = px.histogram(
            rfm,
            x='Final_Score',
            nbins=20,
            title='Distribution of Donor Scores',
            labels={'Final_Score': 'Score (0–100)', 'count': 'Donors'},
            color_discrete_sequence=['#3498db']
        )
        st.plotly_chart(fig9, use_container_width=True)

    st.markdown("---")

    # ── FULL SCORECARD TABLE ──
    st.markdown("### 🏆 Full Donor Scorecard")

    tier_filter = st.multiselect(
        "Filter by Tier",
        options=["🌟 Champion", "💚 Loyal", "🔄 Promising", "⚠️ At Risk", "❌ Lapsed"],
        default=["🌟 Champion", "💚 Loyal", "🔄 Promising", "⚠️ At Risk", "❌ Lapsed"]
    )

    display_df = rfm[rfm['Tier'].isin(tier_filter)][[
        'Full Name', 'Tier', 'Final_Score',
        'R_Score', 'F_Score', 'M_Score',
        'Recency_Days', 'Frequency', 'Total_Donated', 'Last_Donation'
    ]].rename(columns={
        'Full Name':      'Donor',
        'Final_Score':    'Score',
        'R_Score':        'Recency',
        'F_Score':        
