from scraper.normalizer.base import BaseNormalizer

class MyntraNormalizer(BaseNormalizer):

    def normalize(self, product: dict) -> dict:

        """
            Convert raw myntra product data into our common product structure
            
          """
        return {
            "source_site": "myntra",

            "title": product.get("productName")
            or product.get("product"),

            "description": product.get("additionalInfo"),

            "price": product.get("price"),

            "stock": self._get_stock(product),

            "product_url": self._build_product_url(product),

            "source_product_id": str(product.get("productId")),

            "brand": product.get("brand"),

            "image_url": product.get("searchImage"),

            "rating": product.get("rating"),

            "currency": "INR",

            "country_of_origin": None,
                                     
        }

    @staticmethod
    def _get_stock(product: dict):

        """
        Extract inventry from Myntra's inventoryInfo.
        
        """
        inventory_info = product.get("inventoryInfo",[])

        if not inventory_info:
            return None

        total_stock = sum(
            item.get("inventory",0)
            for item in inventory_info
        )

        return total_stock


    @staticmethod
    def _build_product_url(product: dict) -> str | None:

        """
        convert myntra's relative landing PageUrl into a full product url"""

        landing_page = product.get(
            "landingPageUrl"
        )

        if not landing_page:
            return None

        return f"https://www.myntra.com/{landing_page}"

    

    
    