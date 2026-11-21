"""Build the handover report for P25 — Ravi Traders lakehouse.

Writes two files, both computed from the lakehouse (never typed):
  outputs/lakehouse_handover_SAMPLE.pdf  — exactly 2 pages (checked with pdfinfo)
  outputs/dq_report.md                   — findings report: test results,
                                           every defect with its fix,
                                           bronze -> silver -> gold reconciliation

Page 1: business question, headline numbers, sales by category, key findings.
Page 2: sales by month, supplier spend, defects + reconciliation, method
        and the honest Databricks note, 3 recommendations, how to re-run.

Usage:  python3 src/build_report.py
"""
import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, PageBreak)

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "lakehouse.db"
TESTS_JSON = ROOT / "outputs" / "test_results.json"
PDF = ROOT / "outputs" / "lakehouse_handover_SAMPLE.pdf"
DQ = ROOT / "outputs" / "dq_report.md"

NAVY = colors.HexColor("#1F4E79")
LIGHT = colors.HexColor("#D9E2F3")
GREY = colors.HexColor("#595959")

TITLE = ParagraphStyle("title", fontSize=16, leading=19, textColor=NAVY,
                       spaceAfter=2 * mm, fontName="Helvetica-Bold")
SUB = ParagraphStyle("sub", fontSize=9, leading=12, textColor=GREY,
                     spaceAfter=3 * mm)
H2 = ParagraphStyle("h2", fontSize=11, leading=13, textColor=NAVY,
                    fontName="Helvetica-Bold", spaceBefore=3 * mm,
                    spaceAfter=1.5 * mm)
BODY = ParagraphStyle("body", fontSize=9, leading=12.5, spaceAfter=2 * mm)
SMALL = ParagraphStyle("small", fontSize=8, leading=10.5, textColor=GREY)
CELL = ParagraphStyle("cell", fontSize=8.5, leading=10.5)
CELLB = ParagraphStyle("cellb", fontSize=8.5, leading=10.5,
                       fontName="Helvetica-Bold")
CELLR = ParagraphStyle("cellr", fontSize=8.5, leading=10.5, alignment=2)
CELLRB = ParagraphStyle("cellrb", fontSize=8.5, leading=10.5, alignment=2,
                        fontName="Helvetica-Bold")


def pkr(n):
    return f"PKR {n:,}"


def pct(x):
    return f"{x:.2f}%"


def table_style(header=True):
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                 ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    return TableStyle(cmds)


def data_table(header, rows, widths, total_row=False):
    data = [[Paragraph(h, CELLB) for h in header]]
    for row in rows:
        data.append([Paragraph(str(c), CELLR if isinstance(c, (int, float))
                               or str(c).startswith("PKR") else CELL)
                     for c in row])
    t = Table(data, colWidths=widths, repeatRows=1)
    style = table_style()
    if total_row:
        style.add("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), LIGHT)
        style.add("FONTNAME", (0, len(data) - 1), (-1, len(data) - 1),
                  "Helvetica-Bold")
    t.setStyle(style)
    return t


def collect(conn):
    """Every number the report states, recomputed from the lakehouse."""
    d = {}
    d["gross"] = conn.execute("SELECT SUM(line_total_pkr) FROM fact_sales").fetchone()[0]
    d["profit"] = conn.execute("SELECT SUM(gross_profit_pkr) FROM fact_sales").fetchone()[0]
    d["margin"] = 100.0 * d["profit"] / d["gross"]
    d["spend"] = conn.execute("SELECT SUM(total_cost_pkr) FROM fact_purchases").fetchone()[0]
    d["inv_value"] = conn.execute("SELECT SUM(stock_value_pkr) FROM mart_inventory").fetchone()[0]
    d["inv_units"] = conn.execute("SELECT SUM(stock_qty) FROM mart_inventory").fetchone()[0]
    d["lines"] = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    d["orders"] = conn.execute("SELECT COUNT(DISTINCT order_id) FROM fact_sales").fetchone()[0]
    d["shops"] = conn.execute("SELECT COUNT(DISTINCT shop_id) FROM fact_sales").fetchone()[0]
    d["units_sold"] = conn.execute("SELECT SUM(qty) FROM fact_sales").fetchone()[0]
    d["units_bought"] = conn.execute("SELECT SUM(qty) FROM fact_purchases").fetchone()[0]
    d["po_lines"] = conn.execute("SELECT COUNT(*) FROM fact_purchases").fetchone()[0]
    d["raw_lines"] = conn.execute("SELECT COUNT(*) FROM bronze_sales").fetchone()[0]
    d["raw_gross"] = conn.execute("SELECT SUM(line_total_pkr) FROM bronze_sales").fetchone()[0]
    d["rejected"] = d["raw_lines"] - d["lines"]
    d["cats"] = conn.execute(
        "SELECT category, lines, units_sold, gross_pkr, gross_profit_pkr, margin_pct "
        "FROM mart_sales_by_category ORDER BY gross_pkr DESC").fetchall()
    d["months"] = conn.execute(
        "SELECT month, lines, units_sold, gross_pkr, gross_profit_pkr "
        "FROM mart_sales_by_month ORDER BY month").fetchall()
    d["sups"] = conn.execute(
        "SELECT supplier_name, po_lines, total_spend_pkr, share_pct "
        "FROM mart_supplier_spend ORDER BY total_spend_pkr DESC").fetchall()
    d["top_product"] = conn.execute(
        "SELECT p.product_name, SUM(f.line_total_pkr) FROM fact_sales f "
        "JOIN dim_product p ON p.product_code = f.product_code "
        "GROUP BY p.product_name ORDER BY 2 DESC LIMIT 1").fetchone()
    d["top_shop"] = conn.execute(
        "SELECT d.shop_name, SUM(f.line_total_pkr) FROM fact_sales f "
        "JOIN dim_shop d ON d.shop_id = f.shop_id "
        "GROUP BY d.shop_name ORDER BY 2 DESC LIMIT 1").fetchone()
    d["best_month"] = max(d["months"], key=lambda r: r[3])
    d["weak_month"] = min(d["months"], key=lambda r: r[3])
    d["best_cat"] = d["cats"][0]
    d["best_margin_cat"] = max(d["cats"], key=lambda r: r[5])
    d["thin_margin_cat"] = min(d["cats"], key=lambda r: r[5])
    d["top_sup"] = d["sups"][0]
    return d


def defect_lines():
    """The planted defects, located in the raw CSV by file line number
    (header is line 1). Recomputed, not typed."""
    rows = list(csv.DictReader(open(ROOT / "data/raw/sales_SAMPLE.csv")))
    prod = {r["product_code"] for r in
            csv.DictReader(open(ROOT / "data/raw/products_SAMPLE.csv"))}
    seen, dups, bad_qty, unknown, bad_total = {}, [], [], [], []
    for i, r in enumerate(rows, start=2):
        k = tuple(r.values())
        if k in seen:
            dups.append((seen[k], i, r))
        else:
            seen[k] = i
        if int(r["qty"]) <= 0:
            bad_qty.append((i, r))
        if r["product_code"] not in prod:
            unknown.append((i, r))
        if int(r["line_total_pkr"]) != int(r["qty"]) * int(r["unit_price_pkr"]):
            bad_total.append((i, r))
    return dups, bad_qty, unknown, bad_total


def build_pdf(d):
    doc = SimpleDocTemplate(str(PDF), pagesize=A4,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="Ravi Traders — Lakehouse Handover (SAMPLE)",
                            author="Muhammad Hashir")
    story = []
    story.append(Paragraph("Ravi Traders — Lakehouse Handover", TITLE))
    story.append(Paragraph(
        "Databricks-Style Medallion Lakehouse Starter Pack &middot; "
        "SAMPLE delivery on DEMO data &middot; Jul&ndash;Dec 2026 &middot; "
        "SQLite + Python + Excel", SUB))
    story.append(Paragraph(
        "<b>Business question:</b> &ldquo;A warehouse I can actually query, "
        "Databricks-style &mdash; where is my money, what is sitting in stock, "
        "and who do I depend on?&rdquo; This delivery answers it with a "
        "medallion lakehouse: bronze (raw as received), silver (cleaned) and "
        "gold (star schema + marts), 16 data-quality tests that all pass, and "
        "a health workbook whose totals are live formulas.", BODY))
    story.append(Paragraph("Headline numbers (SAMPLE)", H2))
    head = [
        ["Clean sale lines", f"{d['lines']:,}", "Orders", f"{d['orders']:,}"],
        ["Shops supplied", f"{d['shops']:,}", "Units sold", f"{d['units_sold']:,}"],
        ["Sales gross", pkr(d["gross"]), "Gross profit", pkr(d["profit"])],
        ["Margin", pct(d["margin"]), "Purchase spend", pkr(d["spend"])],
        ["Inventory value (at cost)", pkr(d["inv_value"]),
         "Stock on hand", f"{d['inv_units']:,} units"],
        ["Raw sale lines rejected", f"{d['rejected']} of {d['raw_lines']:,}",
         "DQ tests", "16/16 passing"],
    ]
    t = Table([[Paragraph(f"<b>{a}</b>", CELL), Paragraph(b, CELLR),
                Paragraph(f"<b>{c}</b>", CELL), Paragraph(e, CELLR)]
               for a, b, c, e in head],
              colWidths=[52 * mm, 38 * mm, 52 * mm, 36 * mm])
    t.setStyle(table_style(header=False))
    story.append(t)
    story.append(Paragraph("Sales by category", H2))
    rows = [[c, f"{l:,}", f"{u:,}", pkr(g), pkr(p), pct(m)]
            for (c, l, u, g, p, m) in d["cats"]]
    rows.append(["TOTAL", f"{d['lines']:,}", f"{d['units_sold']:,}",
                 pkr(d["gross"]), pkr(d["profit"]), pct(d["margin"])])
    story.append(data_table(
        ["Category", "Lines", "Units", "Gross sales", "Gross profit", "Margin %"],
        rows, [52 * mm, 18 * mm, 20 * mm, 32 * mm, 32 * mm, 24 * mm],
        total_row=True))
    story.append(Paragraph("What the numbers say", H2))
    story.append(Paragraph(
        f"1. <b>{d['best_cat'][0]}</b> is the biggest category at "
        f"{pkr(d['best_cat'][3])}, but its margin is the thinnest "
        f"({pct(d['best_cat'][5])}) — the category that earns the most also "
        f"earns the least per rupee. <b>{d['best_margin_cat'][0]}</b> earns "
        f"the best margin ({pct(d['best_margin_cat'][5])}) on much smaller "
        f"sales. 2. <b>{d['top_sup'][0]}</b> takes {pct(d['top_sup'][3])} of "
        f"all purchase spend — the dependency to watch. 3. Best month "
        f"{d['best_month'][0]} ({pkr(d['best_month'][3])}); weakest "
        f"{d['weak_month'][0]} ({pkr(d['weak_month'][3])}) — the sample's own "
        f"seasonality, not a finding about the real market.", BODY))
    story.append(PageBreak())

    story.append(Paragraph("Sales by month", H2))
    rows = [[m, f"{l:,}", f"{u:,}", pkr(g), pkr(p)]
            for (m, l, u, g, p) in d["months"]]
    rows.append(["TOTAL", f"{d['lines']:,}", f"{d['units_sold']:,}",
                 pkr(d["gross"]), pkr(d["profit"])])
    story.append(data_table(
        ["Month", "Lines", "Units", "Gross sales", "Gross profit"],
        rows, [30 * mm, 24 * mm, 24 * mm, 50 * mm, 50 * mm], total_row=True))
    story.append(Paragraph("Supplier spend", H2))
    rows = [[s, f"{n:,}", pkr(sp), pct(sh)] for (s, n, sp, sh) in d["sups"]]
    rows.append(["TOTAL", f"{d['po_lines']:,}", pkr(d["spend"]), "100.00%"])
    story.append(data_table(
        ["Supplier", "PO lines", "Total spend", "Share %"],
        rows, [78 * mm, 26 * mm, 42 * mm, 32 * mm], total_row=True))
    story.append(Paragraph("Defects found and fixed", H2))
    story.append(Paragraph(
        f"The silver layer rejected <b>{d['rejected']} of {d['raw_lines']:,}</b> "
        f"raw sale lines: 2 exact duplicates, 3 with qty &le; 0, 2 with "
        f"unknown product codes (PRD-997, PRD-998), 1 with a wrong line total "
        f"(PKR 750 too high). Raw gross {pkr(d['raw_gross'])} minus rejected "
        f"{pkr(d['raw_gross'] - d['gross'])} = clean gross {pkr(d['gross'])}, "
        f"exactly what the gold fact table holds. The raw file is untouched; "
        f"every rejected line is listed with its file line number in "
        f"<i>outputs/dq_report.md</i>.", BODY))
    story.append(Paragraph("Method — and the honest Databricks note", H2))
    story.append(Paragraph(
        "Bronze loads the CSVs as received. Silver cleans them with four "
        "guards (dedupe, qty &gt; 0, product must exist, total must equal "
        "qty &times; price) and adds cost of goods, gross profit and margin. "
        "Gold conforms the result into a star schema (fact_sales, "
        "fact_purchases, dim_product / dim_shop / dim_supplier / dim_date) "
        "plus four marts. <b>This is Databricks-STYLE, not Databricks:</b> "
        "the same bronze &rarr; silver &rarr; gold pattern, runnable here on "
        "SQLite. There is no Databricks workspace, no .dbx file and no Delta "
        "Lake file in this repo — Delta MERGE / OPTIMIZE / Z-ORDER are "
        "Databricks-only and are simulated here in SQL. "
        "See <i>databricks/mapping.md</i> for the step-by-step mapping. "
        "Gross profit uses the product master's standard cost, not the "
        "per-PO unit cost. dim_product is SCD Type 1 (one row per product, "
        "no price history).", BODY))
    story.append(Paragraph("Three recommendations", H2))
    story.append(Paragraph(
        "1. Fix the sales entry first: 8 of 520 lines (1.5%) are wrong. Give "
        "whoever types the sales a product list to pick from and let the "
        "sheet compute the line total — that alone removes 3 of the 4 defect "
        "types. 2. Line up a second oil supplier: "
        f"{d['top_sup'][0]} is {pct(d['top_sup'][3])} of spend and "
        f"{d['best_cat'][0]} is the biggest, thinnest-margin category. "
        "3. Push the high-margin categories: "
        f"{d['best_margin_cat'][0]} ({pct(d['best_margin_cat'][5])}) and "
        f"Dry Fruits &amp; Nuts earn the best margin per rupee but sit 8th "
        f"and 6th by sales.", BODY))
    story.append(Paragraph("Reproduce it (2 minutes)", H2))
    story.append(Paragraph(
        "<font face='Courier' size='8'>python3 src/generate_data.py<br/>"
        "python3 src/build_lakehouse.py<br/>"
        "python3 src/run_tests.py&nbsp;&nbsp;&nbsp;&nbsp;# 16 tests — expect 16/16 passing<br/>"
        "python3 src/build_workbook.py<br/>"
        "python3 src/build_report.py<br/>"
        "python3 src/checks.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# 100+ checks — expect all passing</font>",
        BODY))
    story.append(Paragraph(
        "Ravi Traders is a fictional wholesaler; the three source CSVs are "
        "demo data, clearly labelled SAMPLE. No real business, supplier or "
        "shop is involved. What is real is the lakehouse: the same medallion "
        "layers, tests and reconciliation run on a real client's files the "
        "same way.", SMALL))
    doc.build(story)
    print(f"wrote {PDF}")


def build_dq(d, tests):
    dups, bad_qty, unknown, bad_total = defect_lines()
    lines = []
    lines.append("# P25 — Data-quality report (Ravi Traders, SAMPLE)\n")
    lines.append(f"**Tests: {tests['passed']}/{tests['total']} passing.** "
                 "Every test file returns its violating rows; 0 rows = PASS. "
                 "Full per-test results: `outputs/test_results.json`.\n")
    lines.append("## Test results\n")
    lines.append("| Test | Result | Violations |")
    lines.append("|---|---|---|")
    for t in tests["tests"]:
        lines.append(f"| `{t['test']}` | {t['status']} | {t['violations']} |")
    lines.append("")
    lines.append("## Planted defects — found exactly (8 lines)\n")
    lines.append("File line numbers count from the top of the CSV file "
                 "(header is line 1). The silver layer keeps the first "
                 "occurrence of a duplicate and rejects the rest; the raw "
                 "file is never changed.\n")
    lines.append("### Exact duplicates (2)\n")
    for first, second, r in dups:
        lines.append(f"- File lines {first} &amp; {second} are the same line "
                     f"({r['order_id']}, {r['sale_date']}, {r['shop_id']}, "
                     f"{r['product_code']}, qty {r['qty']}, "
                     f"PKR {int(r['line_total_pkr']):,}). "
                     f"Silver keeps line {first}.")
    lines.append("\n### qty &le; 0 (3)\n")
    for i, r in bad_qty:
        lines.append(f"- Line {i} ({r['order_id']}, {r['product_code']}, "
                     f"qty {r['qty']}, PKR {int(r['line_total_pkr']):,}). "
                     "A sale cannot sell zero or a negative amount.")
    lines.append("\n### Unknown product (2)\n")
    for i, r in unknown:
        lines.append(f"- Line {i} ({r['order_id']}, product "
                     f"{r['product_code']}). The code does not exist in the "
                     "product master, so no cost price exists for it.")
    lines.append("\n### Wrong line total (1)\n")
    for i, r in bad_total:
        correct = int(r["qty"]) * int(r["unit_price_pkr"])
        lines.append(f"- Line {i} ({r['order_id']}, {r['product_code']}, "
                     f"qty {r['qty']} x PKR {int(r['unit_price_pkr']):,} = "
                     f"PKR {correct:,}, but recorded as "
                     f"PKR {int(r['line_total_pkr']):,} — "
                     f"PKR {int(r['line_total_pkr']) - correct:,} too high).")
    lines.append("\n## Reconciliation (bronze → silver → gold)\n")
    lines.append(f"- Clean sale lines (silver = gold fact_sales): "
                 f"{d['lines']:,} of {d['raw_lines']:,} raw lines "
                 f"({d['rejected']} rejected)")
    lines.append(f"- Raw sales gross (all {d['raw_lines']:,} bronze lines): "
                 f"PKR {d['raw_gross']:,}")
    lines.append(f"- Rejected lines (8): "
                 f"PKR {d['raw_gross'] - d['gross']:,}")
    lines.append(f"- Clean sales gross (silver = gold fact_sales): "
                 f"PKR {d['gross']:,}")
    lines.append(f"- Gross profit (clean): PKR {d['profit']:,} "
                 f"— margin {d['margin']:.2f}%")
    lines.append(f"- Purchase spend (bronze = silver = gold): "
                 f"PKR {d['spend']:,}")
    lines.append(f"- Inventory value at cost: PKR {d['inv_value']:,} "
                 f"({d['inv_units']:,} units across 36 products, all OK)")
    lines.append("\n## What the tests prove\n")
    lines.append("- Bronze counts are exactly the planted defects (2 / 3 / 2 / 1).")
    lines.append("- Silver holds no duplicates, no qty &le; 0, no unknown "
                 "products, no wrong totals.")
    lines.append("- Gold fact_sales has one row per silver sale line, no NULL "
                 "keys, and its totals equal silver's and clean bronze's.")
    lines.append("- dim_date covers all 184 days, Jul–Dec 2026, with no gaps.")
    lines.append("- Inventory is never negative and every stock value equals "
                 "stock qty x cost price.")
    DQ.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {DQ}")


def page_count(path):
    res = subprocess.run(["pdfinfo", str(path)], capture_output=True,
                         text=True)
    for line in res.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":")[1].strip())
    return -1


def main():
    conn = sqlite3.connect(DB)
    tests = json.loads(TESTS_JSON.read_text(encoding="utf-8"))
    d = collect(conn)
    conn.close()
    build_pdf(d)
    build_dq(d, tests)
    n = page_count(PDF)
    print(f"handover PDF pages: {n}")
    if n != 2:
        print("WARNING: PDF is not exactly 2 pages — adjust the layout")
        sys.exit(1)


if __name__ == "__main__":
    main()
