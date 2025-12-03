import json
import requests
from time import sleep
from pathlib import Path

INPUT_JSON = "sssports_products_original.json"      # исходные данные (англ)
OUTPUT_JSON = "sssports_products_translated.json"   # файл с переводом

def libretranslate(text, source="en", target="ru", max_retries=3):
    url = "https://libretranslate.de/translate"
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text"
    }
    for attempt in range(max_retries):
        try:
            response = requests.post(url, data=payload, timeout=15)
            if response.status_code == 429:  # слишком много запросов
                print("Сервис временно перегружен, пауза...")
                sleep(5)
                continue
            response.raise_for_status()
            data = response.json()
            if "translatedText" in data:
                return data["translatedText"]
            print("Нет поля translatedText в ответе")
        except Exception as e:
            print(f"Ошибка перевода (попытка {attempt+1}): {e}")
            sleep(3)
    return ""

def main():
    # 1. читаем исходный файл всегда
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        original_products = json.load(f)

    # 2. если уже есть файл с переводами — загружаем его
    translated_products = None
    if Path(OUTPUT_JSON).exists():
        with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
            translated_products = json.load(f)
        print(f"Найден существующий {OUTPUT_JSON}, продолжаем перевод.")

    # делаем словарь по id для быстрых совпадений
    by_id_translated = {}
    if translated_products:
        for p in translated_products:
            pid = p.get("id")
            if pid is not None:
                by_id_translated[pid] = p

    result = []
    total = len(original_products)

    for idx, product in enumerate(original_products, start=1):
        pid = product.get("id")

        # если для этого id уже есть перевод с description_ru — используем его и пропускаем
        existing = by_id_translated.get(pid)
        if existing and existing.get("description_ru"):
            result.append(existing)
            print(f"[{idx}/{total}] Уже переведён, пропускаем id={pid}")
            continue

        title_en = product.get("title", "")
        desc_en = product.get("description_original", "")

        # Начинаем с копии оригинала
        current = dict(product)

        # Перевод заголовка
        if title_en:
            title_ru = libretranslate(title_en)
            current["title_ru"] = title_ru
        else:
            current["title_ru"] = ""

        sleep(1.0)

        # Перевод описания
        if desc_en:
            desc_ru = libretranslate(desc_en)
            current["description_ru"] = desc_ru
        else:
            current["description_ru"] = ""

        print(f"[{idx}/{total}] Переведено: {title_en[:40]!r}")
        sleep(1.0)

        result.append(current)

        # ВАЖНО: периодически сохраняем прогресс
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Готово! Обновлён файл с переводами: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
