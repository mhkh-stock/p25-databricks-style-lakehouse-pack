-- t02: bronze sales must contain exactly 3 lines with qty <= 0 (planted).
-- Returns 1 row if the count differs.
SELECT 'bronze sale lines with qty <= 0: expected 3, found '
       || (SELECT COUNT(*) FROM bronze_sales WHERE qty <= 0) AS violation
WHERE (SELECT COUNT(*) FROM bronze_sales WHERE qty <= 0) <> 3;
