-- P25 — gold_marts.sql (gold models, medallion layer 3)
-- The four marts the business actually queries. Each one is a plain
-- SELECT over the gold facts and dimensions, so any of them can be
-- re-pointed at a real Databricks gold table without changing the
-- business logic (see databricks/mapping.md).

-- mart_sales_by_category: lines, units, gross, profit and margin per category.
DROP TABLE IF EXISTS mart_sales_by_category;
CREATE TABLE mart_sales_by_category AS
SELECT
    p.category,
    COUNT(*) AS lines,
    SUM(f.qty) AS units_sold,
    SUM(f.line_total_pkr) AS gross_pkr,
    SUM(f.gross_profit_pkr) AS gross_profit_pkr,
    ROUND(100.0 * SUM(f.gross_profit_pkr) / SUM(f.line_total_pkr), 2) AS margin_pct
FROM fact_sales f
INNER JOIN dim_product p ON p.product_code = f.product_code
GROUP BY p.category;

-- mart_sales_by_month: lines, units, gross and profit per month.
DROP TABLE IF EXISTS mart_sales_by_month;
CREATE TABLE mart_sales_by_month AS
SELECT
    substr(f.sale_date, 1, 7) AS month,
    COUNT(*) AS lines,
    SUM(f.qty) AS units_sold,
    SUM(f.line_total_pkr) AS gross_pkr,
    SUM(f.gross_profit_pkr) AS gross_profit_pkr
FROM fact_sales f
GROUP BY month;

-- mart_inventory: stock on hand per product: everything bought minus
-- everything sold.
--   stock_qty   = purchased_qty - sold_qty
--   stock_value = stock_qty * cost_price_pkr  (standard cost from dim_product)
-- Status rule (stated, not hidden): stock below 10% of what was bought
-- in the period is LOW — reorder. Stock of zero or less is OUT.
-- The SAMPLE data was built so purchases cover sales for every product,
-- so a negative stock here means the load is wrong, and test t15 fails.
DROP TABLE IF EXISTS mart_inventory;
CREATE TABLE mart_inventory AS
SELECT
    p.product_code,
    p.product_name,
    p.category,
    p.supplier_id,
    COALESCE(pur.purchased_qty, 0) AS purchased_qty,
    COALESCE(s.sold_qty, 0) AS sold_qty,
    COALESCE(pur.purchased_qty, 0) - COALESCE(s.sold_qty, 0) AS stock_qty,
    (COALESCE(pur.purchased_qty, 0) - COALESCE(s.sold_qty, 0))
        * p.cost_price_pkr AS stock_value_pkr,
    CASE
        WHEN COALESCE(pur.purchased_qty, 0) - COALESCE(s.sold_qty, 0) <= 0 THEN 'OUT'
        WHEN COALESCE(pur.purchased_qty, 0) - COALESCE(s.sold_qty, 0)
             < 0.10 * COALESCE(pur.purchased_qty, 0) THEN 'LOW'
        ELSE 'OK'
    END AS stock_status
FROM dim_product p
LEFT JOIN (
    SELECT product_code, SUM(qty) AS purchased_qty
    FROM fact_purchases GROUP BY product_code
) pur ON pur.product_code = p.product_code
LEFT JOIN (
    SELECT product_code, SUM(qty) AS sold_qty
    FROM fact_sales GROUP BY product_code
) s ON s.product_code = p.product_code;

-- mart_supplier_spend: spend per supplier — total purchase cost, number of
-- purchase orders, distinct products supplied, and share of total spend.
-- Answers "who do we depend on?" — the supplier with the biggest share
-- is the one whose failure hurts most.
DROP TABLE IF EXISTS mart_supplier_spend;
CREATE TABLE mart_supplier_spend AS
SELECT
    f.supplier_id,
    d.supplier_name,
    COUNT(*) AS po_lines,
    COUNT(DISTINCT f.po_id) AS po_count,
    COUNT(DISTINCT f.product_code) AS products_supplied,
    SUM(f.total_cost_pkr) AS total_spend_pkr,
    ROUND(100.0 * SUM(f.total_cost_pkr)
          / (SELECT SUM(total_cost_pkr) FROM fact_purchases), 2) AS share_pct
FROM fact_purchases f
INNER JOIN dim_supplier d ON d.supplier_id = f.supplier_id
GROUP BY f.supplier_id, d.supplier_name;
