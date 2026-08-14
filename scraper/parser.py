from db.models import Product


class ProductParser:

    @staticmethod
    def parse(product_json: dict) -> Product:

        return Product(

            product_id=product_json.get("productId"),

            product_name=product_json.get("productName"),

            brand=product_json.get("brand"),

            category=product_json.get("category"),

            gender=product_json.get("gender"),

            rating=product_json.get("rating"),

            rating_count=product_json.get("ratingCount"),

            mrp=product_json.get("mrp"),

            price=product_json.get("price"),

            discount=product_json.get("discount"),

            primary_colour=product_json.get("primaryColour"),

            image=product_json.get("searchImage"),
        )