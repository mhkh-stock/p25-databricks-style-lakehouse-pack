-- t03: bronze sales must contain exactly 2 lines with an unknown
-- product code (planted: PRD-997, PRD-998).
-- Returns 1 row if the count differs.
SELECT 'bronze sale lines with unknown product: expected 2, found '
       || (SELECT COUNT(*) FROM bronze_sales
           WHERE product_code NOT IN (SELECT product_code FROM bronze_products))
       AS violation
WHERE (SELECT COUNT(*) FROM bronze_sales
       WHERE product_code NOT IN (SELECT product_code FROM bronze_products)) <> 2;
