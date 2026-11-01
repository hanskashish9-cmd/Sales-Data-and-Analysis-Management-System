"""
main.py
-------
Start the application with:      python main.py
"""

import sys

try:
    import tkinter as tk
    import pandas, numpy, matplotlib, seaborn          # noqa: F401  (checks installation)
except ImportError as error:
    print("A required library is missing:", error)
    print("Activate your virtual environment and run:  pip install -r requirements.txt")
    print("(If the missing module is 'tkinter', reinstall Python from python.org "
          "and keep 'tcl/tk and IDLE' ticked.)")
    sys.exit(1)

from gui import SalesDashboard
from sales_manager import SalesManager


def main():
    manager = SalesManager()                                   # loads sales_data.csv
    print(f"Loaded {manager.count()} sales record(s) from {manager.csv_path}")
    root = tk.Tk()
    SalesDashboard(root, manager)
    root.mainloop()                                            # keep the window open


if __name__ == "__main__":
    main()
