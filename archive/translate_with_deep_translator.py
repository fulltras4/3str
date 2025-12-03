import json
from time import sleep
from deep_translator import GoogleTranslator

INPUT_JSON = "sssports_products_original.json"
OUTPUT_JSON = "sssports_products_translated.json"

def safe_translate(text):
    try:
        return GoogleTranslator(source='en', target='ru').translate(text)
    except Exception as e:
        print("Ошибка перевода:", e)
        sleep(3)
        return ""

def batch_translate_descriptions(products, desc_key='description_original', dest_key='description_ru'):
    for idx, product in enumerate(products, start=1):
        en_text = product.get(desc_key, "")
        if en_text:
            ru_text = safe_translate(en_text)
            product[dest_key] = ru_text
            print(f"[{idx}/{len(products)}] Переведено: {ru_text[:40]}...")
            sleep(1.0)  # короткая пауза, чтобы не получить блокировку
        else:
            product[dest_key] = ""
    return products

if __name__ == "__main__":
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        products = json.load(f)

    products_translated = batch_translate_descriptions(products)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(products_translated, f, ensure_ascii=False, indent=2)

    print(f"Готово! Новый файл с переводами: {OUTPUT_JSON}")
