import requests
from bs4 import BeautifulSoup
import json
import re
import hashlib
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = "https://en-ae.sssports.com/on/demandware.store/Sites-UAE-Site/en_AE/Search-UpdateGrid"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://en-ae.sssports.com/",
    "X-Requested-With": "XMLHttpRequest"
}

def scrape_sssports():
    products = []
    start = 0
    page_size = 24
    
    print("🔍 Начинаем парсинг SSSports...")
    
    while True:
        params = {"start": start, "sz": page_size}
        response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Ошибка {response.status_code} на start={start}")
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        product_tiles = soup.select('.product-tile')  # селектор карточки товара
        
        if not product_tiles:
            print(f"✅ Парсинг завершён на start={start}")
            break
        
        for tile in product_tiles:
            # Извлекаем название
            title_elem = tile.select_one('.product-name a')
            title = title_elem.text.strip() if title_elem else "N/A"
            
            # URL товара
            url = tile.select_one('a.product-tile-link')['href'] if tile.select_one('a.product-tile-link') else ""
            if url and not url.startswith('http'):
                url = f"https://en-ae.sssports.com{url}"
            
            # Цена
            price_elem = tile.select_one('.price-sales')
            price = price_elem.text.strip() if price_elem else "0"
            
            # Картинка
            img_elem = tile.select_one('img.tile-image')
            img = img_elem.get('data-src') or img_elem.get('src') or ""
            if img and not img.startswith('http'):
                img = f"https://en-ae.sssports.com{img}"
            
            # Генерируем ID из URL (хеш)
            product_id = hashlib.md5(url.encode()).hexdigest()[:12] if url else f"sss_{start}_{len(products)}"
            
            products.append({
                "id": product_id,
                "source": "sssports",
                "title": title,
                "url": url,
                "price_aed": float(re.sub(r'[^\d.]', '', price)) if price != "0" else 0.0,
                "image_url": img
            })
        
        print(f"📦 Обработано {len(product_tiles)} товаров (start={start})")
        start += page_size
    
    # Сохраняем в JSON
    with open("sssports_fixed_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Сохранено {len(products)} товаров в sssports_fixed_products.json")
    return products

if __name__ == "__main__":
    scrape_sssports()
