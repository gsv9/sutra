# database.py
# Creates and manages the SQLite database for SUTRA
# All data is stored locally on the Snapdragon PC

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

# Create the database engine
# This connects Python to the SQLite file
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Base class that all our table classes will inherit from
Base = declarative_base()

# Session factory — used to read/write to database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ─── TABLE 1: INVENTORY ───────────────────────────────────────
class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, unique=True, index=True)
    current_weight = Column(Float)
    reorder_threshold = Column(Float)
    unit = Column(String)
    last_updated = Column(DateTime, default=datetime.now)


# ─── TABLE 2: SUPPLIERS ───────────────────────────────────────
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String)
    item = Column(String)
    price_per_unit = Column(Float)
    reliability_score = Column(Float)  # 0 to 100
    lead_time_days = Column(Integer)
    last_updated = Column(DateTime, default=datetime.now)


# ─── TABLE 3: SALES HISTORY ───────────────────────────────────
class SalesHistory(Base):
    __tablename__ = "sales_history"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(String)
    date = Column(String)  # stored as "YYYY-MM-DD"
    quantity_sold = Column(Float)
    revenue = Column(Float)


# ─── TABLE 4: PROCUREMENT ORDERS ──────────────────────────────
class ProcurementOrder(Base):
    __tablename__ = "procurement_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String, unique=True)
    item = Column(String)
    quantity = Column(Float)
    supplier = Column(String)
    unit_price = Column(Float)
    total_cost = Column(Float)
    savings = Column(Float)
    status = Column(String, default="pending_approval")
    reasoning = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    expected_delivery = Column(String)


# ─── HELPER FUNCTION: GET DATABASE SESSION ────────────────────
def get_db():
    # Opens a database session, yields it, then closes it
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── HELPER FUNCTION: CREATE ALL TABLES ───────────────────────
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully")


# ─── HELPER FUNCTION: SEED DEMO DATA ─────────────────────────
def seed_demo_data():
    # Adds starting data so demo works immediately
    db = SessionLocal()

    # Check if data already exists
    if db.query(Inventory).count() > 0:
        print("Demo data already exists — skipping")
        db.close()
        return

    # Add inventory items
    inventory_items = [
        Inventory(item_name="Rice", current_weight=10.0,
                  reorder_threshold=5.0, unit="kg"),
        Inventory(item_name="Sugar", current_weight=8.0,
                  reorder_threshold=3.0, unit="kg"),
        Inventory(item_name="Oil", current_weight=6.0,
                  reorder_threshold=2.0, unit="L"),
    ]
    db.add_all(inventory_items)

    # Add suppliers
    suppliers = [
        Supplier(supplier_name="ABC Traders", item="Rice",
                 price_per_unit=42.0, reliability_score=97.0,
                 lead_time_days=1),
        Supplier(supplier_name="XYZ Wholesale", item="Rice",
                 price_per_unit=44.0, reliability_score=78.0,
                 lead_time_days=3),
        Supplier(supplier_name="ABC Traders", item="Sugar",
                 price_per_unit=38.0, reliability_score=97.0,
                 lead_time_days=1),
        Supplier(supplier_name="Fresh Oils Co", item="Oil",
                 price_per_unit=85.0, reliability_score=90.0,
                 lead_time_days=2),
    ]
    db.add_all(suppliers)

    # Add sample sales history for last 7 days
    sales = [
        SalesHistory(item="Rice", date="2026-07-10",
                     quantity_sold=12.0, revenue=504.0),
        SalesHistory(item="Rice", date="2026-07-09",
                     quantity_sold=15.0, revenue=630.0),
        SalesHistory(item="Rice", date="2026-07-08",
                     quantity_sold=11.0, revenue=462.0),
        SalesHistory(item="Rice", date="2026-07-07",
                     quantity_sold=18.0, revenue=756.0),
        SalesHistory(item="Rice", date="2026-07-06",
                     quantity_sold=22.0, revenue=924.0),
        SalesHistory(item="Sugar", date="2026-07-10",
                     quantity_sold=5.0, revenue=190.0),
        SalesHistory(item="Oil", date="2026-07-10",
                     quantity_sold=3.0, revenue=255.0),
    ]
    db.add_all(sales)

    db.commit()
    db.close()
    print("Demo data seeded successfully")


# ─── RUN THIS FILE DIRECTLY TO TEST ───────────────────────────
if __name__ == "__main__":
    create_tables()
    seed_demo_data()
    print("Database ready!")