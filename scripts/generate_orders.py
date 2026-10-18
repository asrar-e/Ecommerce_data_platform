
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from dotenv import load_dotenv
import os
import psycopg
from psycopg import sql


# 1. Database configuration

load_dotenv()

DATABASE = os.getenv("DB_NAME", "ecommerce_data_platform")
HOST = os.getenv("DB_HOST", "localhost")
PORT = int(os.getenv("DB_PORT", "5432"))
USER = os.getenv("DB_USER", "postgres")
PASSWORD = os.getenv("DB_PASSWORD")
# 2. How much data to generate
ORDER_COUNT = 100_000
BATCH_SIZE = 500

random.seed(42)


def money(value):
    """Round a value to two decimal places."""
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def main():
    with psycopg.connect(
        dbname=DATABASE,
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
    ) as conn:

        with conn.cursor() as cur:

            # 3. Load existing customers and products
            cur.execute(
                "SELECT customer_id FROM customer"
            )
            customer_ids = [
                row[0] for row in cur.fetchall()
            ]

            cur.execute(
                """SELECT product_id, price FROM product WHERE is_active = TRUE"""
            )
            products = cur.fetchall()

            if not customer_ids:
                raise ValueError(
                    "No customers found. Generate customers first."
                )

            if not products:
                raise ValueError(
                    "No active products found. Generate products first."
                )

            # 4. Avoid accidentally generating duplicate orders
            cur.execute("SELECT COUNT(*) FROM orders")
            existing_orders = cur.fetchone()[0]

            if existing_orders > 0:
                raise ValueError(
                    f"Orders table already contains "
                    f"{existing_orders:,} rows. "
                    "This script stops to prevent duplicates."
                )

            print(f"Customers available: {len(customer_ids):,}")
            print(f"Active products available: {len(products):,}")

            # 5. Prepare reusable product lookup data
            product_prices = {
                product_id: Decimal(str(price))
                for product_id, price in products
            }
            product_ids = list(product_prices)

            statuses = [
                "DELIVERED",
                "DELIVERED",
                "DELIVERED",
                "SHIPPED",
                "CONFIRMED",
                "PENDING",
                "CANCELLED",
            ]

            channels = [
                "WEBSITE",
                "WEBSITE",
                "MOBILE_APP",
                "MARKETPLACE",
            ]

            # 6. Generate orders in batches
            for start in range(0, ORDER_COUNT, BATCH_SIZE):
                batch_size = min(
                    BATCH_SIZE,
                    ORDER_COUNT - start,
                )

                order_rows = []
                item_rows_by_position = []

                for _ in range(batch_size):
                    customer_id = random.choice(customer_ids)

                    # Keep each product unique within an order.
                    item_count = random.randint(
                        1,
                        min(5, len(product_ids)),
                    )
                    selected_products = random.sample(
                        product_ids,
                        item_count,
                    )

                    order_items = []
                    subtotal = Decimal("0.00")

                    for product_id in selected_products:
                        quantity = random.randint(1, 3)
                        unit_price = product_prices[product_id]

                        subtotal += unit_price * quantity

                        order_items.append(
                            (
                                product_id,
                                quantity,
                                unit_price,
                            )
                        )

                    discount_rate = random.choice(
                        [0, 0, 0, 0.05, 0.10, 0.15]
                    )
                    discount_amount = money(
                        subtotal * Decimal(str(discount_rate))
                    )
                    total_amount = money(
                        subtotal - discount_amount
                    )

                    days_ago = random.randint(0, 730)
                    seconds_ago = random.randint(0, 86399)

                    order_date = (
                        datetime.now(timezone.utc)
                        - timedelta(
                            days=days_ago,
                            seconds=seconds_ago,
                        )
                    )

                    order_rows.append(
                        (
                            customer_id,
                            random.choice(statuses),
                            total_amount,
                            order_date,
                            random.choice(channels),
                            discount_amount,
                        )
                    )

                    item_rows_by_position.append(order_items)

                # 7. Insert order headers and retrieve generated IDs
                placeholders = sql.SQL(", ").join(
                    [sql.SQL("(%s, %s, %s, %s, %s, %s)")]
                    * len(order_rows)
                )

                query = sql.SQL("""
                    INSERT INTO orders (
                        customer_id,
                        order_status,
                        total_amount,
                        order_date,
                        sales_channel,
                        discount_amount
                    )
                    VALUES {}
                    RETURNING order_id
                """).format(placeholders)

                parameters = [
                    value
                    for row in order_rows
                    for value in row
                ]

                cur.execute(query, parameters)
                inserted_order_ids = [
                    row[0] for row in cur.fetchall()
                ]

                # 8. Link each order to its individual products
                item_rows = []

                for order_id, order_items in zip(
                    inserted_order_ids,
                    item_rows_by_position,
                ):
                    for product_id, quantity, unit_price in order_items:
                        item_rows.append(
                            (
                                order_id,
                                product_id,
                                quantity,
                                unit_price,
                            )
                        )

                cur.executemany(
                    """
                    INSERT INTO order_items (
                        order_id,
                        product_id,
                        quantity,
                        unit_price
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    item_rows,
                )

                # Commit each complete batch.
                conn.commit()

                completed = start + batch_size
                print(
                    f"Orders created: {completed:,}/"
                    f"{ORDER_COUNT:,} | "
                    f"Items in this batch: {len(item_rows):,}"
                )

            print("Order and order-item generation complete.")


if __name__ == "__main__":
    main()
