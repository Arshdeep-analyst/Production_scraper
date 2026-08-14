from sqlalchemy.orm import Session

from db.models import Product


class ProductPipeline:

    def __init__(self, session: Session):
        self.session = session

    def process(self, product_data: dict) -> Product:

        try:
            product = Product(**product_data)

            self.session.add(product)
            self.session.commit()
            self.session.refresh(product)

            return product


        except Exception as e:

            self.session.rollback()

            print(
                f"!!! Failed to save product"
                f"{product_data.get('source_product_id')}: {e}"
            )

            return None

    """def process_batch(
            self,
            products: list[dict],
            batch_size: int=100,
    ) -> int:

         save products in batches.
        
        return the number of successfully saved products .
        
        
        saved_count = 0

        for start in range(0, len(products), batch_size):

            batch = products[start:start + batch_size]

            try:
                product_objects = [
                    Product(**product_data)
                    for product_data in batch
                ]

                self.session.add_all(product_objects)
                self.session.commit()

                saved_count += len(product_objects)

                print(
                    f"✅ Batch saved: "
                    f"{len(product_objects)} products "
                    f"({saved_count}/{len(products)})"
                )

            except Exception as e:

                self.session.rollback()

                print(
                    f"❌ Batch failed "
                    f"({start + 1}-{start + len(batch)}): {e}"
                )

                # Important:
                # Don't let one bad batch stop the entire pipeline.
                #
                # Fall back to processing the products individually.

                for product_data in batch:
                    result = self.process(product_data)

                    if result is not None:
                        saved_count += 1

        return saved_count """