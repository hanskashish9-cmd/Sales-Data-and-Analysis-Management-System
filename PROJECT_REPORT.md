# Sales Data Analysis and Management System - Project Report

**Course:** MCA - Python and Data Analytics  **Type:** Mini Project

---

## 1. Abstract
This project is a desktop application built with Python that manages sales records and turns them into useful
business information. Users can add, view, search, update and delete sales records through a Tkinter interface.
Records are stored in a CSV file, so they remain available after the program is closed. Pandas and NumPy are used
to calculate total revenue, orders, units sold, average order value, best-selling product and top category, as well
as product-, category-, region- and month-wise results. Matplotlib and Seaborn display eight charts embedded in
the application. A data-quality module detects missing values, invalid numbers, invalid dates and duplicates, and
cleans imported files without silently altering important business data.

## 2. Problem Statement
Small shops and students often keep sales data in scattered spreadsheets. Entering data without checks creates
duplicate orders, wrong amounts and missing values, and calculating totals or trends by hand is slow and error-prone.
A simple, validated tool is needed that stores sales data and shows results instantly.

## 3. Objectives
1. Provide a form to add, update, delete and search sales records with full validation.
2. Store data permanently in a CSV file and reload it at start-up.
3. Calculate key sales metrics automatically using Pandas and NumPy.
4. Present results as summary cards, tables and charts that refresh after every change.
5. Detect and handle poor-quality data transparently.
6. Demonstrate Python, OOP, data analytics and visualization concepts in one project.

## 4. Scope
**Included:** single-user desktop use; CRUD operations; CSV import/export; analytics; visualizations; data cleaning.
**Not included:** multi-user access, a database server, web access, user login, machine learning/forecasting, inventory management.

## 5. Hardware and Software Requirements
| Hardware | Software |
|----------|----------|
| Any PC/laptop, 4 GB RAM (8 GB recommended) | Windows 10/11 |
| 200 MB free disk space | Python 3.9 or later (python.org) |
| Display 1280 x 720 or larger | VS Code with the Python extension |
| | pandas, numpy, matplotlib, seaborn |

## 6. Methodology
1. **Requirement analysis** - list the fields, operations and reports needed.
2. **Design** - split the program into five classes with one responsibility each (see section 7).
3. **Implementation** - config -> model -> manager -> analyzer -> charts -> GUI -> main.
4. **Testing** - automatic tests for logic (`test_logic.py`) and a manual checklist for the interface (README, section 8).
5. **Documentation** - README, this report and viva preparation.

## 7. Module Description
| Module | Class / contents | Responsibility |
|--------|------------------|----------------|
| `config.py` | constants, `money()` | Paths, column names, currency, date formats |
| `models.py` | `SalesRecord` | Validate one record; calculate Sales Amount |
| `sales_manager.py` | `SalesManager` | CRUD, search, CSV load/save, import/export (Pandas DataFrame) |
| `sales_manager.py` | `DataCleaner` | Inspect and clean raw data; report assumptions |
| `sales_analyzer.py` | `SalesAnalyzer` | Metrics, group-by tables, NumPy statistics, chart data |
| `visualizations.py` | 8 functions, `CHART_TYPES` | Matplotlib/Seaborn charts, safe for empty data |
| `gui.py` | `SalesDashboard` | Tkinter screens, events, dialogs, refresh |
| `main.py` | `main()` | Entry point |

## 8. Data Flow
```
 User form / CSV file
        |
        v
 SalesRecord (validation)  /  DataCleaner (import cleaning)
        |
        v
 SalesManager --- saves ---> sales_data.csv
        |
        v   (latest DataFrame)
 SalesAnalyzer --> summary cards, tables, statistics
        |
        v
 visualizations --> charts embedded in Tkinter
        ^
        |  every add / update / delete / import calls refresh_all()
```

## 9. Advantages and Limitations
**Advantages:** easy to use; no database installation; validated input; automatic refresh; transparent data cleaning; modular code that is easy to explain; works offline.
**Limitations:** the whole dataset is held in memory (suitable for thousands, not millions of rows); single user; CSV has no transactions; no login or permissions; no undo; dates are limited to a few text formats.

## 10. Future Enhancements
SQLite database; user login with roles; date-range and category filters; PDF/Excel report export; sales forecasting; undo/redo; dark theme; multi-currency support; customer and inventory modules.

## 11. Conclusion
The project shows how Python, OOP, Pandas, NumPy, Matplotlib, Seaborn and Tkinter work together to build a complete
data application. Validation and cleaning keep the data trustworthy, and the automatic refresh makes the dashboard
reflect the data at all times. It meets the requirements of a college mini project and can grow into a larger system.

## 12. Testing Status (honest statement)
* `python -m unittest test_logic -v` - **20 tests, all passing** when this project was built. They cover validation, CRUD, CSV persistence, import/cleaning, analytics values and all charts (with data, with one record and with no data).
* The GUI event handlers (add, update, delete, search, sort, import, export, quality tab, chart drawing) were run in a **simulated Tkinter environment** and behaved correctly.
* The window itself was **not opened on a real Windows desktop** during development. Please run the manual checklist in README section 8 on your machine before the practical.

---

## 13. Viva Questions and Answers

**Project basics**
1. **What is your project about?** A desktop app to manage sales records and analyse them with statistics and charts.
2. **Why did you choose CSV for storage?** It is simple, human-readable, opens in Excel and needs no database server - suitable for a mini project.
3. **Which libraries did you use and why?** Tkinter - GUI; Pandas - tables and analysis; NumPy - numerical statistics; Matplotlib - charts; Seaborn - statistical charts such as the heatmap.
4. **How is data kept after closing the program?** After every add/update/delete the DataFrame is written to `sales_data.csv`; at start-up it is read again.
5. **How is Sales Amount calculated?** Quantity x Unit Price inside `SalesRecord.calculate_sales_amount()`. The user cannot type it.

**OOP**
6. **What is a class and an object?** A class is a blueprint; an object is a real instance. `SalesRecord` is the class; the record created when you press Add is an object.
7. **Which classes did you create?** `SalesRecord`, `SalesManager`, `DataCleaner`, `SalesAnalyzer`, `SalesDashboard`.
8. **What is a constructor?** The `__init__` method that runs when an object is created. `SalesRecord.__init__` validates and stores the values.
9. **What is encapsulation? Where is it used?** Keeping data and the methods that use it together and hiding internals. `SalesRecord` has the private `__sales_amount`; `SalesManager` keeps `_df` protected and returns copies from `get_all()`.
10. **What does the double underscore in `__sales_amount` mean?** Name mangling - it makes the attribute private, so outside code must use the read-only `sales_amount` property.
11. **What is `@property`?** It lets a method be read like an attribute (`record.sales_amount`) without allowing assignment.
12. **What is `@staticmethod`?** A method that does not need `self`. The validation helpers in `SalesRecord` are static.
13. **Did you use inheritance or polymorphism?** No - this project did not need them, and I did not add them artificially. Each class has a separate job (composition: the dashboard *uses* a manager and an analyzer).
14. **What is separation of responsibilities?** Each class does one job: the manager stores data, the analyzer calculates, the dashboard shows. The manager never opens message boxes.

**Python concepts**
15. **Where did you use exception handling?** Validation (`raise ValueError`), file reading (`try/except` for missing/empty/bad files), and the GUI, which catches errors and shows dialogs instead of crashing.
16. **What is a lambda? Where is it used?** A small unnamed function. Example: `command=lambda c=col: self.sort_table(c)` for the column headings.
17. **Why `lambda c=col:` and not `lambda: self.sort_table(col)`?** Without the default argument all buttons would use the last value of `col`. The default fixes the value at creation time.
18. **What is a list comprehension?** A short way to build a list: `REQUIRED_INPUT_COLUMNS = [col for col in COLUMNS if col != "Sales Amount"]`.
19. **Where did you use a tuple, set and dictionary?** Tuple - `ACCEPTED_DATE_FORMATS` (fixed values); set - `MISSING_TOKENS` and the set union of categories; dictionary - `CHART_TYPES` (name -> function) and `record.to_dict()`.
20. **What are default arguments?** Values used when the caller gives none: `SalesManager(csv_path=DATA_FILE)`, `import_csv(path, mode="append")`.

**Pandas / NumPy**
21. **What is a DataFrame and a Series?** A DataFrame is a table of rows and columns; a Series is one column. `df["Quantity"]` is a Series.
22. **What does `groupby` do?** It splits rows into groups (e.g. by Category) and applies a function such as `sum()` to each group.
23. **How did you calculate the best-selling product?** `df.groupby("Product Name")["Quantity"].sum()`, sort descending, take the first name.
24. **How are Total Orders and Average Order Value defined?** Total Orders = number of unique Order IDs (`nunique()`); Average Order Value = Total Revenue / Total Orders, and 0 when there are no orders.
25. **How do you handle an empty dataset?** Every analyzer method checks `is_empty()` and returns 0, "N/A" or an empty result; each chart prints a message instead of drawing.
26. **Where is NumPy used?** `np.mean`, `np.median`, `np.std`, `np.percentile`, `np.min/np.max` on the Sales Amount array, and `np.inf` handling while cleaning.
27. **What does `pd.to_numeric(errors="coerce")` do?** Converts text to numbers and turns invalid values such as "abc" into NaN instead of raising an error.
28. **Why read the CSV with `dtype=str`?** So Pandas does not guess types; invalid values stay visible and can be reported.
29. **How do you find duplicates?** `duplicated()` on the upper-cased Order ID; the first copy is kept and later copies are rejected and reported.
30. **How do you handle missing values?** Critical fields (ID, date, product, quantity, price) -> row rejected and reported; Category/Region -> "Unknown"; Sales Amount -> recalculated.

**Visualization / GUI**
31. **Difference between a bar chart and a histogram?** A bar chart compares categories; a histogram shows how numeric values are distributed in ranges (bins).
32. **What does the heatmap show?** The correlation (-1 to +1) between Quantity, Unit Price and Sales Amount.
33. **What are Figure and Axes?** The Figure is the whole canvas; an Axes is one plot area on it, where title, labels and data are drawn.
34. **How are charts embedded in Tkinter?** `FigureCanvasTkAgg` places a Matplotlib Figure inside a Tkinter frame.
35. **Difference between `pack()` and `grid()`?** `pack()` stacks widgets side by side or top to bottom; `grid()` places them in rows and columns. The form uses `grid`, the main layout uses both.
36. **What does `mainloop()` do?** It keeps the window open and waits for events such as clicks.
37. **How is the screen refreshed after a change?** Every successful change calls `refresh_all()`, which creates a new `SalesAnalyzer` and redraws table, cards, analytics and chart.
38. **How do you stop duplicate Order IDs?** `SalesManager.add_record()` compares IDs (not case sensitive) and raises an error if one exists.
39. **What happens if the CSV is open in Excel when you save?** Windows blocks writing. The program catches the error, shows a message, and does *not* change its in-memory data, so screen and file remain consistent.
40. **How did you test the project?** Automatic unit tests for logic (`test_logic.py`) plus a manual checklist for the interface.

---

## 14. Presentation Script (about 3 minutes)

> "Good morning, sir/madam. My project is the **Sales Data Analysis and Management System**, built in Python.
>
> **Problem:** sales data is often kept in spreadsheets without checks, so duplicates and wrong values creep in, and totals are calculated by hand.
>
> **Solution:** my application lets a user enter sales records through a form. Quantity multiplied by unit price gives the sales amount automatically. The program rejects invalid quantities, prices and dates, and it will not accept a duplicate Order ID.
>
> **Demo 1 - Records:** here are 60 sample records stored in a CSV file. I will add a new record... it is saved immediately. If I search by product name, only matching rows appear. I can click a row, edit it and update it, or delete it after a confirmation.
>
> **Demo 2 - Dashboard:** these six cards show total revenue, orders, units sold, average order value, best-selling product and top category. Notice that they changed as soon as I added the record. Total orders means unique Order IDs, and average order value is revenue divided by orders.
>
> **Demo 3 - Charts:** from this drop-down I can show revenue by product, category or region, the monthly trend line, the category pie chart, a histogram of order values, a scatter plot of quantity versus sales, and a Seaborn correlation heatmap. All charts refresh with the data.
>
> **Demo 4 - Data quality:** if I import a file containing missing values, negative quantities or duplicate IDs, the program does not silently fix them. It rejects invalid rows, lists the reasons, and explains its assumptions.
>
> **Design:** the code is divided into classes - `SalesRecord` for one sale, `SalesManager` for storage, `SalesAnalyzer` for calculations, and `SalesDashboard` for the interface - so every part has one responsibility.
>
> **Technologies:** Python, Tkinter, Pandas, NumPy, Matplotlib and Seaborn.
>
> **Future scope:** a database, user login, forecasting and report export. Thank you. I am ready for your questions."

---

## 15. Mapping to the Python Syllabus
Only concepts that are **actually used** in the code are listed.

| Syllabus topic | Where it is implemented |
|----------------|-------------------------|
| Variables, data types, operators, conditions | Validation in `models.py`; `if/elif` logic throughout |
| Loops and control statements | `for` + `continue` in `parse_date_text()`; `for` loops building the form and tables in `gui.py` (no `while` loop is used) |
| List | `COLUMNS`, `REQUIRED_INPUT_COLUMNS`, report lines |
| Tuple | `ACCEPTED_DATE_FORMATS`, `DEFAULT_CATEGORIES` |
| Set | `MISSING_TOKENS`; set union in `update_choice_lists()`; `existing_ids` in `import_csv()` |
| Dictionary | `CHART_TYPES`, `to_dict()`, `self.vars`, `summary_cards()` |
| Input and output | Form entry, dialogs, status bar; `print()` in `main.py`; text reports |
| Functions, arguments, return values | `money()`, `parse_date_text()`, `empty_sales_frame()`, all chart functions |
| Default arguments | `SalesManager(csv_path=DATA_FILE)`, `import_csv(mode="append")`, `_text(collapse=True)` |
| Lambda functions | Table headings, Home buttons, Enter key in search, delete action in `gui.py` |
| List/dict comprehensions | `REQUIRED_INPUT_COLUMNS`, `self.vars = {...}`; generator expressions in report building |
| Exception handling | `try/except/raise` in `models.py`, `sales_manager.py`, `gui.py`, `main.py` |
| File handling | `open()` in "Save as .txt"; CSV read/write with Pandas; `os.path` for paths |
| Classes and objects, constructors, instance methods | All five classes; `__init__` in each |
| Public / protected / private members | Public methods; protected `_df`, `_commit()`; private `__sales_amount` |
| Encapsulation, modular code | Separate files and classes; `@property`; copies returned from `get_all()` |
| Inheritance, polymorphism | **Not used** - not needed in this design |
| NumPy arrays and operations | `statistics()` in `sales_analyzer.py`; `to_numpy()` |
| Pandas Series and DataFrame | Everywhere in manager and analyzer |
| Filtering, sorting, grouping, aggregation | `search()`, `sort_values()`, `groupby().sum()`, `groupby().agg()` |
| Missing-value handling | `DataCleaner`, `fillna()`, `dropna()`, `to_numeric(errors="coerce")` |
| Statistical calculations | mean, median, std, percentiles, correlation |
| Matplotlib Figure and Axes | `visualizations.py` |
| Bar, line, pie, histogram, scatter | `chart_product_revenue`, `chart_monthly_trend`, `chart_category_pie`, `chart_order_histogram`, `chart_quantity_scatter` |
| Seaborn | `barplot`, `histplot`, `scatterplot`, `heatmap` |
| Tkinter widgets | Label, Entry, Button, Combobox, Frame, LabelFrame, Treeview, Notebook, Text, Scrollbar, Toplevel |
| Events and callbacks | `command=`, `bind("<<TreeviewSelect>>")`, `bind("<KeyRelease>")`, `bind("<Return>")` |
| Geometry managers | `pack()` and `grid()` in `gui.py` |
