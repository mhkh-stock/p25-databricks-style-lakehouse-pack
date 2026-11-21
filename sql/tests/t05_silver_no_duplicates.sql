-- t05: silver_sales must contain no duplicate lines.
-- Returns 1 row per duplicated line group.
SELECT order_id, sale_date, shop_id, product_code, qty,
       unit_price_pkr, line_total_pkr, COUNT(*) AS n
FROM silver_sales
GROUP BY 1, 2, 3, 4, 5, 6, 7
HAVING COUNT(*) > 1;
