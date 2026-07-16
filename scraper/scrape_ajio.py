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
OUTPUT_PATH = "data/ajio_raw.csv"


def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9225")
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
    driver.set_page_load_timeout(40)
    return driver


def scroll_page(driver):
    """Ajio is React-based — scroll slowly to trigger lazy loading"""
    total_height = driver.execute_script("return document.body.scrollHeight")
    step = total_height // 6
    for i in range(1, 7):
        driver.execute_script(f"window.scrollTo(0, {step * i});")
        time.sleep(1.2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)


def parse_name(card):
    # Ajio brand + product name in separate spans
    brand = card.find("div", class_="brand-name") or \
            card.find("strong", class_="brand-name") or \
            card.find("div", class_=re.compile(r'brand', re.IGNORECASE))
    name  = card.find("div", class_="product-name") or \
            card.find("div", class_=re.compile(r'product.*name', re.IGNORECASE))

    if brand and name:
        return f"{brand.get_text(strip=True)} {name.get_text(strip=True)}"[:120]
    if brand:
        return brand.get_text(strip=True)[:120]

    # fallback — first meaningful text chunk
    full = card.get_text(separator=" ", strip=True)
    parts = full.split()
    return " ".join(parts[:10]) if parts else "N/A"


def parse_prices(card):
    current_price  = "N/A"
    original_price = "N/A"
    discount       = "N/A"

    full = card.get_text(separator=" ", strip=True)

    # Ajio uses ₹ symbol
    prices = re.findall(r'₹\s*([\d,]+)', full)
    if len(prices) >= 1:
        current_price = f"₹{prices[0]}"
    if len(prices) >= 2:
        original_price = f"₹{prices[1]}"

    # discount like "60% off" or "(60% OFF)"
    disc_match = re.search(r'\(?\b(\d{1,3})%\s*off\b\)?', full, re.IGNORECASE)
    if disc_match:
        discount = f"{disc_match.group(1)}% off"

    return current_price, original_price, discount


def parse_rating(card):
    full = card.get_text(separator=" ", strip=True)
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
        r'expires\s+soon',
        r'limited\s+time',
        r'offer\s+ends'
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
    # Ajio search URL format
    url = f"https://www.ajio.com/search/?text={query.replace(' ', '%20')}&start={(page-1)*45}"
    print(f"  Scraping: {url}")

    try:
        driver.get(url)
    except Exception:
        print("    ⚠️ Timeout, retrying...")
        time.sleep(5)
        try:
            driver.get(url)
        except Exception:
            return []

    time.sleep(random.uniform(4, 6))
    scroll_page(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Ajio product cards
    cards = (
        soup.find_all("div", class_="item") or
        soup.find_all("div", class_=re.compile(r'product.*card|card.*product', re.IGNORECASE)) or
        soup.find_all("article")
    )

    print(f"    Cards found: {len(cards)}")
    products = []

    for card in cards:
        try:
            full_text = card.get_text(separator=" ", strip=True)
            if len(full_text) < 20:
                continue

            link_tag = card.find("a", href=True)
            product_url = "https://www.ajio.com" + link_tag["href"] if link_tag and link_tag["href"].startswith("/") else (link_tag["href"] if link_tag else "N/A")

            name                                    = parse_name(card)
            current_price, original_price, discount = parse_prices(card)
            rating                                  = parse_rating(card)
            urgency                                 = parse_urgency(full_text)
            fake_discount                           = parse_fake_discount(current_price, original_price, discount)

            has_urgency = urgency != "None"
            suspicious_discount = False
            if discount != "N/A":
                d_match = re.search(r'\d+', discount)
                if d_match:
                    suspicious_discount = int(d_match.group()) >= 70

            products.append({
                "platform":            "Ajio",
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
            time.sleep(random.uniform(3, 5))

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