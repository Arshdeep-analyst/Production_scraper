from urllib.parse import quote

from patchright.sync_api import sync_playwright

from db.connection import SessionLocal
from pipeline.product_pipeline import ProductPipeline
from scraper.clients.meesho import MeeshoClient
from scraper.normalizer.meesho import MeeshoNormalizer


def run_meesho(
    query: str,
    max_scrolls: int = 150,
) -> None:

    print("\n🚀 Starting Meesho pipeline")
    print(f"Query: {query}")

    search_url = f"https://www.meesho.com/search?q={quote(query)}"

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
            # 3. Create page
            # -----------------------------------------
            # Note: unlike Myntra, we do NOT call page.goto() here.
            # MeeshoClient.search() handles navigation itself, because
            # it needs the response listener attached BEFORE the page
            # loads, or it can miss the very first API calls.

            page = browser_context.new_page()

            # -----------------------------------------
            # 4. Create Meesho client
            # -----------------------------------------

            client = MeeshoClient(
                page=page
            )

            # -----------------------------------------
            # 5. Fetch raw catalogs (scroll-driven)
            # -----------------------------------------

            raw_products = client.search(
                url=search_url,
                max_scrolls=max_scrolls,
            )

            print(
                f"\n📦 Raw catalogs collected: "
                f"{len(raw_products)}"
            )

            if not raw_products:
                print("⚠️ No products found.")
                return

            # -----------------------------------------
            # 6. Normalizer
            # -----------------------------------------

            normalizer = MeeshoNormalizer()

            # -----------------------------------------
            # 7. Database session
            # -----------------------------------------

            session = SessionLocal()

            try:

                pipeline = ProductPipeline(
                    session
                )

                saved_count = 0

                # -----------------------------------------
                # 8. Normalize → Pipeline → DB
                # -----------------------------------------

                for raw_product in raw_products:

                    try:

                        normalized_product = (
                            normalizer.normalize(
                                raw_product
                            )
                        )

                        result = pipeline.process(
                            normalized_product
                        )

                        if result is not None:
                            saved_count += 1

                    except Exception as exc:

                        print(
                            f"❌ Failed to process "
                            f"product: {exc}"
                        )

                print("\n" + "=" * 50)
                print("✅ Meesho pipeline completed")
                print(
                    f"📦 Raw catalogs: "
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

    run_meesho(
        query="korean pants",
    )