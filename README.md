<<<<<<< HEAD
# Sales Data Analysis and Management System

A desktop application (Python + Tkinter) to **add, search, update and delete sales records**,
save them in a CSV file, and see **analytics and charts** that refresh automatically.

> Project report, viva questions, presentation script and syllabus mapping are in **PROJECT_REPORT.md**.

---

## 1. Architecture (kaun si file kya karti hai)

```
Sales_Data_Analysis/
├── main.py              Starts the program (creates SalesManager + window)
├── config.py            Constants: file paths, column names, currency, date formats
├── models.py            class SalesRecord      -> ONE sale, validation, Sales Amount
├── sales_manager.py     class SalesManager     -> add/update/delete/search/load/save/import/export
│                        class DataCleaner      -> detect and clean bad data
├── sales_analyzer.py    class SalesAnalyzer    -> totals, group-by tables, NumPy statistics
├── visualizations.py    8 chart functions + CHART_TYPES dictionary
├── gui.py               class SalesDashboard   -> all Tkinter screens and button callbacks
├── sales_data.csv       60 sample records (also your database file)
├── test_logic.py        20 automatic tests (no window needed)
├── requirements.txt     pandas, numpy, matplotlib, seaborn
└── README.md / PROJECT_REPORT.md
```

**How the files connect (import chain):**

```
main.py ──> gui.py ──> sales_manager.py ──> models.py ──> config.py
                  ├──> sales_analyzer.py ──> config.py
                  └──> visualizations.py ──> config.py
```

**Data flow of one "Add Record" click:**

1. `gui.py` reads the form and builds a `SalesRecord` (it validates every field).
2. `SalesManager.add_record()` checks for a duplicate Order ID, adds the row to its DataFrame and **saves the CSV**.
3. `gui.refresh_all()` creates a fresh `SalesAnalyzer` from the new data.
4. The table, the six summary cards, the analytics tab and the current chart are redrawn.

**Separation of responsibilities:** `SalesManager` and `SalesAnalyzer` never touch the screen; they only
return values or raise errors. `gui.py` is the only file that knows about Tkinter dialogs.

**Classes and objects in this project:** a *class* is a blueprint, an *object* is one real thing made from it.
`SalesRecord` is the blueprint of a sale; every time you press *Add Record*, one `SalesRecord` **object** is created
with its own `order_id`, `quantity`, etc. There is exactly one `SalesManager` object (holds all data),
a new `SalesAnalyzer` object after every change, and one `SalesDashboard` object (the window).

---

## 2. Create the folder in VS Code

1. Create a folder, e.g. `C:\Projects\Sales_Data_Analysis`.
2. Open VS Code -> **File -> Open Folder...** -> select that folder.
3. In the Explorer panel click **New File** and create each file with the exact names above.
   Paste the code of each file (or just copy the whole folder).
4. Install the **Python** extension (Microsoft) in VS Code if it is not installed.

## 3. Virtual environment (PowerShell)

Open the terminal in VS Code (**Terminal -> New Terminal**) and run:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` at the start of the prompt.

If PowerShell says *"running scripts is disabled on this system"*, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then press `Ctrl+Shift+P` -> **Python: Select Interpreter** -> choose the one inside `venv`.

## 4. Install the libraries

```powershell
pip install pandas numpy matplotlib seaborn
```
(or `pip install -r requirements.txt`).

## 5. Tkinter on Windows

Tkinter is **already included** with the Python installer from python.org (the *tcl/tk and IDLE* option is ticked
by default). Check with:

```powershell
python -m tkinter
```
A small test window should open. If you get `No module named tkinter`, re-run the Python installer -> *Modify* ->
tick **tcl/tk and IDLE**.

## 6. Run the application

```powershell
python main.py
```
Keep all files in the **same folder**; the program finds `sales_data.csv` automatically.

## 7. Run the automatic tests

```powershell
python -m unittest test_logic -v
```
Expected result: `Ran 20 tests ... OK`. These tests check validation, add/update/delete/search, CSV saving and
reloading, import and cleaning, all analytics numbers, and that all 8 charts draw (with data, with one record, and with no data).

---

## 8. Manual test checklist (do this before your practical)

| # | Test | Expected result |
|---|------|-----------------|
| 1 | Start the app | 60 records in *Sales Records*, six cards filled on *Home* |
| 2 | Add: ID `TEST-1`, today's date, Pen, Stationery, 5, 10, North | "Record added", table shows 61 records, Total Orders = 61, Sales Amount ₹50.00 |
| 3 | Add `TEST-1` again | Error: Order ID already exists |
| 4 | Quantity `0`, `-3`, `2.5` or `abc` | Error message each time |
| 5 | Click the `TEST-1` row, change Quantity to 20, **Update Record** | Amount becomes ₹200.00, cards and chart change |
| 6 | Search `lap` | Only Laptop rows; **Show All** brings everything back |
| 7 | Click a column heading twice | Table sorts ascending, then descending |
| 8 | Select `TEST-1`, **Delete Selected**, click Yes | Record removed, totals return to 60 |
| 9 | **Charts** tab -> try all 8 chart types | Each has title, axis labels, legend where useful |
| 10 | Close the app and start it again | Your changes are still there (saved in the CSV) |
| 11 | **Export CSV**, open the file in Excel | All records present |
| 12 | Make a CSV with a duplicate ID, a negative quantity and a bad date, then **Import CSV** | Import report lists every rejected row and the reason |
| 13 | **Data Quality** tab -> Inspect / Clean a CSV | Report with counts and assumptions; cleaned file + `_rejected.csv` |
| 14 | Delete all records | Cards show 0 / N/A, charts show "No sales data", nothing crashes |

(Tip: before test 14 use *Export CSV* to keep a backup, or copy `sales_data.csv`.)

---

## 9. Key definitions

* **Sales Amount** = Quantity x Unit Price (always calculated by the program, never typed).
* **Total Orders** = number of **unique Order IDs**.
* **Average Order Value** = Total Revenue / Total Orders (0 if there are no orders).
* **Best-Selling Product** = product with the most **units** sold.
* **Highest-Revenue Category** = category with the largest **revenue**.

## 10. Data cleaning assumptions (nothing is changed silently)

1. Rows with a missing/invalid Order ID, date, product, quantity or unit price are **rejected and reported** - never guessed.
2. Missing Category/Region -> `Unknown` (reported).
3. Sales Amount is recalculated (Quantity x Unit Price); the report says how many values differed.
4. Duplicate Order ID -> first row kept, later copies rejected.
5. `dd/mm/yyyy` dates are read day-first.
6. Category/Region typed fully in lower or UPPER case become Title Case (`north` -> `North`).
7. If `sales_data.csv` contains bad rows at start-up, they are skipped, you get a warning, and the skipped rows are
   saved to `rejected_rows.csv` so no data is lost.

## 11. Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: pandas` | Activate the venv and run `pip install -r requirements.txt` |
| `No module named tkinter` | Reinstall Python with *tcl/tk and IDLE* |
| "Cannot write to sales_data.csv" | Close the CSV if it is open in Excel |
| Rupee symbol looks like a box | Change `CURRENCY` in `config.py` to `"Rs. "` |
| App starts but table is empty | `sales_data.csv` is missing or not in the same folder as `main.py` |
=======
# Sales-Data-and-Analysis-Management-System
>>>>>>> 8ce14554855ca8e6b05e4b2993f984ad08ca8df4
