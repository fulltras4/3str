import json
from pathlib import Path
from time import sleep
from deep_translator import GoogleTranslator

INPUT_JSON = "sssports_products_original.json"      # исходные данные (англ)
OUTPUT_JSON = "sssports_products_translated_deep.json"  # файл с тестовым переводом (20шт)

# создаём один экземпляр переводчика
translator = GoogleTranslator(source="en", target="ru")

def translate_text(text: str) -> str:
    """Обёртка над deep_translator с простой обработкой ошибок."""
    if not text:
        return ""
    try:
        return translator.translate(text)
    except Exception as e:
        print(f"⚠️ Ошибка перевода: {e}")
        # небольшая пауза и одна повторная попытка
        sleep(2)
        try:
            return translator.translate(text)
        except Exception as e2:
            print(f"❌ Повторная ошибка перевода: {e2}")
            return text  # в крайнем случае вернём оригинал

def main():
    # 1. Загружаем оригинальные товары
    if not Path(INPUT_JSON).exists():
        print(f"Файл {INPUT_JSON} не найден")
        return

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        products = json.load(f)

    print(f"Всего товаров в исходнике: {len(products)}")

    # берём только первые 20 для теста
    test_products = products

    translated = []

    for i, product in enumerate(test_products, start=1):
        title = product.get("title", "")
        desc_orig = product.get("description_original", "")

        title_ru = translate_text(title)
        desc_ru = translate_text(desc_orig)

        new_product = {
            **product,
            "title_ru": title_ru,
            "description_ru": desc_ru,
        }

        translated.append(new_product)
        print(f"[{i}/20] Переведён товар: {title}")

        # необязательно, но можно чуть притормозить, чтобы не словить лимиты
        sleep(1)

    # 3. Сохраняем результат в новый файл
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(translated, f, ensure_ascii=False, indent=2)

    print(f"Готово! Тестовый перевод 20 товаров сохранён в {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
