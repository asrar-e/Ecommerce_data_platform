
from decimal import Decimal


def transform_sales_summary(columns, rows):
    """
    Convert extracted daily sales rows into structured records
    and calculate discount metrics.
    """

    transformed_rows = []

    for row in rows:
        record = dict(zip(columns, row))

        order_date = record["order_date"]
        item_count = record["item_count"]
        units_sold = record["units_sold"]
        gross_revenue = record["gross_revenue"]
        net_revenue = record["net_revenue"]

        # Validate the extracted data.
        if item_count < 0 or units_sold < 0:
            raise ValueError(
                f"Negative sales counts found for {order_date}"
            )

        if gross_revenue is None or net_revenue is None:
            raise ValueError(
                f"Missing revenue values for {order_date}"
            )

        if gross_revenue < net_revenue:
            raise ValueError(
                f"Net revenue exceeds gross revenue for {order_date}"
            )

        # Calculate discounts from the revenue difference.
        discount_amount = gross_revenue - net_revenue

        if gross_revenue > 0:
            discount_percentage = (
                discount_amount / gross_revenue
            ) * Decimal("100")
        else:
            discount_percentage = Decimal("0")

        # Build the transformed record.
        transformed_record = {
            "order_date": order_date,
            "item_count": item_count,
            "units_sold": units_sold,
            "gross_revenue": gross_revenue,
            "discount_amount": discount_amount,
            "discount_percentage": discount_percentage,
            "net_revenue": net_revenue,
        }

        transformed_rows.append(transformed_record)

    return transformed_rows
