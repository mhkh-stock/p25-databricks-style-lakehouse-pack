"""Build the Ravi Traders (SAMPLE) lakehouse into data/processed/lakehouse.db.

Medallion order of operations:
  1. schema.sql               — bronze landing tables + gold star-schema DDL
  2. load raw CSVs into bronze_sales / bronze_purchases / bronze_products
  3. silver_*.sql             — silver models (cleaning, rejection guards)
  4. silver_sales_enriched.sql — silver enrichment (joins + margins)
  5. gold_dimensions.sql      — dim_product / dim_supplier / dim_shop / dim_date
  6. gold_facts.sql           — fact_sales + fact_purchases
  7. gold_marts.sql           — the 4 gold marts
  8. export processed CSVs (facts) and mart CSVs (outputs)

Rejection counts per reason are printed, so the build log shows exactly
which raw lines were dropped and why (the 8 planted defects).

Usage:  python3 src/build_lakehouse.py
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL = ROOT / "sql"
DB = ROOT / "data" / "processed" / "lakehouse.db"
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"

MODELS = [
    "silver_sales.sql",
    "silver_purchases.sql",
    "silver_products.sql",
    "silver_sales_enriched.sql",
    "gold_dimensions.sql",
    "gold_facts.sql",
    "gold_marts.sql",
]


def run_sql(conn, path):
    conn.executescript(path.read_text(encoding="utf-8"))


def load_csv(conn, table, path, columns):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    placeholders = ", ".join("?" * (len(columns) + 1))
    cols = "raw_line_no, " + ", ".join(columns)
    for i, row in enumerate(rows, start=1):
        conn.execute(
            f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
            [i] + [row[c] for c in columns],
        )
    return len(rows)


def one(conn, sql):
    return conn.execute(sql).fetchone()[0]


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")

    run_sql(conn, SQL / "schema.sql")

    n_sales = load_csv(conn, "bronze_sales", ROOT / "data/raw/sales_SAMPLE.csv",
                       ["order_id", "sale_date", "shop_id", "product_code",
                        "qty", "unit_price_pkr", "line_total_pkr"])
    n_purch = load_csv(conn, "bronze_purchases", ROOT / "data/raw/purchases_SAMPLE.csv",
                       ["po_id", "purchase_date", "supplier_id", "product_code",
                        "qty", "unit_cost_pkr", "total_cost_pkr"])
    n_prod = load_csv(conn, "bronze_products", ROOT / "data/raw/products_SAMPLE.csv",
                      ["product_code", "product_name", "category", "supplier_id",
                       "unit", "cost_price_pkr", "sell_price_pkr"])
    conn.commit()
    print(f"bronze_sales:     {n_sales} lines")
    print(f"bronze_purchases: {n_purch} lines")
    print(f"bronze_products:  {n_prod} products")

    for model in MODELS:
        run_sql(conn, SQL / model)
        conn.commit()
        print(f"ran {model}")

    # --- rejection breakdown (why each raw sale line was dropped) ---
    dup_extra = n_sales - one(conn, """SELECT COUNT(*) FROM (
        SELECT DISTINCT order_id, sale_date, shop_id, product_code,
        qty, unit_price_pkr, line_total_pkr FROM bronze_sales)""")
    bad_qty = one(conn, "SELECT COUNT(*) FROM bronze_sales WHERE qty <= 0")
    unknown = one(conn, """SELECT COUNT(*) FROM bronze_sales WHERE product_code
        NOT IN (SELECT product_code FROM bronze_products)""")
    bad_total = one(conn, """SELECT COUNT(*) FROM bronze_sales
        WHERE line_total_pkr <> qty * unit_price_pkr""")
    print(f"rejected: {dup_extra} duplicate lines, {bad_qty} qty<=0 lines, "
          f"{unknown} unknown-product lines, {bad_total} wrong-total lines")
    print(f"rejected total: {n_sales - one(conn, 'SELECT COUNT(*) FROM silver_sales')} "
          f"of {n_sales} raw sale lines")

    # --- row counts per table ---
    print("\nrow counts:")
    for table in ["silver_sales", "silver_purchases", "silver_products",
                  "silver_sales_enriched", "dim_date", "dim_product",
                  "dim_shop", "dim_supplier", "fact_sales",
                  "fact_purchases", "mart_sales_by_category",
                  "mart_sales_by_month", "mart_inventory",
                  "mart_supplier_spend"]:
        print(f"  {table:<24} {one(conn, f'SELECT COUNT(*) FROM {table}')}")

    # --- headline totals ---
    gross = one(conn, "SELECT SUM(line_total_pkr) FROM fact_sales")
    profit = one(conn, "SELECT SUM(gross_profit_pkr) FROM fact_sales")
    spend = one(conn, "SELECT SUM(total_cost_pkr) FROM fact_purchases")
    stock = one(conn, "SELECT SUM(stock_value_pkr) FROM mart_inventory")
    print(f"\nsales gross (clean):   PKR {gross:,}")
    print(f"gross profit (clean):  PKR {profit:,}")
    print(f"purchase spend:        PKR {spend:,}")
    print(f"inventory value:       PKR {stock:,}")

    # --- processed CSV exports (facts) ---
    fact_exports = {
        "fact_sales.csv": "SELECT * FROM fact_sales ORDER BY sale_line_id",
        "fact_purchases.csv": "SELECT * FROM fact_purchases ORDER BY po_line_id",
    }
    for name, query in fact_exports.items():
        cur = conn.execute(query)
        with open(PROCESSED / name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([d[0] for d in cur.description])
            w.writerows(cur.fetchall())
        print(f"wrote data/processed/{name}")

    # --- gold mart CSVs (the deliverable tables, in outputs/) ---
    mart_exports = {
        "mart_sales_by_category.csv": """SELECT * FROM mart_sales_by_category
            ORDER BY gross_pkr DESC""",
        "mart_sales_by_month.csv": """SELECT * FROM mart_sales_by_month
            ORDER BY month""",
        "mart_inventory.csv": """SELECT * FROM mart_inventory
            ORDER BY product_code""",
        "mart_supplier_spend.csv": """SELECT * FROM mart_supplier_spend
            ORDER BY total_spend_pkr DESC""",
    }
    for name, query in mart_exports.items():
        cur = conn.execute(query)
        with open(OUTPUTS / name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([d[0] for d in cur.description])
            w.writerows(cur.fetchall())
        print(f"wrote outputs/{name}")

    conn.close()
    print(f"\nlakehouse built: data/processed/lakehouse.db")


if __name__ == "__main__":
    main()
