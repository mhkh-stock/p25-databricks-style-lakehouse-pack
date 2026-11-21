-- t07: every silver sale line must reference a product in dim_product.
SELECT 'silver sale lines with unknown product: ' || COUNT(*) AS violation
FROM silver_sales
WHERE product_code NOT IN (SELECT product_code FROM dim_product)
HAVING COUNT(*) > 0;
