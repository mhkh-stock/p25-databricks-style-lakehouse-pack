-- t01: bronze sales must contain exactly 2 duplicate lines (planted).
-- Returns 1 row if the count differs.
WITH dup AS (
    SELECT order_id, sale_date, shop_id, product_code, qty,
           unit_price_pkr, line_total_pkr
    FROM bronze_sales
    GROUP BY 1, 2, 3, 4, 5, 6, 7
    HAVING COUNT(*) > 1
)
SELECT 'duplicate bronze sale lines: expected 2, found '
       || (SELECT COUNT(*) FROM dup) AS violation
WHERE (SELECT COUNT(*) FROM dup) <> 2;
