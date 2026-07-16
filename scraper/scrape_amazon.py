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
OUTPUT_PATH = "data/amazon_raw.csv"


def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9223")
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


def parse_name(card):
    tag = card.find("span", class_="a-size-medium") or \
          card.find("span", class_="a-size-base-plus") or \
          card.find("h2")
    if tag:
        return tag.get_text(strip=True)[:120]
    return "N/A"


def parse_current_price(card):
    tag = card.find("span", class_="a-price-whole")
    if tag:
        fraction = card.find("span", class_="a-price-fraction")
        price = tag.get_text(strip=True).replace(",", "").replace(".", "")
        frac = fraction.get_text(strip=True) if fraction else "00"
        return f"₹{price}.{frac}"
    return "N/A"


def parse_original_price(card):
    tag = card.find("span", class_="a-price a-text-price")
    if tag:
        inner = tag.find("span", class_="a-offscreen")
        if inner:
            return inner.get_text(strip=True)
    return "N/A"


def parse_discount(card):
    tag = card.find("span", class_="a-letter-space")
    # try badge savings text
    badge = card.find("span", string=re.compile(r'\d+%\s*off', re.IGNORECASE))
    if badge:
        return badge.get_text(strip=True)
    # fallback from full text
    full_text = card.get_text(separator=" ", strip=True)
    match = re.search(r'\b(\d{1,3})%\s*off\b', full_text, re.IGNORECASE)
    return f"{match.group(1)}% off" if match else "N/A"


def parse_rating(card):
    tag = card.find("span", class_="a-icon-alt")
    if tag:
        match = re.search(r'[\d.]+', tag.get_text())
        return match.group(0) if match else "N/A"
    full_text = card.get_text(separator=" ", strip=True)
    match = re.search(r'\b([1-5]\.[0-9])\b', full_text)
    return match.group(1) if match else "N/A"


def parse_urgency(full_text):
    patterns = [
        r'only\s+\d+\s+left',
        r'only\s+\d+\s+in\s+stock',
        r'limited time deal',
        r'deal of the day',
        r'lightning deal',
        r'expires soon',
        r'selling fast',
        r'few left',
        r'in stock soon',
        r'hurry'
    ]
    for pattern in patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return "None"


def parse_fake_discount(current, original):
    try:
        c = float(re.sub(r'[^\d.]', '', current))
        o = float(re.sub(r'[^\d.]', '', original))
        return "Yes" if c >= o else "No"
    except Exception:
        return "N/A"


def scrape_page(driver, query, page):
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}&page={page}"
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

    time.sleep(random.uniform(4, 6))

    # check for CAPTCHA
    if "captcha" in driver.page_source.lower() or "robot" in driver.page_source.lower():
        print("    ⚠️ CAPTCHA detected — waiting 15 seconds...")
        time.sleep(15)
        driver.get(url)
        time.sleep(random.uniform(4, 6))

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.find_all("div", {"data-component-type": "s-search-result"})
    print(f"    Cards found: {len(cards)}")

    products = []
    for card in cards:
        try:
            full_text = card.get_text(separator=" ", strip=True)
            if len(full_text) < 30:
                continue

            link_tag = card.find("a", class_="a-link-normal", href=True)
            product_url = "https://www.amazon.in" + link_tag["href"] if link_tag else "N/A"

            name           = parse_name(card)
            current_price  = parse_current_price(card)
            original_price = parse_original_price(card)
            discount       = parse_discount(card)
            rating         = parse_rating(card)
            urgency        = parse_urgency(full_text)
            fake_discount  = parse_fake_discount(current_price, original_price)

            has_urgency = urgency != "None"
            suspicious_discount = False
            if discount != "N/A":
                d_match = re.search(r'\d+', discount)
                if d_match:
                    suspicious_discount = int(d_match.group()) >= 70

            # detect sponsored content (another dark pattern)
            is_sponsored = bool(card.find("span", string=re.compile(r'Sponsored', re.IGNORECASE)))

            products.append({
                "platform":            "Amazon",
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
                "is_sponsored":        is_sponsored,
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
        print(df[["product_name", "current_price", "original_price", "discount", "urgency_text", "is_sponsored"]].head(10))
    else:
        print("\n❌ No products scraped.")


if __name__ == "__main__":
    main()