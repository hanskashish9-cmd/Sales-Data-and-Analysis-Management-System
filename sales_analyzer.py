"""
sales_analyzer.py
-----------------
SalesAnalyzer receives a DataFrame of sales records and answers questions
about it (totals, best product, monthly trend ...) using Pandas and NumPy.

It is rebuilt from the latest data every time the dashboard refreshes, so the
numbers always match the current records. Every method is safe for an EMPTY
dataset: it returns 0, 'N/A' or an empty result instead of crashing.
"""

import numpy as np
import pandas as pd

from config import COLUMNS, DATE_FORMAT, money


class SalesAnalyzer:
    """Calculates statistics and prepares data for charts."""

    def __init__(self, df):
        self._df = self._prepare(df)

    # ------------------------------------------------------------- set-up
    @staticmethod
    def _prepare(df):
        """Convert columns to proper types and handle missing values."""
        if df is None or len(df) == 0:
            empty = pd.DataFrame(columns=COLUMNS)
            empty["Month"] = pd.Series(dtype="object")
            return empty

        data = df.copy()
        for col in ("Quantity", "Unit Price", "Sales Amount"):
            data[col] = pd.to_numeric(data[col], errors="coerce")
        # Missing Sales Amount -> calculate it from Quantity x Unit Price
        data["Sales Amount"] = data["Sales Amount"].fillna(data["Quantity"] * data["Unit Price"])
        # Rows that still have no usable number cannot be analysed
        data = data.dropna(subset=["Quantity", "Sales Amount"])

        data["Order Date"] = pd.to_datetime(data["Order Date"], format=DATE_FORMAT, errors="coerce")
        data["Month"] = data["Order Date"].dt.strftime("%Y-%m")   # '2025-03'
        return data.reset_index(drop=True)

    # ------------------------------------------------------------ access
    @property
    def data(self):
        """A copy of the prepared data (used by the scatter plot / heatmap)."""
        return self._df.copy()

    def is_empty(self):
        return self._df.empty

    # --------------------------------------------------------- key figures
    def total_revenue(self):
        """Sum of all Sales Amounts."""
        return float(self._df["Sales Amount"].sum()) if not self.is_empty() else 0.0

    def total_orders(self):
        """
        Number of UNIQUE Order IDs. Each Order ID is one order, so a repeated
        ID would still be counted once.
        """
        return int(self._df["Order ID"].nunique()) if not self.is_empty() else 0

    def total_units(self):
        """Sum of all Quantities."""
        return int(self._df["Quantity"].sum()) if not self.is_empty() else 0

    def average_order_value(self):
        """Total Revenue divided by Total Orders (0 when there are no orders)."""
        orders = self.total_orders()
        return self.total_revenue() / orders if orders > 0 else 0.0

    # --------------------------------------------------------- group-by tables
    def quantity_by_product(self):
        """Units sold per product, highest first."""
        if self.is_empty():
            return pd.Series(dtype="float64")
        return (self._df.groupby("Product Name")["Quantity"].sum()
                .sort_values(ascending=False, kind="stable"))

    def revenue_by_product(self):
        if self.is_empty():
            return pd.Series(dtype="float64")
        return (self._df.groupby("Product Name")["Sales Amount"].sum()
                .sort_values(ascending=False, kind="stable"))

    def revenue_by_category(self):
        if self.is_empty():
            return pd.Series(dtype="float64")
        return (self._df.groupby("Category")["Sales Amount"].sum()
                .sort_values(ascending=False, kind="stable"))

    def revenue_by_region(self):
        if self.is_empty():
            return pd.Series(dtype="float64")
        return (self._df.groupby("Region")["Sales Amount"].sum()
                .sort_values(ascending=False, kind="stable"))

    def monthly_revenue(self):
        """Revenue per month in date order. Rows with an invalid date are skipped."""
        if self.is_empty():
            return pd.Series(dtype="float64")
        return self._df.groupby("Month")["Sales Amount"].sum().sort_index()

    def product_summary(self):
        """One table: units, revenue, orders and average sale for every product."""
        if self.is_empty():
            return pd.DataFrame(columns=["Units", "Revenue", "Orders", "Avg_Sale"])
        return (self._df.groupby("Product Name")
                .agg(Units=("Quantity", "sum"),
                     Revenue=("Sales Amount", "sum"),
                     Orders=("Order ID", "nunique"),
                     Avg_Sale=("Sales Amount", "mean"))
                .sort_values("Revenue", ascending=False, kind="stable"))

    # ------------------------------------------------------------ winners
    def best_selling_product(self):
        """Product with the most UNITS sold."""
        units = self.quantity_by_product()
        return str(units.index[0]) if not units.empty else "N/A"

    def top_category(self):
        """Category with the highest REVENUE."""
        revenue = self.revenue_by_category()
        return str(revenue.index[0]) if not revenue.empty else "N/A"

    def highest_revenue_product(self):
        revenue = self.revenue_by_product()
        return (str(revenue.index[0]), float(revenue.iloc[0])) if not revenue.empty else ("N/A", 0.0)

    def lowest_revenue_product(self):
        revenue = self.revenue_by_product()
        return (str(revenue.index[-1]), float(revenue.iloc[-1])) if not revenue.empty else ("N/A", 0.0)

    # ------------------------------------------------------- NumPy statistics
    def order_values(self):
        """Sales Amounts as a NumPy array."""
        return self._df["Sales Amount"].to_numpy(dtype=float)

    def average_sales_amount(self):
        values = self.order_values()
        return float(np.mean(values)) if values.size else 0.0

    def statistics(self):
        """Descriptive statistics of order values (empty dict if no data)."""
        values = self.order_values()
        if values.size == 0:
            return {}
        return {
            "Mean": float(np.mean(values)),
            "Median": float(np.median(values)),
            "Standard deviation": float(np.std(values)),
            "Minimum": float(np.min(values)),
            "25th percentile": float(np.percentile(values, 25)),
            "75th percentile": float(np.percentile(values, 75)),
            "Maximum": float(np.max(values)),
        }

    def correlation(self):
        """Correlation matrix of the numeric columns."""
        return self._df[["Quantity", "Unit Price", "Sales Amount"]].corr()

    # ------------------------------------------------------------ dashboard
    def summary_cards(self):
        """The six dashboard numbers, already formatted as display text."""
        return {
            "Total Revenue": money(self.total_revenue()),
            "Total Orders": f"{self.total_orders():,}",
            "Total Units Sold": f"{self.total_units():,}",
            "Average Order Value": money(self.average_order_value()),
            "Best-Selling Product": self.best_selling_product(),
            "Highest-Revenue Category": self.top_category(),
        }
