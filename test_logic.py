"""
test_logic.py
-------------
Automatic tests for everything that does NOT need a window:
validation, CRUD, CSV saving, import/cleaning, analytics and charts.

Run from the project folder:
        python -m unittest test_logic -v
"""

import os
import tempfile
import unittest

import matplotlib
matplotlib.use("Agg")                      # draw charts in memory (no window needed)
import pandas as pd
from matplotlib.figure import Figure

from models import SalesRecord
from sales_manager import SalesManager, DataCleaner
from sales_analyzer import SalesAnalyzer
from visualizations import CHART_TYPES
from config import DATA_FILE, COLUMNS


def make_record(order_id="T-1", qty=2, price=100.0, product="Pen", category="Stationery",
                date="2025-03-15", region="North"):
    return SalesRecord(order_id, date, product, category, qty, price, region)


class TestSalesRecord(unittest.TestCase):
    def test_sales_amount_is_quantity_times_price(self):
        self.assertEqual(make_record(qty=3, price=19.99).sales_amount, 59.97)

    def test_invalid_values_are_rejected(self):
        bad_inputs = [
            dict(qty=0), dict(qty=-2), dict(qty="abc"), dict(qty=2.5),
            dict(price=0), dict(price=-5), dict(price="x"),
            dict(date="15-03-2025"), dict(date="2025-02-30"),
            dict(order_id="  "), dict(product=""), dict(region=""),
        ]
        for kwargs in bad_inputs:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    make_record(**kwargs)

    def test_text_inputs_are_converted(self):
        record = make_record(qty="4", price="1,250.50")
        self.assertEqual(record.quantity, 4)
        self.assertEqual(record.unit_price, 1250.5)


class TestSalesManager(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "data.csv")
        self.manager = SalesManager(self.path)

    def tearDown(self):
        self.folder.cleanup()

    def test_starts_empty_when_file_missing(self):
        self.assertEqual(self.manager.count(), 0)

    def test_add_and_persist(self):
        self.manager.add_record(make_record("A1"))
        self.manager.add_record(make_record("A2", product="Book"))
        self.assertEqual(self.manager.count(), 2)
        reloaded = SalesManager(self.path)                 # simulates restarting the app
        self.assertEqual(reloaded.count(), 2)
        self.assertEqual(reloaded.get_record("a2")["Product Name"], "Book")

    def test_duplicate_order_id_rejected(self):
        self.manager.add_record(make_record("A1"))
        with self.assertRaises(ValueError):
            self.manager.add_record(make_record("a1"))     # not case sensitive
        self.assertEqual(self.manager.count(), 1)

    def test_update(self):
        self.manager.add_record(make_record("A1", qty=1, price=50))
        self.manager.update_record(make_record("A1", qty=10, price=60, product="Notebook"))
        row = self.manager.get_record("A1")
        self.assertEqual((row["Quantity"], row["Sales Amount"], row["Product Name"]),
                         (10, 600.0, "Notebook"))
        with self.assertRaises(ValueError):
            self.manager.update_record(make_record("NOPE"))

    def test_delete(self):
        self.manager.add_record(make_record("A1"))
        self.manager.add_record(make_record("A2"))
        self.manager.delete_record("A1")
        self.assertIsNone(self.manager.get_record("A1"))
        self.assertEqual(self.manager.count(), 1)
        with self.assertRaises(ValueError):
            self.manager.delete_record("A1")

    def test_search(self):
        self.manager.add_record(make_record("ORD-1", product="Laptop"))
        self.manager.add_record(make_record("ORD-2", product="Lamp"))
        self.manager.add_record(make_record("XYZ-3", product="Pen"))
        self.assertEqual(len(self.manager.search("lap")), 1)
        self.assertEqual(len(self.manager.search("ord")), 2)
        self.assertEqual(len(self.manager.search("")), 3)
        self.assertEqual(len(self.manager.search("nothing")), 0)

    def test_failed_save_keeps_memory_unchanged(self):
        bad_manager = SalesManager(os.path.join(self.folder.name, "no_such_folder", "x.csv"))
        with self.assertRaises(OSError):
            bad_manager.add_record(make_record("A1"))
        self.assertEqual(bad_manager.count(), 0)

    def test_import_append_and_replace(self):
        self.manager.add_record(make_record("A1"))
        source = os.path.join(self.folder.name, "in.csv")
        pd.DataFrame([
            {"Order ID": "A1", "Order Date": "2025-01-01", "Product Name": "P", "Category": "C",
             "Quantity": 1, "Unit Price": 10, "Region": "North"},
            {"Order ID": "B1", "Order Date": "05/02/2025", "Product Name": "Q", "Category": "c",
             "Quantity": 2, "Unit Price": 20, "Region": "south"},
        ]).to_csv(source, index=False)
        self.manager.import_csv(source, "append")
        self.assertEqual(self.manager.count(), 2)          # A1 skipped, B1 added
        row = self.manager.get_record("B1")
        self.assertEqual((row["Order Date"], row["Category"], row["Region"], row["Sales Amount"]),
                         ("2025-02-05", "C", "South", 40.0))
        self.manager.import_csv(source, "replace")
        self.assertEqual(self.manager.count(), 2)
        self.assertEqual(self.manager.get_record("A1")["Product Name"], "P")

    def test_bad_files_give_friendly_errors(self):
        empty = os.path.join(self.folder.name, "empty.csv")
        open(empty, "w").close()
        wrong = os.path.join(self.folder.name, "wrong.csv")
        with open(wrong, "w") as f:
            f.write("a,b\n1,2\n")
        for path in (empty, wrong, os.path.join(self.folder.name, "missing.csv")):
            with self.subTest(path=os.path.basename(path)):
                with self.assertRaises(ValueError):
                    self.manager.import_csv(path)


class TestDataCleaner(unittest.TestCase):
    def test_dirty_file(self):
        raw = pd.DataFrame({
            "Order ID":     ["1", "2", "2", "3", "4", "5", "6", ""],
            "Order Date":   ["2025-01-01", "2025-01-02", "2025-01-02", "bad", "2025-01-04",
                             "2025-01-05", "2025-01-06", "2025-01-07"],
            "Product Name": ["A", "B", "B", "C", "D", "E", "F", "G"],
            "Category":     ["x", "Y", "Y", "Z", "", "W", "V", "U"],
            "Quantity":     ["1", "2", "2", "1", "-3", "abc", "2", "1"],
            "Unit Price":   ["10", "20", "20", "5", "5", "5", "7.5", "5"],
            "Sales Amount": ["10", "999", "999", "5", "5", "5", "", "5"],
            "Region":       ["north", "East", "East", "West", "West", "West", "", "West"],
        })
        clean, rejected, log = DataCleaner().clean(raw)
        self.assertEqual(list(clean["Order ID"]), ["1", "2", "6"])
        self.assertEqual(len(rejected), 5)
        self.assertEqual(clean.loc[1, "Sales Amount"], 40.0)       # 999 corrected
        self.assertEqual(clean.loc[2, "Sales Amount"], 15.0)       # missing calculated
        self.assertEqual(clean.loc[0, "Region"], "North")          # case fixed
        self.assertEqual(clean.loc[2, "Region"], "Unknown")        # filled
        self.assertIn("Assumptions", "\n".join(log))
        self.assertIn("5 row(s) would be rejected", DataCleaner().inspect(raw))

    def test_empty_frame(self):
        clean, rejected, log = DataCleaner().clean(pd.DataFrame(columns=COLUMNS))
        self.assertTrue(clean.empty and rejected.empty)


class TestSalesAnalyzer(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv(DATA_FILE)

    def test_numbers_match_pandas(self):
        a = SalesAnalyzer(self.df)
        self.assertAlmostEqual(a.total_revenue(), self.df["Sales Amount"].sum())
        self.assertEqual(a.total_orders(), self.df["Order ID"].nunique())
        self.assertEqual(a.total_units(), self.df["Quantity"].sum())
        self.assertAlmostEqual(a.average_order_value(), a.total_revenue() / a.total_orders())
        self.assertEqual(a.best_selling_product(),
                         self.df.groupby("Product Name")["Quantity"].sum().idxmax())
        self.assertEqual(a.top_category(),
                         self.df.groupby("Category")["Sales Amount"].sum().idxmax())
        self.assertAlmostEqual(a.monthly_revenue().sum(), a.total_revenue())

    def test_sample_file_has_at_least_50_records(self):
        self.assertGreaterEqual(len(self.df), 50)

    def test_empty_dataset_is_safe(self):
        for source in (None, pd.DataFrame(columns=COLUMNS)):
            a = SalesAnalyzer(source)
            self.assertEqual(a.total_revenue(), 0)
            self.assertEqual(a.average_order_value(), 0)
            self.assertEqual(a.best_selling_product(), "N/A")
            self.assertEqual(a.statistics(), {})
            self.assertEqual(a.highest_revenue_product(), ("N/A", 0.0))
            self.assertEqual(a.summary_cards()["Total Orders"], "0")


class TestCharts(unittest.TestCase):
    def draw_all(self, analyzer):
        for name, function in CHART_TYPES.items():
            with self.subTest(chart=name):
                fig = Figure(figsize=(8, 5))
                function(analyzer, fig)
                fig.tight_layout()
                self.assertTrue(len(fig.axes) >= 1)

    def test_all_charts_with_data(self):
        self.draw_all(SalesAnalyzer(pd.read_csv(DATA_FILE)))

    def test_all_charts_with_empty_data(self):
        self.draw_all(SalesAnalyzer(pd.DataFrame(columns=COLUMNS)))

    def test_all_charts_with_single_record(self):
        one = pd.DataFrame([make_record().to_dict()])
        self.draw_all(SalesAnalyzer(one))


if __name__ == "__main__":
    unittest.main()
