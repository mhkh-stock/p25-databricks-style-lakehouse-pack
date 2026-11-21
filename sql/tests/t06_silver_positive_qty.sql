-- t06: silver_sales must contain no line with qty <= 0.
SELECT 'silver sale lines with qty <= 0: ' || COUNT(*) AS violation
FROM silver_sales WHERE qty <= 0
HAVING COUNT(*) > 0;
