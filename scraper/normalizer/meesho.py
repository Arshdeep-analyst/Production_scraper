from typing import Any

from scraper.normalizer.base import BaseNormalizer


class MeeshoNormalizer(BaseNormalizer):
    """
    Converts raw Meesho catalog data into the common
    product schema used by the application.
    """

    SOURCE_SITE = "meesho"
    CURRENCY = "INR"

    def normalize(self, product: dict) -> dict:
        """
        Convert a raw Meesho catalog into the common
        product structure.
        """

        if not isinstance(product, dict):
            raise TypeError("product must be a dictionary")

        catalog_id = product.get("id")

        if not catalog_id:
            raise ValueError(
                "Meesho product is missing catalog ID"
            )

        # -----------------------------------------
        # Title
        # -----------------------------------------

        title = (
            product.get("hero_product_name")
            or product.get("name")
            or ""
        )

        # -----------------------------------------
        # Description
        # -----------------------------------------

        description = (
            product.get("description")
            or product.get("full_details")
            or ""
        )

        # -----------------------------------------
        # Price
        # -----------------------------------------

        price = (
            product.get("min_product_price")
            or product.get("min_catalog_price")
        )

        # -----------------------------------------
        # Product ID
        # -----------------------------------------

        source_product_id = (
            product.get("product_id")
            or product.get("hero_pid")
            or catalog_id
        )

        # -----------------------------------------
        # Image
        # -----------------------------------------

        image_url = product.get("image")

        if not image_url:

            product_images = (
                product.get("product_images") or []
            )

            if product_images:
                image_url = product_images[0].get("url")

        # -----------------------------------------
        # Rating
        # -----------------------------------------

        review_summary = (
            product.get("catalog_reviews_summary")
            or product.get("supplier_reviews_summary")
            or {}
        )

        rating = review_summary.get(
            "average_rating"
        )

        # -----------------------------------------
        # Product URL
        # -----------------------------------------

        product_id = product.get("product_id")

        product_url = None

        if product_id:
            product_url = (
                f"https://www.meesho.com/s/p/{product_id}"
            )

        # -----------------------------------------
        # Brand
        # -----------------------------------------

        brand = product.get("brand")

        # -----------------------------------------
        # Stock
        # -----------------------------------------

        # Meesho search responses don't reliably
        # expose stock quantity.
        stock = product.get("stock")

        # -----------------------------------------
        # Country of origin
        # -----------------------------------------

        country_of_origin = product.get(
            "country_of_origin"
        )

        # -----------------------------------------
        # Common product schema
        # -----------------------------------------

        return {
            "source_site": self.SOURCE_SITE,
            "title": title,
            "description": description,
            "price": price,
            "stock": stock,
            "product_url": product_url,
            "source_product_id": str(
                source_product_id
            ),
            "brand": brand,
            "image_url": image_url,
            "rating": rating,
            "currency": self.CURRENCY,
            "country_of_origin": country_of_origin,
        }