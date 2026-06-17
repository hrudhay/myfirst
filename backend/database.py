from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./restaurant_inventory.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    category = Column(String, default="Other")
    quantity = Column(Float, default=0.0)
    unit = Column(String, default="each")
    cost_per_unit = Column(Float, default=0.0)
    low_stock_threshold = Column(Float, default=10.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sales = relationship("Sale", back_populates="inventory_item")


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, default=0.0)
    parsed_items = Column(Text, default="[]")  # JSON string
    status = Column(String, default="pending")  # pending, confirmed


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True)
    item_name = Column(String, nullable=False)
    quantity_sold = Column(Float, nullable=False)
    unit = Column(String, default="each")
    sale_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, default="")

    inventory_item = relationship("InventoryItem", back_populates="sales")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
