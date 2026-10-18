
from src.database import get_connection


def load_sales_summary(rows):
    if not rows:
        raise ValueError("No transformed sales records to load.")

    query = """
        INSERT INTO warehouse.daily_sales_summary (
            order_date,
            item_count,
            units_sold,
            gross_revenue,
            discount_amount,
            discount_percentage,
            net_revenue,
            refreshed_at
        )
        VALUES (
            %(order_date)s,
            %(item_count)s,
            %(units_sold)s,
            %(gross_revenue)s,
            %(discount_amount)s,
            %(discount_percentage)s,
            %(net_revenue)s,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (order_date)
        DO UPDATE SET
            item_count = EXCLUDED.item_count,
            units_sold = EXCLUDED.units_sold,
            gross_revenue = EXCLUDED.gross_revenue,
            discount_amount = EXCLUDED.discount_amount,
            discount_percentage = EXCLUDED.discount_percentage,
            net_revenue = EXCLUDED.net_revenue,
            refreshed_at = CURRENT_TIMESTAMP;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(query, rows)

    return len(rows)
