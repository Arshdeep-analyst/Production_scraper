from playwright.sync_api import sync_playwright

from scraper.clients import MyntraClient


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()

        print("🌐 Opening Myntra...")

        page.goto(
            "https://www.myntra.com/",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        print("✅ Myntra session established")

        client = MyntraClient(
            context=context.request
        )

        products = client.search(
            query="korean pants",
            pincode="144002",
        )

        print(
            f"\nTotal products: {len(products)}"
        )

        if products:

            print("\nFirst product:")
            print(products[0])

        browser.close()


if __name__ == "__main__":
    main()