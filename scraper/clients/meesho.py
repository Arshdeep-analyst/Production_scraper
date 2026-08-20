import random
import time

from patchright.sync_api import Page


class MeeshoClient:
    """
    Client for extracting Meesho search catalog data.

    Uses a real browser page and listens for:
        /api/v1/products/search

    Responsibilities:
    - Capture raw Meesho catalog responses
    - Extract catalogs[]
    - Deduplicate catalogs by catalog ID
    - Track the cursor returned by Meesho
    - Scroll the page to trigger additional API calls
    - Track API failures
    - Provide diagnostics for infinite-scroll exhaustion

    Does NOT:
    - Normalize product data
    - Save data to MySQL
    - Create SQLAlchemy models
    """

    SEARCH_ENDPOINT = "/api/v1/products/search"

    def __init__(self, page: Page):
        self.page = page

        # catalog_id -> raw catalog
        self.catalogs: dict[str, dict] = {}

        # Diagnostics
        self.response_count = 0
        self.successful_response_count = 0
        self.new_catalog_count = 0

        self.last_api_status: int | None = None

        # Cursor state returned by Meesho
        self.last_cursor: str | None = None
        self.cursor_history: list[str | None] = []

        # API errors
        self.api_errors: list[dict] = []

        # Print response keys only once
        self._printed_response_keys = False

        #self.api_context = api_context

    # =========================================================
    # PUBLIC SEARCH
    # =========================================================

    def search(
        self,
        url: str,
        max_scrolls: int = 200,
        no_new_limit: int = 4,
        scroll_min: int = 1500,
        scroll_max: int = 2500,
        wait_min: float = 2.0,
        wait_max: float = 4.0,
    ) -> list[dict]:
        """
        Scrape Meesho's infinite-scroll search results.

        We currently use:
            - new catalog IDs
            - successful API responses
            - cursor changes
            - consecutive empty/no-new cycles

        max_scrolls remains a hard safety limit.
        """

        # Reset state for a new search
        self.catalogs.clear()

        self.response_count = 0
        self.successful_response_count = 0
        self.new_catalog_count = 0

        self.last_api_status = None

        self.last_cursor = None
        self.cursor_history.clear()

        self.api_errors.clear()

        self._printed_response_keys = False

        # Install response listener
        self.page.on(
            "response",
            self._handle_response,
        )

        try:
            print(
                f"🌐 Opening Meesho: {url}"
            )

            self.page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60_000,
            )

            print("✅ Meesho page loaded")

            # Initial API calls may need a moment.
            time.sleep(
                random.uniform(3, 5)
            )

            consecutive_no_new = 0

            for scroll_number in range(
                1,
                max_scrolls + 1,
            ):
                before_catalog_count = len(
                    self.catalogs
                )

                previous_response_count = (
                    self.response_count
                )

                previous_cursor = (
                    self.last_cursor
                )

                # Trigger more results
                self._scroll(
                    scroll_min=scroll_min,
                    scroll_max=scroll_max,
                )

                # Allow API request + rendering
                time.sleep(
                    random.uniform(
                        wait_min,
                        wait_max,
                    )
                )

                after_catalog_count = len(
                    self.catalogs
                )

                new_this_scroll = (
                    after_catalog_count
                    - before_catalog_count
                )

                responses_this_scroll = (
                    self.response_count
                    - previous_response_count
                )

                cursor_changed = (
                    self.last_cursor
                    != previous_cursor
                )

                print(
                    f"scroll {scroll_number}/{max_scrolls} | "
                    f"new={new_this_scroll} | "
                    f"unique={after_catalog_count} | "
                    f"responses+={responses_this_scroll} | "
                    f"cursor_changed={cursor_changed} | "
                    f"last_status={self.last_api_status}"
                )

                # -------------------------------------------------
                # API FAILURE
                # -------------------------------------------------

                if (
                    responses_this_scroll > 0
                    and self.last_api_status != 200
                ):
                    raise RuntimeError(
                        "Meesho search API returned "
                        f"status {self.last_api_status} "
                        f"during scroll {scroll_number}."
                    )

                # -------------------------------------------------
                # NEW PRODUCTS
                # -------------------------------------------------

                if new_this_scroll > 0:
                    consecutive_no_new = 0
                    continue

                # -------------------------------------------------
                # SUCCESSFUL RESPONSE BUT NO NEW PRODUCTS
                # -------------------------------------------------

                if responses_this_scroll > 0:
                    print(
                        "⚠️ Successful search API response "
                        "but no new catalog IDs."
                    )

                    consecutive_no_new += 1

                # -------------------------------------------------
                # NO RESPONSE
                # -------------------------------------------------

                else:
                    print(
                        "⚠️ No new search API response "
                        "was observed after this scroll."
                    )

                    consecutive_no_new += 1

                # -------------------------------------------------
                # POSSIBLE EXHAUSTION
                # -------------------------------------------------

                if (
                    consecutive_no_new
                    >= no_new_limit
                ):
                    print(
                        "🛑 No new catalogs found for "
                        f"{no_new_limit} consecutive "
                        "scroll cycles."
                    )
                    break

            else:
                print(
                    f"⚠️ Reached max_scrolls="
                    f"{max_scrolls} before exhaustion."
                )

        finally:
            try:
                self.page.remove_listener(
                    "response",
                    self._handle_response,
                )
            except Exception:
                pass

        products = list(
            self.catalogs.values()
        )

        print("\n" + "=" * 60)
        print("✅ Meesho scrape completed")
        print("=" * 60)

        print(
            f"API responses captured : "
            f"{self.response_count}"
        )

        print(
            f"Successful responses   : "
            f"{self.successful_response_count}"
        )

        print(
            f"Unique catalogs        : "
            f"{len(products)}"
        )

        print(
            f"Catalogs discovered    : "
            f"{self.new_catalog_count}"
        )

        print(
            f"API errors             : "
            f"{len(self.api_errors)}"
        )

        print(
            f"Unique cursors         : "
            f"{len(set(self.cursor_history))}"
        )

        print("=" * 60)

        return products

    # =========================================================
    # RESPONSE HANDLER
    # =========================================================

    def _handle_response(
        self,
        response,
    ) -> None:
        """
        Process a Meesho product-search API response.
        """

        if self.SEARCH_ENDPOINT not in response.url:
            return

        self.response_count += 1

        self.last_api_status = (
            response.status
        )

        # -----------------------------------------------------
        # NON-200
        # -----------------------------------------------------

        if response.status != 200:
            print(
                f"⚠️ Meesho API returned "
                f"status={response.status}"
            )

            error = {
                "url": response.url,
                "status": response.status,
            }

            try:
                body = response.text()

                error["body"] = body[:1000]

                print(
                    f"   Response body: "
                    f"{body[:500]}"
                )

            except Exception as exc:
                error["body_error"] = str(exc)

            self.api_errors.append(error)

            return

        self.successful_response_count += 1

        # -----------------------------------------------------
        # PARSE JSON
        # -----------------------------------------------------

        try:
            data = response.json()

        except Exception as exc:
            print(
                f"⚠️ Failed to decode "
                f"Meesho API JSON: {exc}"
            )
            return

        # -----------------------------------------------------
        # RESPONSE KEYS
        # -----------------------------------------------------

        if not self._printed_response_keys:
            print(
                "🔎 Meesho response keys:",
                list(data.keys()),
            )

            self._printed_response_keys = True

        # -----------------------------------------------------
        # CURSOR
        # -----------------------------------------------------

        cursor = data.get("cursor")

        self.cursor_history.append(
            cursor
        )

        if cursor != self.last_cursor:
            print(
                "🔗 Cursor changed:"
                f" {self.last_cursor} -> {cursor}"
            )

            self.last_cursor = cursor

        # -----------------------------------------------------
        # CATALOGS
        # -----------------------------------------------------

        catalogs = data.get(
            "catalogs",
            [],
        )

        print(
            f"📦 catalogs={len(catalogs)}"
        )

        if not isinstance(
            catalogs,
            list,
        ):
            print(
                "⚠️ 'catalogs' is not a list."
            )
            return

        new_count = 0

        for catalog in catalogs:

            if not isinstance(
                catalog,
                dict,
            ):
                continue

            catalog_id = catalog.get(
                "id"
            )

            if catalog_id is None:
                continue

            catalog_id = str(
                catalog_id
            )

            # Deduplicate
            if catalog_id in self.catalogs:
                continue

            self.catalogs[
                catalog_id
            ] = catalog

            new_count += 1
            self.new_catalog_count += 1

        if new_count:
            print(
                f"  📦 API response -> "
                f"{new_count} new catalogs"
            )

    # =========================================================
    # SCROLL
    # =========================================================

    def _scroll(
        self,
        scroll_min: int,
        scroll_max: int,
    ) -> None:

        distance = random.randint(
            scroll_min,
            scroll_max,
        )

        self.page.mouse.wheel(
            0,
            distance,
        )