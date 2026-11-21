-- P25 — silver_purchases.sql (silver model, medallion layer 2)
-- Cleans bronze_purchases. The SAMPLE purchase file has no planted defects,
-- so this model is a pass-through with the same guards as silver_sales:
-- qty must be positive, the product must exist in the master, and the
-- total must equal qty * unit cost. Any line failing a guard is rejected
-- and counted in the build log instead of silently loaded.
-- In real Databricks this is the bronze -> silver step for the purchase
-- feed (see databricks/mapping.md).

DROP TABLE IF EXISTS silver_purchases;
CREATE TABLE silver_purchases AS
SELECT
    raw_line_no AS po_line_id,
    po_id,
    purchase_date,
    supplier_id,
    product_code,
    CAST(qty AS INTEGER) AS qty,
    CAST(unit_cost_pkr AS INTEGER) AS unit_cost_pkr,
    CAST(total_cost_pkr AS INTEGER) AS total_cost_pkr
FROM bronze_purchases
WHERE qty > 0
  AND product_code IN (SELECT product_code FROM bronze_products)
  AND total_cost_pkr = qty * unit_cost_pkr;
