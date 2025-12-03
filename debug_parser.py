import json
from playwright.sync_api import sync_playwright

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    target_url = config['base_url']

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    print(f"Открываю страницу: {target_url}")
    page.goto(target_url, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_selector('.product-tile', timeout=15000)

    # Сохраняем весь HTML страницы
    html_content = page.content()
    with open('debug_page.html', 'w', encoding='utf-8') as file:
        file.write(html_content)
    print("HTML всей страницы сохранён в debug_page.html")

    # Сохраняем HTML первой карточки товара отдельно
    first_tile = page.query_selector('.product-tile')
    if first_tile:
        tile_html = first_tile.inner_html()
        with open('debug_first_tile.html', 'w', encoding='utf-8') as file:
            file.write(tile_html)
        print("HTML первой карточки сохранён в debug_first_tile.html")
        print("\nПервые 1000 символов HTML карточки:")
        print(tile_html[:1000])
    else:
        print("❌ Карточка товара не найдена!")

    input("\nНажми Enter для закрытия браузера...")
    browser.close()
