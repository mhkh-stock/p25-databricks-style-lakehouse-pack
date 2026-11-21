-- P25 — Databricks-Style Medallion Lakehouse Starter Pack (Ravi Traders, SAMPLE)
-- schema.sql — bronze landing tables + gold star-schema DDL.
-- Runs on SQLite. Created by src/build_lakehouse.py before the models.
--
-- Medallion layers (Databricks-style, runnable here on SQLite — see
-- databricks/mapping.md for what each step maps to in real Databricks):
--   BRONZE  bronze_sales / bronze_purchases / bronze_products
--           — the client CSVs exactly as received, plus raw_line_no
--             (the CSV data-row number) so a rejected line is traceable.
--   SILVER  silver_sales / silver_purchases / silver_products
--           — cleaned: duplicates, bad quantities, unknown products and
--             wrong totals rejected (see sql/silver_*.sql).
--           silver_sales_enriched adds COGS, gross profit and margin.
--   GOLD    fact_sales (one row per clean sale line)
--           fact_purchases (one row per purchase-order line)
--           dim_product (SCD Type 1), dim_shop, dim_supplier, dim_date
--           mart_sales_by_category / mart_sales_by_month /
--           mart_inventory / mart_supplier_spend (the tables the business queries)

DROP TABLE IF EXISTS bronze_sales;
CREATE TABLE bronze_sales (
    raw_line_no    INTEGER PRIMARY KEY,
    order_id       TEXT    NOT NULL,
    sale_date      TEXT    NOT NULL,  -- yyyy-mm-dd
    shop_id        TEXT    NOT NULL,
    product_code   TEXT    NOT NULL,
    qty            INTEGER NOT NULL,
    unit_price_pkr INTEGER NOT NULL,
    line_total_pkr INTEGER NOT NULL
);

DROP TABLE IF EXISTS bronze_purchases;
CREATE TABLE bronze_purchases (
    raw_line_no    INTEGER PRIMARY KEY,
    po_id          TEXT    NOT NULL,
    purchase_date  TEXT    NOT NULL,  -- yyyy-mm-dd
    supplier_id    TEXT    NOT NULL,
    product_code   TEXT    NOT NULL,
    qty            INTEGER NOT NULL,
    unit_cost_pkr  INTEGER NOT NULL,
    total_cost_pkr INTEGER NOT NULL
);

DROP TABLE IF EXISTS bronze_products;
CREATE TABLE bronze_products (
    raw_line_no     INTEGER PRIMARY KEY,
    product_code    TEXT NOT NULL,
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,
    supplier_id     TEXT NOT NULL,
    unit            TEXT NOT NULL,
    cost_price_pkr  INTEGER NOT NULL,
    sell_price_pkr  INTEGER NOT NULL
);

DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (
    date_key    TEXT PRIMARY KEY,  -- yyyy-mm-dd
    full_date   TEXT NOT NULL,
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    month_name  TEXT NOT NULL,
    quarter     INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,  -- 0 = Sunday .. 6 = Saturday (SQLite strftime %w)
    day_name    TEXT NOT NULL,
    is_weekend  INTEGER NOT NULL   -- 1 = Sat/Sun, else 0
);

DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product (
    product_code    TEXT PRIMARY KEY,
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,
    supplier_id     TEXT NOT NULL,
    unit            TEXT NOT NULL,
    cost_price_pkr  INTEGER NOT NULL,
    sell_price_pkr  INTEGER NOT NULL
);

DROP TABLE IF EXISTS dim_shop;
CREATE TABLE dim_shop (
    shop_id    TEXT PRIMARY KEY,
    shop_name  TEXT NOT NULL,
    area       TEXT NOT NULL,
    city       TEXT NOT NULL DEFAULT 'Lahore'
);

DROP TABLE IF EXISTS dim_supplier;
CREATE TABLE dim_supplier (
    supplier_id   TEXT PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    city          TEXT NOT NULL
);

DROP TABLE IF EXISTS fact_sales;
CREATE TABLE fact_sales (
    sale_line_id   INTEGER PRIMARY KEY,  -- = raw_line_no of the clean line
    order_id       TEXT    NOT NULL,
    sale_date      TEXT    NOT NULL,
    shop_id        TEXT    NOT NULL,
    product_code   TEXT    NOT NULL,
    qty            INTEGER NOT NULL,
    unit_price_pkr INTEGER NOT NULL,
    line_total_pkr INTEGER NOT NULL,
    cost_price_pkr INTEGER NOT NULL,
    gross_profit_pkr INTEGER NOT NULL,
    margin_pct     REAL    NOT NULL,
    FOREIGN KEY (sale_date)   REFERENCES dim_date (date_key),
    FOREIGN KEY (shop_id)     REFERENCES dim_shop (shop_id),
    FOREIGN KEY (product_code) REFERENCES dim_product (product_code)
);

DROP TABLE IF EXISTS fact_purchases;
CREATE TABLE fact_purchases (
    po_line_id     INTEGER PRIMARY KEY,  -- = raw_line_no of the PO line
    po_id          TEXT    NOT NULL,
    purchase_date  TEXT    NOT NULL,
    supplier_id    TEXT    NOT NULL,
    product_code   TEXT    NOT NULL,
    qty            INTEGER NOT NULL,
    unit_cost_pkr  INTEGER NOT NULL,
    total_cost_pkr INTEGER NOT NULL,
    FOREIGN KEY (purchase_date) REFERENCES dim_date (date_key),
    FOREIGN KEY (supplier_id)   REFERENCES dim_supplier (supplier_id),
    FOREIGN KEY (product_code)  REFERENCES dim_product (product_code)
);
