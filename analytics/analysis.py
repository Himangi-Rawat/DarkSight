import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os
import warnings
warnings.filterwarnings("ignore")

# ── CONFIG ───────────────────────────────────────────────────────────────────
INPUT_PATH  = "scraper/data/classified_dataset.csv"
SCORES_PATH = "scraper/data/manipulation_scores.csv"
OUTPUT_DIR  = "analytics/charts"
# ─────────────────────────────────────────────────────────────────────────────

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── STYLE ────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor":  "#0e0e1a",
    "axes.facecolor":    "#0e0e1a",
    "axes.edgecolor":    "#444",
    "axes.labelcolor":   "white",
    "xtick.color":       "white",
    "ytick.color":       "white",
    "text.color":        "white",
    "grid.color":        "#333",
    "grid.linestyle":    "--",
    "grid.alpha":        0.5,
    "font.family":       "DejaVu Sans"
})

PLATFORM_COLORS = {
    "Amazon":   "#FF4B4B",
    "Flipkart": "#FF8C00",
    "Myntra":   "#FFD700",
    "Ajio":     "#90EE90"
}


def save(fig, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight",
                facecolor="#0e0e1a", edgecolor="none")
    plt.close(fig)
    print(f"  ✅ Saved: {path}")


def load_data():
    df     = pd.read_csv(INPUT_PATH,  encoding="utf-8-sig")
    scores = pd.read_csv(SCORES_PATH, encoding="utf-8-sig")
    return df, scores


# ── CHART 1 — Manipulation Index Leaderboard ──────────────────────────────────
def chart_manipulation_index(scores):
    print("\n📊 Chart 1: Manipulation Index Leaderboard")
    fig, ax = plt.subplots(figsize=(10, 5))

    platforms = scores["platform"].tolist()
    values    = scores["manipulation_index"].tolist()
    colors    = [PLATFORM_COLORS.get(p, "#888") for p in platforms]

    bars = ax.barh(platforms, values, color=colors, height=0.5, edgecolor="none")

    for bar, val in zip(bars, values):
        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2,
                f"{val}", va="center", fontsize=13, fontweight="bold", color="white")

    ax.set_xlabel("Manipulation Index (0–100)", fontsize=12)
    ax.set_title("DarkSight — Manipulation Index by Platform\n"
                 "Higher score = More manipulative",
                 fontsize=14, fontweight="bold", pad=15)
    ax.axvline(x=25, color="#FF4B4B", linestyle="--", alpha=0.5, label="High risk threshold")
    ax.legend(fontsize=10)
    ax.set_xlim(0, 50)
    ax.grid(axis="x")

    save(fig, "01_manipulation_index.png")


# ── CHART 2 — Dark Pattern Rate by Platform ───────────────────────────────────
def chart_dark_pattern_rate(scores):
    print("📊 Chart 2: Dark Pattern Rate by Platform")
    fig, ax = plt.subplots(figsize=(9, 5))

    platforms = scores["platform"].tolist()
    rates     = scores["dark_pattern_rate"].tolist()
    colors    = [PLATFORM_COLORS.get(p, "#888") for p in platforms]

    bars = ax.bar(platforms, rates, color=colors, width=0.5, edgecolor="none")
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{rate}%", ha="center", fontsize=13, fontweight="bold", color="white")

    ax.set_ylabel("Products with Dark Patterns (%)", fontsize=12)
    ax.set_title("DarkSight — % of Products Containing Dark Patterns",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_ylim(0, 110)
    ax.axhline(y=50, color="#FFD700", linestyle="--", alpha=0.6, label="50% reference line")
    ax.legend(fontsize=10)
    ax.grid(axis="y")

    save(fig, "02_dark_pattern_rate.png")


# ── CHART 3 — Pattern Type Breakdown ──────────────────────────────────────────
def chart_pattern_breakdown(df):
    print("📊 Chart 3: Pattern Type Breakdown")

    pattern_cols = {
        "dp_fake_urgency":      "Fake Urgency",
        "dp_extreme_discount":  "Extreme Discount",
        "dp_misleading_price":  "Misleading Price",
        "dp_inflated_discount": "Inflated Discount",
        "dp_bait_discount":     "Bait Discount",
        "dp_drip_pricing":      "Drip Pricing"
    }

    counts = {name: df[col].sum() for col, name in pattern_cols.items()}
    counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    fig, ax = plt.subplots(figsize=(10, 5))
    colors  = ["#FF4B4B", "#FF6B35", "#FF8C00", "#FFB347", "#FFD700", "#90EE90"]

    bars = ax.barh(list(counts.keys()), list(counts.values()),
                   color=colors, height=0.5, edgecolor="none")

    for bar, val in zip(bars, counts.values()):
        pct = val / len(df) * 100
        ax.text(val + 2, bar.get_y() + bar.get_height()/2,
                f"{val} ({pct:.1f}%)", va="center", fontsize=11, color="white")

    ax.set_xlabel("Number of Products", fontsize=12)
    ax.set_title("DarkSight — Dark Pattern Type Frequency\n"
                 f"Across {len(df):,} Products on 4 Platforms",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlim(0, max(counts.values()) * 1.3)
    ax.grid(axis="x")

    save(fig, "03_pattern_breakdown.png")


# ── CHART 4 — Heatmap: Pattern × Platform ────────────────────────────────────
def chart_heatmap(df):
    print("📊 Chart 4: Pattern × Platform Heatmap")

    pattern_cols = {
        "dp_fake_urgency":      "Fake Urgency",
        "dp_extreme_discount":  "Extreme Disc",
        "dp_misleading_price":  "Misleading Price",
        "dp_inflated_discount": "Inflated Disc",
        "dp_bait_discount":     "Bait Discount",
    }

    heat_data = []
    for col, name in pattern_cols.items():
        row = {"Pattern": name}
        for platform in df["platform"].unique():
            pf = df[df["platform"] == platform]
            row[platform] = round(pf[col].sum() / len(pf) * 100, 1)
        heat_data.append(row)

    heat_df = pd.DataFrame(heat_data).set_index("Pattern")

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(
        heat_df,
        annot=True,
        fmt=".1f",
        cmap="Reds",
        linewidths=0.5,
        linecolor="#222",
        ax=ax,
        cbar_kws={"label": "% of Products"}
    )
    ax.set_title("DarkSight — Dark Pattern Prevalence (%) by Platform",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("")
    ax.set_ylabel("")

    save(fig, "04_heatmap_pattern_platform.png")


# ── CHART 5 — Discount Distribution ──────────────────────────────────────────
def chart_discount_distribution(df):
    print("📊 Chart 5: Discount Distribution by Platform")
    fig, ax = plt.subplots(figsize=(11, 5))

    for platform, color in PLATFORM_COLORS.items():
        data = df[df["platform"] == platform]["discount_pct"].dropna()
        if len(data) == 0:
            continue
        sns.kdeplot(data, ax=ax, label=platform, color=color,
                    linewidth=2.5, fill=True, alpha=0.15)

    ax.axvline(x=70, color="#FF4B4B", linestyle="--",
               linewidth=1.5, label="70% suspicious threshold")
    ax.set_xlabel("Discount %", fontsize=12)
    ax.set_ylabel("Density", fontsize=12)
    ax.set_title("DarkSight — Discount Distribution by Platform\n"
                 "Spike near 70%+ indicates inflated original prices",
                 fontsize=14, fontweight="bold", pad=15)
    ax.legend(fontsize=10)
    ax.set_xlim(0, 110)
    ax.grid()

    save(fig, "05_discount_distribution.png")


# ── CHART 6 — Urgency Tactics by Platform ────────────────────────────────────
def chart_urgency(df):
    print("📊 Chart 6: Urgency Tactics by Platform")

    urgency_rates = df.groupby("platform").apply(
        lambda x: round(x["has_urgency"].sum() / len(x) * 100, 1)
    ).reset_index()
    urgency_rates.columns = ["platform", "urgency_rate"]
    urgency_rates = urgency_rates.sort_values("urgency_rate", ascending=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [PLATFORM_COLORS.get(p, "#888") for p in urgency_rates["platform"]]
    bars   = ax.bar(urgency_rates["platform"], urgency_rates["urgency_rate"],
                    color=colors, width=0.5, edgecolor="none")

    for bar, val in zip(bars, urgency_rates["urgency_rate"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f"{val}%", ha="center", fontsize=13, fontweight="bold", color="white")

    ax.set_ylabel("Products Using Urgency Tactics (%)", fontsize=12)
    ax.set_title("DarkSight — Fake Urgency Tactic Usage by Platform",
                 fontsize=14, fontweight="bold", pad=15)
    ax.set_ylim(0, max(urgency_rates["urgency_rate"]) * 1.25)
    ax.grid(axis="y")

    save(fig, "06_urgency_by_platform.png")


# ── CHART 7 — Category Analysis ───────────────────────────────────────────────
def chart_category_analysis(df):
    print("📊 Chart 7: Dark Pattern Rate by Category")

    cat = df.groupby("query").agg(
        total      = ("has_dark_pattern", "count"),
        dark_count = ("has_dark_pattern", "sum"),
        avg_disc   = ("discount_pct", "mean")
    ).reset_index()
    cat["dark_rate"] = (cat["dark_count"] / cat["total"] * 100).round(1)
    cat = cat.sort_values("dark_rate", ascending=False)

    fig, ax1 = plt.subplots(figsize=(12, 5))

    bars = ax1.bar(cat["query"], cat["dark_rate"],
                   color="#FF4B4B", alpha=0.8, width=0.5, label="Dark Pattern Rate %")
    ax1.set_ylabel("Dark Pattern Rate (%)", fontsize=12, color="#FF4B4B")
    ax1.set_ylim(0, 110)

    ax2 = ax1.twinx()
    ax2.plot(cat["query"], cat["avg_disc"], color="#FFD700",
             marker="o", linewidth=2.5, markersize=8, label="Avg Discount %")
    ax2.set_ylabel("Average Discount (%)", fontsize=12, color="#FFD700")

    for bar, val in zip(bars, cat["dark_rate"]):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f"{val}%", ha="center", fontsize=10, color="white")

    ax1.set_title("DarkSight — Dark Pattern Rate & Avg Discount by Product Category",
                  fontsize=14, fontweight="bold", pad=15)
    ax1.set_xlabel("Product Category", fontsize=12)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=10, loc="upper right")
    ax1.grid(axis="y", alpha=0.3)

    plt.xticks(rotation=20, ha="right")
    save(fig, "07_category_analysis.png")


# ── CHART 8 — Top 10 Most Manipulative Products ───────────────────────────────
def chart_top_manipulative(df):
    print("📊 Chart 8: Top 10 Most Manipulative Products")

    df["dp_score"] = (
        df["dp_fake_urgency"].astype(int) * 25 +
        df["dp_extreme_discount"].astype(int) * 20 +
        df["dp_inflated_discount"].astype(int) * 20 +
        df["dp_misleading_price"].astype(int) * 15 +
        df["dp_bait_discount"].astype(int) * 10 +
        df["dp_drip_pricing"].astype(int) * 10
    )

    top10 = df.nlargest(10, "dp_score")[
        ["platform", "product_name", "current_price",
         "discount_pct", "dp_score", "patterns_detected"]
    ].reset_index(drop=True)

    print("\n🚨 Top 10 Most Manipulative Products:")
    print(top10[["platform", "product_name", "discount_pct",
                 "dp_score", "patterns_detected"]].to_string(index=False))

    fig, ax = plt.subplots(figsize=(12, 6))
    colors  = [PLATFORM_COLORS.get(p, "#888") for p in top10["platform"]]

    names = [f"{row['platform']}: {str(row['product_name'])[:30]}..."
             for _, row in top10.iterrows()]

    bars = ax.barh(names[::-1], top10["dp_score"][::-1].tolist(),
                   color=colors[::-1], height=0.6, edgecolor="none")

    for bar, val in zip(bars, top10["dp_score"][::-1].tolist()):
        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2,
                f"{val} pts", va="center", fontsize=10, color="white")

    ax.set_xlabel("Manipulation Score (pts)", fontsize=12)
    ax.set_title("DarkSight — Top 10 Most Manipulative Products\n"
                 "Scored by weighted dark pattern presence",
                 fontsize=14, fontweight="bold", pad=15)

    patches = [mpatches.Patch(color=c, label=p)
               for p, c in PLATFORM_COLORS.items()]
    ax.legend(handles=patches, fontsize=10, loc="lower right")
    ax.grid(axis="x", alpha=0.3)

    save(fig, "08_top10_manipulative.png")
    return top10


# ── CHART 9 — Price vs Discount Scatter ───────────────────────────────────────
def chart_price_discount_scatter(df):
    print("📊 Chart 9: Price vs Discount Scatter")

    sample = df.dropna(subset=["current_price", "discount_pct"]).sample(
        min(500, len(df)), random_state=42
    )

    fig, ax = plt.subplots(figsize=(11, 6))

    for platform, color in PLATFORM_COLORS.items():
        pf = sample[sample["platform"] == platform]
        ax.scatter(pf["current_price"], pf["discount_pct"],
                   c=color, alpha=0.6, s=40, label=platform, edgecolors="none")

    ax.axhline(y=70, color="#FF4B4B", linestyle="--",
               linewidth=1.5, label="70% suspicious threshold")
    ax.set_xlabel("Current Price (₹)", fontsize=12)
    ax.set_ylabel("Discount %", fontsize=12)
    ax.set_title("DarkSight — Price vs Discount Scatter\n"
                 "Products above red line have suspiciously high discounts",
                 fontsize=14, fontweight="bold", pad=15)
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    save(fig, "09_price_discount_scatter.png")


# ── SUMMARY STATS ─────────────────────────────────────────────────────────────
def print_summary(df, scores):
    print("\n" + "="*65)
    print("  DARKSIGHT — ANALYTICAL SUMMARY")
    print("="*65)
    print(f"\n  Total products analysed   : {len(df):,}")
    print(f"  Platforms covered         : {df['platform'].nunique()}")
    print(f"  Product categories        : {df['query'].nunique()}")
    print(f"\n  Dark pattern findings:")
    print(f"  → Products with dark patterns : {df['has_dark_pattern'].sum():,} ({df['has_dark_pattern'].mean()*100:.1f}%)")
    print(f"  → Avg discount across all     : {df['discount_pct'].mean():.1f}%")
    print(f"  → Products with fake urgency  : {df['dp_fake_urgency'].sum():,}")
    print(f"  → Extreme discounts (70%+)    : {df['dp_extreme_discount'].sum():,}")
    print(f"  → Misleading prices           : {df['dp_misleading_price'].sum():,}")
    print(f"\n  Manipulation Index rankings:")
    for _, row in scores.iterrows():
        bar = "█" * int(row["manipulation_index"] / 2)
        print(f"  {row['platform']:<10} {bar:<25} {row['manipulation_index']}")
    print("\n" + "="*65)


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("🚀 DarkSight Analytics Engine Starting...\n")

    df, scores = load_data()
    print(f"✅ Loaded {len(df):,} products\n")

    print_summary(df, scores)

    print("\n🎨 Generating charts...\n")
    chart_manipulation_index(scores)
    chart_dark_pattern_rate(scores)
    chart_pattern_breakdown(df)
    chart_heatmap(df)
    chart_discount_distribution(df)
    chart_urgency(df)
    chart_category_analysis(df)
    top10 = chart_top_manipulative(df)
    chart_price_discount_scatter(df)

    print(f"\n🎉 All charts saved to {OUTPUT_DIR}/")
    print("   Use these in your README, report, and presentation!\n")


if __name__ == "__main__":
    main()