
import random
import os
from dotenv import load_dotenv
import getpass

import psycopg
from faker import Faker

# Reproducible data: rerunning with the same seed
# produces the same generated customer/product attributes.
random.seed(42)
fake = Faker("en_US")
Faker.seed(42)

load_dotenv()

DATABASE = os.getenv("DB_NAME", "ecommerce_data_platform")
HOST = os.getenv("DB_HOST", "localhost")
PORT = int(os.getenv("DB_PORT", "5432"))
USER = os.getenv("DB_USER", "postgres")
PASSWORD = os.getenv("DB_PASSWORD")

CUSTOMER_COUNT = 10_000
PRODUCT_COUNT = 2_000

CITIES = [
    "Dubai", "Abu Dhabi", "Sharjah", "Ajman",
    "Al Ain", "Ras Al Khaimah", "Fujairah",
    "Umm Al Quwain",
]

SEGMENTS = ["STANDARD", "SILVER", "GOLD", "PLATINUM"]
SEGMENT_WEIGHTS = [55, 25, 15, 5]

CATALOG = {
    "Electronics": {
        "brands": ["Samsung", "Sony", "Anker", "Apple"],
        "products": [
            "Wireless Headphones", "Bluetooth Speaker",
            "USB-C Charger", "Power Bank", "Smart Watch",
            "Wireless Mouse", "Mechanical Keyboard",
            "4K Monitor", "Webcam", "Tablet",
        ],
        "price_range": (39, 6500),
    },
    "Home Appliances": {
        "brands": ["Philips", "LG", "Samsung", "Tefal"],
        "products": [
            "Air Fryer", "Coffee Machine", "Vacuum Cleaner",
            "Blender", "Electric Kettle", "Rice Cooker",
            "Microwave Oven", "Steam Iron",
        ],
        "price_range": (49, 3500),
    },
    "Fashion": {
        "brands": ["Nike", "Adidas", "Puma", "Levi's"],
        "products": [
            "Running Shoes", "Casual T-Shirt", "Jeans",
            "Sports Jacket", "Backpack", "Training Shorts",
        ],
        "price_range": (39, 1200),
    },
    "Beauty": {
        "brands": ["Nivea", "L'Oreal", "Dove", "Neutrogena"],
        "products": [
            "Face Moisturizer", "Sunscreen SPF 50",
            "Shampoo", "Body Lotion", "Face Cleanser",
            "Hair Conditioner",
        ],
        "price_range": (15, 350),
    },
    "Sports": {
        "brands": ["Nike", "Adidas", "Puma", "Wilson"],
        "products": [
            "Yoga Mat", "Football", "Dumbbell Set",
            "Tennis Racket", "Resistance Bands",
            "Running Bottle",
        ],
        "price_range": (25, 900),
    },
}

def connect():
    password = getpass.getpass("PostgreSQL password: ")
    return psycopg.connect(
        host=HOST,
        port=PORT,
        dbname=DATABASE,
        user=USER,
        password=password,
    )

def generate_customers(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM customer")
        existing = cur.fetchone()[0]

        if existing:
            print(
                f"Customers table already has {existing:,} rows. "
                "Skipping to prevent duplicate generation."
            )
            return

        rows = []
        used_emails = set()

        for _ in range(CUSTOMER_COUNT):
            first_name = fake.first_name()
            last_name = fake.last_name()

            # Unique email addresses satisfy the database constraint.
            while True:
                email = fake.unique.email().lower()
                if email not in used_emails:
                    used_emails.add(email)
                    break

            rows.append((
                first_name,
                last_name,
                email,
                fake.numerify("+9715########"),
                "United Arab Emirates",
                random.choice(CITIES),
                random.choices(
                    SEGMENTS, weights=SEGMENT_WEIGHTS, k=1
                )[0],
                random.random() < 0.65,
                fake.date_time_between(
                    start_date="-4y",
                    end_date="now",
                    tzinfo=__import__("datetime").timezone.utc,
                ),
            ))

            if len(rows) >= 1000:
                cur.executemany(
                    """
                    INSERT INTO customer (
                        first_name, last_name, email, phone,
                        country, city, customer_segment,
                        marketing_opt_in, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    rows,
                )
                rows.clear()

        if rows:
            cur.executemany(
                """
                INSERT INTO customer (
                    first_name, last_name, email, phone,
                    country, city, customer_segment,
                    marketing_opt_in, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                rows,
            )

    conn.commit()
    print(f"Inserted {CUSTOMER_COUNT:,} customer.")

def generate_products(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM product")
        existing = cur.fetchone()[0]

        if existing:
            print(
                f"Product table already has {existing:,} rows. "
                "Skipping to prevent duplicate generation."
            )
            return

        rows = []

        for number in range(1, PRODUCT_COUNT + 1):
            category = random.choice(list(CATALOG.keys()))
            details = CATALOG[category]

            base_name = random.choice(details["products"])
            brand = random.choice(details["brands"])
            price_min, price_max = details["price_range"]

            price = round(
                random.uniform(price_min, price_max), 2
            )
            # Product costs are below selling prices.
            cost_price = round(
                price * random.uniform(0.50, 0.85), 2
            )

            rows.append((
                f"{brand} {base_name} Model {number:04d}",
                category,
                price,
                random.choices(
                    [0, random.randint(1, 25),
                     random.randint(26, 500)],
                    weights=[3, 17, 80],
                    k=1,
                )[0],
                random.random() > 0.04,
                f"UAE-{number:06d}",
                brand,
                cost_price,
            ))

            if len(rows) >= 500:
                cur.executemany(
                    """
                    INSERT INTO product (
                        product_name, category, price,
                        stock_quantity, is_active, sku,
                        brand, cost_price
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    rows,
                )
                rows.clear()

        if rows:
            cur.executemany(
                """
                INSERT INTO product (
                    product_name, category, price,
                    stock_quantity, is_active, sku,
                    brand, cost_price
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                rows,
            )

    conn.commit()
    print(f"Inserted {PRODUCT_COUNT:,} products.")

def main():
    with connect() as conn:
        print(f"Connected to database: {DATABASE}")
        generate_customers(conn)
        generate_products(conn)

        with conn.cursor() as cur:
            cur.execute("""
                SELECT 'customer' AS table_name, COUNT(*) AS rows
                FROM customer
                UNION ALL
                SELECT 'product', COUNT(*)
                FROM product
            """)
            print("\nCurrent record counts:")
            for table_name, count in cur.fetchall():
                print(f"{table_name}: {count:,}")

if __name__ == "__main__":
    main()
