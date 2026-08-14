from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar


ResponseT = TypeVar("ResponseT")
ProductT = TypeVar("ProductT")



class BaseScraper(ABC, Generic[ResponseT, ProductT]):

    """
    Base interface for all marketplace scrapers.

    Every scraper must implement:
        - fetch()
        - parse()
        - validate()

    The scraper is responsible for extracting and validating data.
    Saving data belongs to the pipeline/database layer.
    """

    async def scrape(self, **Kwargs: Any) -> list[ProductT]:
        """
        Main entry point used by the pipeline.

        Flow:
            fetch -> parse -> validate
        """

        response = await self.fetch(**Kwargs)

        products = self.parse(response)

        valid_products = [
            product
            for product in products
            if self.validate(product)
        ]

        return valid_products

    @abstractmethod
    async def fetch(self, **Kwargs:Any) -> ResponseT:
        """
        Fetch raw data from the target website/API.

        Each marketplace implements its own fetching logic.
        """
        raise NotImplementedError

    @abstractmethod
    def parse(self, response: ResponseT) -> list[ProductT]:
        """
        Convert the raw response into product objects/dictionaries.
        """
        raise NotImplementedError

    @abstractmethod
    def validate(self, product: ProductT) -> bool:
        """
        Validate a parsed product before it enters the pipeline.
        """
        raise NotImplementedError 