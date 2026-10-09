"""
SQLAlchemy models — one class per table. This is the Python mirror of the
schema we'd otherwise write as raw CREATE TABLE statements.
"""
from sqlalchemy import Column, String, Integer, Numeric, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)


class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    cost_price = Column(Numeric(12, 2), nullable=False, default=0)
    stock = Column(Integer, nullable=False, default=0)


class Sale(Base):
    __tablename__ = "sales"
    id = Column(String, primary_key=True)
    ts = Column(BigInteger, nullable=False, index=True)
    total = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String, nullable=False, default="Cash")
    customer_name = Column(String, default="")
    customer_phone = Column(String, default="")

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(String, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False, default=0)
    qty = Column(Integer, nullable=False)

    sale = relationship("Sale", back_populates="items")


class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(String, primary_key=True)
    ts = Column(BigInteger, nullable=False, index=True)
    product_id = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(String, primary_key=True)
    ts = Column(BigInteger, nullable=False, index=True)
    description = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    category = Column(String, nullable=False, default="Misc")
