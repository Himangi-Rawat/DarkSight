import pandas as pd
import numpy as np
import re
import os

INPUT_PATH  = "scraper/data/master_dataset.csv"
OUTPUT_PATH = "scraper/data/classified_dataset.csv"


# ── DARK PATTERN TAXONOMY ───────────────────────────────────────────────────
# Based on real academic research (Princeton, FTC, CCPA India 2023)
# 6 pattern types we detect:
#
# 1. FAKE_URGENCY      — false scarcity/time pressure
# 2. INFLATED_DISCOUNT — original price artificially inflated
# 3. MISLEADING_PRICE  — current price > original price
# 4. BAIT_DISCOUNT     — discount claimed but negligible (< 5%)
# 5. SPONSORED_BLUR    — sponsored product mixed with organic (Amazon)
# 6. EXTREME_DISCOUNT  — 70%+ discount (almost always fake MRP)
# ────────────────────────────────────────────────────────────────────────────


def detect_fake_urgency(row):
    """Detect false scarcity or time pressure tactics."""
    urgency = str(row.get("urgency_text", "None")).lower()
    fake_urgency_phrases = [
        "only few left", "only 1 left", "only 2 left", "only 3 left",
        "only 4 left", "only 5 left", "limited stock", "selling fast",
        "hurry", "deal ends", "offer ends", "limited time",
        "today only", "expires soon", "lightning deal"
    ]
    for phrase in fake_urgency_phrases:
        if phrase in urgency:
            return True
    return False


def detect_inflated_discount(row):
    """
    Detect inflated original price — when claimed discount
    is significantly higher than what the price difference suggests.
    """
    try:
        current  = float(row["current_price"])
        original = float(row["original_price"])
        claimed  = float(row["discount_pct"])

        if original <= 0 or current <= 0:
            return False

        actual_discount = ((original - current) / original) * 100

        # if claimed discount is 10+ points higher than actual → inflated
        if claimed - actual_discount > 10:
            return True

        return False
    except Exception:
        return False


def detect_misleading_price(row):
    """Detect when current price is higher than or equal to original price."""
    try:
        current  = float(row["current_price"])
        original = float(row["original_price"])
        if current >= original and original > 0:
            return True
        return False
    except Exception:
        return False


def detect_bait_discount(row):
    """
    Detect bait discounts — discount is claimed but is negligible (< 5%).
    Creates illusion of a deal.
    """
    try:
        discount = float(row["discount_pct"])
        if 0 < discount < 5:
            return True
        return False
    except Exception:
        return False


def detect_extreme_discount(row):
    """
    Detect extreme discounts (70%+) — almost always means
    MRP was artificially inflated to show a big discount.
    """
    try:
        discount = float(row["discount_pct"])
        return discount >= 70
    except Exception:
        return False


def detect_drip_pricing(row):
    """
    Detect drip pricing signals in full text —
    hidden charges revealed only at checkout.
    """
    full_text = str(row.get("full_text", "")).lower()
    drip_phrases = [
        "extra charges", "additional fee", "convenience fee",
        "handling charges", "packaging charges", "gst extra",
        "taxes extra", "exclusive of tax", "+ tax",
        "delivery charges apply", "installation charges"
    ]
    for phrase in drip_phrases:
        if phrase in full_text:
            return True
    return False


def classify_patterns(df):
    """Apply all dark pattern detectors to the dataset."""
    print("🔍 Classifying dark patterns...")

    df["dp_fake_urgency"]       = df.apply(detect_fake_urgency, axis=1)
    df["dp_inflated_discount"]  = df.apply(detect_inflated_discount, axis=1)
    df["dp_misleading_price"]   = df.apply(detect_misleading_price, axis=1)
    df["dp_bait_discount"]      = df.apply(detect_bait_discount, axis=1)
    df["dp_extreme_discount"]   = df.apply(detect_extreme_discount, axis=1)
    df["dp_drip_pricing"]       = df.apply(detect_drip_pricing, axis=1)

    # ── Count total dark patterns per product ──────────────────────────────
    dp_cols = [
        "dp_fake_urgency", "dp_inflated_discount", "dp_misleading_price",
        "dp_bait_discount", "dp_extreme_discount", "dp_drip_pricing"
    ]
    df["dark_pattern_count"] = df[dp_cols].sum(axis=1)
    df["has_dark_pattern"]   = df["dark_pattern_count"] > 0

    # ── List which patterns are present per product ────────────────────────
    def list_patterns(row):
        patterns = []
        if row["dp_fake_urgency"]:       patterns.append("Fake Urgency")
        if row["dp_inflated_discount"]:  patterns.append("Inflated Discount")
        if row["dp_misleading_price"]:   patterns.append("Misleading Price")
        if row["dp_bait_discount"]:      patterns.append("Bait Discount")
        if row["dp_extreme_discount"]:   patterns.append("Extreme Discount")
        if row["dp_drip_pricing"]:       patterns.append("Drip Pricing")
        return ", ".join(patterns) if patterns else "None"

    df["patterns_detected"] = df.apply(list_patterns, axis=1)

    return df


def compute_manipulation_index(df):
    """
    Compute Manipulation Index per platform (0-100).
    This is our custom original metric — key for the resume.

    Formula:
    MI = (weighted sum of dark pattern flags) / max_possible * 100

    Weights based on severity:
    - Fake Urgency       : 25 pts (psychological pressure)
    - Extreme Discount   : 20 pts (most common misleading tactic)
    - Inflated Discount  : 20 pts (price manipulation)
    - Misleading Price   : 15 pts (direct deception)
    - Bait Discount      : 10 pts (minor but deceptive)
    - Drip Pricing       : 10 pts (hidden costs)
    """
    print("\n📊 Computing Manipulation Index per platform...")

    weights = {
        "dp_fake_urgency":      25,
        "dp_extreme_discount":  20,
        "dp_inflated_discount": 20,
        "dp_misleading_price":  15,
        "dp_bait_discount":     10,
        "dp_drip_pricing":      10
    }
    max_score = sum(weights.values())  # 100

    platform_scores = []
    for platform in df["platform"].unique():
        pf = df[df["platform"] == platform]
        total_products = len(pf)

        weighted_score = 0
        for col, weight in weights.items():
            prevalence = pf[col].sum() / total_products  # 0 to 1
            weighted_score += prevalence * weight

        manipulation_index = round((weighted_score / max_score) * 100, 1)

        platform_scores.append({
            "platform":             platform,
            "total_products":       total_products,
            "fake_urgency_count":   pf["dp_fake_urgency"].sum(),
            "extreme_disc_count":   pf["dp_extreme_discount"].sum(),
            "inflated_disc_count":  pf["dp_inflated_discount"].sum(),
            "misleading_price_count": pf["dp_misleading_price"].sum(),
            "bait_discount_count":  pf["dp_bait_discount"].sum(),
            "drip_pricing_count":   pf["dp_drip_pricing"].sum(),
            "total_dark_patterns":  pf["has_dark_pattern"].sum(),
            "dark_pattern_rate":    round(pf["has_dark_pattern"].mean() * 100, 1),
            "manipulation_index":   manipulation_index
        })

    scores_df = pd.DataFrame(platform_scores).sort_values(
        "manipulation_index", ascending=False
    ).reset_index(drop=True)

    return scores_df


def main():
    print("🚀 Dark Pattern Classification Starting...\n")

    if not os.path.exists(INPUT_PATH):
        print(f"❌ Master dataset not found at {INPUT_PATH}")
        print("   Run clean_data.py first.")
        return

    df = pd.read_csv(INPUT_PATH, encoding="utf-8-sig")
    print(f"✅ Loaded {len(df)} products from master dataset\n")

    # ── Classify ───────────────────────────────────────────────────────────
    df = classify_patterns(df)

    # ── Manipulation Index ─────────────────────────────────────────────────
    scores_df = compute_manipulation_index(df)

    # ── Print results ──────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("DARK PATTERN CLASSIFICATION RESULTS")
    print("="*60)

    dp_cols = [
        "dp_fake_urgency", "dp_inflated_discount", "dp_misleading_price",
        "dp_bait_discount", "dp_extreme_discount", "dp_drip_pricing"
    ]

    print(f"\n📦 Total products analysed : {len(df)}")
    print(f"🚨 Products with dark patterns : {df['has_dark_pattern'].sum()} ({df['has_dark_pattern'].mean()*100:.1f}%)")
    print(f"\n📋 Pattern breakdown:")
    pattern_names = {
        "dp_fake_urgency":      "Fake Urgency",
        "dp_inflated_discount": "Inflated Discount",
        "dp_misleading_price":  "Misleading Price",
        "dp_bait_discount":     "Bait Discount",
        "dp_extreme_discount":  "Extreme Discount (70%+)",
        "dp_drip_pricing":      "Drip Pricing"
    }
    for col, name in pattern_names.items():
        count = df[col].sum()
        pct   = count / len(df) * 100
        print(f"   {name:<30} : {count:>4} products ({pct:.1f}%)")

    print(f"\n🏆 Manipulation Index by Platform:")
    print(scores_df[["platform", "total_products", "dark_pattern_rate",
                      "manipulation_index"]].to_string(index=False))

    # ── Save outputs ───────────────────────────────────────────────────────
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    scores_df.to_csv("scraper/data/manipulation_scores.csv", index=False, encoding="utf-8-sig")

    print(f"\n💾 Classified dataset saved to {OUTPUT_PATH}")
    print(f"💾 Manipulation scores saved to scraper/data/manipulation_scores.csv")


if __name__ == "__main__":
    main()