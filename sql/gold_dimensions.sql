-- P25 — gold_dimensions.sql (gold model, medallion layer 3)
-- Loads the four dimensions. The shop and supplier masters are small
-- reference lists the client keeps outside the transaction exports, so
-- they are loaded here as VALUES (documented in data/README.md); the
-- product master comes from the products CSV via silver_products, and the
-- date dimension is generated for the whole period with a recursive CTE.
-- SCD policy: dim_product is Type 1 — one row per product, overwritten
-- when a price changes. History is NOT kept; if the client later needs
-- price history, dim_product becomes Type 2 (valid_from / valid_to).
-- dim_date covers 2026-07-01 .. 2026-12-31 (184 days), the full SAMPLE
-- period, so every sale and purchase date joins.
-- In real Databricks these are gold Delta tables built from silver
-- (see databricks/mapping.md).

-- dim_product (SCD Type 1)
INSERT INTO dim_product
SELECT product_code, product_name, category, supplier_id, unit,
       cost_price_pkr, sell_price_pkr
FROM silver_products;

-- dim_supplier (reference list)
INSERT INTO dim_supplier (supplier_id, supplier_name, city) VALUES
('SUP-01', 'Chenab Rice Mills', 'Gujranwala'),
('SUP-02', 'Ravi Flour Mills', 'Lahore'),
('SUP-03', 'Jhang Sugar Traders', 'Jhang'),
('SUP-04', 'Al-Haq Oil & Ghee', 'Lahore'),
('SUP-05', 'Multan Pulses Traders', 'Multan'),
('SUP-06', 'Kashmiri Masala House', 'Lahore'),
('SUP-07', 'Punjab Tea & Dry Fruit Traders', 'Lahore');

-- dim_shop (reference list — the 22 shops Ravi Traders supplies)
INSERT INTO dim_shop (shop_id, shop_name, area, city) VALUES
('SHP-01', 'Usman Karyana Store', 'Akbari Mandi', 'Lahore'),
('SHP-02', 'Al-Noor General Store', 'Shah Alam Market', 'Lahore'),
('SHP-03', 'Bilal Cash & Carry', 'Ichhra', 'Lahore'),
('SHP-04', 'Haji Ahmed & Sons', 'Township', 'Lahore'),
('SHP-05', 'Rehman Store', 'Gulberg III', 'Lahore'),
('SHP-06', 'Chaudhry Karyana', 'Model Town', 'Lahore'),
('SHP-07', 'Zain Super Store', 'Johar Town', 'Lahore'),
('SHP-08', 'Bismillah General Store', 'Samanabad', 'Lahore'),
('SHP-09', 'Noor Traders', 'DHA Phase 5', 'Lahore'),
('SHP-10', 'Shahzad Karyana', 'Faisal Town', 'Lahore'),
('SHP-11', 'Al-Habib Store', 'Green Town', 'Lahore'),
('SHP-12', 'Malik & Sons', 'Sabzazar', 'Lahore'),
('SHP-13', 'Rana General Store', 'Cavalry Ground', 'Lahore'),
('SHP-14', 'Imran Karyana', 'Mughalpura', 'Lahore'),
('SHP-15', 'Siddique Store', 'Shadbagh', 'Lahore'),
('SHP-16', 'Al-Rehman Traders', 'Allama Iqbal Town', 'Lahore'),
('SHP-17', 'Farooq General Store', 'Bhatti Gate', 'Lahore'),
('SHP-18', 'Naseer Cash & Carry', 'Misri Shah', 'Lahore'),
('SHP-19', 'Tariq Store', 'Wapda Town', 'Lahore'),
('SHP-20', 'Hassan Traders', 'Gulshan-e-Ravi', 'Lahore'),
('SHP-21', 'Khan Karyana Store', 'Ravi Road', 'Lahore'),
('SHP-22', 'Al-Madina Super Store', 'Wahdat Road', 'Lahore');

-- dim_date: every day 2026-07-01 .. 2026-12-31
WITH RECURSIVE days(d) AS (
    SELECT DATE('2026-07-01')
    UNION ALL
    SELECT DATE(d, '+1 day') FROM days WHERE d < DATE('2026-12-31')
)
INSERT INTO dim_date
SELECT
    d AS date_key,
    d AS full_date,
    CAST(strftime('%Y', d) AS INTEGER) AS year,
    CAST(strftime('%m', d) AS INTEGER) AS month,
    CASE CAST(strftime('%m', d) AS INTEGER)
        WHEN 1 THEN 'January' WHEN 2 THEN 'February' WHEN 3 THEN 'March'
        WHEN 4 THEN 'April' WHEN 5 THEN 'May' WHEN 6 THEN 'June'
        WHEN 7 THEN 'July' WHEN 8 THEN 'August' WHEN 9 THEN 'September'
        WHEN 10 THEN 'October' WHEN 11 THEN 'November' ELSE 'December' END AS month_name,
    (CAST(strftime('%m', d) AS INTEGER) - 1) / 3 + 1 AS quarter,
    CAST(strftime('%w', d) AS INTEGER) AS day_of_week,
    CASE CAST(strftime('%w', d) AS INTEGER)
        WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'
        ELSE 'Saturday' END AS day_name,
    CASE WHEN CAST(strftime('%w', d) AS INTEGER) IN (0, 6) THEN 1 ELSE 0 END AS is_weekend
FROM days;
