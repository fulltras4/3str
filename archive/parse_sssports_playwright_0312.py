import os
import json
import time
import re
import json as js
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Загружаем переменные окружения
load_dotenv()
TARGET_BASE_URL = os.environ.get("TARGET_BASE_URL")
if not TARGET_BASE_URL:
    print("ERROR: TARGET_BASE_URL не задан в .env")
    exit(1)
OUTPUT_JSON = "sssports_products_original.json"
MAX_ITEMS = 220

def extract_ld_json_description(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = js.loads(script.string)
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and "description" in entry:
                        return entry["description"]
            elif "description" in data:
                return data["description"]
        except Exception:
            continue
    return None

def extract_description(soup):
    description = extract_ld_json_description(soup)
    if description:
        return description.strip()
    desc_tag = soup.find("div", class_="product-description")
    if not desc_tag:
        desc_tag = soup.find("div", class_="description")
    if desc_tag:
        return desc_tag.get_text(separator=" ", strip=True)
    meta_desc = soup.find("meta", {"name": "description"})
    if meta_desc and meta_desc.get("content"):
        return meta_desc["content"].strip()
    return ""

def extract_coupon_code(soup):
    code_tag = soup.find("span", class_="promotion-coupon-detail__section")
    if code_tag:
        return code_tag.text.strip()
    promo_li = soup.find("li", string=re.compile("USE CODE"))
    if promo_li:
        match = re.search(r'USE CODE\s*:?\s*([A-Z0-9]+)', promo_li.text)
        if match:
            return match.group(1)
    return ""

def extract_color(soup, title):
    meta_color = soup.find("meta", {"property": "product:color"})
    if meta_color and meta_color.get("content"):
        return meta_color["content"].strip()
    color_span = soup.find("span", class_="variation-attribute__selected-value")
    if color_span:
        value = color_span.get_text(strip=True)
        if value and len(value) < 20:
            return value
    match = None
    if title:
        match = re.search(r'\b([A-Za-zА-Яа-я]+)\b$', title.strip())
    if match:
        return match.group(1)
    return ""

def detect_category(title_text):
    categories = {
        "shoe": "Shoes", "boot": "Shoes", "sneaker": "Shoes",
        "sandals": "Sandals", "slippers": "Slippers", "t-shirt": "T-Shirt",
        "hoodie": "Hoodie", "short": "Shorts", "sock": "Socks",
        "jacket": "Jacket", "pants": "Pants", "bag": "Bag",
        "cap": "Cap", "track": "Track Pants", "swim": "Swimwear"
    }
    t = title_text.lower()
    for keyword, category in categories.items():
        if keyword in t:
            return category
    return "Other"

def parse_product_details(page, product_url):
    page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
    time.sleep(1.2)
    soup = BeautifulSoup(page.content(), "html.parser")

    meta_brand = soup.find("meta", property="og:brand")
    brand = meta_brand["content"].strip() if meta_brand and meta_brand.get("content") else ""
    meta_title = soup.find("meta", property="og:title")
    title_text = meta_title["content"] if meta_title and meta_title.get("content") else ""
    category = detect_category(title_text)
    description = extract_description(soup)
    coupon_code = extract_coupon_code(soup)
    color = extract_color(soup, title_text)

    sizes = []
    for size_el in page.query_selector_all('button.js-size-attribute'):
        size_text = size_el.get_attribute('data-attr-display-value') or size_el.inner_text().strip()
        is_disabled = "disabled" in (size_el.get_attribute("class") or "")
        if size_text and not is_disabled:
            sizes.append(size_text)

    additional_images = []
    for div in page.query_selector_all('div.pdp-thumbnails'):
        for img in div.query_selector_all('img'):
            src = img.get_attribute('src') or img.get_attribute('data-src') or ""
            if src and not src.startswith('http'):
                src = "https://en-ae.sssports.com" + src
            if src:
                additional_images.append(src)
    return brand, category, color, sizes, additional_images, description, coupon_code

def run():
    products = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.set_default_navigation_timeout(300000)

        print(f"Открываю страницу: {TARGET_BASE_URL}")
        page.goto(TARGET_BASE_URL, wait_until="domcontentloaded")
        time.sleep(8)
        print("Первая загрузка завершена")

        click_count, max_clicks = 0, 50
        while click_count < max_clicks:
            try:
                load_more_btn = page.query_selector('button.js-show-more-btn, button.load-more, button[data-test="load-more"]')
                if load_more_btn and load_more_btn.is_visible():
                    load_more_btn.scroll_into_view_if_needed()
                    time.sleep(1)
                    load_more_btn.evaluate("btn => btn.click()")
                    click_count += 1
                    time.sleep(3)
                    current_count = len(page.query_selector_all('.product-tile'))
                    print(f"Клик #{click_count}: найдено товаров {current_count}")
                    if current_count >= MAX_ITEMS:
                        break
                else:
                    print("Кнопка Load More больше не доступна")
                    break
            except Exception as e:
                print(f"Ошибка при клике Load More: {e}")
                break

        tiles = page.query_selector_all('.product-tile')
        print(f"Обрабатываем товаров: {min(MAX_ITEMS, len(tiles))}")
        for i, tile in enumerate(tiles[:MAX_ITEMS]):
            img_tag = tile.query_selector('img.image-container__tile-image')
            img_url = ""
            if img_tag:
                img_url = (
                    img_tag.get_attribute('data-high-res-src') or
                    img_tag.get_attribute('src') or
                    img_tag.get_attribute('data-src') or ""
                )
                if img_url and not img_url.startswith('http'):
                    img_url = "https://en-ae.sssports.com" + img_url

            title = ""
            if img_tag:
                title = img_tag.get_attribute('alt') or img_tag.get_attribute('title') or ""
            if not title:
                title_tag = tile.query_selector('a')
                title = title_tag.inner_text().strip() if title_tag else ""

            url = ""
            link_tag = tile.query_selector('a.image-container__link')
            if link_tag:
                url = link_tag.get_attribute('href') or ""
                if url and not url.startswith('http'):
                    url = "https://en-ae.sssports.com" + url

            price_aed = 0.0
            price_tag = tile.query_selector('span.value[content]')
            if price_tag:
                price_aed_str = price_tag.get_attribute('content')
                try:
                    price_aed = float(price_aed_str)
                except (TypeError, ValueError):
                    price_aed = 0.0

            brand, category, color, sizes, additional_images, description, coupon_code = ("", "", "", [], [], "", "")
            if url:
                print(f"[{i+1}] Детали: {url}")
                page2 = browser.new_page()
                try:
                    brand, category, color, sizes, additional_images, description, coupon_code = parse_product_details(page2, url)
                except Exception as e:
                    print(f"Ошибка при детализации: {e}")
                page2.close()

            products.append({
                "title": title,
                "url": url,
                "price_aed": price_aed,
                "image_url": img_url,
                "brand": brand,
                "category": category,
                "color": color,
                "sizes": sizes,
                "additional_images": additional_images,
                "description_original": description,
                "coupon_code": coupon_code
            })

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"JSON с товарами сохранён: {OUTPUT_JSON}")
        browser.close()

if __name__ == "__main__":
    run()
