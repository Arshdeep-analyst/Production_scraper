from playwright.sync_api import sync_playwright


class BrowserManager:

    def __enter__(self):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=False,
            channel="chrome"
        )

        self.context = self.browser.new_context()

        self.page = self.context.new_page()

        return self

    def __exit__(self, exc_type, exc, tb):

        self.browser.close()
        self.playwright.stop()