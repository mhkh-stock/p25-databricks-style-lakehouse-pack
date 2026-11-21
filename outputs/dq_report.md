# P25 — Data-quality report (Ravi Traders, SAMPLE)

**Tests: 16/16 passing.** Every test file returns its violating rows; 0 rows = PASS. Full per-test results: `outputs/test_results.json`.

## Test results

| Test | Result | Violations |
|---|---|---|
| `t01_bronze_duplicate_lines.sql` | PASS | 0 |
| `t02_bronze_nonpositive_qty.sql` | PASS | 0 |
| `t03_bronze_unknown_product.sql` | PASS | 0 |
| `t04_bronze_wrong_line_total.sql` | PASS | 0 |
| `t05_silver_no_duplicates.sql` | PASS | 0 |
| `t06_silver_positive_qty.sql` | PASS | 0 |
| `t07_silver_product_exists.sql` | PASS | 0 |
| `t08_silver_totals_correct.sql` | PASS | 0 |
| `t09_gold_fact_grain.sql` | PASS | 0 |
| `t10_gold_no_null_keys.sql` | PASS | 0 |
| `t11_totals_reconcile_bronze_silver_gold.sql` | PASS | 0 |
| `t12_dim_date_coverage.sql` | PASS | 0 |
| `t13_dim_product_scd_type1.sql` | PASS | 0 |
| `t14_gold_no_stale_dates.sql` | PASS | 0 |
| `t15_inventory_nonnegative.sql` | PASS | 0 |
| `t16_fact_purchases_reconcile.sql` | PASS | 0 |

## Planted defects — found exactly (8 lines)

File line numbers count from the top of the CSV file (header is line 1). The silver layer keeps the first occurrence of a duplicate and rejects the rest; the raw file is never changed.

### Exact duplicates (2)

- File lines 140 &amp; 281 are the same line (ORD-0059, 2026-09-18, SHP-21, PRD-026, qty 39, PKR 20,280). Silver keeps line 140.
- File lines 156 &amp; 458 are the same line (ORD-0063, 2026-09-14, SHP-04, PRD-030, qty 13, PKR 64,350). Silver keeps line 156.

### qty &le; 0 (3)

- Line 50 (ORD-0208, PRD-025, qty 0, PKR 0). A sale cannot sell zero or a negative amount.
- Line 131 (ORD-0210, PRD-019, qty -3, PKR -9,450). A sale cannot sell zero or a negative amount.
- Line 171 (ORD-0209, PRD-017, qty -1, PKR -6,300). A sale cannot sell zero or a negative amount.

### Unknown product (2)

- Line 206 (ORD-0211, product PRD-997). The code does not exist in the product master, so no cost price exists for it.
- Line 317 (ORD-0212, product PRD-998). The code does not exist in the product master, so no cost price exists for it.

### Wrong line total (1)

- Line 511 (ORD-0213, PRD-035, qty 9 x PKR 3,000 = PKR 27,000, but recorded as PKR 27,750 — PKR 750 too high).

## Reconciliation (bronze → silver → gold)

- Clean sale lines (silver = gold fact_sales): 512 of 520 raw lines (8 rejected)
- Raw sales gross (all 520 bronze lines): PKR 16,261,690
- Rejected lines (8): PKR 106,630
- Clean sales gross (silver = gold fact_sales): PKR 16,155,060
- Gross profit (clean): PKR 1,525,120 — margin 9.44%
- Purchase spend (bronze = silver = gold): PKR 18,490,710
- Inventory value at cost: PKR 3,871,920 (2,162 units across 36 products, all OK)

## What the tests prove

- Bronze counts are exactly the planted defects (2 / 3 / 2 / 1).
- Silver holds no duplicates, no qty &le; 0, no unknown products, no wrong totals.
- Gold fact_sales has one row per silver sale line, no NULL keys, and its totals equal silver's and clean bronze's.
- dim_date covers all 184 days, Jul–Dec 2026, with no gaps.
- Inventory is never negative and every stock value equals stock qty x cost price.
