# P25 — Databricks-Style Medallion Lakehouse Starter Pack

**Client (SAMPLE):** Ravi Traders — fictional wholesale distributor,
Lahore, 6 months (Wed 2026-07-01 → Thu 2026-12-31, 184 days) ·
**Status: SAMPLE delivery on DEMO data**
**Tools:** SQL (SQLite) · Python · Excel (live formulas) · reportlab
**Deliverable:** `outputs/lakehouse_health_SAMPLE.xlsx` +
`outputs/lakehouse_handover_SAMPLE.pdf` — a runnable medallion
lakehouse built from the client's own CSVs

> ⚠️ **What this is and is not.** Ravi Traders is a fictional
> distributor and the three source CSVs are demo data, generated to
> show the method. No real business, supplier or shop is involved.
> What is real is the lakehouse: the same bronze → silver → gold
> layers, star schema, data-quality tests and reconciliation checks
> run on a real client's sales, purchase and product files the same
> way, and every number in the report is recomputed from the data,
> never typed.

> ⚠️ **Databricks-STYLE, not Databricks.** This repo runs the
> Databricks medallion pattern (bronze → silver → gold) on SQLite so
> a client can see it work without a Databricks account. There is
> **no Databricks workspace, no .dbx file and no Delta Lake file**
> here — Delta Lake MERGE / OPTIMIZE are Databricks-only and are
> simulated here in SQL. `databricks/mapping.md` maps every step to
> its real Databricks equivalent.

## Business question it answers

> "A warehouse I can actually query, Databricks-style — where is my
> money, what is sitting in stock, and who do I depend on?"

A distributor running on three spreadsheets cannot answer that: the
sales file has duplicate lines, negative quantities and products
that do not exist; nobody knows what is actually in stock; and the
biggest supplier's share is a guess. This delivery answers it with a
medallion lakehouse: clean sale and purchase facts, four dimensions,
four gold marts, 16 data-quality tests that all pass, and a health
workbook whose totals are live formulas — so the owner can ask the
lakehouse a question and trust the answer.

## The method (plainly stated)

**Medallion layers:** **Bronze** loads the CSVs exactly as received.
**Silver** cleans them — duplicates, qty ≤ 0, unknown products and
wrong totals are rejected, never silently fixed — and adds the
economics. **Gold** conforms the result into a star schema:
`fact_sales` (one row per clean sale line) and `fact_purchases` (one
row per purchase-order line), joined to `dim_product`, `dim_shop`,
`dim_supplier` and `dim_date`, plus four marts the business queries
(`mart_sales_by_category`, `mart_sales_by_month`, `mart_inventory`,
`mart_supplier_spend`).

**Gross profit = line total − qty × cost price.** Cost price is the
product master's standard cost, not the per-PO unit cost (which
moves ±3% around it) — so profit is the margin on the price list,
not on each individual purchase. **Margin % = gross profit / gross
sales = 9.44%** — a wholesale margin: thin, high volume.

**Inventory value = stock qty × cost price**, where stock qty =
purchased qty − sold qty. **Stock status rule, stated:** stock below
10% of what was bought in the period is LOW; zero or less is OUT.
All 36 products are OK in this sample.

**Supplier share % = supplier spend / total purchase spend.**
Al-Haq Oil & Ghee is the biggest at 21.37% — the supplier whose
failure would hurt most.

**The 8 rejected lines:** 2 duplicates, 3 qty ≤ 0, 2 unknown
products (PRD-997, PRD-998), 1 wrong line total (PKR 750 too high).
They are rejected by the silver layer, never silently fixed, and
the raw file is untouched — see `outputs/dq_report.md` for the line
numbers and the fix for each one. Raw gross PKR 16,261,690 minus
rejected PKR 106,630 = clean gross PKR 16,155,060, exactly what the
fact table holds.

**SCD policy, stated:** `dim_product` is Type 1 — one row per
product, overwritten when a price changes. No price history is kept.
If the client later needs history, the dimension becomes Type 2
(`valid_from` / `valid_to`) and only the loader changes.

**Limits, stated upfront:** the shop and supplier masters are small
reference lists loaded from SQL (`sql/gold_dimensions.sql`), not
CSVs, because the client keeps them outside the transaction
exports. One supplier, Punjab Tea & Dry Fruit Traders, supplies two
categories (Tea & Beverages and Dry Fruits & Nuts). Every purchase
order has exactly one line in this sample, so `po_count` and
`po_lines` are the same number (160) — on a real file with
multi-line POs they will differ, and the mart counts them
separately. November is the best month and December the weakest in
this sample — that is the sample's own pattern, not a finding
about the real market.

## What is inside

| File | What it does |
|---|---|
| `outputs/lakehouse_health_SAMPLE.xlsx` | The deliverable: Health (row counts + test pass rate + money totals as live formulas) + Sales by category + Sales by month + Inventory value + Supplier spend + Method |
| `outputs/lakehouse_handover_SAMPLE.pdf` | 2-page handover report: question, headline numbers, tables, method, recommendations |
| `outputs/dq_report.md` | Findings report: 16/16 test results, every defect with its fix, reconciliation |
| `outputs/test_results.json` | Machine-readable test results (16 tests) |
| `outputs/mart_*.csv` | The four gold marts as CSVs (category, month, inventory, supplier spend) |
| `data/raw/sales_SAMPLE.csv` | The sales file: 520 lines, 512 clean + 8 planted defects |
| `data/raw/purchases_SAMPLE.csv` | The purchase file: 160 lines, 7 suppliers, 36 products |
| `data/raw/products_SAMPLE.csv` | The product master: 36 products, 8 categories |
| `data/processed/lakehouse.db` | The built lakehouse (SQLite — NOT committed; rebuilds from the scripts) |
| `data/processed/fact_sales.csv` | The fact table as a CSV (512 rows) |
| `data/README.md` | Data dictionary + planted defects + known quirks |
| `sql/schema.sql` | Bronze landing tables + gold star-schema DDL |
| `sql/silver_*.sql` | Silver models (cleaning + rejection guards + enrichment) |
| `sql/gold_dimensions.sql`, `gold_facts.sql`, `gold_marts.sql` | Gold models (dimensions + facts + 4 marts) |
| `sql/tests/` | 16 data-quality test queries (bronze counts, silver guards, gold grain, reconciliation) |
| `databricks/mapping.md` | What each medallion step maps to in real Databricks — and what is Databricks-only |
| `src/generate_data.py` | Makes the SAMPLE files (seed 20261121; NOT run on a real client file) |
| `src/build_lakehouse.py` | Runs bronze → silver → gold into `lakehouse.db`, prints row counts |
| `src/run_tests.py` | Runs all 16 tests, prints PASS/FAIL per test + summary |
| `src/build_workbook.py` | Builds the workbook: 6 sheets, live formulas |
| `src/build_report.py` | Builds the 2-page handover PDF + `dq_report.md` |
| `src/checks.py` | Verification suite — 100+ checks, all passing (incl. LibreOffice recalc) |
| `requirements.txt` | Pinned: `openpyxl==3.1.2`, `reportlab==5.0.1` (Python 3.12) |

## How it fits together

```
Client CSVs (sales, purchases, products) ──▶ bronze_* tables ──▶ silver_* models
   (520 / 160 / 36 rows in the demo)              (8 bad lines rejected)
                                                        ▼
                                           silver_sales_enriched ──▶ fact_sales
                                           gold_dimensions ──▶ dim_* (4 dims)
                                                        ▼
                              mart_sales_by_category + mart_sales_by_month
                              mart_inventory + mart_supplier_spend
                                                        ▼
                     src/build_workbook.py ──▶ lakehouse_health_SAMPLE.xlsx
                     src/build_report.py   ──▶ lakehouse_handover_SAMPLE.pdf
                        ▲ src/checks.py verifies all of it (100+ checks)
```

## Headline numbers (SAMPLE — Ravi Traders, 6 months)

- **512 clean sale lines · 207 orders · 22 shops ·
  7,842 units sold** · **sales gross PKR 16,155,060** · **gross
  profit PKR 1,525,120** · **margin 9.44%**
- **160 purchase lines · 7 suppliers · 10,004 units bought** ·
  **purchase spend PKR 18,490,710**
- **Inventory value at cost: PKR 3,871,920** — 2,162 units in stock
  across 36 products, all OK (0 LOW, 0 OUT)
- **16/16 data-quality tests passing** · **8 raw lines rejected**
  (2 duplicates, 3 qty ≤ 0, 2 unknown products, 1 wrong total)
- **Biggest category: Cooking Oil & Ghee (PKR 3,255,740)**; biggest
  supplier: **Al-Haq Oil & Ghee (PKR 3,951,360, 21.37% of spend)**;
  best month: **November (PKR 3,454,030)**; weakest: **December
  (PKR 1,328,550)**
- **Top product: Honey (1 kg jar) — PKR 1,097,250**; top shop:
  **Farooq General Store (Bhatti Gate) — PKR 1,420,660**

## Sales by category

| Category | Lines | Units | Gross sales | Gross profit | Margin |
|---|---|---|---|---|---|
| Cooking Oil & Ghee | 82 | 671 | PKR 3,255,740 | PKR 231,650 | 7.12% |
| Rice & Grains | 66 | 977 | PKR 3,183,900 | PKR 296,960 | 9.33% |
| Pulses & Lentils | 61 | 875 | PKR 2,532,180 | PKR 227,000 | 8.96% |
| Sugar & Sweeteners | 59 | 1,106 | PKR 2,423,550 | PKR 240,900 | 9.94% |
| Tea & Beverages | 60 | 1,061 | PKR 1,434,140 | PKR 136,230 | 9.50% |
| Dry Fruits & Nuts | 45 | 381 | PKR 1,371,100 | PKR 159,750 | 11.65% |
| Flour & Atta | 69 | 1,480 | PKR 1,076,340 | PKR 122,830 | 11.41% |
| Spices & Masala | 70 | 1,291 | PKR 878,110 | PKR 109,800 | 12.50% |
| **TOTAL** | **512** | **7,842** | **PKR 16,155,060** | **PKR 1,525,120** | **9.44%** |

Flour & Atta moves the most units (1,480) at the lowest ticket;
Cooking Oil & Ghee brings the most rupees (PKR 3,255,740) on the
thinnest margin (7.12%). Spices & Masala and Dry Fruits & Nuts
carry the best margins (12.50% and 11.65%); Cooking Oil & Ghee the
thinnest — the category that earns the most also earns the least
per rupee.

## Supplier spend

| Supplier | POs | Products | Total spend | Share |
|---|---|---|---|---|
| Al-Haq Oil & Ghee | 21 | 5 | PKR 3,951,360 | 21.37% |
| Chenab Rice Mills | 24 | 5 | PKR 3,684,490 | 19.93% |
| Punjab Tea & Dry Fruit Traders | 30 | 7 | PKR 3,063,760 | 16.57% |
| Multan Pulses Traders | 23 | 5 | PKR 2,826,020 | 15.28% |
| Jhang Sugar Traders | 19 | 4 | PKR 2,719,510 | 14.71% |
| Ravi Flour Mills | 21 | 5 | PKR 1,188,690 | 6.43% |
| Kashmiri Masala House | 22 | 5 | PKR 1,056,880 | 5.72% |
| **TOTAL** | **160** | **36** | **PKR 18,490,710** | **100.00%** |

The top two suppliers take 41.30% of all spend. Al-Haq Oil & Ghee
alone is more than a fifth of the money — the dependency to watch
first.

## Month by month

| Month | Lines | Units | Gross sales | Gross profit |
|---|---|---|---|---|
| 2026-07 | 77 | 1,196 | PKR 2,505,260 | PKR 251,890 |
| 2026-08 | 91 | 1,447 | PKR 2,890,640 | PKR 268,370 |
| 2026-09 | 89 | 1,225 | PKR 2,557,220 | PKR 243,190 |
| 2026-10 | 109 | 1,794 | PKR 3,419,360 | PKR 310,210 |
| 2026-11 | 104 | 1,622 | PKR 3,454,030 | PKR 333,160 |
| 2026-12 | 42 | 558 | PKR 1,328,550 | PKR 118,300 |
| **TOTAL** | **512** | **7,842** | **PKR 16,155,060** | **PKR 1,525,120** |

## The three recommendations (from the data, not from a template)

1. **Fix the sales file before anything else: 8 of 520 lines (1.5%)
   are wrong — duplicates, negative quantities, products that do not
   exist, and a total PKR 750 too high.** The lakehouse already
   rejects them, but the source file keeps producing them. Whoever
   types the sales must get a product list to pick from (no free
   typing of product codes) and the sheet must compute the line
   total itself — that alone removes 3 of the 4 defect types.
2. **Watch the Al-Haq Oil & Ghee dependency: PKR 3,951,360 — 21.37%
   of all purchase spend — goes to one supplier, and Cooking Oil &
   Ghee is both the biggest sales category (PKR 3,255,740) and the
   thinnest margin (7.12%).** If that supplier raises prices or
   fails to deliver, the biggest revenue line is the one that
   hurts. Line up a second oil supplier before the next quarter.
3. **Push the high-margin categories: Spices & Masala (12.50%) and
   Dry Fruits & Nuts (11.65%) earn the best margin per rupee but sit
   8th and 6th by sales.** They are the categories where an extra
   rupee of sales keeps the most profit — worth a push to the shops
   that already buy them, before chasing more low-margin oil volume.

## Same logic, three ways — and they must agree

The headline numbers exist in three forms: the SQL in `sql/`, the
workbook's formulas, and the handover PDF. `src/checks.py` runs all
three against the raw files and compares them — a mistake in any one
shows up as a failure. The workbook's formulas were also
recalculated in LibreOffice: every total matches the recompute
exactly, with zero error values.

## Reproduce it (2 minutes)

```bash
python3 src/generate_data.py    # rebuild the SAMPLE files (seed 20261121)
python3 src/build_lakehouse.py  # bronze → silver → gold → data/processed/lakehouse.db
python3 src/run_tests.py        # 16 tests — expect 16/16 passing
python3 src/build_workbook.py   # outputs/lakehouse_health_SAMPLE.xlsx
python3 src/build_report.py     # outputs/lakehouse_handover_SAMPLE.pdf (2 pages) + dq_report.md
python3 src/checks.py           # 100+ checks — expect all passing
```

On a real client file, replace the three CSVs in `data/raw/` with the
client's exports (same columns) and skip `generate_data.py` — add the
client's shop and supplier lists to `sql/gold_dimensions.sql` and
everything downstream runs unchanged. The `.db` file is never
committed; it rebuilds from the scripts.
