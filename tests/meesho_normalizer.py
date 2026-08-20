from playwright.sync_api import sync_playwright

from scraper.clients.meesho import MeeshoClient
from scraper.normalizer.meesho import MeeshoNormalizer


MEESHO_URL = "https://www.meesho.com/search?q=korean%20pants"

MAX_SCROLLS = 5
TEST_PRODUCTS = 5


def main():
    print("\n" + "=" * 60)
    print("🧪 Meesho Normalizer Test (live scrape)")
    print("=" * 60)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        )

        try:
            page = context.new_page()

            # MeeshoClient.search() calls page.goto() itself internally,
            # so we don't need to (and shouldn't) navigate here too --
            # that would just be a wasted duplicate page load.
            client = MeeshoClient(page=page)

            print(f"\n🌐 Scraping: {MEESHO_URL}")
            raw_products = client.search(
                url=MEESHO_URL,
                max_scrolls=MAX_SCROLLS,
            )

            print(f"\n📦 Raw catalogs collected: {len(raw_products)}")

            if not raw_products:
                print("❌ No catalogs returned")
                return

            normalizer = MeeshoNormalizer()
            test_products = raw_products[:TEST_PRODUCTS]

            print(f"\n🔄 Normalizing {len(test_products)} products...")

            successful = 0
            failed = 0

            for index, raw_product in enumerate(test_products, start=1):
                try:
                    normalized = normalizer.normalize(raw_product)
                    successful += 1

                    print("\n" + "-" * 60)
                    print(f"✅ Product {index}")
                    print("-" * 60)
                    for key, value in normalized.items():
                        print(f"{key:<20}: {value}")

                except Exception as exc:
                    failed += 1
                    print(f"\n❌ Product {index} failed: {exc}")
                    # print the raw dict's keys too -- makes it obvious
                    # which field the normalizer expected but didn't find
                    print(f"   raw keys were: {list(raw_product.keys())}")

            print("\n" + "=" * 60)
            print("✅ Meesho normalizer test completed")
            print("=" * 60)
            print(f"📦 Raw catalogs: {len(raw_products)}")
            print(f"🔄 Tested:       {len(test_products)}")
            print(f"✅ Normalized:   {successful}")
            print(f"❌ Failed:       {failed}")
            print("=" * 60)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()