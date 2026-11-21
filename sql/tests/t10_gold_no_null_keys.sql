-- t10: fact_sales must have no NULL keys or amounts.
SELECT 'fact_sales rows with NULL keys: ' || COUNT(*) AS violation
FROM fact_sales
WHERE order_id IS NULL OR sale_date IS NULL OR shop_id IS NULL
   OR product_code IS NULL OR qty IS NULL OR line_total_pkr IS NULL
HAVING COUNT(*) > 0;
