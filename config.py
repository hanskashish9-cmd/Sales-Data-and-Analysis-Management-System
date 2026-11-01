"""
config.py
---------
Project-wide settings. Every other file imports its constants from here,
so a value (for example the currency symbol) is changed in ONE place only.
"""

import os

# Folder where this project lives. Using __file__ means the project works
# on any computer - no hard-coded "C:\Users\..." paths.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "sales_data.csv")          # main database file
REJECTED_FILE = os.path.join(BASE_DIR, "rejected_rows.csv")   # rows skipped while loading

APP_TITLE = "Sales Data Analysis and Management System"
CURRENCY = "₹"

# The 8 columns of the sales table, in the order they are stored in the CSV
COLUMNS = ["Order ID", "Order Date", "Product Name", "Category",
           "Quantity", "Unit Price", "Sales Amount", "Region"]

# When importing a file, "Sales Amount" is optional because we can calculate it.
# (list comprehension)
REQUIRED_INPUT_COLUMNS = [col for col in COLUMNS if col != "Sales Amount"]

# Dates are stored as text in this format, e.g. 2025-03-15
DATE_FORMAT = "%Y-%m-%d"
# Formats accepted when IMPORTING a file (day-first is assumed for dd/mm/yyyy)
ACCEPTED_DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y")   # tuple

# Suggestions shown in the drop-down lists of the form
DEFAULT_CATEGORIES = ("Electronics", "Furniture", "Stationery", "Clothing", "Home Appliances")
DEFAULT_REGIONS = ("North", "South", "East", "West", "Central")

# Text values that are treated as "missing" while cleaning
MISSING_TOKENS = {"", "nan", "none", "null", "na", "n/a", "-"}   # set


def money(value):
    """Format a number as money.  money(1234.5) -> '₹1,234.50'"""
    try:
        return f"{CURRENCY}{float(value):,.2f}"
    except (TypeError, ValueError):
        return f"{CURRENCY}0.00"
