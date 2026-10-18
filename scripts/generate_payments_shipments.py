
import os
import random
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv


# 1. Load database settings from the project's .env file.
load_dotenv()

DATABASE = os.getenv("DB_NAME", "ecommerce_data_platform")
HOST = os.getenv("DB_HOST", "localhost")
PORT = int(os.getenv("DB_PORT", "5432"))
USER = os.getenv("DB_USER", "postgres")
PASSWORD = os.getenv("DB_PASSWORD")

BATCH_SIZE = 500
random.seed(42)

PAYMENT_METHODS = [
    "CARD",
    "UPI",
    "BANK_TRANSFER",
    "CASH_ON_DELIVERY",
    "WALLET",
]

CARRIERS = ["Aramex", "DHL", "Emirates Post", "iMile"]

UAE_STREETS = [
    "Sheikh Zayed Road",
    "Al Wasl Road",
    "Khalifa Street",
    "Al Khail Road",
    "Corniche Road",
]


def capped_timestamp(timestamp, now):
    """Ensure a generated event timestamp is not in the future."""
    return min(timestamp, now)


def main():
    now = datetime.now(timezone.utc)

    with psycopg.connect(
        dbname=DATABASE,
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
    ) as conn:

        with conn.cursor() as cur:

            # 2. Prevent accidental duplicate generation.
            cur.execute("SELECT COUNT(*) FROM payments")
            existing_payments = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM shipments")
            existing_shipments = cur.fetchone()[0]

            if existing_payments or existing_shipments:
                raise ValueError(
                    "Payments or shipments already exist. "
                    "Stopping to avoid duplicate records."
                )

            # 3. Read the order and customer information we need.
            cur.execute("""
                SELECT
                    o.order_id,
                    o.order_status,
                    o.total_amount,
                    o.order_date,
                    c.city,
                    c.country
                FROM orders AS o
                JOIN customer AS c
                    ON c.customer_id = o.customer_id
                ORDER BY o.order_id
            """)

            orders = cur.fetchall()

            if not orders:
                raise ValueError(
                    "No orders found. Generate orders first."
                )

            print(f"Orders to process: {len(orders):,}")

            # 4. Process the orders in batches.
            for start in range(0, len(orders), BATCH_SIZE):
                batch = orders[start:start + BATCH_SIZE]

                payment_rows = []
                shipment_rows = []

                for (
                    order_id,
                    order_status,
                    total_amount,
                    order_date,
                    city,
                    country,
                ) in batch:

                    # 5. Assign a payment status consistent
                    # with the order's current status.
                    if order_status in ("DELIVERED", "SHIPPED", "CONFIRMED"):
                        payment_status = "SUCCESS"

                    elif order_status == "PENDING":
                        payment_status = random.choices(
                            ["PENDING", "SUCCESS", "FAILED"],
                            weights=[50, 35, 15],
                            k=1,
                        )[0]

                    else:  # CANCELLED
                        payment_status = random.choice(
                            ["REFUNDED", "FAILED"]
                        )

                    payment_method = random.choice(PAYMENT_METHODS)

                    paid_at = None
                    transaction_reference = None

                    if payment_status in ("SUCCESS", "REFUNDED"):
                        paid_at = capped_timestamp(
                            order_date
                            + timedelta(
                                minutes=random.randint(1, 60)
                            ),
                            now,
                        )
                        transaction_reference = (
                            f"PAY-{order_id:09d}"
                        )

                    payment_rows.append(
                        (
                            order_id,
                            payment_method,
                            payment_status,
                            total_amount,
                            transaction_reference,
                            paid_at,
                        )
                    )

                    # 6. Cancelled orders do not get shipments.
                    if order_status == "CANCELLED":
                        continue

                    # 7. Map order status to shipment status.
                    if order_status == "DELIVERED":
                        shipment_status = "DELIVERED"
                    elif order_status == "SHIPPED":
                        shipment_status = random.choice(
                            ["SHIPPED", "IN_TRANSIT"]
                        )
                    else:
                        shipment_status = "PENDING"

                    shipped_at = None
                    delivered_at = None
                    carrier = None
                    tracking_number = None

                    if shipment_status != "PENDING":
                        carrier = random.choice(CARRIERS)
                        tracking_number = (
                            f"TRK-{order_id:09d}"
                        )
                        shipped_at = capped_timestamp(
                            order_date
                            + timedelta(
                                hours=random.randint(2, 24)
                            ),
                            now,
                        )

                    if shipment_status == "DELIVERED":
                        delivered_at = capped_timestamp(
                            shipped_at
                            + timedelta(
                                days=random.randint(1, 5)
                            ),
                            now,
                        )

                    delivery_city = city or "Dubai"
                    delivery_country = country or "United Arab Emirates"
                    street = random.choice(UAE_STREETS)
                    building = random.randint(1, 200)

                    shipping_address = (
                        f"Building {building}, {street}, "
                        f"{delivery_city}"
                    )

                    shipment_rows.append(
                        (
                            order_id,
                            shipping_address,
                            delivery_city,
                            delivery_country,
                            carrier,
                            tracking_number,
                            shipment_status,
                            shipped_at,
                            delivered_at,
                        )
                    )

                # 8. Insert payment records.
                cur.executemany(
                    """
                    INSERT INTO payments (
                        order_id,
                        payment_method,
                        payment_status,
                        amount,
                        transaction_reference,
                        paid_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    payment_rows,
                )

                # 9. Insert shipment records.
                cur.executemany(
                    """
                    INSERT INTO shipments (
                        order_id,
                        shipping_address,
                        city,
                        country,
                        carrier,
                        tracking_number,
                        shipment_status,
                        shipped_at,
                        delivered_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    shipment_rows,
                )

                # Commit both sets of records together.
                conn.commit()

                completed = start + len(batch)
                print(
                    f"Orders processed: {completed:,}/"
                    f"{len(orders):,} | "
                    f"Payments: {len(payment_rows):,} | "
                    f"Shipments: {len(shipment_rows):,}"
                )

            print("Payment and shipment generation complete.")


if __name__ == "__main__":
    main()
