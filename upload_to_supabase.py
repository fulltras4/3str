import os
import json
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL или SUPABASE_KEY не заданы!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# файл, который создает translate_with_deep_translator.py
INPUT_JSON = "sssports_products_translated_deep.json"

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    products = json.load(f)

rows_to_upsert = []

for idx, item in enumerate(products, start=1):
    price_aed = item.get("price_aed") or 0

    row = {
        "id": idx,
        "title": item.get("title"),
        "title_ru": item.get("title_ru"),
        "url": item.get("url"),
        "price_aed": price_aed,
        "price_ru": round(price_aed * 25),  # <── добавили цену в рублях
        "image_url": item.get("image_url"),
        "brand": item.get("brand"),
        "category": item.get("category"),
        "color": item.get("color"),
        "sizes": item.get("sizes"),
        "additional_images": item.get("additional_images"),
        "description_original": item.get("description_original"),
        "description_ru": item.get("description_ru"),
        "coupon_code": item.get("coupon_code"),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    rows_to_upsert.append(row)

supabase.table("productsSS").upsert(rows_to_upsert).execute()
print(f"✅ Загружено товаров: {len(rows_to_upsert)}")
