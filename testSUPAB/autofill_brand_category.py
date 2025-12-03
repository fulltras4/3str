from supabase import create_client, Client

# === Вставьте свои реальные данные ===
SUPABASE_URL = "https://aunwsdwrezijzexkdkxv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF1bndzZHdyZXppanpleGtka3h2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwNTg4MzgsImV4cCI6MjA3MjYzNDgzOH0.3ORHFGCpQ9ziIy3N7R0vWcAJlOsXI3CTYTorr9XMnKk"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

brands_list = [
    "ADIDAS", "Arena", "Asics", "Beyond Yoga", "Billabong", "Body Sculpture", "Bowflex",
    "Chupps", "COEGA", "Columbia", "Converse", "Crocs", "Dahon Bike", "Dickies", "Dunlop",
    "EA7 Emporio Armani", "Ellesse", "Fuji", "Gaiam", "Giant", "Gym King", "Havaianas", "HOKA",
    "iFIT", "Jordan", "New Balance", "New Era", "Nicce", "Nike", "On Running", "Puma", "Prana",
    "Proform", "Reebok", "Sanuk", "Speedo", "SQUATWOLF", "Sun and Sand Sports", "The Giving Movement",
    "The North Face", "Timberland", "Under Armour", "Vans", "Venum"
]

def detect_brand(title):
    for brand in brands_list:
        if brand.lower() in title.lower():
            return brand
    return "Other"

def detect_category(title):
    text = title.lower()
    if "shoe" in text or "boot" in text or "кросс" in text:
        return "Shoes"
    if "t-shirt" in text or "tee" in text or "футбол" in text:
        return "T-shirt"
    if "hoodie" in text or "толст" in text:
        return "Hoodie"
    if "short" in text or "шорт" in text:
        return "Shorts"
    if "sock" in text or "носок" in text:
        return "Socks"
    if "cap" in text or "hat" in text or "кепк" in text:
        return "Cap"
    return "Other"

# Получаем все товары
response = supabase.table("productsSS").select("id, title, brand, category").execute()
products = response.data

for product in products:
    title = product.get("title", "")
    # Пропускаем, если пусто или уже есть значения!
    if not title or (product.get("brand") and product.get("category")):
        continue
    brand = detect_brand(title)
    category = detect_category(title)
    supabase.table("productsSS").update(
        {"brand": brand, "category": category}
    ).eq("id", product["id"]).execute()
    print(f"Product ID {product['id']}: set brand='{brand}', category='{category}'")

print("\nГотово! Проверьте Supabase Table Editor.")
