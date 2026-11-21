"""Build outputs/lakehouse_health_SAMPLE.xlsx from the lakehouse.

Sheets (every total is a live formula; only SUM / COUNT / division are
used, so no post-2007 functions — LibreOffice recalculates them cleanly):
  Health              — row counts per table, DQ test pass rate, money totals
                        (each money total is a formula pointing at the
                        TOTAL cell of its detail sheet)
  Sales by category   — 8 categories, TOTAL row = SUM formulas, margin % = formula
  Sales by month      — 6 months, TOTAL row = SUM formulas
  Inventory value     — 36 products, TOTAL row = SUM formulas
  Supplier spend      — 7 suppliers, TOTAL row = SUM formulas, share % = formula
  Method              — definitions, so a reader can check every number

Usage:  python3 src/build_workbook.py
"""
import json
import sqlite3
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "lakehouse.db"
OUT = ROOT / "outputs" / "lakehouse_health_SAMPLE.xlsx"
TESTS_JSON = ROOT / "outputs" / "test_results.json"

TITLE_FILL = PatternFill("solid", fgColor="1F4E79")
TITLE_FONT = Font(bold=True, color="FFFFFF", size=12)
HDR_FILL = PatternFill("solid", fgColor="D9E2F3")
HDR_FONT = Font(bold=True)
TOTAL_FONT = Font(bold=True)
MONEY = '#,##0'
PCT = '0.00%'


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT


def total_row(ws, row, ncols, sum_cols, label="TOTAL"):
    ws.cell(row=row, column=1, value=label).font = TOTAL_FONT
    for col in sum_cols:
        letter = get_column_letter(col)
        ws.cell(row=row, column=col,
               value=f"=SUM({letter}2:{letter}{row - 1})").font = TOTAL_FONT


def money(cell):
    cell.number_format = MONEY


def main():
    conn = sqlite3.connect(DB)
    tests = json.loads(TESTS_JSON.read_text(encoding="utf-8"))
    wb = Workbook()

    # ---------- Health ----------
    ws = wb.active
    ws.title = "Health"
    ws["A1"] = "Ravi Traders — Lakehouse Health (SAMPLE)"
    ws["A1"].font = TITLE_FONT
    ws["A1"].fill = TITLE_FILL
    ws["A2"] = ("Jul–Dec 2026 · SAMPLE demo data · every money total below is a "
                "live formula pointing at its detail sheet")
    ws["A3"] = "Table"
    ws["B3"] = "Rows"
    style_header(ws, 3, 2)
    counts = [
        ("bronze_sales (as received)", "SELECT COUNT(*) FROM bronze_sales"),
        ("bronze_purchases (as received)", "SELECT COUNT(*) FROM bronze_purchases"),
        ("bronze_products (as received)", "SELECT COUNT(*) FROM bronze_products"),
        ("silver_sales (clean sale lines)", "SELECT COUNT(*) FROM silver_sales"),
        ("silver_purchases (clean PO lines)", "SELECT COUNT(*) FROM silver_purchases"),
        ("silver_products (clean products)", "SELECT COUNT(*) FROM silver_products"),
        ("fact_sales", "SELECT COUNT(*) FROM fact_sales"),
        ("fact_purchases", "SELECT COUNT(*) FROM fact_purchases"),
        ("dim_product", "SELECT COUNT(*) FROM dim_product"),
        ("dim_shop", "SELECT COUNT(*) FROM dim_shop"),
        ("dim_supplier", "SELECT COUNT(*) FROM dim_supplier"),
        ("dim_date (days)", "SELECT COUNT(*) FROM dim_date"),
    ]
    r = 4
    for label, q in counts:
        ws.cell(row=r, column=1, value=label)
        ws.cell(row=r, column=2, value=conn.execute(q).fetchone()[0])
        r += 1
    r += 1  # blank
    ws.cell(row=r, column=1, value="Data-quality tests passed").font = TOTAL_FONT
    ws.cell(row=r, column=2, value=tests["passed"])
    pass_row = r
    r += 1
    ws.cell(row=r, column=1, value="Data-quality tests run").font = TOTAL_FONT
    ws.cell(row=r, column=2, value=tests["total"])
    total_row_tests = r
    r += 1
    ws.cell(row=r, column=1, value="Test pass rate").font = TOTAL_FONT
    c = ws.cell(row=r, column=2, value=f"=B{pass_row}/B{total_row_tests}")
    c.number_format = PCT
    c.font = TOTAL_FONT
    r += 1
    ws.cell(row=r, column=1, value="Raw sale lines rejected (planted defects)").font = TOTAL_FONT
    ws.cell(row=r, column=2, value=conn.execute(
        "SELECT COUNT(*) FROM bronze_sales").fetchone()[0]
        - conn.execute("SELECT COUNT(*) FROM silver_sales").fetchone()[0])
    r += 2
    ws.cell(row=r, column=1, value="Money totals (live formulas)").font = TOTAL_FONT
    r += 1
    money_rows = [
        ("Sales gross, clean (PKR)", "='Sales by category'!D10"),
        ("Gross profit, clean (PKR)", "='Sales by category'!E10"),
        ("Purchase spend (PKR)", "='Supplier spend'!E9"),
        ("Inventory value at cost (PKR)", "='Inventory value'!G38"),
    ]
    for label, formula in money_rows:
        ws.cell(row=r, column=1, value=label).font = TOTAL_FONT
        c = ws.cell(row=r, column=2, value=formula)
        money(c)
        c.font = TOTAL_FONT
        r += 1
    ws.column_dimensions["A"].width = 44
    ws.column_dimensions["B"].width = 18

    # ---------- Sales by category ----------
    ws = wb.create_sheet("Sales by category")
    ws.append(["Category", "Sale lines", "Units sold", "Gross sales (PKR)",
               "Gross profit (PKR)", "Margin %"])
    style_header(ws, 1, 6)
    rows = conn.execute("""SELECT category, lines, units_sold, gross_pkr,
        gross_profit_pkr, margin_pct
        FROM mart_sales_by_category ORDER BY gross_pkr DESC""").fetchall()
    for row in rows:
        ws.append(list(row))
    for r in range(2, 2 + len(rows)):
        money(ws.cell(row=r, column=4))
        money(ws.cell(row=r, column=5))
        c = ws.cell(row=r, column=6, value=f"=E{r}/D{r}")
        c.number_format = PCT
    total = 2 + len(rows)  # row 10
    total_row(ws, total, 6, [2, 3, 4, 5])
    money(ws.cell(row=total, column=4))
    money(ws.cell(row=total, column=5))
    c = ws.cell(row=total, column=6, value=f"=E{total}/D{total}")
    c.number_format = PCT
    c.font = TOTAL_FONT
    for col, w in zip("ABCDEF", [24, 11, 11, 17, 18, 10]):
        ws.column_dimensions[col].width = w

    # ---------- Sales by month ----------
    ws = wb.create_sheet("Sales by month")
    ws.append(["Month", "Sale lines", "Units sold", "Gross sales (PKR)",
               "Gross profit (PKR)"])
    style_header(ws, 1, 5)
    rows = conn.execute("""SELECT month, lines, units_sold, gross_pkr,
        gross_profit_pkr FROM mart_sales_by_month ORDER BY month""").fetchall()
    for row in rows:
        ws.append(list(row))
    for r in range(2, 2 + len(rows)):
        money(ws.cell(row=r, column=4))
        money(ws.cell(row=r, column=5))
    total = 2 + len(rows)  # row 8
    total_row(ws, total, 5, [2, 3, 4, 5])
    money(ws.cell(row=total, column=4))
    money(ws.cell(row=total, column=5))
    for col, w in zip("ABCDE", [12, 11, 11, 17, 18]):
        ws.column_dimensions[col].width = w

    # ---------- Inventory value ----------
    ws = wb.create_sheet("Inventory value")
    ws.append(["Product code", "Product", "Category", "Purchased qty",
               "Sold qty", "Stock qty", "Stock value (PKR)", "Status"])
    style_header(ws, 1, 8)
    rows = conn.execute("""SELECT product_code, product_name, category,
        purchased_qty, sold_qty, stock_qty, stock_value_pkr, stock_status
        FROM mart_inventory ORDER BY stock_value_pkr DESC""").fetchall()
    for row in rows:
        ws.append(list(row))
    for r in range(2, 2 + len(rows)):
        money(ws.cell(row=r, column=7))
    total = 2 + len(rows)  # row 38
    total_row(ws, total, 8, [4, 5, 6, 7])
    money(ws.cell(row=total, column=7))
    ws.cell(row=total, column=8, value="—")
    for col, w in zip("ABCDEFGH", [13, 34, 20, 14, 10, 10, 17, 8]):
        ws.column_dimensions[col].width = w

    # ---------- Supplier spend ----------
    ws = wb.create_sheet("Supplier spend")
    ws.append(["Supplier", "PO lines", "POs", "Products supplied",
               "Total spend (PKR)", "Share %"])
    style_header(ws, 1, 6)
    rows = conn.execute("""SELECT supplier_name, po_lines, po_count,
        products_supplied, total_spend_pkr FROM mart_supplier_spend
        ORDER BY total_spend_pkr DESC""").fetchall()
    for row in rows:
        ws.append(list(row))
    for r in range(2, 2 + len(rows)):
        money(ws.cell(row=r, column=5))
        c = ws.cell(row=r, column=6, value=f"=E{r}/$E$9")
        c.number_format = PCT
    total = 2 + len(rows)  # row 9
    total_row(ws, total, 6, [2, 3, 4, 5])
    money(ws.cell(row=total, column=5))
    c = ws.cell(row=total, column=6, value=f"=SUM(F2:F{total - 1})")
    c.number_format = PCT
    c.font = TOTAL_FONT
    for col, w in zip("ABCDEF", [32, 10, 8, 17, 18, 10]):
        ws.column_dimensions[col].width = w

    # ---------- Method ----------
    ws = wb.create_sheet("Method")
    ws["A1"] = "Method — how every number is made"
    ws["A1"].font = TITLE_FONT
    ws["A1"].fill = TITLE_FILL
    notes = [
        "SAMPLE data: Ravi Traders is a fictional wholesale distributor in Lahore.",
        "The 3 source CSVs are demo data (Jul–Dec 2026), clearly labelled SAMPLE.",
        "Medallion layers: bronze = CSVs as received; silver = cleaned; gold = star schema + marts.",
        "This is Databricks-STYLE: the same bronze -> silver -> gold pattern, runnable here on SQLite.",
        "There is no Databricks workspace, no .dbx file and no Delta Lake file in this repo.",
        "Sales gross = SUM of line_total_pkr over the 512 clean sale lines.",
        "Gross profit = line_total - qty x cost price (standard cost from the product master).",
        "Margin % = gross profit / gross sales.",
        "8 raw sale lines were rejected in silver: 2 duplicates, 3 qty <= 0,",
        "2 unknown products (PRD-997, PRD-998), 1 wrong line total. See outputs/dq_report.md.",
        "Inventory value = stock qty x cost price. Stock = purchased qty - sold qty.",
        "Stock status: LOW when stock is under 10% of what was bought; OUT at zero or less.",
        "Supplier share % = supplier spend / total purchase spend.",
        "Rebuild the lakehouse any time with: python3 src/build_lakehouse.py",
        "Re-run the tests with: python3 src/run_tests.py (16 tests, all must pass).",
        "Verify everything with: python3 src/checks.py",
    ]
    for i, line in enumerate(notes, start=3):
        ws.cell(row=i, column=1, value=line)
    ws.column_dimensions["A"].width = 95

    conn.close()
    wb.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
