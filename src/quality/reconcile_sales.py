
from src.database import get_connection


def reconcile_sales_summary():
    query = """
        SELECT
            (SELECT COUNT(*)
             FROM warehouse.fact_sales) AS source_rows,

            (SELECT COALESCE(SUM(item_count), 0)
             FROM warehouse.daily_sales_summary) AS summary_rows,

            (SELECT COALESCE(SUM(quantity), 0)
             FROM warehouse.fact_sales) AS source_units,

            (SELECT COALESCE(SUM(units_sold), 0)
             FROM warehouse.daily_sales_summary) AS summary_units,

            (SELECT COALESCE(SUM(gross_sales), 0)
             FROM warehouse.fact_sales) AS source_gross,

            (SELECT COALESCE(SUM(gross_revenue), 0)
             FROM warehouse.daily_sales_summary) AS summary_gross,

            (SELECT COALESCE(SUM(net_sales), 0)
             FROM warehouse.fact_sales) AS source_net,

            (SELECT COALESCE(SUM(net_revenue), 0)
             FROM warehouse.daily_sales_summary) AS summary_net;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            result = cur.fetchone()

    checks = {
        "row count": (result[0], result[1]),
        "units sold": (result[2], result[3]),
        "gross revenue": (result[4], result[5]),
        "net revenue": (result[6], result[7]),
    }

    failures = {
        name: values
        for name, values in checks.items()
        if values[0] != values[1]
    }

    if failures:
        raise ValueError(
            f"Sales reconciliation failed: {failures}"
        )

    return checks
