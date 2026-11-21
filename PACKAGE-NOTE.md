# P25 — Package Note (Fiverr-ready)

**Gig title:** I will build you a Databricks-style medallion lakehouse from your sales and purchase files

**What the client gets:** a runnable lakehouse built from their
own CSVs — Databricks-style medallion layers (bronze as received,
silver cleaned, gold star schema + marts), a mapping doc that shows
exactly what each step becomes on real Databricks, 16 data-quality
tests that catch duplicates, negative quantities, unknown products
and wrong totals, a reconciliation report proving the money agrees
from bronze to silver to gold to workbook, a live Excel health
workbook (row counts, test pass rate, sales by category / by month,
inventory value, supplier spend — every total a formula), and a
2-page handover PDF they can hand to their accountant. Delivered as
a GitHub repo they can re-run on next month's files themselves.

**Honest note (in the repo, stated plainly):** this is Databricks-STYLE
patterns runnable on SQLite — no Databricks workspace, no .dbx file,
no Delta Lake file. Delta MERGE / OPTIMIZE are Databricks-only and
are simulated here in SQL; `databricks/mapping.md` shows the exact
translation for a real Databricks move.

## Tiers (Hashir's band)

| Tier | Price | Delivery | Includes |
|---|---|---|---|
| Basic | $20 | 2 days | The lakehouse on up to 3 source files (sales, purchases, products): bronze → silver → gold, the 16 data-quality tests with a pass/fail report, the health workbook with live formulas |
| Standard | $65 | 4 days | Everything in Basic + the 4 gold marts (sales by category / by month, inventory, supplier spend), the full DQ report with every rejected line listed and its fix, the 2-page handover PDF, the reconciliation proof (bronze → silver → gold to the rupee) |
| Premium | $140 | 6 days | Everything in Standard + up to 6 source files (extra files: returns, expenses, staff, or a second branch), the Databricks mapping doc (what each step becomes on real Databricks, incl. the Delta-only parts), a second lakehouse run on their next month's files to prove it re-runs, a 1-page owner guide (how to add a product, a supplier, a shop — and how to re-run the build), 1 revision round |

**What's NOT included:** a live Databricks workspace or Delta Lake
setup (this service builds the Databricks-style pattern + the
migration map — the workspace itself is quoted separately); running
their business systems or talking to their suppliers (they send
their own CSV exports — quoted separately if they need the exports
pulled from their software); changing their prices or product costs
(this service shows them what their own files say — the margin uses
the cost price they give); a live dashboard that updates itself
(this service is a lakehouse + a workbook they re-run — a live
dashboard is a different gig); cleaning years of back-files (quoted
separately by file count).

**Delivery time note:** counts from the day the client uploads
their 3 CSV exports (same columns as the sample), not from order
placement.

**Proof this service works:** this repo's SAMPLE — Ravi Traders
(fictional Lahore wholesaler), 520 sale lines over 6 months,
PKR 16,155,060 clean sales gross, PKR 1,525,120 gross profit at
9.44% margin, PKR 18,490,710 purchase spend, PKR 3,871,920
inventory value, 207 orders across 22 shops, 8 planted defects
found exactly (2 duplicates, 3 qty ≤ 0, 2 unknown products,
1 wrong total), 16/16 data-quality tests passing, 100+ automated
checks passing including a LibreOffice recalculation of the
workbook with zero error values and a verified 2-page handover
PDF, biggest category Cooking Oil & Ghee at PKR 3,255,740, biggest
supplier Al-Haq Oil & Ghee at PKR 3,951,360 (21.37% of spend), and
3 recommendations the owner can act on — fix the sales entry,
watch the oil supplier, push the high-margin categories.
