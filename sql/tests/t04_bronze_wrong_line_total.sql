-- t04: bronze sales must contain exactly 1 line with a wrong line
-- total (planted: off by PKR 750).
-- Returns 1 row if the count differs.
SELECT 'bronze sale lines with wrong total: expected 1, found '
       || (SELECT COUNT(*) FROM bronze_sales
           WHERE line_total_pkr <> qty * unit_price_pkr) AS violation
WHERE (SELECT COUNT(*) FROM bronze_sales
       WHERE line_total_pkr <> qty * unit_price_pkr) <> 1;
