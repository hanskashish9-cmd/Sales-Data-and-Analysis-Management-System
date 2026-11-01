"""
models.py
---------
Contains the SalesRecord class - ONE sales record (one row of the table).

The class checks (validates) every value in its constructor, so an invalid
record can never be created. This is called "defensive programming".
"""

import math
from datetime import datetime

from config import COLUMNS, DATE_FORMAT


class SalesRecord:
    """Stores the details of one sale and calculates its Sales Amount."""

    def __init__(self, order_id, order_date, product_name, category,
                 quantity, unit_price, region):
        # Each helper below returns a cleaned value or raises ValueError
        self.order_id = self._text(order_id, "Order ID", 30, collapse=False)
        self.order_date = self._date(order_date)
        self.product_name = self._text(product_name, "Product Name", 60)
        self.category = self._text(category, "Category", 40)
        self.quantity = self._quantity(quantity)
        self.unit_price = self._price(unit_price)
        self.region = self._text(region, "Region", 30)

        # Private attribute (name starts with double underscore).
        # Outside code cannot change it directly; it is always Quantity x Unit Price.
        self.__sales_amount = self.calculate_sales_amount()

    # ------------------------------------------------------------ methods
    def calculate_sales_amount(self):
        """Sales Amount = Quantity x Unit Price (rounded to 2 decimals)."""
        return round(self.quantity * self.unit_price, 2)

    @property
    def sales_amount(self):
        """Read-only access to the private sales amount."""
        return self.__sales_amount

    def to_dict(self):
        """Return the record as a dictionary whose keys are the CSV column names."""
        return {
            "Order ID": self.order_id,
            "Order Date": self.order_date,
            "Product Name": self.product_name,
            "Category": self.category,
            "Quantity": self.quantity,
            "Unit Price": self.unit_price,
            "Sales Amount": self.sales_amount,
            "Region": self.region,
        }

    def __str__(self):
        return (f"{self.order_id} | {self.order_date} | {self.product_name} | "
                f"{self.quantity} x {self.unit_price} = {self.sales_amount}")

    # --------------------------------------------------- validation helpers
    @staticmethod
    def _text(value, label, max_length, collapse=True):
        """Text must not be empty or too long. Extra spaces are removed."""
        text = "" if value is None else str(value)
        text = " ".join(text.split()) if collapse else text.strip()
        if not text:
            raise ValueError(f"{label} cannot be empty.")
        if len(text) > max_length:
            raise ValueError(f"{label} is too long (maximum {max_length} characters).")
        return text

    @staticmethod
    def _date(value):
        """Date must look like YYYY-MM-DD and must be a real calendar date."""
        text = "" if value is None else str(value).strip()
        try:
            return datetime.strptime(text, DATE_FORMAT).strftime(DATE_FORMAT)
        except ValueError:
            raise ValueError("Order Date must be a valid date in YYYY-MM-DD format, "
                             "for example 2025-03-15.")

    @staticmethod
    def _quantity(value):
        """Quantity must be a whole number greater than zero."""
        try:
            number = float(str(value).strip())
        except ValueError:
            raise ValueError("Quantity must be a whole number, for example 5.")
        if not math.isfinite(number) or number != int(number):
            raise ValueError("Quantity must be a whole number, for example 5.")
        if number <= 0:
            raise ValueError("Quantity must be greater than zero.")
        return int(number)

    @staticmethod
    def _price(value):
        """Unit Price must be a number greater than zero."""
        try:
            number = float(str(value).strip().replace(",", ""))
        except ValueError:
            raise ValueError("Unit Price must be a number, for example 499.50.")
        if not math.isfinite(number):
            raise ValueError("Unit Price must be a number, for example 499.50.")
        if number <= 0:
            raise ValueError("Unit Price must be greater than zero.")
        return round(number, 2)


# Safety check: the dictionary keys must match the shared column list
assert list(SalesRecord("X", "2025-01-01", "P", "C", 1, 1, "R").to_dict()) == COLUMNS
