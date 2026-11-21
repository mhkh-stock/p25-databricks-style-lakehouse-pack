-- P25 — silver_sales_enriched.sql (silver model, medallion layer 2)
-- Joins clean sale lines to the product master and adds the economics:
--   cost of goods  = qty * cost_price_pkr   (standard cost from the master)
--   gross profit   = line_total - cost of goods
--   margin_pct     = gross profit / line_total * 100
-- A sale line whose product is missing from the master cannot reach this
-- model (silver_sales already rejects it), so the join is an INNER JOIN
-- on purpose: a silent NULL cost would be worse than a failed build.
-- In real Databricks this enrichment lives in the silver layer too; the
-- gold layer then only conforms it into the star schema (see
-- databricks/mapping.md).

DROP TABLE IF EXISTS silver_sales_enriched;
CREATE TABLE silver_sales_enriched AS
SELECT
    s.sale_line_id,
    s.order_id,
    s.sale_date,
    s.shop_id,
    s.product_code,
    p.product_name,
    p.category,
    p.supplier_id,
    s.qty,
    s.unit_price_pkr,
    s.line_total_pkr,
    p.cost_price_pkr,
    s.qty * p.cost_price_pkr AS cogs_pkr,
    s.line_total_pkr - (s.qty * p.cost_price_pkr) AS gross_profit_pkr,
    ROUND(100.0 * (s.line_total_pkr - (s.qty * p.cost_price_pkr))
          / s.line_total_pkr, 2) AS margin_pct
FROM silver_sales s
INNER JOIN silver_products p
    ON p.product_code = s.product_code;
