import sqlite3
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_name="ehub.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # 1. Product Table (Holds inventory)
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

        # AUTO-MIGRATION (Upgrades old DBs to include 'status')
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN status TEXT DEFAULT 'Active'")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # 2. Sales Table (Holds transaction history)
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
        conn.close()


    # PRODUCT MANAGEMENT
    def add_product(self, model, name, cat, specs, color, storage, qty, price):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO products 
                (model_number, name, category, specs, color, storage, quantity, price, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active')
            """, (model, name, cat, specs, color, storage, qty, price))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Model number duplicate
        finally:
            conn.close()

    def update_product(self, pid, model, name, cat, specs, color, storage, price):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products 
            SET model_number=?, name=?, category=?, specs=?, color=?, storage=?, price=? 
            WHERE id=?""", (model, name, cat, specs, color, storage, price, pid))
        conn.commit()
        conn.close()

    def delete_product(self, product_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        conn.close()

    def fetch_all(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def search_product(self, keyword):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE name LIKE ? OR model_number LIKE ?",
                       ('%' + keyword + '%', '%' + keyword + '%'))
        rows = cursor.fetchall()
        conn.close()
        return rows

    # NEW CATEGORY FEATURES
    def get_unique_categories(self):
        # Returns a list of all unique categories currently in the database.
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Fetch distinct categories, ignore empty ones
        cursor.execute(
            "SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category ASC")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories

    def fetch_by_category(self, category):
        # Returns products that match a specific category.
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE category = ?", (category,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    # STOCK & STATUS LOGIC
    def toggle_product_status(self, product_id, current_status):
        # Switches between Active and Phased Out.
        new_status = "Phased Out" if current_status == "Active" else "Active"
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET status=? WHERE id=?", (new_status, product_id))
        conn.commit()
        conn.close()
        return new_status

    def update_stock(self, product_id, amount_to_add):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET quantity = quantity + ? WHERE id=?", (amount_to_add, product_id))
        conn.commit()
        conn.close()

    # SALES LOGIC
    def record_sale(self, product_id, qty_sold):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Check availability first
        cursor.execute("SELECT quantity, name, price, status FROM products WHERE id=?", (product_id,))
        result = cursor.fetchone()

        if not result: return "Error: Product not found"

        current_stock, name, price_per_unit, status = result

        if status == "Phased Out":
            return "Error: Cannot sell a Phased Out product!"

        if current_stock < qty_sold:
            return f"Error: Not enough stock! Only {current_stock} left."

        # Calculate totals
        total_price = price_per_unit * qty_sold
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # 1. Deduct Stock
            cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id=?", (qty_sold, product_id))

            # 2. Add to Sales History
            cursor.execute("""
                INSERT INTO sales (product_id, product_name, quantity_sold, total_price, sale_date)
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, name, qty_sold, total_price, date_now))

            conn.commit()
            return f"Success! Sold {qty_sold} units."
        except Exception as e:
            return f"Database Error: {e}"
        finally:
            conn.close()

    def fetch_sales_history(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sales ORDER BY sale_date DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows