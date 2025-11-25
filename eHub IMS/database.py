import sqlite3
import os


class DatabaseManager:
    def __init__(self, db_name="ehub.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        with self.connect() as conn:
            cursor = conn.cursor()

        # PRODUCT TABLE (Holds inventory)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_number TEXT UNIQUE,
                    name TEXT NOT NULL,
                    category TEXT,
                    specs TEXT,
                    color TEXT,
                    storage TEXT,
                    quantity INTEGER,
                    price REAL,
                    status TEXT DEFAULT 'Active'
                )
            """)

        # MIGRATION CHECKING
            cursor.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in cursor.fetchall()]

            if "status" not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN status TEXT DEFAULT 'Active'")

        # INDEXES for speed
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_model ON products(model_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_name ON products(name)")

        # SALES TABLE (Holds transaction history)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    product_name TEXT,
                    quantity_sold INTEGER,
                    total_price REAL,
                    sale_date TIMESTAMP,
                    FOREIGN KEY(product_id) REFERENCES products(id)
                )
            """)
            conn.commit()
