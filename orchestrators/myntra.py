from playwright.sync_api import sync_playwright

from db.connection import SessionLocal
from pipeline.product_pipeline import ProductPipeline
from scraper.clients.myntra import MyntraClient
from scraper.normalizer.myntra import MyntraNormalizer


def run_myntra(
    query: str,
    pincode: str,
) -> None:

    print("\n🚀 Starting Myntra pipeline")
    print(f"Query: {query}")
    print(f"Pincode: {pincode}")

    with sync_playwright() as playwright:

        # -----------------------------------------
        # 1. Launch real Chromium browser
        # -----------------------------------------

        browser = playwright.chromium.launch(
            headless=False
        )

        # -----------------------------------------
        # 2. Create browser context
        # -----------------------------------------

        browser_context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        try:

            # -----------------------------------------
            # 3. Establish Myntra browser session
            # -----------------------------------------

            page = browser_context.new_page()

            print("🌐 Opening Myntra...")

            page.goto(
                "https://www.myntra.com/", 
                timeout=30000, 
                wait_until="domcontentloaded", 
            ) 
 
            print("✅ Myntra browser session established") 
 
            # ----------------------------------------- 
            # 4. Get API context belonging to browser 
            # ----------------------------------------- 
 
            api_context = browser_context.request 
 
            # ----------------------------------------- 
            # 5. Create Myntra client 
            # ----------------------------------------- 
 
            client = MyntraClient( 
                api_context 
            ) 
 
            # ----------------------------------------- 
            # 6. Fetch raw products 
            # ----------------------------------------- 
 
            raw_products = client.search( 
                query=query, 
                pincode=pincode, 
            ) 
 
            print( 
                f"\n📦 Raw products collected: " 
                f"{len(raw_products)}" 
            ) 
 
            if not raw_products: 
                print("⚠️ No products found.") 
                return 
 
            # ----------------------------------------- 
            # 7. Normalizer 
            # ----------------------------------------- 
 
            normalizer = MyntraNormalizer() 
 
            # ----------------------------------------- 
            # 8. Database session 
            # ----------------------------------------- 
 
            session = SessionLocal() 
 
            try: 
 
                pipeline = ProductPipeline( 
                    session 
                ) 
 
                saved_count = 0 
 
                # ----------------------------------------- 
                # 9. Normalize → Pipeline → DB 
                # ----------------------------------------- 
 
                for raw_product in raw_products: 
 
                    try: 
 
                        normalized_product = ( 
                            normalizer.normalize( 
                                raw_product 
                            ) 
                        ) 
 
                        pipeline.process( 
                            normalized_product 
                        ) 
 
                        saved_count += 1 
 
                    except Exception as exc: 
 
                        print( 
                            f"❌ Failed to process " 
                            f"product: {exc}" 
                        ) 
 
                print("\n" + "=" * 50) 
                print("✅ Myntra pipeline completed") 
                print( 
                    f"📦 Raw products: " 
                    f"{len(raw_products)}" 
                ) 
                print( 
                    f"💾 Saved products: " 
                    f"{saved_count}" 
                ) 
                print("=" * 50) 
 
            finally: 
 
                session.close() 
 
        finally: 
 
            browser_context.close() 
            browser.close() 
 
 
if __name__ == "__main__": 
 
    run_myntra( 
        query="korean pants", 
        pincode="144002", 
    )    