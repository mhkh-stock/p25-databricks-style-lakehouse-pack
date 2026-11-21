-- t14: no fact sale date may fall outside Jul–Dec 2026.
SELECT 'fact_sales rows outside Jul-Dec 2026: ' || COUNT(*) AS violation
FROM fact_sales
WHERE sale_date < '2026-07-01' OR sale_date > '2026-12-31'
HAVING COUNT(*) > 0;
