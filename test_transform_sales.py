
from src.extraction.extract_sales import extract_sales_summary
from src.transformations.transform_sales import transform_sales_summary


columns, rows = extract_sales_summary()

transformed_rows = transform_sales_summary(columns, rows)

print(f"Extracted daily records: {len(rows):,}")
print(f"Transformed daily records: {len(transformed_rows):,}")

if len(rows) != len(transformed_rows):
    raise ValueError("Record count changed during transformation.")

print("\nFirst transformed record:")

if transformed_rows:
    print(transformed_rows[0])

print("\nExtraction and transformation completed successfully.")
