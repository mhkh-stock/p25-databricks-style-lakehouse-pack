-- t16: purchase spend must reconcile bronze -> silver -> gold.
SELECT 'purchase spend broken: bronze '
       || (SELECT SUM(total_cost_pkr) FROM bronze_purchases)
       || ' vs silver ' || (SELECT SUM(total_cost_pkr) FROM silver_purchases)
       || ' vs gold ' || (SELECT SUM(total_cost_pkr) FROM fact_purchases)
       AS violation
WHERE (SELECT SUM(total_cost_pkr) FROM bronze_purchases)
   <> (SELECT SUM(total_cost_pkr) FROM silver_purchases)
   OR (SELECT SUM(total_cost_pkr) FROM silver_purchases)
   <> (SELECT SUM(total_cost_pkr) FROM fact_purchases);
