
from datetime import date
from decimal import Decimal

import pytest

from src.transformations.transform_sales import transform_sales_summary


def test_transform_calculates_discount_correctly():
    columns = [
        "order_date",
        "item_count",
        "units_sold",
        "gross_revenue",
        "net_revenue",
    ]

    rows = [
        (
            date(2026, 10, 15),
            100,
            150,
            Decimal("1000.00"),
            Decimal("900.00"),
        )
    ]

    result = transform_sales_summary(columns, rows)

    assert len(result) == 1
    assert result[0]["discount_amount"] == Decimal("100.00")
    assert result[0]["discount_percentage"] == Decimal("10.0000")
    assert result[0]["net_revenue"] == Decimal("900.00")


def test_zero_gross_revenue_produces_zero_discount_percentage():
    columns = [
        "order_date",
        "item_count",
        "units_sold",
        "gross_revenue",
        "net_revenue",
    ]

    rows = [
        (
            date(2026, 10, 15),
            1,
            1,
            Decimal("0.00"),
            Decimal("0.00"),
        )
    ]

    result = transform_sales_summary(columns, rows)

    assert result[0]["discount_percentage"] == Decimal("0")


def test_negative_sales_counts_are_rejected():
    columns = [
        "order_date",
        "item_count",
        "units_sold",
        "gross_revenue",
        "net_revenue",
    ]

    rows = [
        (
            date(2026, 10, 15),
            -1,
            1,
            Decimal("100.00"),
            Decimal("90.00"),
        )
    ]

    with pytest.raises(ValueError, match="Negative sales counts"):
        transform_sales_summary(columns, rows)


def test_missing_revenue_is_rejected():
    columns = [
        "order_date",
        "item_count",
        "units_sold",
        "gross_revenue",
        "net_revenue",
    ]

    rows = [
        (
            date(2026, 10, 15),
            1,
            1,
            None,
            Decimal("90.00"),
        )
    ]

    with pytest.raises(ValueError, match="Missing revenue"):
        transform_sales_summary(columns, rows)


def test_net_revenue_cannot_exceed_gross_revenue():
    columns = [
        "order_date",
        "item_count",
        "units_sold",
        "gross_revenue",
        "net_revenue",
    ]

    rows = [
        (
            date(2026, 10, 15),
            1,
            1,
            Decimal("100.00"),
            Decimal("110.00"),
        )
    ]

    with pytest.raises(ValueError, match="Net revenue exceeds gross"):
        transform_sales_summary(columns, rows)
