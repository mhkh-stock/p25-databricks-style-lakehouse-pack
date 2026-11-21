# Databricks mapping — what each medallion step is in real Databricks

**Read this first.** This repo is Databricks-**STYLE**: the bronze →
silver → gold medallion pattern, built and runnable here on SQLite so a
client can see it work without a Databricks account. There is **no
Databricks workspace, no .dbx file and no Delta Lake file** in this repo,
and nothing here claims otherwise. What is real is the pattern, the SQL
and the numbers — the same steps run on a real Databricks lakehouse with
the translations below.

## Layer by layer

| This repo (SQLite) | Real Databricks equivalent | What changes |
|---|---|---|
| `bronze_*` tables — CSVs loaded as received (`src/build_lakehouse.py`) | **Bronze Delta tables** fed by **Auto Loader** (`cloudFiles`) from the client's landing folder | The load becomes a streaming `cloudFiles` read; the table shape is identical (raw columns + a load timestamp) |
| `silver_sales.sql` — four guards: dedupe, qty > 0, product must exist, total = qty × price | **Silver Delta table** built by a **Delta Live Tables (DLT) pipeline** or a Databricks notebook with **expectations** (`EXPECT qty > 0`, `EXPECT product_code IS NOT NULL`) | The guards become DLT expectations; rows that fail them go to the quarantine table instead of being dropped silently — the same rejection counts this repo prints |
| `silver_sales_enriched.sql` — join to the product master, add COGS / gross profit / margin | **Silver enrichment** in the same DLT pipeline (a second transformation step) | Same SQL, written as Spark SQL; the INNER JOIN stays an INNER JOIN on purpose |
| `gold_dimensions.sql` — dim_product (SCD Type 1), dim_shop, dim_supplier, dim_date | **Gold dimension Delta tables** | Same loads; dim_date becomes a generated date table in Spark SQL |
| `gold_facts.sql` — fact_sales, fact_purchases | **Gold fact Delta tables** | Same loads |
| `gold_marts.sql` — 4 marts (category, month, inventory, supplier spend) | **Gold mart Delta tables**, queried from **Databricks SQL** / a dashboard | Same SQL; the workbook's live formulas become a Databricks SQL dashboard |
| `sql/tests/t01`–`t16` — DQ tests returning violating rows | **DLT expectations + Databricks SQL alerts** (or dbt tests if the client uses dbt on Databricks) | Each test file maps 1:1 to an expectation; a failing expectation fails the pipeline run, the same way a failing test fails `src/run_tests.py` |
| `src/build_lakehouse.py` — runs the layers in order | **Databricks Workflow / Job** with one task per layer, or a DLT pipeline | The order is the same: bronze → silver → gold; the job retries a failed layer, never a half-loaded one |

## What is Databricks-only (simulated here, not real)

- **Delta Lake MERGE** (upsert into a table by key). Here the silver
  dedupe is a `MIN(raw_line_no)` subquery in plain SQL — the same
  result, a different mechanism. On Databricks the dedupe becomes a
  `MERGE INTO silver_sales ... WHEN MATCHED THEN UPDATE`.
- **OPTIMIZE / Z-ORDER** (file compaction and clustering). SQLite has no
  equivalent; the tables here are small enough that it does not matter.
- **Auto Loader / streaming ingest** (new files arriving continuously).
  Here the load is a batch `INSERT` from the CSVs; on Databricks the
  same folder becomes a streaming source and the bronze table updates
  as files land.
- **Unity Catalog** (governance: who can see which table). Here the
  isolation is the file layout itself — bronze, silver and gold are
  separate tables, and only gold is handed to the business.
- **Photon / serverless compute** (speed). Nothing in this repo needs it:
  520 sale lines build in under a second.

## What a client gets by moving this to Databricks

Nothing in the business logic changes: the same four silver guards, the
same star schema, the same four marts, the same 16 tests. What changes
is scale and operations — files land continuously instead of by hand,
the pipeline re-runs on a schedule, and the workbook becomes a live
Databricks SQL dashboard. That is the Premium tier in `PACKAGE-NOTE.md`:
this repo first, Databricks migration second, quoted separately.
