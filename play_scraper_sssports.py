import os
import json
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

load_dotenv()

def extract_color(soup, title):
    meta_color = soup.find("meta", {"property": "product:color"})
    if meta_color and meta_color.get("content"):
        return meta_color["content"].strip()
    color_span = soup.find("span", class_="variation-attribute__selected-value")
    if color_span:
        return color_span.text.strip()
    # fallback color extraction from title last word
    import re
    match = re.search(r'([A-Z][a-z]+)$', title)
    return match.group(1) if match else ""

def extract_description(soup):
    meta_desc = soup.find("meta", {"name": "description"})
    if meta_desc and meta_desc.get("content"):
        return meta_desc["content"].strip()
    desc_tag = soup.find("div", class_="description") or soup.find("div", class_="product-description")
    if desc_tag:
        return desc_tag.get_text(separator=" ", strip=True)
    return ""

def parse_product_details(browser, product_url):
    page = browser.new_page()
    page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
    time.sleep(2)  # Даем странице прогрузиться

    page_content = page.content()
    soup = BeautifulSoup(page_content, "html.parser")

    meta_brand = soup.find("meta", property="og:brand")
    brand = meta_brand["content"].strip() if meta_brand and meta_brand.get("content") else ""

    meta_title = soup.find("meta", property="og:title")
    category = ""
    title_text = ""
    if meta_title and meta_title.get("content"):
        title_text = meta_title["content"].lower()
        for keyword in ["shoes", "boots", "sneakers", "sandals", "slippers", "t-shirt", "hoodie", "short", "sock", "jacket", "pants", "bag", "cap", "track", "swim"]:
            if keyword in title_text:
                category = keyword
                break
        if not category:
            category = "other"

    color = extract_color(soup, title_text)
    description = extract_description(soup)

    sizes = []
    size_elements = page.query_selector_all('button.js-size-attribute')
    for size_el in size_elements:
        size_text = size_el.get_attribute('data-attr-display-value') or size_el.inner_text().strip()
        is_disabled = "disabled" in (size_el.get_attribute("class") or "")
        if size_text and not is_disabled:
            sizes.append(size_text)

    additional_images = []
    thumbnail_divs = page.query_selector_all('div.pdp-thumbnails')
    for div in thumbnail_divs:
        img_tags = div.query_selector_all('img')
        for img in img_tags:
            src = img.get_attribute('src') or img.get_attribute('data-src') or ""
            if src and not src.startswith('http'):
                src = "https://en-ae.sssports.com" + src
            if src:
                additional_images.append(src)

    page.close()
    return sizes, additional_images, brand, category, color, description

def parse_products(browser, page, max_items):
    products = []
    tiles = page.query_selector_all('.product-tile')

    for i, tile in enumerate(tiles):
        img_tag = tile.query_selector('img.image-container__tile-image')
        img_url = ""
        if img_tag:
            img_url = (
                img_tag.get_attribute('data-high-res-src') or
                img_tag.get_attribute('src') or
                img_tag.get_attribute('data-src') or
                ""
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

        sizes = []
        additional_images = []
        brand = ""
        category = ""
        color = ""
        description = ""

        if url:
            print(f"Парсим детали товара: {url} ({i+1}/{max_items})")
            sizes, additional_images, brand, category, color, description = parse_product_details(browser, url)

        products.append({
            "title": title,
            "url": url,
            "price_aed": price_aed,
            "image_url": img_url,
            "sizes": sizes,
            "additional_images": additional_images,
            "brand": brand,
            "category": category,
            "color": color,
            "description_original": description
        })

        if len(products) >= max_items:
            break

    return products

def main():
    # Загрузка конфигурации из файла
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    target_url = config.get('base_url', '')
    max_items = 33  # Количество товаров для теста

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Открываю страницу: {target_url}")
        page.goto(target_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_selector('.product-tile', timeout=15000)
        time.sleep(2)

        click_count = 0
        max_clicks = 50  # Максимум кликов по кнопке Load More

        while click_count < max_clicks:
            load_more_btn = page.query_selector('button.js-show-more-btn')
            if load_more_btn and load_more_btn.is_visible():
                load_more_btn.scroll_into_view_if_needed()
                time.sleep(1)
                load_more_btn.click()
                click_count += 1
                time.sleep(3)
                current_count = len(page.query_selector_all('.product-tile'))
                print(f"Клик #{click_count}: найдено товаров {current_count}")
                if current_count >= max_items:
                    break
            else:
                print("Кнопка Load More больше не доступна")
                break

        print("Парсинг товаров...")
        products = parse_products(browser, page, max_items)
        browser.close()

        with open('sssports_fixed.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"✅ Сохранено товаров: {len(products)} в sssports_fixed.json")

if __name__ == "__main__":
    main()
