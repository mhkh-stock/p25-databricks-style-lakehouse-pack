-- t15: inventory stock must never be negative, and the stock value
-- must equal stock qty x cost price for every product.
SELECT 'inventory rows with negative stock or wrong value: ' || COUNT(*)
       AS violation
FROM mart_inventory
WHERE stock_qty < 0
   OR stock_value_pkr <> stock_qty * (
       SELECT cost_price_pkr FROM dim_product
       WHERE dim_product.product_code = mart_inventory.product_code)
HAVING COUNT(*) > 0;
