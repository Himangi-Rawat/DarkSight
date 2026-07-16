import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# ── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dark Pattern Analytics",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #FF4B4B;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e, #2d2d44);
        border-radius: 12px;
        padding: 1.2rem;
        border-left: 4px solid #FF4B4B;
        margin-bottom: 1rem;
    }
    .winner-badge {
        background: #FF4B4B;
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #FF4B4B;
        border-bottom: 2px solid #FF4B4B;
        padding-bottom: 0.3rem;
        margin: 1.5rem 0 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    classified_path = os.path.join(base, "..", "scraper", "data", "classified_dataset.csv")
    scores_path     = os.path.join(base, "..", "scraper", "data", "manipulation_scores.csv")

    df     = pd.read_csv(classified_path, encoding="utf-8-sig")
    scores = pd.read_csv(scores_path,     encoding="utf-8-sig")
    return df, scores


try:
    df, scores = load_data()
except FileNotFoundError:
    st.error("❌ Dataset not found. Please run the scraper and classifier first.")
    st.stop()


# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/emoji/96/detective.png", width=80)
    st.title("🕵️ Dark Pattern\nAnalytics")
    st.markdown("---")

    st.markdown("### 🔽 Filters")
    selected_platforms = st.multiselect(
        "Platforms",
        options=df["platform"].unique().tolist(),
        default=df["platform"].unique().tolist()
    )

    selected_queries = st.multiselect(
        "Product Categories",
        options=df["query"].unique().tolist(),
        default=df["query"].unique().tolist()
    )

    show_only_dark = st.checkbox("Show only products with dark patterns", value=False)

    st.markdown("---")
    st.markdown("### 📊 Dataset Info")
    st.metric("Total Products", len(df))
    st.metric("Platforms", df["platform"].nunique())
    st.metric("Categories", df["query"].nunique())


# ── FILTER DATA ───────────────────────────────────────────────────────────────
filtered = df[
    (df["platform"].isin(selected_platforms)) &
    (df["query"].isin(selected_queries))
]
if show_only_dark:
    filtered = filtered[filtered["has_dark_pattern"] == True]


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">🕵️ Dark Pattern Detection & E-Commerce Manipulation Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Analysing manipulative UI/UX patterns across Flipkart, Amazon, Myntra & Ajio</div>', unsafe_allow_html=True)


# ── KPI METRICS ───────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("📦 Products Analysed", len(filtered))
with col2:
    dark_count = filtered["has_dark_pattern"].sum()
    dark_pct   = dark_count / len(filtered) * 100 if len(filtered) > 0 else 0
    st.metric("🚨 Dark Patterns Found", f"{dark_count} ({dark_pct:.1f}%)")
with col3:
    st.metric("⚡ Fake Urgency", filtered["dp_fake_urgency"].sum())
with col4:
    st.metric("💸 Extreme Discounts", filtered["dp_extreme_discount"].sum())
with col5:
    most_manipulative = scores.iloc[0]["platform"] if len(scores) > 0 else "N/A"
    st.metric("🏆 Most Manipulative", most_manipulative)


st.markdown("---")


# ── MANIPULATION INDEX ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🏆 Manipulation Index by Platform</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1.5, 1])

with col1:
    fig_mi = go.Figure()
    colors = ["#FF4B4B", "#FF8C00", "#FFD700", "#90EE90"]
    for i, row in scores.iterrows():
        fig_mi.add_trace(go.Bar(
            x=[row["manipulation_index"]],
            y=[row["platform"]],
            orientation="h",
            marker_color=colors[i % len(colors)],
            text=f"{row['manipulation_index']}",
            textposition="outside",
            name=row["platform"]
        ))
    fig_mi.update_layout(
        title="Manipulation Index (0-100) — Higher = More Manipulative",
        xaxis_title="Manipulation Index",
        xaxis=dict(range=[0, 50]),
        height=300,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_mi, use_container_width=True)

with col2:
    st.markdown("#### Platform Scorecard")
    for _, row in scores.iterrows():
        badge = "🔴" if row["manipulation_index"] > 30 else "🟡" if row["manipulation_index"] > 15 else "🟢"
        st.markdown(f"""
        **{badge} {row['platform']}**
        - Manipulation Index: **{row['manipulation_index']}**
        - Dark Pattern Rate: **{row['dark_pattern_rate']}%**
        - Products analysed: {row['total_products']}
        """)


st.markdown("---")


# ── PATTERN BREAKDOWN ─────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📋 Dark Pattern Breakdown</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    pattern_data = {
        "Fake Urgency":        filtered["dp_fake_urgency"].sum(),
        "Extreme Discount":    filtered["dp_extreme_discount"].sum(),
        "Misleading Price":    filtered["dp_misleading_price"].sum(),
        "Inflated Discount":   filtered["dp_inflated_discount"].sum(),
        "Bait Discount":       filtered["dp_bait_discount"].sum(),
        "Drip Pricing":        filtered["dp_drip_pricing"].sum(),
    }
    pattern_df = pd.DataFrame(list(pattern_data.items()), columns=["Pattern", "Count"])
    pattern_df = pattern_df[pattern_df["Count"] > 0].sort_values("Count", ascending=True)

    fig_bar = px.bar(
        pattern_df,
        x="Count",
        y="Pattern",
        orientation="h",
        color="Count",
        color_continuous_scale="Reds",
        title="Dark Pattern Frequency Across All Platforms"
    )
    fig_bar.update_layout(
        height=350,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    # Pattern prevalence by platform
    platform_pattern = filtered.groupby("platform").agg(
        fake_urgency    = ("dp_fake_urgency", "sum"),
        extreme_disc    = ("dp_extreme_discount", "sum"),
        misleading      = ("dp_misleading_price", "sum"),
        inflated        = ("dp_inflated_discount", "sum"),
        bait            = ("dp_bait_discount", "sum"),
    ).reset_index()

    fig_heat = go.Figure(data=go.Heatmap(
        z=platform_pattern[["fake_urgency","extreme_disc","misleading","inflated","bait"]].values,
        x=["Fake Urgency","Extreme Disc","Misleading Price","Inflated Disc","Bait Disc"],
        y=platform_pattern["platform"].tolist(),
        colorscale="Reds",
        text=platform_pattern[["fake_urgency","extreme_disc","misleading","inflated","bait"]].values,
        texttemplate="%{text}",
    ))
    fig_heat.update_layout(
        title="Dark Pattern Heatmap by Platform",
        height=350,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)


st.markdown("---")


# ── DISCOUNT ANALYSIS ─────────────────────────────────────────────────────────
st.markdown('<div class="section-title">💸 Discount Analysis</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fig_box = px.box(
        filtered.dropna(subset=["discount_pct"]),
        x="platform",
        y="discount_pct",
        color="platform",
        title="Discount Distribution by Platform",
        labels={"discount_pct": "Discount %", "platform": "Platform"},
        color_discrete_sequence=["#FF4B4B", "#FF8C00", "#FFD700", "#90EE90"]
    )
    fig_box.update_layout(
        height=350,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_box, use_container_width=True)

with col2:
    avg_disc = filtered.groupby("platform")["discount_pct"].mean().reset_index()
    avg_disc.columns = ["Platform", "Avg Discount %"]
    avg_disc = avg_disc.sort_values("Avg Discount %", ascending=False)

    fig_disc = px.bar(
        avg_disc,
        x="Platform",
        y="Avg Discount %",
        color="Avg Discount %",
        color_continuous_scale="Reds",
        title="Average Discount % by Platform",
        text=avg_disc["Avg Discount %"].round(1)
    )
    fig_disc.update_layout(
        height=350,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_disc, use_container_width=True)


st.markdown("---")


# ── URGENCY ANALYSIS ──────────────────────────────────────────────────────────
st.markdown('<div class="section-title">⚡ Urgency Tactics Analysis</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    urgency_df = filtered[filtered["has_urgency"] == True]
    urgency_counts = urgency_df.groupby("platform").size().reset_index(name="Urgency Count")
    total_counts   = filtered.groupby("platform").size().reset_index(name="Total")
    urgency_merged = urgency_counts.merge(total_counts, on="platform")
    urgency_merged["Urgency Rate %"] = (urgency_merged["Urgency Count"] / urgency_merged["Total"] * 100).round(1)

    fig_urg = px.bar(
        urgency_merged,
        x="platform",
        y="Urgency Rate %",
        color="platform",
        title="% of Products Using Urgency Tactics",
        text="Urgency Rate %",
        color_discrete_sequence=["#FF4B4B", "#FF8C00", "#FFD700", "#90EE90"]
    )
    fig_urg.update_layout(
        height=320,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_urg, use_container_width=True)

with col2:
    urgency_types = filtered[filtered["urgency_text"] != "None"]["urgency_text"].value_counts().head(10).reset_index()
    urgency_types.columns = ["Urgency Text", "Count"]

    fig_ut = px.bar(
        urgency_types,
        x="Count",
        y="Urgency Text",
        orientation="h",
        color="Count",
        color_continuous_scale="Oranges",
        title="Most Common Urgency Phrases"
    )
    fig_ut.update_layout(
        height=320,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_ut, use_container_width=True)


st.markdown("---")


# ── CATEGORY ANALYSIS ─────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🛍️ Dark Patterns by Product Category</div>', unsafe_allow_html=True)

cat_dark = filtered.groupby("query").agg(
    total        = ("has_dark_pattern", "count"),
    dark_count   = ("has_dark_pattern", "sum"),
    avg_discount = ("discount_pct", "mean")
).reset_index()
cat_dark["dark_rate"] = (cat_dark["dark_count"] / cat_dark["total"] * 100).round(1)
cat_dark = cat_dark.sort_values("dark_rate", ascending=False)

fig_cat = px.bar(
    cat_dark,
    x="query",
    y="dark_rate",
    color="avg_discount",
    color_continuous_scale="Reds",
    title="Dark Pattern Rate % by Product Category",
    labels={"query": "Category", "dark_rate": "Dark Pattern Rate %"},
    text=cat_dark["dark_rate"].astype(str) + "%"
)
fig_cat.update_layout(
    height=350,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)
st.plotly_chart(fig_cat, use_container_width=True)


st.markdown("---")


# ── PRODUCT EXPLORER ──────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🔎 Product-Level Dark Pattern Explorer</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    platform_filter = st.selectbox("Platform", ["All"] + df["platform"].unique().tolist())
with col2:
    pattern_filter = st.selectbox("Dark Pattern Type", [
        "All", "Fake Urgency", "Extreme Discount", "Misleading Price",
        "Inflated Discount", "Bait Discount"
    ])
with col3:
    query_filter = st.selectbox("Category", ["All"] + df["query"].unique().tolist())

explorer_df = filtered.copy()
if platform_filter != "All":
    explorer_df = explorer_df[explorer_df["platform"] == platform_filter]
if query_filter != "All":
    explorer_df = explorer_df[explorer_df["query"] == query_filter]
if pattern_filter != "All":
    col_map = {
        "Fake Urgency":       "dp_fake_urgency",
        "Extreme Discount":   "dp_extreme_discount",
        "Misleading Price":   "dp_misleading_price",
        "Inflated Discount":  "dp_inflated_discount",
        "Bait Discount":      "dp_bait_discount"
    }
    explorer_df = explorer_df[explorer_df[col_map[pattern_filter]] == True]

display_cols = ["platform", "product_name", "current_price", "original_price",
                "discount_pct", "urgency_text", "patterns_detected"]
st.dataframe(
    explorer_df[display_cols].head(100).reset_index(drop=True),
    use_container_width=True,
    height=400
)

st.markdown(f"*Showing {min(100, len(explorer_df))} of {len(explorer_df)} products*")


st.markdown("---")


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; color:#666; padding:1rem;'>
    🕵️ Dark Pattern Detection & E-Commerce Manipulation Analytics<br>
    Built with Python • Selenium • Pandas • Streamlit • Plotly<br>
    Data scraped from Flipkart, Amazon India, Myntra & Ajio
</div>
""", unsafe_allow_html=True)