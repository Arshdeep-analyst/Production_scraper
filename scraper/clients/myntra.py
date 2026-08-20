import json
import random
import time
from urllib.parse import quote

from patchright.sync_api import APIRequestContext


class MyntraClient:
    """
    Client responsible for communicating with Myntra's search API.

    Responsibilities:
    - Build Myntra search URLs
    - Fetch search pages
    - Read brand facets
    - Work around Myntra's pagination limit
    - Deduplicate raw products

    This class DOES NOT:
    - Normalize product data
    - Save products to the database
    - Create SQLAlchemy models
    - Export CSV files
    """

    BASE_URL = "https://www.myntra.com/gateway/v4/search/"

    SAFE_LIMIT = 500
    ROWS_PER_PAGE = 50
    MAX_PAGES_SAFETY = 12

    def __init__(self, context: APIRequestContext):
        self.context = context

    # ---------------------------------------------------------
    # PUBLIC METHOD
    # ---------------------------------------------------------

    def search(
        self,
        query: str,
        pincode: str,
    ) -> list[dict]:
        """
        Search Myntra and return raw product dictionaries.

        The brand-facet strategy is used automatically to
        work around Myntra's pagination limitation.
        """

        print(f"🔎 Searching Myntra for: {query}")

        print("📊 Fetching brand facets...")

        brands = self.get_brand_facets(
            query=query,
            pincode=pincode,
        )

        if not brands:
            print("⚠️ No brand facets found.")
            return []

        print(f"🏷️ Found {len(brands)} brands")

        all_products: dict[str, dict] = {}

        for index, brand_entry in enumerate(brands, start=1):

            brand_name = (
                brand_entry.get("value")
                or brand_entry.get("id")
            )

            count = brand_entry.get("count", 0)

            if not brand_name:
                continue

            print(
                f"[{index}/{len(brands)}] "
                f"{brand_name} | count={count}"
            )

            products = self.scrape_brand(
                query=query,
                pincode=pincode,
                brand=brand_name,
                count=count,
            )

            # Deduplicate globally
            for product in products:

                product_id = self.get_product_id(product)

                if product_id:
                    all_products[product_id] = product

            print(
                f"    collected={len(products)} | "
                f"total_unique={len(all_products)}"
            )

            # Small delay between brands
            time.sleep(
                random.uniform(2, 4)
            )

        print(
            f"\n✅ Total unique products: "
            f"{len(all_products)}"
        )

        return list(all_products.values())

    # ---------------------------------------------------------
    # BRAND FACETS
    # ---------------------------------------------------------

    def get_brand_facets(
        self,
        query: str,
        pincode: str,
    ) -> list[dict]:
        """
        Fetch the first search response and extract
        Myntra's Brand facet.
        """

        data = self.fetch_page(
            query=query,
            pincode=pincode,
            page=1,
            filter_param="",
            sort="price_asc",
        )

        if data is None:
            raise RuntimeError(
                "Could not fetch initial Myntra search response."
            )

        filters = data.get(
            "filters",
            {}
        )

        primary_filters = filters.get(
            "primaryFilters",
            []
        )

        for facet in primary_filters:

            if facet.get("id") == "Brand":

                return facet.get(
                    "filterValues",
                    []
                )

        return []

    # ---------------------------------------------------------
    # BRAND SCRAPING
    # ---------------------------------------------------------

    def scrape_brand(
        self,
        query: str,
        pincode: str,
        brand: str,
        count: int,
    ) -> list[dict]:
        """
        Scrape a single brand.

        Brands <= SAFE_LIMIT:
            one ascending-price pass.

        Brands > SAFE_LIMIT:
            ascending + descending passes,
            followed by deduplication.
        """

        filter_param = f"Brand:{brand}"

        # Normal case
        if count <= self.SAFE_LIMIT:

            print(
                f"    → single pass "
                f"(price_asc)"
            )

            return self.scrape_one_pass(
                query=query,
                pincode=pincode,
                filter_param=filter_param,
                sort="price_asc",
            )

        # Large brand
        print(
            f"    → over pagination limit"
        )

        print(
            f"    → scraping price_asc"
        )

        asc_results = self.scrape_one_pass(
            query=query,
            pincode=pincode,
            filter_param=filter_param,
            sort="price_asc",
        )

        time.sleep(
            random.uniform(1.5, 3)
        )

        print(
            f"    → scraping price_desc"
        )

        desc_results = self.scrape_one_pass(
            query=query,
            pincode=pincode,
            filter_param=filter_param,
            sort="price_desc",
        )

        # Merge + deduplicate
        merged: dict[str, dict] = {}

        for product in asc_results + desc_results:

            product_id = self.get_product_id(
                product
            )

            if product_id:
                merged[product_id] = product

        print(
            f"    asc={len(asc_results)}, "
            f"desc={len(desc_results)}, "
            f"unique={len(merged)}"
        )

        return list(merged.values())

    # ---------------------------------------------------------
    # PAGINATION
    # ---------------------------------------------------------

    def scrape_one_pass(
        self,
        query: str,
        pincode: str,
        filter_param: str,
        sort: str,
    ) -> list[dict]:
        """
        Paginate one search/filter/sort combination.
        """

        collected: list[dict] = []

        total_count = None

        for page in range(
            1,
            self.MAX_PAGES_SAFETY + 1
        ):

            print(
                f"        page={page} "
                f"sort={sort}"
            )

            data = self.fetch_page(
                query=query,
                pincode=pincode,
                page=page,
                filter_param=filter_param,
                sort=sort,
            )

            if data is None:
                break

            # Get total count from first response
            if total_count is None:

                total_count = data.get(
                    "totalCount"
                )

                print(
                    f"        total_count="
                    f"{total_count}"
                )

            products = data.get(
                "products",
                []
            )

            if not products:
                print(
                    "        no products "
                    "returned"
                )
                break

            collected.extend(products)

            # Myntra's offset pattern
            offset = (
                0
                if page == 1
                else (
                    (page - 1)
                    * self.ROWS_PER_PAGE
                    - 1
                )
            )

            # Stop when we've reached total_count
            if (
                total_count
                and offset + self.ROWS_PER_PAGE
                >= total_count
            ):
                break

            time.sleep(
                random.uniform(1.5, 3)
            )

        return collected

    # ---------------------------------------------------------
    # API REQUEST
    # ---------------------------------------------------------

    def fetch_page(
        self,
        query: str,
        pincode: str,
        page: int,
        filter_param: str,
        sort: str,
    ) -> dict | None:
        """
        Fetch one page from Myntra's search API.
        """

        url = self.build_url(
            query=query,
            pincode=pincode,
            page=page,
            filter_param=filter_param,
            sort=sort,
        )

        response = self.context.get(
            url,
            headers={
                "Referer": "https://www.myntra.com/",
                "Accept": "application/json",
            },
        )

        if response.status != 200:

            print(
                f"        ❌ page={page} "
                f"status={response.status}"
            )

            return None

        try:

            return response.json()

        except Exception:

            try:
                return json.loads(
                    response.text()
                )

            except json.JSONDecodeError:

                print(
                    f"        ❌ Invalid JSON "
                    f"on page={page}"
                )

                return None

    # ---------------------------------------------------------
    # URL BUILDER
    # ---------------------------------------------------------

    def build_url(
        self,
        query: str,
        pincode: str,
        page: int,
        filter_param: str,
        sort: str,
    ) -> str:
        """
        Build Myntra search API URL.
        """

        encoded_query = quote(query)

        # Myntra's observed offset pattern
        offset = (
            0
            if page == 1
            else (
                (page - 1)
                * self.ROWS_PER_PAGE
                - 1
            )
        )

        url = (
            f"{self.BASE_URL}"
            f"{encoded_query}"
            f"?sort={sort}"
            f"&rawQuery={encoded_query}"
            f"&rows={self.ROWS_PER_PAGE}"
            f"&o={offset}"
            f"&plaEnabled=true"
            f"&xdEnabled=false"
            f"&isFacet=true"
            f"&p={page}"
            f"&pincode={pincode}"
        )

        if filter_param:

            url += (
                f"&f="
                f"{quote(filter_param, safe='')}"
            )

        return url

    # ---------------------------------------------------------
    # PRODUCT ID
    # ---------------------------------------------------------

    @staticmethod
    def get_product_id(
        product: dict,
    ) -> str | None:
        """
        Return Myntra's product ID.

        Myntra search responses expose productId
        directly, so there is no need for the
        previous generic fallback logic.
        """

        product_id = product.get(
            "productId"
        )

        if product_id is None:
            return None

        return str(product_id)