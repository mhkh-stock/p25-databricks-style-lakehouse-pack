"""Run every data-quality test in sql/tests/ against the lakehouse.

Each test file returns its violating rows; 0 rows = PASS.
Prints PASS/FAIL per test plus a summary, and writes
outputs/test_results.json (machine-readable, used by the workbook,
the DQ report and the handover PDF).

Usage:  python3 src/run_tests.py
Exit code 0 when every test passes, 1 otherwise.
"""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "processed" / "lakehouse.db"
TESTS = ROOT / "sql" / "tests"
OUT = ROOT / "outputs" / "test_results.json"


def main():
    if not DB.exists():
        print("lakehouse.db not found — run python3 src/build_lakehouse.py first")
        sys.exit(1)
    conn = sqlite3.connect(DB)
    results = []
    for path in sorted(TESTS.glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        rows = conn.execute(sql).fetchall()
        status = "PASS" if not rows else "FAIL"
        detail = [str(r) for r in rows[:5]]
        results.append({"test": path.name, "status": status,
                        "violations": len(rows), "detail": detail})
        print(f"{status}  {path.name}  ({len(rows)} violating rows)")
        for d in detail:
            print(f"        {d}")
    conn.close()
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print(f"\n{passed}/{total} tests passed")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"passed": passed, "total": total,
                               "tests": results}, indent=2), encoding="utf-8")
    print(f"wrote outputs/test_results.json")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
