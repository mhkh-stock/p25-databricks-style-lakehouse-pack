"""Generate the SAMPLE source files for P25 — Ravi Traders (SAMPLE client).

Seeded (seed 20261121) so the same files regenerate exactly.
Writes data/raw/products_SAMPLE.csv, sales_SAMPLE.csv, purchases_SAMPLE.csv.

The sales file deliberately contains 8 planted defects so the data-quality
tests have something real to catch (recorded in data/README.md):
  * 2 exact duplicate lines
  * 3 lines with qty <= 0
  * 2 lines referencing an unknown product (PRD-997, PRD-998)
  * 1 line with a wrong line total (off by PKR 750)
Valid sales lines: 512. Raw sales lines total: 520.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20261121
rng = random.Random(SEED)

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

SUPPLIERS = [
    ("SUP-01", "Chenab Rice Mills", "Gujranwala"),
    ("SUP-02", "Ravi Flour Mills", "Lahore"),
    ("SUP-03", "Jhang Sugar Traders", "Jhang"),
    ("SUP-04", "Al-Haq Oil & Ghee", "Lahore"),
    ("SUP-05", "Multan Pulses Traders", "Multan"),
    ("SUP-06", "Kashmiri Masala House", "Lahore"),
    ("SUP-07", "Punjab Tea & Dry Fruit Traders", "Lahore"),
]

# code, name, category, supplier, unit, cost_price, sell_price (PKR)
PRODUCTS = [
    ("PRD-001", "Basmati Rice 1121 (25 kg bag)", "Rice & Grains", "SUP-01", "25 kg bag", 7300, 7950),
    ("PRD-002", "Super Basmati (10 kg bag)", "Rice & Grains", "SUP-01", "10 kg bag", 2950, 3250),
    ("PRD-003", "Irri-6 Rice (25 kg bag)", "Rice & Grains", "SUP-01", "25 kg bag", 3850, 4250),
    ("PRD-004", "Brown Rice (5 kg bag)", "Rice & Grains", "SUP-01", "5 kg bag", 1650, 1850),
    ("PRD-005", "Barley (10 kg bag)", "Rice & Grains", "SUP-01", "10 kg bag", 1980, 2200),
    ("PRD-006", "Chakki Atta (10 kg bag)", "Flour & Atta", "SUP-02", "10 kg bag", 1180, 1320),
    ("PRD-007", "Chakki Atta (5 kg bag)", "Flour & Atta", "SUP-02", "5 kg bag", 620, 700),
    ("PRD-008", "Fine Maida (5 kg bag)", "Flour & Atta", "SUP-02", "5 kg bag", 640, 720),
    ("PRD-009", "Besan / Gram Flour (2 kg)", "Flour & Atta", "SUP-02", "2 kg", 420, 480),
    ("PRD-010", "Suji / Semolina (2 kg)", "Flour & Atta", "SUP-02", "2 kg", 310, 360),
    ("PRD-011", "White Sugar (50 kg bag)", "Sugar & Sweeteners", "SUP-03", "50 kg bag", 7900, 8400),
    ("PRD-012", "White Sugar (5 kg bag)", "Sugar & Sweeteners", "SUP-03", "5 kg bag", 830, 900),
    ("PRD-013", "Gur / Jaggery (5 kg)", "Sugar & Sweeteners", "SUP-03", "5 kg", 780, 900),
    ("PRD-014", "Honey (1 kg jar)", "Sugar & Sweeteners", "SUP-03", "1 kg jar", 2400, 2750),
    ("PRD-015", "Cooking Oil (16 L tin)", "Cooking Oil & Ghee", "SUP-04", "16 L tin", 9900, 10550),
    ("PRD-016", "Cooking Oil (5 L)", "Cooking Oil & Ghee", "SUP-04", "5 L", 3180, 3430),
    ("PRD-017", "Banaspati Ghee (10 kg tin)", "Cooking Oil & Ghee", "SUP-04", "10 kg tin", 5900, 6300),
    ("PRD-018", "Banaspati Ghee (5 kg)", "Cooking Oil & Ghee", "SUP-04", "5 kg", 2980, 3230),
    ("PRD-019", "Desi Ghee (1 kg)", "Cooking Oil & Ghee", "SUP-04", "1 kg", 2850, 3150),
    ("PRD-020", "Chana Dal (25 kg bag)", "Pulses & Lentils", "SUP-05", "25 kg bag", 5450, 5950),
    ("PRD-021", "Masoor Dal (10 kg bag)", "Pulses & Lentils", "SUP-05", "10 kg bag", 2480, 2720),
    ("PRD-022", "Moong Dal (10 kg bag)", "Pulses & Lentils", "SUP-05", "10 kg bag", 2350, 2580),
    ("PRD-023", "Mash Dal (5 kg bag)", "Pulses & Lentils", "SUP-05", "5 kg bag", 1480, 1650),
    ("PRD-024", "Black Chana (10 kg bag)", "Pulses & Lentils", "SUP-05", "10 kg bag", 2750, 3020),
    ("PRD-025", "Red Chilli Powder (1 kg)", "Spices & Masala", "SUP-06", "1 kg", 720, 820),
    ("PRD-026", "Turmeric Powder (1 kg)", "Spices & Masala", "SUP-06", "1 kg", 450, 520),
    ("PRD-027", "Coriander Powder (1 kg)", "Spices & Masala", "SUP-06", "1 kg", 390, 450),
    ("PRD-028", "Garam Masala (500 g)", "Spices & Masala", "SUP-06", "500 g", 460, 530),
    ("PRD-029", "Cumin Seeds (1 kg)", "Spices & Masala", "SUP-06", "1 kg", 1080, 1220),
    ("PRD-030", "Black Tea (5 kg)", "Tea & Beverages", "SUP-07", "5 kg", 4550, 4950),
    ("PRD-031", "Black Tea (1 kg)", "Tea & Beverages", "SUP-07", "1 kg", 940, 1030),
    ("PRD-032", "Green Tea (500 g)", "Tea & Beverages", "SUP-07", "500 g", 620, 710),
    ("PRD-033", "Milk Powder (1 kg)", "Tea & Beverages", "SUP-07", "1 kg", 1650, 1820),
    ("PRD-034", "Almonds (1 kg)", "Dry Fruits & Nuts", "SUP-07", "1 kg", 3400, 3850),
    ("PRD-035", "Walnuts (1 kg)", "Dry Fruits & Nuts", "SUP-07", "1 kg", 2650, 3000),
    ("PRD-036", "Dates, Ajwa (1 kg)", "Dry Fruits & Nuts", "SUP-07", "1 kg", 4200, 4750),
]

SHOPS = [
    ("SHP-01", "Usman Karyana Store", "Akbari Mandi"),
    ("SHP-02", "Al-Noor General Store", "Shah Alam Market"),
    ("SHP-03", "Bilal Cash & Carry", "Ichhra"),
    ("SHP-04", "Haji Ahmed & Sons", "Township"),
    ("SHP-05", "Rehman Store", "Gulberg III"),
    ("SHP-06", "Chaudhry Karyana", "Model Town"),
    ("SHP-07", "Zain Super Store", "Johar Town"),
    ("SHP-08", "Bismillah General Store", "Samanabad"),
    ("SHP-09", "Noor Traders", "DHA Phase 5"),
    ("SHP-10", "Shahzad Karyana", "Faisal Town"),
    ("SHP-11", "Al-Habib Store", "Green Town"),
    ("SHP-12", "Malik & Sons", "Sabzazar"),
    ("SHP-13", "Rana General Store", "Cavalry Ground"),
    ("SHP-14", "Imran Karyana", "Mughalpura"),
    ("SHP-15", "Siddique Store", "Shadbagh"),
    ("SHP-16", "Al-Rehman Traders", "Allama Iqbal Town"),
    ("SHP-17", "Farooq General Store", "Bhatti Gate"),
    ("SHP-18", "Naseer Cash & Carry", "Misri Shah"),
    ("SHP-19", "Tariq Store", "Wapda Town"),
    ("SHP-20", "Hassan Traders", "Gulshan-e-Ravi"),
    ("SHP-21", "Khan Karyana Store", "Ravi Road"),
    ("SHP-22", "Al-Madina Super Store", "Wahdat Road"),
]

START = date(2026, 7, 1)
END = date(2026, 12, 31)
DAYS = (END - START).days + 1  # 184


def rand_date():
    return START + timedelta(days=rng.randrange(DAYS))


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    # --- products ---
    write_csv(
        RAW / "products_SAMPLE.csv",
        ["product_code", "product_name", "category", "supplier_id", "unit",
         "cost_price_pkr", "sell_price_pkr"],
        [[c, n, cat, s, u, cp, sp] for (c, n, cat, s, u, cp, sp) in PRODUCTS],
    )

    # --- valid sales: 512 lines across ~200 orders ---
    valid = []
    order_no = 0
    lines_left = 512
    while lines_left > 0:
        order_no += 1
        n_lines = min(rng.randint(1, 4), lines_left)
        lines_left -= n_lines
        oid = f"ORD-{order_no:04d}"
        d = rand_date()
        shop = rng.choice(SHOPS)[0]
        chosen = rng.sample(PRODUCTS, n_lines)
        for p in chosen:
            qty = rng.randint(2, 40) if p[6] < 3000 else rng.randint(2, 15)
            unit_price = p[6]
            valid.append([oid, d.isoformat(), shop, p[0], qty, unit_price,
                          qty * unit_price])
    valid.sort(key=lambda r: (r[1], r[0]))

    # --- planted defects (8 lines) ---
    defects = []
    # 2 exact duplicates of valid lines
    for row in rng.sample(valid, 2):
        defects.append(list(row))
    # 3 lines with qty <= 0
    for qty in (0, -1, -3):
        p = rng.choice(PRODUCTS)
        d = rand_date()
        shop = rng.choice(SHOPS)[0]
        defects.append([f"ORD-{order_no + 1:04d}", d.isoformat(), shop,
                        p[0], qty, p[6], qty * p[6]])
        order_no += 1
    # 2 lines referencing an unknown product
    for code in ("PRD-997", "PRD-998"):
        d = rand_date()
        shop = rng.choice(SHOPS)[0]
        defects.append([f"ORD-{order_no + 1:04d}", d.isoformat(), shop,
                        code, 5, 1000, 5000])
        order_no += 1
    # 1 line with a wrong line total (off by PKR 750)
    p = rng.choice(PRODUCTS)
    qty = rng.randint(3, 10)
    defects.append([f"ORD-{order_no + 1:04d}", rand_date().isoformat(),
                    rng.choice(SHOPS)[0], p[0], qty, p[6],
                    qty * p[6] + 750])

    raw_sales = valid + defects
    # insert defects at random positions so they are not all at the end
    rng.shuffle(raw_sales)
    write_csv(
        RAW / "sales_SAMPLE.csv",
        ["order_id", "sale_date", "shop_id", "product_code", "qty",
         "unit_price_pkr", "line_total_pkr"],
        raw_sales,
    )

    # --- purchases: 160 lines, per-product purchased qty >= sold qty ---
    sold_qty = {}
    for row in valid:
        sold_qty[row[3]] = sold_qty.get(row[3], 0) + row[4]
    purchases = []
    po_no = 0
    for i, p in enumerate(PRODUCTS):
        n_pos = 5 if (i % 9) < 4 else 4  # 16*5 + 20*4 = 160
        target = int(sold_qty[p[0]] * rng.uniform(1.15, 1.45))
        # split target across POs, each at least 1
        cuts = sorted(rng.sample(range(1, target), n_pos - 1)) if target > n_pos else list(range(1, n_pos))
        parts, prev = [], 0
        for c in cuts + [target]:
            parts.append(c - prev)
            prev = c
        for qty in parts:
            po_no += 1
            unit_cost = int(round(p[5] * rng.uniform(0.97, 1.03) / 10.0) * 10)
            purchases.append([f"PO-{po_no:04d}", rand_date().isoformat(),
                              p[3], p[0], qty, unit_cost, qty * unit_cost])
    purchases.sort(key=lambda r: (r[1], r[0]))
    write_csv(
        RAW / "purchases_SAMPLE.csv",
        ["po_id", "purchase_date", "supplier_id", "product_code", "qty",
         "unit_cost_pkr", "total_cost_pkr"],
        purchases,
    )

    print(f"products: {len(PRODUCTS)}")
    print(f"sales raw: {len(raw_sales)} (valid {len(valid)} + defects {len(defects)})")
    print(f"purchases: {len(purchases)}")
    print(f"sold qty check: min purchase/sold ratio per product = "
          f"{min(sum(r[4] for r in purchases if r[3] == p[0]) / sold_qty[p[0]] for p in PRODUCTS):.2f}")


if __name__ == "__main__":
    main()
