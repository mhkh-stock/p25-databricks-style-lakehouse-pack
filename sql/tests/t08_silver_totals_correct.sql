-- t08: every silver sale line total must equal qty * unit price.
SELECT 'silver sale lines with wrong total: ' || COUNT(*) AS violation
FROM silver_sales
WHERE line_total_pkr <> qty * unit_price_pkr
HAVING COUNT(*) > 0;
