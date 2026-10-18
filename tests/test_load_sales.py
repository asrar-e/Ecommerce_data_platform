
from pathlib import Path


def test_load_uses_upsert_to_prevent_duplicate_dates():
    project_root = Path(__file__).resolve().parent.parent
    load_file = project_root / "src" / "loading" / "load_sales.py"

    sql_source = load_file.read_text(encoding="utf-8").upper()

    assert "ON CONFLICT (ORDER_DATE)" in sql_source
    assert "DO UPDATE SET" in sql_source
    assert "REFRESHED_AT = CURRENT_TIMESTAMP" in sql_source


def test_load_rejects_empty_input():
    import pytest

    from src.loading.load_sales import load_sales_summary

    with pytest.raises(ValueError, match="No transformed sales records"):
        load_sales_summary([])
