from scraper.normalizer.myntra import MyntraNormalizer

def main():

    # Small sample of the raw Myntra response
    raw_product = {
        "productId": 24403160,
        "product": "The Roadster Lifestyle Co. Women Button Detail High Rise Pleated Korean Pants",
        "productName": "The Roadster Lifestyle Co. Women Button Detail High Rise Pleated Korean Pants",
        "brand": "Roadster",
        "price": 539,
        "rating": 4.408388614654541,
        "additionalInfo": "Women High Rise Korean Pants",
        "landingPageUrl": (
            "Trousers/Roadster/"
            "The-Roadster-Lifestyle-Co-Women-Button-Detail-"
            "High-Rise-Pleated-Korean-Pants/24403160/buy"
        ),
        "searchImage": (
            "http://assets.myntassets.com/assets/images/"
            "24403160/2023/12/6/"
            "c49654b3-19f0-4e00-a6f9-61cfdbdb2c10"
            "1701843467219-Roadster-Women-Trousers-"
            "161701843466802-1.jpg"
        ),
        "inventoryInfo": [
            {
                "skuId": 78305556,
                "label": "28",
                "inventory": 17,
                "available": True,
                "brandSizeLabel": "28",
            }
        ],
    }

    normalizer = MyntraNormalizer()

    normalized_product = normalizer.normalize(
        raw_product
    )

    print("\nNormalized product:\n")

    for key, value in normalized_product.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()