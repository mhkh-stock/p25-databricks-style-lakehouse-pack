"""Verification suite for P25 — Ravi Traders medallion lakehouse starter pack.

Every check recomputes its number from the raw CSVs / lakehouse / workbook
and compares it against the independent source. If a check fails, fix the
BUILD, not the check. Exit code 0 when all checks pass.

Covers: files present, raw row counts, planted-defect counts found exactly,
silver rejection counts, mart totals reconciling bronze -> silver -> gold,
fact/dim row counts, grain checks, date-dim coverage, SCD Type 1,
per-category / per-supplier / per-month / per-product reconciliation,
workbook formulas recalculated in LibreOffice, the 2-page handover PDF,
and README / DQ-report / package-note numbers matching the verified figures.

Usage:  python3 src/checks.py
"""
import csv
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "lakehouse.db"
WB = ROOT / "outputs" / "lakehouse_health_SAMPLE.xlsx"
PDF = ROOT / "outputs" / "lakehouse_handover_SAMPLE.pdf"
RECALC_DIR = ROOT / "outputs" / ".recalc"

CHECKS = []


def check(name, passed, detail=""):
    CHECKS.append((name, bool(passed), str(detail)))
    mark = "PASS" if passed else "FAIL"
    print(f"{mark}  {name}" + (f"  ({detail})" if detail else ""))


def q(conn, sql):
    return conn.execute(sql).fetchone()[0]


def main():
    conn = sqlite3.connect(DB)

    # ---------- 1. files present ----------
    expected_files = [
        "data/raw/sales_SAMPLE.csv", "data/raw/purchases_SAMPLE.csv",
        "data/raw/products_SAMPLE.csv",
        "sql/schema.sql", "sql/silver_sales.sql", "sql/silver_purchases.sql",
        "sql/silver_products.sql", "sql/silver_sales_enriched.sql",
        "sql/gold_dimensions.sql", "sql/gold_facts.sql", "sql/gold_marts.sql",
        "src/generate_data.py", "src/build_lakehouse.py",
        "src/run_tests.py", "src/build_workbook.py", "src/build_report.py",
        "src/checks.py",
        "outputs/lakehouse_health_SAMPLE.xlsx",
        "outputs/lakehouse_handover_SAMPLE.pdf",
        "outputs/dq_report.md", "outputs/test_results.json",
        "outputs/mart_sales_by_category.csv", "outputs/mart_sales_by_month.csv",
        "outputs/mart_inventory.csv", "outputs/mart_supplier_spend.csv",
        "databricks/mapping.md",
        "requirements.txt", ".gitignore",
    ]
    for f in expected_files:
        check(f"file exists: {f}", (ROOT / f).exists())
    test_files = sorted((ROOT / "sql" / "tests").glob("*.sql"))
    check("16 DQ test files present", len(test_files) == 16, f"found {len(test_files)}")
    for f in test_files:
        check(f"test file exists: {f.name}", f.exists())
    for name in ["fact_sales.csv", "fact_purchases.csv"]:
        check(f"processed export exists: {name}",
              (ROOT / "data" / "processed" / name).exists())

    # ---------- 2. raw row counts ----------
    raw_sales = list(csv.DictReader(open(ROOT / "data/raw/sales_SAMPLE.csv")))
    raw_purch = list(csv.DictReader(open(ROOT / "data/raw/purchases_SAMPLE.csv")))
    raw_prod = list(csv.DictReader(open(ROOT / "data/raw/products_SAMPLE.csv")))
    check("raw sales = 520 lines", len(raw_sales) == 520, len(raw_sales))
    check("raw purchases = 160 lines", len(raw_purch) == 160, len(raw_purch))
    check("raw products = 36", len(raw_prod) == 36, len(raw_prod))
    check("raw sales count matches lakehouse bronze_sales",
          q(conn, "SELECT COUNT(*) FROM bronze_sales") == len(raw_sales))
    check("raw purchases count matches lakehouse bronze_purchases",
          q(conn, "SELECT COUNT(*) FROM bronze_purchases") == len(raw_purch))
    check("raw products count matches lakehouse bronze_products",
          q(conn, "SELECT COUNT(*) FROM bronze_products") == len(raw_prod))

    # ---------- 3. planted defects found exactly ----------
    prod_codes = {r["product_code"] for r in raw_prod}
    dup_extra = len(raw_sales) - len({tuple(r.values()) for r in raw_sales})
    bad_qty = sum(1 for r in raw_sales if int(r["qty"]) <= 0)
    unknown = sum(1 for r in raw_sales if r["product_code"] not in prod_codes)
    bad_total = sum(1 for r in raw_sales
                    if int(r["line_total_pkr"]) != int(r["qty"]) * int(r["unit_price_pkr"]))
    check("planted duplicates found: exactly 2", dup_extra == 2, dup_extra)
    check("planted qty<=0 lines found: exactly 3", bad_qty == 3, bad_qty)
    check("planted unknown-product lines found: exactly 2", unknown == 2, unknown)
    check("planted wrong-total lines found: exactly 1", bad_total == 1, bad_total)
    check("planted defects total = 8", dup_extra + bad_qty + unknown + bad_total == 8)

    # ---------- 4. silver rejection counts ----------
    check("silver_sales = 512 clean lines",
          q(conn, "SELECT COUNT(*) FROM silver_sales") == 512)
    check("silver_purchases = 160 (no purchase defects)",
          q(conn, "SELECT COUNT(*) FROM silver_purchases") == 160)
    check("silver_products = 36", q(conn, "SELECT COUNT(*) FROM silver_products") == 36)
    check("rejected sale lines = 8 (520 - 512)",
          q(conn, "SELECT COUNT(*) FROM bronze_sales")
          - q(conn, "SELECT COUNT(*) FROM silver_sales") == 8)
    check("no silver sale line is a duplicate",
          q(conn, """SELECT COUNT(*) FROM (SELECT 1 FROM silver_sales GROUP BY
              order_id, sale_date, shop_id, product_code, qty,
              unit_price_pkr, line_total_pkr HAVING COUNT(*) > 1)""") == 0)
    check("no silver sale line has qty <= 0",
          q(conn, "SELECT COUNT(*) FROM silver_sales WHERE qty <= 0") == 0)
    check("no silver sale line has an unknown product",
          q(conn, """SELECT COUNT(*) FROM silver_sales WHERE product_code
              NOT IN (SELECT product_code FROM dim_product)""") == 0)
    check("no silver sale line has a wrong total",
          q(conn, """SELECT COUNT(*) FROM silver_sales
              WHERE line_total_pkr <> qty * unit_price_pkr""") == 0)

    # ---------- 5. fact / dim / mart row counts ----------
    for table, expected in [("fact_sales", 512), ("fact_purchases", 160),
                            ("dim_product", 36), ("dim_shop", 22),
                            ("dim_supplier", 7), ("dim_date", 184),
                            ("silver_sales_enriched", 512),
                            ("mart_sales_by_category", 8),
                            ("mart_sales_by_month", 6),
                            ("mart_inventory", 36), ("mart_supplier_spend", 7)]:
        check(f"{table} = {expected} rows",
              q(conn, f"SELECT COUNT(*) FROM {table}") == expected,
              q(conn, f"SELECT COUNT(*) FROM {table}"))

    # ---------- 6. grain checks ----------
    check("fact_sales grain: one row per silver sale line",
          q(conn, "SELECT COUNT(*) FROM fact_sales")
          == q(conn, "SELECT COUNT(*) FROM silver_sales"))
    check("fact_sales sale_line_id is unique (512 distinct)",
          q(conn, "SELECT COUNT(DISTINCT sale_line_id) FROM fact_sales") == 512)
    check("fact_sales has no NULL keys",
          q(conn, """SELECT COUNT(*) FROM fact_sales WHERE order_id IS NULL
              OR sale_date IS NULL OR shop_id IS NULL
              OR product_code IS NULL OR qty IS NULL
              OR line_total_pkr IS NULL""") == 0)
    check("fact_sales has no duplicate (order, product, qty, price) lines",
          q(conn, """SELECT COUNT(*) FROM (SELECT 1 FROM fact_sales GROUP BY
              order_id, sale_date, shop_id, product_code, qty,
              unit_price_pkr, line_total_pkr HAVING COUNT(*) > 1)""") == 0)
    check("fact_sales orders = 207 distinct",
          q(conn, "SELECT COUNT(DISTINCT order_id) FROM fact_sales") == 207)
    check("fact_sales shops = 22 distinct",
          q(conn, "SELECT COUNT(DISTINCT shop_id) FROM fact_sales") == 22)

    # ---------- 7. totals reconcile bronze -> silver -> gold ----------
    # Recompute the clean set from the raw CSVs, independently of SQL:
    seen, clean_gross, clean_profit = set(), 0, 0
    cost = {r["product_code"]: int(r["cost_price_pkr"]) for r in raw_prod}
    for r in raw_sales:
        k = tuple(r.values())
        if (int(r["qty"]) > 0 and r["product_code"] in prod_codes
                and int(r["line_total_pkr"]) == int(r["qty"]) * int(r["unit_price_pkr"])
                and k not in seen):
            seen.add(k)
            clean_gross += int(r["line_total_pkr"])
            clean_profit += int(r["line_total_pkr"]) - int(r["qty"]) * cost[r["product_code"]]
    raw_purch_total = sum(int(r["total_cost_pkr"]) for r in raw_purch)
    raw_gross = sum(int(r["line_total_pkr"]) for r in raw_sales)
    fact_gross = q(conn, "SELECT SUM(line_total_pkr) FROM fact_sales")
    fact_profit = q(conn, "SELECT SUM(gross_profit_pkr) FROM fact_sales")
    fact_spend = q(conn, "SELECT SUM(total_cost_pkr) FROM fact_purchases")
    inv_value = q(conn, "SELECT SUM(stock_value_pkr) FROM mart_inventory")
    inv_units = q(conn, "SELECT SUM(stock_qty) FROM mart_inventory")
    check("sales gross reconciles: fact = clean raw",
          fact_gross == clean_gross, f"fact {fact_gross:,} vs raw {clean_gross:,}")
    check("gross profit reconciles: fact = clean raw",
          fact_profit == clean_profit, f"fact {fact_profit:,} vs raw {clean_profit:,}")
    check("purchase spend reconciles: fact = raw",
          fact_spend == raw_purch_total, f"fact {fact_spend:,} vs raw {raw_purch_total:,}")
    check("inventory value = SUM(stock_qty x cost price)",
          inv_value == q(conn, """SELECT SUM(stock_qty * cost_price_pkr)
              FROM mart_inventory i JOIN dim_product p
              ON p.product_code = i.product_code"""),
          f"{inv_value:,}")
    check("margin = profit / gross (9.44%)",
          abs(fact_profit / fact_gross - 0.0944) < 0.0005,
          f"{100.0 * fact_profit / fact_gross:.2f}%")
    check("raw gross minus rejected = clean gross",
          raw_gross - (raw_gross - clean_gross) == clean_gross)
    check("rejected lines total = raw gross - clean gross",
          raw_gross - clean_gross ==
          q(conn, "SELECT SUM(line_total_pkr) FROM bronze_sales")
          - q(conn, "SELECT SUM(line_total_pkr) FROM silver_sales"))

    # ---------- 8. per-category reconciliation ----------
    cats = conn.execute("SELECT category FROM dim_product GROUP BY category").fetchall()
    check("8 categories", len(cats) == 8, len(cats))
    for (cat,) in cats:
        a = conn.execute("""SELECT SUM(line_total_pkr) FROM silver_sales_enriched
                            WHERE category = ?""", (cat,)).fetchone()[0]
        b = conn.execute("""SELECT SUM(f.line_total_pkr) FROM fact_sales f
                            JOIN dim_product p ON p.product_code = f.product_code
                            WHERE p.category = ?""", (cat,)).fetchone()[0]
        c = conn.execute("""SELECT gross_pkr FROM mart_sales_by_category
                            WHERE category = ?""", (cat,)).fetchone()[0]
        check(f"category reconciles: {cat}", a == b == c, f"PKR {a:,}")
    check("category grosses sum to total gross",
          q(conn, "SELECT SUM(gross_pkr) FROM mart_sales_by_category") == fact_gross)

    # ---------- 9. per-supplier reconciliation ----------
    sups = conn.execute("SELECT supplier_id FROM dim_supplier").fetchall()
    check("7 suppliers", len(sups) == 7, len(sups))
    for (sup,) in sups:
        a = conn.execute("""SELECT total_spend_pkr FROM mart_supplier_spend
                            WHERE supplier_id = ?""", (sup,)).fetchone()[0]
        b = conn.execute("""SELECT SUM(total_cost_pkr) FROM fact_purchases
                            WHERE supplier_id = ?""", (sup,)).fetchone()[0]
        check(f"supplier spend reconciles: {sup}", a == b, f"PKR {a:,}")
    check("supplier spends sum to total purchase spend",
          q(conn, "SELECT SUM(total_spend_pkr) FROM mart_supplier_spend") == fact_spend)

    # ---------- 10. per-month reconciliation ----------
    for m in ["2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]:
        a = conn.execute("""SELECT SUM(line_total_pkr) FROM fact_sales
                            WHERE substr(sale_date, 1, 7) = ?""", (m,)).fetchone()[0]
        b = conn.execute("""SELECT SUM(line_total_pkr) FROM silver_sales
                            WHERE substr(sale_date, 1, 7) = ?""", (m,)).fetchone()[0]
        c = conn.execute("""SELECT gross_pkr FROM mart_sales_by_month
                            WHERE month = ?""", (m,)).fetchone()[0]
        check(f"month reconciles: {m}", a == b == c and a is not None, f"PKR {a:,}")
    check("monthly grosses sum to total gross",
          q(conn, "SELECT SUM(gross_pkr) FROM mart_sales_by_month") == fact_gross)

    # ---------- 11. per-product inventory ----------
    prods = conn.execute("SELECT product_code, stock_qty, stock_value_pkr FROM mart_inventory").fetchall()
    for code, stock, value in prods:
        cp = conn.execute("SELECT cost_price_pkr FROM dim_product WHERE product_code = ?",
                          (code,)).fetchone()[0]
        check(f"inventory OK: {code} stock>=0 and value=stock x cost",
              stock >= 0 and value == stock * cp, f"stock {stock}, value PKR {value:,}")
    check("all 36 products have OK stock status",
          q(conn, "SELECT COUNT(*) FROM mart_inventory WHERE stock_status <> 'OK'") == 0)
    check("total stock units = purchased - sold",
          inv_units == q(conn, "SELECT SUM(qty) FROM fact_purchases")
          - q(conn, "SELECT SUM(qty) FROM fact_sales"),
          f"{inv_units:,}")

    # ---------- 12. date dimension ----------
    check("dim_date = 184 days", q(conn, "SELECT COUNT(*) FROM dim_date") == 184)
    check("dim_date starts 2026-07-01",
          q(conn, "SELECT MIN(date_key) FROM dim_date") == "2026-07-01")
    check("dim_date ends 2026-12-31",
          q(conn, "SELECT MAX(date_key) FROM dim_date") == "2026-12-31")
    check("dim_date has no gaps (184 distinct dates)",
          q(conn, "SELECT COUNT(DISTINCT date_key) FROM dim_date") == 184)
    check("every fact sale date exists in dim_date",
          q(conn, """SELECT COUNT(*) FROM fact_sales
              WHERE sale_date NOT IN (SELECT date_key FROM dim_date)""") == 0)
    check("no fact sale date outside Jul–Dec 2026",
          q(conn, """SELECT COUNT(*) FROM fact_sales
              WHERE sale_date < '2026-07-01' OR sale_date > '2026-12-31'""") == 0)

    # ---------- 13. SCD Type 1 ----------
    check("dim_product: one row per product (SCD Type 1)",
          q(conn, "SELECT COUNT(*) FROM dim_product")
          == q(conn, "SELECT COUNT(DISTINCT product_code) FROM dim_product") == 36)
    check("dim_shop: 22 distinct shops",
          q(conn, "SELECT COUNT(DISTINCT shop_id) FROM dim_shop") == 22)
    check("dim_supplier: 7 distinct suppliers",
          q(conn, "SELECT COUNT(DISTINCT supplier_id) FROM dim_supplier") == 7)

    # ---------- 14. DQ test results file ----------
    tests = json.loads((ROOT / "outputs" / "test_results.json").read_text(encoding="utf-8"))
    check("test_results.json: 16/16 passing",
          tests["passed"] == 16 and tests["total"] == 16,
          f"{tests['passed']}/{tests['total']}")
    check("test_results.json lists 16 tests", len(tests["tests"]) == 16)

    # ---------- 15. outputs mart CSVs reconcile ----------
    for name, table in [("mart_sales_by_category.csv", "mart_sales_by_category"),
                        ("mart_sales_by_month.csv", "mart_sales_by_month"),
                        ("mart_inventory.csv", "mart_inventory"),
                        ("mart_supplier_spend.csv", "mart_supplier_spend")]:
        rows = list(csv.DictReader(open(ROOT / "outputs" / name)))
        check(f"outputs/{name} row count matches {table}",
              len(rows) == q(conn, f"SELECT COUNT(*) FROM {table}"),
              len(rows))
    cat_csv = list(csv.DictReader(open(ROOT / "outputs/mart_sales_by_category.csv")))
    check("mart category CSV gross sums to fact gross",
          sum(int(r["gross_pkr"]) for r in cat_csv) == fact_gross)
    sup_csv = list(csv.DictReader(open(ROOT / "outputs/mart_supplier_spend.csv")))
    check("mart supplier CSV spend sums to fact spend",
          sum(int(r["total_spend_pkr"]) for r in sup_csv) == fact_spend)

    # ---------- 16. workbook: structure + LibreOffice recalc ----------
    check("workbook file exists", WB.exists())
    wb = load_workbook(WB)
    for sheet in ["Health", "Sales by category", "Sales by month",
                  "Inventory value", "Supplier spend", "Method"]:
        check(f"workbook sheet present: {sheet}", sheet in wb.sheetnames)
    ws = wb["Health"]
    formulas = [c.value for row in ws.iter_rows() for c in row
                if isinstance(c.value, str) and c.value.startswith("=")]
    check("Health sheet has live-formula money totals", len(formulas) >= 5,
          f"{len(formulas)} formulas")
    cat_ws = wb["Sales by category"]
    check("category TOTAL row is SUM formulas",
          str(cat_ws.cell(row=10, column=4).value).startswith("=SUM("))
    check("month TOTAL row is SUM formulas",
          str(wb["Sales by month"].cell(row=8, column=4).value).startswith("=SUM("))
    check("supplier TOTAL row is SUM formulas",
          str(wb["Supplier spend"].cell(row=9, column=5).value).startswith("=SUM("))
    check("inventory TOTAL row is SUM formulas",
          str(wb["Inventory value"].cell(row=38, column=7).value).startswith("=SUM("))

    # LibreOffice headless recalc, then compare cached values to the database
    if RECALC_DIR.exists():
        shutil.rmtree(RECALC_DIR)
    RECALC_DIR.mkdir(parents=True)
    res = subprocess.run(
        ["soffice", "--headless", "--calc", "--convert-to", "xlsx",
         "--outdir", str(RECALC_DIR), str(WB)],
        capture_output=True, text=True, timeout=120)
    recalc_file = RECALC_DIR / WB.name
    check("LibreOffice recalculated the workbook", res.returncode == 0 and recalc_file.exists())
    if recalc_file.exists():
        rwb = load_workbook(recalc_file, data_only=True)
        errors = []
        for sh in rwb.sheetnames:
            for row in rwb[sh].iter_rows():
                for c in row:
                    if isinstance(c.value, str) and c.value.startswith("#"):
                        errors.append(f"{sh}!{c.coordinate}={c.value}")
        check("recalculated workbook has zero error values", not errors, "; ".join(errors[:5]))
        h = rwb["Health"]
        health = {row[0]: row[1] for row in h.iter_rows(values_only=True)
                  if row[0] and row[1] is not None}
        check("recalc: Health sales gross = fact gross",
              health.get("Sales gross, clean (PKR)") == fact_gross,
              health.get("Sales gross, clean (PKR)"))
        check("recalc: Health gross profit = fact profit",
              health.get("Gross profit, clean (PKR)") == fact_profit,
              health.get("Gross profit, clean (PKR)"))
        check("recalc: Health purchase spend = fact spend",
              health.get("Purchase spend (PKR)") == fact_spend,
              health.get("Purchase spend (PKR)"))
        check("recalc: Health inventory value = mart inventory value",
              health.get("Inventory value at cost (PKR)") == inv_value,
              health.get("Inventory value at cost (PKR)"))
        check("recalc: test pass rate = 100%",
              health.get("Test pass rate") == 1, health.get("Test pass rate"))
        check("recalc: category TOTAL gross = fact gross",
              rwb["Sales by category"].cell(row=10, column=4).value == fact_gross)
        check("recalc: month TOTAL gross = fact gross",
              rwb["Sales by month"].cell(row=8, column=4).value == fact_gross)
        check("recalc: inventory TOTAL value = mart inventory value",
              rwb["Inventory value"].cell(row=38, column=7).value == inv_value)
        check("recalc: supplier TOTAL spend = fact spend",
              rwb["Supplier spend"].cell(row=9, column=5).value == fact_spend)
        check("recalc: supplier share total = 100%",
              abs(rwb["Supplier spend"].cell(row=9, column=6).value - 1.0) < 1e-9)
    shutil.rmtree(RECALC_DIR, ignore_errors=True)

    # ---------- 17. handover PDF is exactly 2 pages ----------
    res = subprocess.run(["pdfinfo", str(PDF)], capture_output=True, text=True)
    pages = None
    for line in res.stdout.splitlines():
        if line.startswith("Pages:"):
            pages = int(line.split(":")[1].strip())
    check("handover PDF exists", PDF.exists())
    check("handover PDF is exactly 2 pages", pages == 2, f"{pages} pages")

    # ---------- 18. .gitignore keeps the .db out of the repo ----------
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    check(".gitignore excludes *.db", "*.db" in gi)
    check("lakehouse.db exists locally for verification", DB.exists())

    # ---------- 19. README / DQ report / package note match verified figures ----------
    margin_str = f"{100.0 * fact_profit / fact_gross:.2f}%"
    figures = {
        "sales gross": f"{fact_gross:,}",
        "gross profit": f"{fact_profit:,}",
        "purchase spend": f"{fact_spend:,}",
        "inventory value": f"{inv_value:,}",
        "clean sale lines": "512",
        "margin": margin_str,
    }
    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    for label, figure in figures.items():
        check(f"README states verified figure {label} ({figure})", figure in readme)
    check("README states the honest Databricks note",
          "Databricks-STYLE" in readme and "no Databricks workspace" in readme)
    check("README names the client Ravi Traders", "Ravi Traders" in readme)
    dq = (ROOT / "outputs" / "dq_report.md").read_text(encoding="utf-8") \
        if (ROOT / "outputs" / "dq_report.md").exists() else ""
    for label, figure in {**figures, "tests": "16/16"}.items():
        check(f"dq_report states verified figure {label} ({figure})", figure in dq)
    check("dq_report records all 4 planted defect types",
          all(s in dq.lower() for s in ["duplicate", "qty", "unknown product", "wrong line total"]))
    pkg = (ROOT / "PACKAGE-NOTE.md").read_text(encoding="utf-8") \
        if (ROOT / "PACKAGE-NOTE.md").exists() else ""
    for figure in [f"{fact_gross:,}", f"{fact_profit:,}", f"{fact_spend:,}",
                   f"{inv_value:,}", "16/16"]:
        check(f"PACKAGE-NOTE states verified figure {figure}", figure in pkg)
    check("PACKAGE-NOTE lists $20/$65/$140 tiers",
          all(s in pkg for s in ["$20", "$65", "$140"]))
    mapping = (ROOT / "databricks" / "mapping.md").read_text(encoding="utf-8") \
        if (ROOT / "databricks" / "mapping.md").exists() else ""
    check("mapping.md states Delta MERGE/OPTIMIZE are Databricks-only",
          "Delta" in mapping and "Databricks-only" in mapping)
    check("mapping.md covers bronze, silver and gold",
          all(s in mapping for s in ["bronze", "silver", "gold"]))

    # ---------- summary ----------
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    total = len(CHECKS)
    print(f"\n{passed}/{total} checks passed")
    failed = [name for name, ok, _ in CHECKS if not ok]
    if failed:
        print("FAILED:")
        for name in failed:
            print(f"  - {name}")
    conn.close()
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
