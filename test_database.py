
from src.database import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                current_database(),
                current_user,
                version()
        """)

        result = cur.fetchone()

        print("Database:", result[0])
        print("User:", result[1])
        print("PostgreSQL:", result[2].split(",")[0])
from src.database import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) AS total_sales_rows,
                SUM(gross_sales) AS gross_revenue,
                SUM(net_sales) AS net_revenue
            FROM warehouse.fact_sales;
        """)

        result = cur.fetchone()

        print(f"Fact rows: {result[0]:,}")
        print(f"Gross revenue: {result[1]:,.2f}")
        print(f"Net revenue: {result[2]:,.2f}")
