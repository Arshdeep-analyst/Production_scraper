from abc import ABC, abstractmethod


class BaseNormalizer(ABC):


    @abstractmethod
    def normalize(self, product: dict) -> dict:
        """
        convert raw product data into the common
        product structure used by the application.

        """
        pass
