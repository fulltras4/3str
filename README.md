# myshop-scraper

Scraper + pricing for MyShop. Put your Supabase credentials into GitHub Secrets:
SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET. Optionally TARGET_BASE_URL.

Run locally:
1. copy .env.example to .env and fill real values
2. python -m venv env && source env/bin/activate
3. pip install -r requirements.txt
4. python scraper.py
5. python pricing.py
