from db.connection import SessionLocal
from pipeline.product_pipeline import ProductPipeline


def main():

    session = SessionLocal()

    try:
        product_data = {
            "source_site": "myntra",
            "title": "Test Product",
            "description": "Pipeline test product",
            "price": 539,
            "stock": "17",
            "product_url": "https://www.myntra.com/test-product",
            "source_product_id": "PIPELINE_TEST_001",
            "brand": "Test Brand",
            "image_url": None,
            "rating": 4.5,
            "currency": "INR",
            "country_of_origin": None,
        }

        pipeline = ProductPipeline(session)

        product = pipeline.process(product_data)

        print("\n✅ Product inserted successfully!")
        print(f"Database ID: {product.id}")
        print(f"Title: {product.title}")
        print(f"Source ID: {product.source_product_id}")

    finally:
        session.close()


if __name__ == "__main__":
    main()