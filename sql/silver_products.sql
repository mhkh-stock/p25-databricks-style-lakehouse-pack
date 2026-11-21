-- P25 — silver_products.sql (silver model, medallion layer 2)
-- Cleans bronze_products (the product master). Guards: cost price must be
-- positive and the sell price must not be below cost — a master row that
-- fails either guard is rejected, not loaded, so a bad master can never
-- produce a negative margin downstream. The SAMPLE master is clean, so
-- all 36 products pass.
-- In real Databricks this is the bronze -> silver step for the reference
-- feed (see databricks/mapping.md).

DROP TABLE IF EXISTS silver_products;
CREATE TABLE silver_products AS
SELECT
    product_code,
    product_name,
    category,
    supplier_id,
    unit,
    CAST(cost_price_pkr AS INTEGER) AS cost_price_pkr,
    CAST(sell_price_pkr AS INTEGER) AS sell_price_pkr
FROM bronze_products
WHERE cost_price_pkr > 0
  AND sell_price_pkr >= cost_price_pkr;
