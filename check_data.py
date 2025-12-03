import json

INPUT_JSON = "sssports_products_original.json"  # файл, который пишет parse_sssports_playwright.py

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Всего товаров: {len(data)}\n")

print("Первый товар:")
print(json.dumps(data[0], indent=2, ensure_ascii=False))

print("\nПоследний товар:")
print(json.dumps(data[-1], indent=2, ensure_ascii=False))
