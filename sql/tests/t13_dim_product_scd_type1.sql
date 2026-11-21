-- t13: dim_product is SCD Type 1 — exactly one row per product (36).
SELECT 'dim_product rows: expected 36, found ' || rows
       || ' (distinct codes ' || distinct_codes || ')' AS violation
FROM (SELECT COUNT(*) AS rows, COUNT(DISTINCT product_code) AS distinct_codes
      FROM dim_product)
WHERE rows <> 36 OR distinct_codes <> 36;
