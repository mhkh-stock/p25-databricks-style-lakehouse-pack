-- t09: fact_sales grain — one fact row per silver sale line.
SELECT 'fact_sales rows: expected ' || (SELECT COUNT(*) FROM silver_sales)
       || ', found ' || (SELECT COUNT(*) FROM fact_sales) AS violation
WHERE (SELECT COUNT(*) FROM fact_sales) <> (SELECT COUNT(*) FROM silver_sales);
