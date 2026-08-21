from patchright.sync_api import sync_playwright

from db.connection import SessionLocal
from pipeline.product_pipeline import ProductPipeline
from pipeline.run_tracker import start_run, finish_run, fail_run
from scraper.clients.myntra import MyntraClient
from scraper.normalizer.myntra import MyntraNormalizer


def run_myntra(
    query: str,
    pincode: str,
) -> int:
    """Returns the number of products actually saved -- used by the
    dashboard's product counts and by Celery tasks for logging."""

    print("\n🚀 Starting Myntra pipeline")
    print(f"Query: {query}")
    print(f"Pincode: {pincode}")

    # A separate session just for run tracking, opened before anything
    # else -- this way a run record exists (status="running") even if
    # the browser itself fails to launch, so the dashboard shows
    # "failed" instead of silently showing nothing for that attempt.
    tracking_session = SessionLocal()
    run = start_run(tracking_session, site="myntra", query=query)

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
                print("🌐 Opening Myntra...")
                page.goto(
                    "https://www.myntra.com/",
                    timeout=30000,
                    wait_until="domcontentloaded",
                )
                print("✅ Myntra browser session established")

                api_context = browser_context.request
                client = MyntraClient(api_context)

                raw_products = client.search(query=query, pincode=pincode)
                print(f"\n📦 Raw products collected: {len(raw_products)}")

                if not raw_products:
                    print("⚠️ No products found.")
                else:
                    normalizer = MyntraNormalizer()
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
                        print("✅ Myntra pipeline completed")
                        print(f"📦 Raw products: {len(raw_products)}")
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
    run_myntra(
        query="korean pants",
        pincode="144002",
    )