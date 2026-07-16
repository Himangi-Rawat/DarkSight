import pandas as pd
import numpy as np
import re
import os

# ── CONFIG ─────────────────────────────────────────────────────────────────
INPUT_FILES = {
    "Flipkart": "flipkart_raw.csv",
    "Amazon":   "amazon_raw.csv",
    "Myntra":   "myntra_raw.csv",
    "Ajio":     "ajio_raw.csv"
}
OUTPUT_PATH = "master_dataset.csv"
# ───────────────────────────────────────────────────────────────────────────


def clean_price(price_str):
    """Convert any price string to float. Returns NaN if unparseable."""
    if pd.isna(price_str) or str(price_str).strip() in ["N/A", "NaN", "", "nan"]:
        return np.nan
    price_str = str(price_str)
    # remove ₹, Rs., spaces, commas
    cleaned = re.sub(r'[₹Rs\.,\s]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return np.nan


def clean_discount(discount_str):
    """Extract discount percentage as integer. Returns NaN if unparseable."""
    if pd.isna(discount_str) or str(discount_str).strip() in ["N/A", "NaN", "", "nan"]:
        return np.nan
    match = re.search(r'(\d+)', str(discount_str))
    return int(match.group(1)) if match else np.nan


def calculate_discount(current, original):
    """Calculate actual discount % from prices."""
    try:
        if pd.isna(current) or pd.isna(original) or original == 0:
            return np.nan
        if original <= current:
            return np.nan
        return round(((original - current) / original) * 100, 1)
    except Exception:
        return np.nan


def flag_fake_discount(current, original, discount_pct):
    """Flag if claimed discount doesn't match actual price difference."""
    try:
        if pd.isna(current) or pd.isna(original) or pd.isna(discount_pct):
            return "Unknown"
        actual_discount = calculate_discount(current, original)
        if pd.isna(actual_discount):
            return "Unknown"
        # if claimed discount differs from actual by more than 5%, it's suspicious
        if abs(actual_discount - discount_pct) > 5:
            return "Yes"
        return "No"
    except Exception:
        return "Unknown"


def flag_suspicious_discount(discount_pct):
    """Flag discounts >= 70% as suspicious (common dark pattern)."""
    try:
        if pd.isna(discount_pct):
            return False
        return discount_pct >= 70
    except Exception:
        return False


def clean_urgency(urgency_str):
    """Standardize urgency text."""
    if pd.isna(urgency_str) or str(urgency_str).strip() in ["None", "NaN", "nan", ""]:
        return "None"
    return str(urgency_str).strip().title()


def clean_rating(rating_str):
    """Extract numeric rating."""
    if pd.isna(rating_str) or str(rating_str).strip() in ["N/A", "NaN", "", "nan"]:
        return np.nan
    match = re.search(r'[\d.]+', str(rating_str))
    if match:
        val = float(match.group())
        # Myntra sometimes shows review count instead of rating
        if val > 5:
            return np.nan
        return val
    return np.nan


def load_and_clean(platform, filepath):
    """Load one platform CSV and clean it."""
    print(f"  Loading {platform}...")

    if not os.path.exists(filepath):
        print(f"    ⚠️ File not found: {filepath} — skipping")
        return None

    df = pd.read_csv(filepath, encoding="utf-8-sig")
    print(f"    Raw rows: {len(df)}")

    # ── Standardize column names ───────────────────────────────────────────
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # ── Clean prices ───────────────────────────────────────────────────────
    df["current_price_clean"]  = df["current_price"].apply(clean_price)
    df["original_price_clean"] = df["original_price"].apply(clean_price)

    # ── Clean discount ─────────────────────────────────────────────────────
    df["discount_pct"] = df["discount"].apply(clean_discount)

    # Fill missing discounts by calculating from prices
    mask = df["discount_pct"].isna()
    df.loc[mask, "discount_pct"] = df[mask].apply(
        lambda r: calculate_discount(r["current_price_clean"], r["original_price_clean"]),
        axis=1
    )

    # ── Recalculate fake discount flag properly ────────────────────────────
    df["fake_discount_flag"] = df.apply(
        lambda r: flag_fake_discount(
            r["current_price_clean"],
            r["original_price_clean"],
            r["discount_pct"]
        ),
        axis=1
    )

    # ── Suspicious discount flag ───────────────────────────────────────────
    df["suspicious_discount_flag"] = df["discount_pct"].apply(flag_suspicious_discount)

    # ── Clean urgency ──────────────────────────────────────────────────────
    df["urgency_clean"] = df["urgency_text"].apply(clean_urgency)
    df["has_urgency"]   = df["urgency_clean"] != "None"

    # ── Clean rating ───────────────────────────────────────────────────────
    df["rating_clean"] = df["rating"].apply(clean_rating)

    # ── Clean product name ─────────────────────────────────────────────────
    df["product_name"] = df["product_name"].astype(str).str.strip()
    df["product_name"] = df["product_name"].replace(["nan", "N/A", ""], np.nan)

    # ── Add savings amount ─────────────────────────────────────────────────
    df["savings_amount"] = df["original_price_clean"] - df["current_price_clean"]
    df["savings_amount"] = df["savings_amount"].apply(lambda x: round(x, 2) if not pd.isna(x) else np.nan)

    # ── Select and rename final columns ───────────────────────────────────
    final_df = pd.DataFrame({
        "platform":             df["platform"],
        "query":                df["query"],
        "product_name":         df["product_name"],
        "current_price":        df["current_price_clean"],
        "original_price":       df["original_price_clean"],
        "discount_pct":         df["discount_pct"],
        "savings_amount":       df["savings_amount"],
        "rating":               df["rating_clean"],
        "urgency_text":         df["urgency_clean"],
        "has_urgency":          df["has_urgency"],
        "fake_discount_flag":   df["fake_discount_flag"],
        "suspicious_discount":  df["suspicious_discount_flag"],
        "product_url":          df["product_url"],
        "full_text":            df["full_text"]
    })

    # ── Drop rows with no price at all ────────────────────────────────────
    final_df = final_df.dropna(subset=["current_price"])

    print(f"    Clean rows: {len(final_df)}")
    return final_df


def main():
    print("🧹 Starting data cleaning...\n")
    all_dfs = []

    for platform, filepath in INPUT_FILES.items():
        df = load_and_clean(platform, filepath)
        if df is not None:
            all_dfs.append(df)

    if not all_dfs:
        print("❌ No data loaded.")
        return

    # ── Combine all platforms ──────────────────────────────────────────────
    master = pd.concat(all_dfs, ignore_index=True)

    # ── Remove duplicates across platforms ────────────────────────────────
    master.drop_duplicates(subset=["product_name", "current_price", "platform"], inplace=True)

    # ── Final summary ──────────────────────────────────────────────────────
    print(f"\n✅ Master dataset created!")
    print(f"   Total products : {len(master)}")
    print(f"   Platforms      : {master['platform'].value_counts().to_dict()}")
    print(f"   Queries        : {master['query'].nunique()} categories")
    print(f"   Avg discount   : {master['discount_pct'].mean():.1f}%")
    print(f"   Has urgency    : {master['has_urgency'].sum()} products")
    print(f"   Suspicious disc: {master['suspicious_discount'].sum()} products")
    print(f"   Fake discounts : {(master['fake_discount_flag']=='Yes').sum()} products")

    master.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n💾 Saved to {OUTPUT_PATH}")

    print("\n📊 Sample:")
    print(master[["platform", "product_name", "current_price", "original_price",
                  "discount_pct", "urgency_text", "fake_discount_flag"]].head(10).to_string())


if __name__ == "__main__":
    main()