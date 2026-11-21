-- P25 — gold_facts.sql (gold model, medallion layer 3)
-- Loads fact_sales from the enriched silver model and fact_purchases
-- from silver_purchases.
-- Grain: fact_sales is one row per clean sale line
-- (sale_line_id = raw_line_no); fact_purchases is one row per
-- purchase-order line (po_line_id = raw_line_no). fact_sales is the
-- table the business queries: revenue, gross profit and margin by
-- product, category, shop, supplier or month.
-- In real Databricks these are gold Delta tables; the load here is an
-- overwrite of the gold table from silver (see databricks/mapping.md).

INSERT INTO fact_sales
    (sale_line_id, order_id, sale_date, shop_id, product_code,
     qty, unit_price_pkr, line_total_pkr, cost_price_pkr,
     gross_profit_pkr, margin_pct)
SELECT
    sale_line_id, order_id, sale_date, shop_id, product_code,
    qty, unit_price_pkr, line_total_pkr, cost_price_pkr,
    gross_profit_pkr, margin_pct
FROM silver_sales_enriched;

-- fact_purchases loads here too (same gold step, one load per fact).
INSERT INTO fact_purchases
    (po_line_id, po_id, purchase_date, supplier_id, product_code,
     qty, unit_cost_pkr, total_cost_pkr)
SELECT
    po_line_id, po_id, purchase_date, supplier_id, product_code,
    qty, unit_cost_pkr, total_cost_pkr
FROM silver_purchases;
