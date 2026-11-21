-- t12: dim_date must cover the whole SAMPLE period, 2026-07-01 ..
-- 2026-12-31 (184 days), with no gaps.
SELECT 'dim_date days: expected 184, found ' || days
       || ' (range ' || first_day || ' .. ' || last_day
       || ', distinct ' || distinct_days || ')' AS violation
FROM (SELECT COUNT(*) AS days, MIN(date_key) AS first_day,
             MAX(date_key) AS last_day,
             COUNT(DISTINCT date_key) AS distinct_days
      FROM dim_date)
WHERE days <> 184 OR first_day <> '2026-07-01'
   OR last_day <> '2026-12-31' OR distinct_days <> 184;
