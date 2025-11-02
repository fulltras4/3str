import json
import asyncio
from playwright.sync_api import sync_playwright

def parse_products(page):
    products = []
    tiles = page.query_selector_all('.product-tile')
    for tile in tiles:
        title_tag = tile.query_selector('.product-name a')
        title = title_tag.inner_text().strip() if title_tag else "N/A"

        url_tag = tile.query_selector('a.product-tile-link')
        url = url_tag.get_attribute('href') if url_tag else ""
        if url and not url.startswith('http'):
            url = "https://en-ae.sssports.com" + url

        price_tag = tile.query_selector('.price-sales')
        price_text = price_tag.inner_text().strip() if price_tag else "0"
        try:
            price_aed = float(''.join([c for c in price_text if c.isdigit() or c == '.']))
        except:
            price_aed = 0.0

        img_tag = tile.query_selector('img.tile-image')
        img_url = ""
        if img_tag:
            img_url = img_tag.get_attribute('data-src') or img_tag.get_attribute('src') or ""
        if img_url and not img_url.startswith('http'):
            img_url = "https:" + img_url

        products.append({
            "title": title,
            "url": url,
            "price_aed": price_aed,
            "image_url": img_url
        })
    return products

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Прочитать ссылку из config.json
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            target_url = config['base_url']

        print("Открываю страницу SSSports...")
        page.goto(target_url)
        page.wait_for_selector('.product-tile')

        # Нажимать "Load More", пока кнопка есть и не соберём достаточно товаров
        max_items = 300
        while True:
            try:
                # Нажимаем "Load More", если кнопка есть
                load_more_btn = page.query_selector('button.load-more') or page.query_selector('a.load-more')
                if load_more_btn:
                    print("Жду подгрузку новых товаров...")
                    load_more_btn.click()
                    page.wait_for_timeout(2000)
                else:
                    break
                if len(page.query_selector_all('.product-tile')) >= max_items:
                    break
            except Exception:
                break

        products = parse_products(page)[:max_items]
        browser.close()

        with open('sssports_fixed.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"✅ Сохранено товаров: {len(products)} в sssports_fixed.json")

if __name__ == "__main__":
    main()
