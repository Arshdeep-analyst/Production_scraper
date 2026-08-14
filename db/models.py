from datetime import datetime, UTC

from sqlalchemy import Float,String,Text,DateTime,Integer
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Product(Base):

    __tablename__ = "client_products"

    ## primary key ## (for now , later maybe asin, or some unique product id)

    id: Mapped[int] = mapped_column(

        Integer,
        primary_key=True,
        autoincrement=True,
    )

    source_site: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )

    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    stock: Mapped[int|None] = mapped_column(
        Integer,
        nullable=True,
    )

    product_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    source_product_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    brand: Mapped[str|None] = mapped_column(
        String(255),
        nullable=True,
    )

    image_url: Mapped[str|None] = mapped_column(
        String(1000),
        nullable=True,
    )

    rating: Mapped[float|None] = mapped_column(
        Float,
        nullable=True,
    )

    currency: Mapped[str|None] = mapped_column(
        String(20),
        nullable=True
    )

    country_of_origin: Mapped[str|None] = mapped_column(
        String(100),
        nullable=True,
    )


    ## Audit fields

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    
