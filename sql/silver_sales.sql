-- P25 — silver_sales.sql (silver model, medallion layer 2)
-- Cleans bronze_sales into one row per genuine sale line.
-- Rejects, with the reason recorded in the build log (see
-- src/build_lakehouse.py):
--   1. exact duplicate lines (same order, date, shop, product, qty, prices)
--   2. qty <= 0 (a sale cannot sell zero or a negative amount)
--   3. product_code not in the product master (unknown product)
--   4. line_total_pkr <> qty * unit_price_pkr (wrong line total)
-- Casting: dates kept as TEXT yyyy-mm-dd (SQLite has no DATE type);
-- qty / prices cast to INTEGER so a stray decimal fails loudly, not silently.
-- Grain after this model: one row per sale line. sale_line_id = raw_line_no.
-- In real Databricks this is the bronze -> silver step: a Delta MERGE /
-- overwrite with the same four quality guards (see databricks/mapping.md).

DROP TABLE IF EXISTS silver_sales;
CREATE TABLE silver_sales AS
SELECT
    raw_line_no AS sale_line_id,
    order_id,
    sale_date,
    shop_id,
    product_code,
    CAST(qty AS INTEGER) AS qty,
    CAST(unit_price_pkr AS INTEGER) AS unit_price_pkr,
    CAST(line_total_pkr AS INTEGER) AS line_total_pkr
FROM bronze_sales
WHERE qty > 0
  AND product_code IN (SELECT product_code FROM bronze_products)
  AND line_total_pkr = qty * unit_price_pkr
  -- exact duplicates: keep the first occurrence only (lowest raw_line_no)
  AND raw_line_no IN (
      SELECT MIN(raw_line_no)
      FROM bronze_sales
      GROUP BY order_id, sale_date, shop_id, product_code,
               qty, unit_price_pkr, line_total_pkr
  );
