
from src.database import get_connection


def extract_sales_summary():
    query = """
        SELECT
            order_date,
            COUNT(*) AS item_count,
            SUM(quantity) AS units_sold,
            SUM(gross_sales) AS gross_revenue,
            SUM(net_sales) AS net_revenue
        FROM warehouse.fact_sales
        GROUP BY order_date
        ORDER BY order_date;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            columns = [column.name for column in cur.description]

    return columns, rows


if __name__ == "__main__":
    columns, rows = extract_sales_summary()

    print("Columns:", columns)
    print("Number of daily records:", len(rows))
    print("First 5 records:")

    for row in rows[:5]:
        print(row)


    columns, rows = extract_sales_summary()

    print(f"Columns: {columns}")
    print(f"Daily records extracted: {len(rows):,}")

    if not rows:
        raise ValueError("Extraction returned no sales data.")

    invalid_rows = [
        row for row in rows
        if row[1] < 0
        or row[2] < 0
        or row[3] is None
        or row[4] is None
    ]

    if invalid_rows:
        raise ValueError(
            f"Found {len(invalid_rows)} invalid daily summary rows."
        )

    print("Basic data-quality check passed.")
    print("First 5 records:")

    for row in rows[:5]:
        print(row)
