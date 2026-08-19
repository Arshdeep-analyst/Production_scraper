from scraper.browser import BrowserManager
from scraper.clients.meesho import MeeshoClient


def main():

    url = (
        "https://www.meesho.com/"
        "search?q=korean%20pants"
    )

    with BrowserManager() as browser:

        client = MeeshoClient(
            page=browser.page
        )

        try:

            catalogs = client.search(
                url=url,
                max_scrolls=20,
                no_new_limit=4,
            )

        except RuntimeError as exc:

            print(
                f"\n❌ Scrape stopped because "
                f"the API failed: {exc}"
            )

            return

        print(
            f"\nCollected "
            f"{len(catalogs)} unique catalogs"
        )

        if catalogs:

            print("\nFirst catalog:")

            print(
                catalogs[0]
            )


if __name__ == "__main__":
    main()