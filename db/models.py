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
        default=None
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
    




"""
ADD THIS CLASS to your existing db/models.py (alongside Product).
Do not create this as a separate file in your real project -- it
needs to share the same Base as Product so create_all() picks it up
in one call.

This is a NEW table, so unlike the 'stock' column fix earlier, no
ALTER TABLE is needed -- create_all() creates missing tables
automatically without touching existing ones. Just run your normal
init step after adding this class:

    uv run python -m db.init_db
""" 


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    site: Mapped[str] = mapped_column(String(50), nullable=False)
    query: Mapped[str] = mapped_column(String(255), nullable=False)

    # "running" -> "success" -> or "failed"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")

    product_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )