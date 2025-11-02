import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Явно указываем путь к .env файлу
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"🔍 Ищем .env файл: {env_path}")
print(f"📂 Файл существует: {os.path.exists(env_path)}")

load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Диагностика: проверяем, загрузились ли переменные
print(f"✅ SUPABASE_URL: {SUPABASE_URL}")
print(f"✅ SUPABASE_KEY: {'Загружен' if SUPABASE_KEY else 'НЕ ЗАГРУЖЕН!'}")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ОШИБКА: Переменные окружения не загружены!")
    print("📝 Создай файл .env с содержимым:")
    print("SUPABASE_URL=https://aunwsdwrezijzexkdkxv.supabase.co")
    print("SUPABASE_KEY=твой_service_role_key")
    exit(1)

AED_TO_RUB = 27.5
DELTA = 1.35

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_products(json_file: str):
    if not os.path.exists(json_file):
        print(f"❌ Файл {json_file} не найден!")
        return
    
    with open(json_file, "r", encoding="utf-8") as f:
        products = json.load(f)
    
    print(f"📤 Загружаем {len(products)} товаров в Supabase...")
    
    for i, product in enumerate(products):
        price_rub = product.get("price_aed", 0) * AED_TO_RUB * DELTA
        
        data = {
            "id": product.get("id", f"sss_{i}"),
            "source": product.get("source", "sssports"),
            "title": product.get("title", "N/A"),
            "url": product.get("url", ""),
            "price_aed": product.get("price_aed", 0),
            "price_rub": round(price_rub, 2),
            "image_url": product.get("image_url", ""),
            "availability": True
        }
        
        try:
            response = supabase.table("products").upsert(data).execute()
            if i % 10 == 0:  # показываем прогресс каждые 10 товаров
                print(f"✅ Загружено {i}/{len(products)}")
        except Exception as e:
            print(f"❌ Ошибка при загрузке товара {i}: {e}")
    
    print("🎉 Загрузка завершена!")

if __name__ == "__main__":
    # Используй старый JSON (sssports_all_products.json) пока не исправишь парсер
    upload_products("sssports_all_products.json")
