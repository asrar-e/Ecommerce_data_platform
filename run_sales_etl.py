
import logging

from src.logging_config import configure_logging
from src.extraction.extract_sales import extract_sales_summary
from src.transformations.transform_sales import transform_sales_summary
from src.loading.load_sales import load_sales_summary
from src.quality.reconcile_sales import reconcile_sales_summary


configure_logging()
logger = logging.getLogger("sales_etl")


def run_pipeline():
    logger.info("Sales ETL pipeline started")

    try:
        logger.info("Extracting sales data")
        columns, rows = extract_sales_summary()
        logger.info("Extracted %s daily records", len(rows))

        logger.info("Transforming sales data")
        transformed_rows = transform_sales_summary(columns, rows)
        logger.info("Transformed %s daily records", len(transformed_rows))

        if len(rows) != len(transformed_rows):
            raise ValueError("Record count changed during transformation")

        logger.info("Loading daily sales summaries")
        loaded_count = load_sales_summary(transformed_rows)
        logger.info("Loaded or updated %s daily records", loaded_count)

        logger.info("Reconciling source and reporting totals")
        checks = reconcile_sales_summary()

        for name, values in checks.items():
            logger.info(
                "Reconciliation passed: %s | source=%s | summary=%s",
                name,
                values[0],
                values[1],
            )

        logger.info("Sales ETL pipeline completed successfully")

    except Exception:
        logger.exception("Sales ETL pipeline failed")
        raise


if __name__ == "__main__":
    run_pipeline()
