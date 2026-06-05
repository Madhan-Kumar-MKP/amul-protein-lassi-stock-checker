import asyncio
import os
import requests
from playwright.async_api import async_playwright

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID        = os.environ["CHAT_ID"]

PRODUCT_PAGE = "https://shop.amul.com/en/product/amul-high-protein-rose-lassi-200-ml-or-pack-of-30"
API_URL = (
    "https://shop.amul.com/api/1/entity/ms.products"
    "?q=%7B%22alias%22:%22amul-high-protein-rose-lassi-200-ml-or-pack-of-30%22%7D"
    "&limit=1&substore=66505ff0998183e1b1935c75"
)
BUY_URL = PRODUCT_PAGE

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

async def check_stock():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Visiting product page (solving Cloudflare)...")
        await page.goto(PRODUCT_PAGE, wait_until="networkidle", timeout=30000)

        print("Fetching stock API...")
        result = await page.evaluate(f"""
            async () => {{
                const r = await fetch("{API_URL}", {{
                    headers: {{
                        "accept": "application/json",
                        "frontend": "1",
                        "base_url": "{PRODUCT_PAGE}",
                        "referer": "{PRODUCT_PAGE}"
                    }}
                }});
                return await r.json();
            }}
        """)

        await browser.close()

        product = result["data"][0]
        available = product.get("available", 0)
        quantity  = product.get("inventory_quantity", 0)
        print(f"  available={available}, inventory_quantity={quantity}")
        return available == 1

def main():
    print("🥛 Amul stock checker started...")
    try:
        in_stock = asyncio.run(check_stock())

        if in_stock:
            send_telegram(
                "🚨 <b>AMUL PROTEIN LASSI IS BACK IN STOCK!</b> 🥛\n\n"
                f"👉 <a href='{BUY_URL}'>Buy Now — Pack of 30 × 200ml @ ₹750</a>"
            )
            print("✅ In stock! Notification sent.")
        else:
            print("❌ Out of stock — no notification sent.")

    except Exception as e:
        import traceback
        print(f"⚠️  Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
