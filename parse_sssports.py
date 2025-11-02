import requests
from bs4 import BeautifulSoup
import json
import time
import os

# Читаем базовый URL из config.json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

BASE_URL = config['base_url']

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Referer": "https://en-ae.sssports.com/sale",
    "X-Requested-With": "XMLHttpRequest"
}

# Файл для прогресса и результата
PROGRESS_FILE = "parse_progress.json"
RESULT_FILE = "sssports_fixed.json"

def get_products(start=0, size=24):
    params = {
        "start": start,
        "sz": size
    }
    response = requests.get(BASE_URL, headers=HEADERS, params=params)
    
    if not response.ok:
        print(f"❌ Ошибка запроса: код {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    tiles = soup.select('.product-tile')

    products = []
    for tile in tiles:
        title_tag = tile.select_one('.product-name a')
        title = title_tag.text.strip() if title_tag else "N/A"

        url_tag = tile.select_one('a.product-tile-link')
        url = url_tag['href'] if url_tag and url_tag.has_attr('href') else ""
        if url and not url.startswith('http'):
            url = "https://en-ae.sssports.com" + url

        price_tag = tile.select_one('.price-sales')
        price_text = price_tag.text.strip() if price_tag else "0"
        try:
            price_aed = float(''.join(filter(lambda c: c.isdigit() or c == '.', price_text)))
        except:
            price_aed = 0.0

        img_tag = tile.select_one('img.tile-image')
        img_url = ""
        if img_tag:
            if img_tag.has_attr('data-src'):
                img_url = img_tag['data-src']
            elif img_tag.has_attr('src'):
                img_url = img_tag['src']
        if img_url and not img_url.startswith('http'):
            img_url = "https:" + img_url

        products.append({
            "title": title,
            "url": url,
            "price_aed": price_aed,
            "image_url": img_url
        })

    return products

def save_progress(start, products):
    data = {
        "start": start,
        "products": products
    }
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get('start', 0), data.get('products', [])
    return 0, []

def main():
    start, all_products = load_progress()
    size = 24
    max_items = 300  # Ограничение по товарам для теста

    print(f"Начинаем с позиции {start}")

    while True:
        print(f"Запрашиваю товары с {start} по {start + size}...")
        products = get_products(start, size)
        if not products:
            print("Товары закончились или ошибка.")
            break

        all_products.extend(products)
        save_progress(start + size, all_products)

        if len(all_products) >= max_items:
            print(f"Достигнуто максимальное количество товаров: {max_items}")
            break

        if len(products) < size:
            break

        start += size
        time.sleep(1)

    all_products = all_products[:max_items]

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"✅ Всего товаров получено и сохранено: {len(all_products)}")
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == "__main__":
    main()
