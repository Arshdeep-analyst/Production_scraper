from db.connection import SessionLocal
from pipeline.product_pipeline import ProductPipeline


def main():

    test_products = [
        {
            "source_site": "myntra",
            "title": "Batch Test Product 1",
            "description": "Testing batch pipeline",
            "price": 500,
            "stock": 10,
            "product_url": "https://www.myntra.com/test-1",
            "source_product_id": "BATCH_TEST_001",
            "brand": "Test Brand",
            "image_url": None,
            "rating": 4.5,
            "currency": "INR",
            "country_of_origin": None,
        },
        {
            "source_site": "myntra",
            "title": "Batch Test Product 2",
            "description": "Testing batch pipeline",
            "price": 600,
            "stock": 20,
            "product_url": "https://www.myntra.com/test-2",
            "source_product_id": "BATCH_TEST_002",
            "brand": "Test Brand",
            "image_url": None,
            "rating": 4.2,
            "currency": "INR",
            "country_of_origin": None,
        },
        {
            "source_site": "myntra",
            "title": "Batch Test Product 3",
            "description": "Testing batch pipeline",
            "price": 700,
            "stock": 15,
            "product_url": "https://www.myntra.com/test-3",
            "source_product_id": "BATCH_TEST_003",
            "brand": "Test Brand",
            "image_url": None,
            "rating": 4.8,
            "currency": "INR",
            "country_of_origin": None,
        },
    ]

    session = SessionLocal()

    try:

        pipeline = ProductPipeline(session)

        saved = pipeline.process_batch(
            test_products,
            batch_size=2,
        )

        print()
        print("=" * 50)
        print(f"✅ Batch test completed")
        print(f"📦 Input products: {len(test_products)}")
        print(f"💾 Saved products: {saved}")
        print("=" * 50)

    finally:
        session.close()


if __name__ == "__main__":
    main()