from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
import os

SEARCH_QUERIES = ["shoes", "watches", "bags", "clothing", "sunglasses"]
PAGES_PER_QUERY = 3
OUTPUT_PATH = "data/myntra_raw.csv"


def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9224")
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


def scroll_page(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(4):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def parse_name(card):
    brand = card.find("h3", class_="product-brand")
    name  = card.find("h4", class_="product-product")
    if brand and name:
        return f"{brand.get_text(strip=True)} {name.get_text(strip=True)}"[:120]
    if brand:
        return brand.get_text(strip=True)[:120]
    full = card.get_text(separator=" ", strip=True)
    return full[:80] if full else "N/A"


def parse_prices(card):
    current_price  = "N/A"
    original_price = "N/A"
    discount       = "N/A"

    full = card.get_text(separator=" ", strip=True)

    # Myntra uses Rs. not ₹
    prices = re.findall(r'Rs\.?\s*([\d,]+)', full)
    if len(prices) >= 1:
        current_price = f"₹{prices[0]}"
    if len(prices) >= 2:
        original_price = f"₹{prices[1]}"

    # discount like (50% OFF)
    disc_match = re.search(r'\((\d+)%\s*OFF\)', full, re.IGNORECASE)
    if disc_match:
        discount = f"{disc_match.group(1)}% off"

    return current_price, original_price, discount


def parse_rating(card):
    full = card.get_text(separator=" ", strip=True)
    # Myntra rating format: "4.4 | 5.1k"
    match = re.search(r'\b([1-5]\.\d)\b', full)
    return match.group(1) if match else "N/A"


def parse_urgency(full_text):
    patterns = [
        r'only\s+few\s+left',
        r'few\s+left',
        r'only\s+\d+\s+left',
        r'limited\s+stock',
        r'selling\s+fast',
        r'hurry',
        r'deal\s+ends',
        r'today\s+only',
        r'expires\s+soon'
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return "None"


def parse_fake_discount(current, original, discount):
    try:
        c = float(re.sub(r'[^\d.]', '', current))
        o = float(re.sub(r'[^\d.]', '', original))
        if c >= o and discount != "N/A":
            return "Yes"
        return "No"
    except Exception:
        return "N/A"


def scrape_page(driver, query, page):
    url = f"https://www.myntra.com/{query.replace(' ', '-')}?p={page}"
    print(f"  Scraping: {url}")

    try:
        driver.get(url)
    except Exception:
        print("    ⚠️ Timeout, retrying...")
        time.sleep(4)
        try:
            driver.get(url)
        except Exception:
            return []

    time.sleep(random.uniform(3, 5))
    scroll_page(driver)
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    cards = (
        soup.find_all("li", class_="product-base") or
        soup.find_all("div", class_="product-base")
    )

    print(f"    Cards found: {len(cards)}")
    products = []

    for card in cards:
        try:
            full_text = card.get_text(separator=" ", strip=True)
            if len(full_text) < 20:
                continue

            link_tag = card.find("a", href=True)
            product_url = "https://www.myntra.com/" + link_tag["href"].lstrip("/") if link_tag else "N/A"

            name                                     = parse_name(card)
            current_price, original_price, discount  = parse_prices(card)
            rating                                   = parse_rating(card)
            urgency                                  = parse_urgency(full_text)
            fake_discount                            = parse_fake_discount(current_price, original_price, discount)

            has_urgency = urgency != "None"
            suspicious_discount = False
            if discount != "N/A":
                d_match = re.search(r'\d+', discount)
                if d_match:
                    suspicious_discount = int(d_match.group()) >= 70

            products.append({
                "platform":            "Myntra",
                "query":               query,
                "page":                page,
                "product_name":        name,
                "current_price":       current_price,
                "original_price":      original_price,
                "discount":            discount,
                "fake_discount":       fake_discount,
                "rating":              rating,
                "urgency_text":        urgency,
                "has_urgency":         has_urgency,
                "suspicious_discount": suspicious_discount,
                "full_text":           full_text[:400],
                "product_url":         product_url
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