from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
import os

SEARCH_QUERIES = ["smartphones", "laptops", "headphones", "shoes", "watches"]
PAGES_PER_QUERY = 3
OUTPUT_PATH = "data/flipkart_raw.csv"


def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9222")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.set_page_load_timeout(30)
    return driver


def parse_from_text(full_text):
    """
    Extract price, original price, discount cleanly from full card text.
    Flipkart text pattern: ... ₹12,692 ₹15,499 18% off ...
    """
    # find all prices like ₹12,692
    prices = re.findall(r'₹([\d,]+)', full_text)
    prices_clean = [p.replace(',', '') for p in prices]

    # find discount like "18% off"
    discount_match = re.search(r'\b(\d{1,3})%\s*off\b', full_text, re.IGNORECASE)
    discount = f"{discount_match.group(1)}% off" if discount_match else "N/A"

    current_price = f"₹{prices[0]}" if len(prices) >= 1 else "N/A"
    original_price = f"₹{prices[1]}" if len(prices) >= 2 else "N/A"

    # detect fake discount: discount claimed but prices are same
    fake_discount = "N/A"
    if discount != "N/A" and len(prices_clean) >= 2:
        fake_discount = "Yes" if prices_clean[0] == prices_clean[1] else "No"
    elif discount == "N/A":
        fake_discount = "N/A"
    else:
        fake_discount = "No"

    return current_price, original_price, discount, fake_discount


def parse_urgency(full_text):
    patterns = [
        r'only\s+\d+\s+left',
        r'only few left',
        r'hurry',
        r'selling fast',
        r'limited stock',
        r'deal ends',
        r'offer ends',
        r'today only',
        r'expires soon',
        r'lowest price'
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return "None"


def parse_name(full_text):
    # remove common prefixes
    text = re.sub(r'^(Add to Compare|Currently unavailable|Coming Soon)\s*', '', full_text, flags=re.IGNORECASE).strip()
    # split at rating pattern like "4.2" or price like ₹
    parts = re.split(r'\b[1-5]\.\d\b|₹|\d+\s*(GB RAM|GB ROM|inch|mAh|Ratings)', text)
    name = parts[0].strip() if parts else "N/A"
    # clean up trailing punctuation/spaces
    name = re.sub(r'[\s,.\-]+$', '', name).strip()
    return name[:120] if name else "N/A"


def parse_rating(full_text):
    match = re.search(r'\b([1-5]\.[0-9])\b', full_text)
    return match.group(1) if match else "N/A"


def scrape_page(driver, query, page):
    url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}&page={page}"
    print(f"  Scraping: {url}")

    try:
        driver.get(url)
    except Exception:
        print("    ⚠️ Timeout, retrying...")
        time.sleep(3)
        try:
            driver.get(url)
        except Exception:
            return []

    time.sleep(random.uniform(3, 5))
    soup = BeautifulSoup(driver.page_source, "html.parser")

    cards = (
        soup.find_all("div", class_="cPHDOP") or
        soup.find_all("div", class_="_1AtVbE") or
        soup.find_all("div", class_="tUxRFH") or
        soup.find_all("div", class_="_2kHMtA") or
        soup.find_all("div", {"data-id": True})
    )

    print(f"    Cards found: {len(cards)}")
    products = []

    for card in cards:
        try:
            full_text = card.get_text(separator=" ", strip=True)
            if len(full_text) < 30:
                continue

            link_tag = card.find("a", href=True)
            product_url = "https://www.flipkart.com" + link_tag["href"] if link_tag else "N/A"

            name                                          = parse_name(full_text)
            current_price, original_price, discount, fake_discount = parse_from_text(full_text)
            urgency                                       = parse_urgency(full_text)
            rating                                        = parse_rating(full_text)

            # detect dark patterns
            has_urgency     = urgency != "None"
            high_discount   = False
            if discount != "N/A":
                d = int(re.search(r'\d+', discount).group())
                high_discount = d >= 70  # 70%+ discount is suspicious on Flipkart

            products.append({
                "platform":       "Flipkart",
                "query":          query,
                "page":           page,
                "product_name":   name,
                "current_price":  current_price,
                "original_price": original_price,
                "discount":       discount,
                "fake_discount":  fake_discount,
                "rating":         rating,
                "urgency_text":   urgency,
                "has_urgency":    has_urgency,
                "suspicious_discount": high_discount,
                "full_text":      full_text[:400],
                "product_url":    product_url
            })

        except Exception:
            continue

    return products


def main():
    os.makedirs("data", exist_ok=True)
    all_products = []

    for query in SEARCH_QUERIES:
        print(f"\n🔍 Query: '{query}'")
        for page in range(1, PAGES_PER_QUERY + 1):
            driver = init_driver()
            try:
                products = scrape_page(driver, query, page)
                all_products.extend(products)
                print(f"     ✅ Page {page} — {len(products)} products scraped")
            except Exception as e:
                print(f"     ❌ Page {page} error: {e}")
            finally:
                driver.quit()
            time.sleep(random.uniform(2, 4))

    if all_products:
        df = pd.DataFrame(all_products)
        df.drop_duplicates(subset=["product_name", "current_price"], inplace=True)
        df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
        print(f"\n🎉 Done! {len(df)} products saved to {OUTPUT_PATH}")
        print(df[["product_name", "current_price", "original_price", "discount", "urgency_text"]].head(10))
    else:
        print("\n❌ No products scraped.")


if __name__ == "__main__":
    main()