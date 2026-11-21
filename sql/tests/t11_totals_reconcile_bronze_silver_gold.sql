-- t11: totals must reconcile across all three medallion layers:
-- fact_sales gross = silver_sales gross = clean bronze gross, where
-- "clean bronze" is the bronze total after applying the same four
-- silver guards and keeping the first copy of each duplicate.
-- Returns 1 row if any layer disagrees.
WITH clean_bronze AS (
    SELECT line_total_pkr FROM bronze_sales
    WHERE qty > 0
      AND product_code IN (SELECT product_code FROM bronze_products)
      AND line_total_pkr = qty * unit_price_pkr
      AND raw_line_no IN (
          SELECT MIN(raw_line_no) FROM bronze_sales
          GROUP BY order_id, sale_date, shop_id, product_code,
                   qty, unit_price_pkr, line_total_pkr
      )
)
SELECT 'reconciliation broken: bronze clean '
       || (SELECT SUM(line_total_pkr) FROM clean_bronze)
       || ' vs silver ' || (SELECT SUM(line_total_pkr) FROM silver_sales)
       || ' vs gold ' || (SELECT SUM(line_total_pkr) FROM fact_sales)
       AS violation
WHERE (SELECT SUM(line_total_pkr) FROM clean_bronze)
   <> (SELECT SUM(line_total_pkr) FROM silver_sales)
   OR (SELECT SUM(line_total_pkr) FROM silver_sales)
   <> (SELECT SUM(line_total_pkr) FROM fact_sales);
