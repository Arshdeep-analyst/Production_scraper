from urllib.parse import quote

from patchright.sync_api import sync_playwright

from db.connection import SessionLocal
from pipeline.product_pipeline import ProductPipeline
from pipeline.run_tracker import start_run, finish_run, fail_run
from scraper.clients.meesho import MeeshoClient
from scraper.normalizer.meesho import MeeshoNormalizer


def run_meesho(
    query: str,
    max_scrolls: int = 150,
) -> int:
    """Returns the number of products actually saved -- used by the
    dashboard's product counts and by Celery tasks for logging."""

    print("\n🚀 Starting Meesho pipeline")
    print(f"Query: {query}")

    search_url = f"https://www.meesho.com/search?q={quote(query)}"

    tracking_session = SessionLocal()
    run = start_run(tracking_session, site="meesho", query=query)

    saved_count = 0

    try:
        with sync_playwright() as playwright:

            browser = playwright.chromium.launch(headless=False)
            browser_context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )

            try:
                page = browser_context.new_page()
                client = MeeshoClient(page=page)

                raw_products = client.search(
                    url=search_url,
                    max_scrolls=max_scrolls,
                )

                print(f"\n📦 Raw catalogs collected: {len(raw_products)}")

                if not raw_products:
                    print("⚠️ No products found.")
                else:
                    normalizer = MeeshoNormalizer()
                    session = SessionLocal()

                    try:
                        pipeline = ProductPipeline(session)

                        for raw_product in raw_products:
                            try:
                                normalized_product = normalizer.normalize(raw_product)
                                result = pipeline.process(normalized_product)
                                if result is not None:
                                    saved_count += 1
                            except Exception as exc:
                                print(f"❌ Failed to process product: {exc}")

                        print("\n" + "=" * 50)
                        print("✅ Meesho pipeline completed")
                        print(f"📦 Raw catalogs: {len(raw_products)}")
                        print(f"💾 Saved products: {saved_count}")
                        print("=" * 50)

                    finally:
                        session.close()

            finally:
                browser_context.close()
                browser.close()

        finish_run(tracking_session, run, product_count=saved_count)
        return saved_count

    except Exception as exc:
        fail_run(tracking_session, run, error=str(exc))
        raise

    finally:
        tracking_session.close()


if __name__ == "__main__":
    run_meesho(
        query="korean pants",
    )