from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import json

load_dotenv()

TARGET_BASE_URL = os.environ.get("TARGET_BASE_URL")
if not TARGET_BASE_URL:
    print("ERROR: TARGET_BASE_URL не задан в .env")
    exit(1)

OUTPUT_JSON = "sssports_products.json"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()

        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.set_default_navigation_timeout(300000)  # 5 минут

        print(f"Открываю страницу: {TARGET_BASE_URL}")

        products = []

        # ловим все XHR ответы с товарами
        def handle_response(response):
            if "Search-UpdateGrid" in response.url:
                try:
                    data = response.json()
                    for item in data.get("products", []):
                        products.append({
                            "title": item.get("name"),
                            "price": item.get("price", {}).get("formatted", "N/A"),
                            "img_url": item.get("image", {}).get("url", "")
                        })
                    print(f"Найдено товаров в этом блоке: {len(data.get('products', []))}")
                except Exception:
                    pass

        page.on("response", handle_response)

        page.goto(TARGET_BASE_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(15000)
        print("Дополнительная загрузка завершена")

        # Кликаем Load More пока есть
        while True:
            try:
                load_more = page.query_selector("button.load-more, button[data-test='load-more']")
                if not load_more:
                    break
                print("Нажимаем Load More...")
                load_more.click()
                page.wait_for_timeout(5000)
            except Exception:
                break

        print(f"Всего найдено товаров: {len(products)}")

        # сохраняем JSON
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"JSON с товарами сохранён: {OUTPUT_JSON}")

        browser.close()

if __name__ == "__main__":
    run()
