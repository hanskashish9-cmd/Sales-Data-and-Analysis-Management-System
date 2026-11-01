"""
gui.py
------
SalesDashboard builds the Tkinter window and connects every button to the
right method of SalesManager / SalesAnalyzer.

Screen layout:
  Header + toolbar (Import CSV, Export CSV, Refresh Dashboard)
  Tabs:  Home | Sales Records | Analytics | Charts | Data Quality
  Status bar (bottom)

Flow of every data change (add / update / delete / import):
  1. read the form  ->  2. SalesManager changes + saves the CSV
  3. refresh_all()  ->  table, cards, analytics and chart are redrawn
"""

import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, filedialog

import matplotlib
matplotlib.use("TkAgg")   # must be set BEFORE pyplot is imported (visualizations imports it)
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from config import (APP_TITLE, COLUMNS, DATE_FORMAT,
                    DEFAULT_CATEGORIES, DEFAULT_REGIONS, money)
from models import SalesRecord
from sales_manager import SalesManager, DataCleaner
from sales_analyzer import SalesAnalyzer
from visualizations import CHART_TYPES

# Fields shown in the entry form (Sales Amount is calculated, not typed)
FORM_FIELDS = ["Order ID", "Order Date", "Product Name", "Category",
               "Quantity", "Unit Price", "Region"]

KPI_NAMES = ["Total Revenue", "Total Orders", "Total Units Sold",
             "Average Order Value", "Best-Selling Product", "Highest-Revenue Category"]

COLUMN_WIDTHS = {"Order ID": 85, "Order Date": 90, "Product Name": 150, "Category": 110,
                 "Quantity": 70, "Unit Price": 90, "Sales Amount": 100, "Region": 80}

DARK = "#1d3557"
ACCENT = "#2a6f97"
BG = "#f4f6f8"


class SalesDashboard:
    """The main window of the application."""

    def __init__(self, root, manager=None):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1280x780")
        self.root.minsize(1100, 680)
        self.root.configure(bg=BG)

        # Objects this window works with
        self.manager = manager if manager is not None else SalesManager()
        self.analyzer = SalesAnalyzer(self.manager.get_all())

        # State
        self.selected_order_id = None          # None = "add" mode, otherwise "edit" mode
        self.visible_df = self.manager.get_all()
        self.sort_column = None
        self.sort_ascending = True
        self.kpi_label_sets = []               # KPI labels (Home tab + Analytics tab)

        # Tkinter variables linked to widgets
        self.vars = {field: tk.StringVar() for field in FORM_FIELDS}    # dict comprehension
        self.amount_var = tk.StringVar(value="-")
        self.search_var = tk.StringVar()
        self.chart_var = tk.StringVar(value=list(CHART_TYPES)[0])
        self.status_var = tk.StringVar(value="Ready")
        self.count_var = tk.StringVar()
        self.home_info_var = tk.StringVar()
        self.widgets = {}

        self._build_styles()
        self._build_header()
        self._build_toolbar()
        self._build_status_bar()       # packed before the tabs so it always stays visible
        self._build_tabs()

        self.clear_form()
        self.refresh_all()
        self._show_load_warnings()

    # ==================================================================
    # BUILDING THE SCREEN
    # ==================================================================
    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=24, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(14, 6))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=6)

    def _build_header(self):
        header = tk.Frame(self.root, bg=DARK)
        header.pack(fill="x")
        tk.Label(header, text=APP_TITLE, bg=DARK, fg="white",
                 font=("Segoe UI", 20, "bold")).pack(pady=(10, 0))
        tk.Label(header, text="Python  |  Tkinter  |  Pandas  |  NumPy  |  Matplotlib  |  Seaborn",
                 bg=DARK, fg="#a8dadc", font=("Segoe UI", 10)).pack(pady=(0, 10))

    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x", padx=10, pady=8)
        ttk.Button(bar, text="Import CSV", command=self.import_csv).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Export CSV", command=self.export_csv).pack(side="left", padx=6)
        ttk.Button(bar, text="Refresh Dashboard", style="Accent.TButton",
                   command=self.refresh_dashboard).pack(side="left", padx=6)
        ttk.Button(bar, text="Exit", command=self.root.destroy).pack(side="right")

    def _build_status_bar(self):
        tk.Label(self.root, textvariable=self.status_var, anchor="w", bg="#dee2e6",
                 font=("Segoe UI", 9), padx=10, pady=4).pack(fill="x", side="bottom")

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.tabs = {}
        for name in ("Home", "Sales Records", "Analytics", "Charts", "Data Quality"):
            frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(frame, text=f"  {name}  ")
            self.tabs[name] = frame

        self._build_home_tab(self.tabs["Home"])
        self._build_records_tab(self.tabs["Sales Records"])
        self._build_analytics_tab(self.tabs["Analytics"])
        self._build_charts_tab(self.tabs["Charts"])
        self._build_quality_tab(self.tabs["Data Quality"])

    # ------------------------------------------------------------ KPI cards
    def _make_kpi_cards(self, parent):
        """Create the six summary cards. The labels are stored so they can be updated."""
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=(0, 10))
        labels = {}
        for column, name in enumerate(KPI_NAMES):
            card = tk.Frame(row, bg="white", highlightbackground="#ced4da", highlightthickness=1)
            card.grid(row=0, column=column, padx=4, sticky="nsew")
            row.columnconfigure(column, weight=1, uniform="kpi")
            tk.Label(card, text=name, bg="white", fg="#6c757d",
                     font=("Segoe UI", 9)).pack(pady=(10, 0))
            value = tk.Label(card, text="-", bg="white", fg=ACCENT, wraplength=170,
                             font=("Segoe UI", 14, "bold"))
            value.pack(pady=(2, 10))
            labels[name] = value
        self.kpi_label_sets.append(labels)

    # ------------------------------------------------------------- Home tab
    def _build_home_tab(self, tab):
        self._make_kpi_cards(tab)

        tk.Label(tab, text="Welcome to the Sales Data Analysis and Management System",
                 font=("Segoe UI", 15, "bold"), fg=DARK).pack(anchor="w", pady=(10, 4))
        ttk.Label(tab, textvariable=self.home_info_var, font=("Segoe UI", 10)).pack(anchor="w")

        guide = ("Use the buttons below to move around:\n"
                 "  - Sales Records : add, search, update and delete sales records\n"
                 "  - Analytics     : detailed tables and statistics\n"
                 "  - Charts        : bar, line, pie, histogram, scatter and heatmap\n"
                 "  - Data Quality  : find and clean problems in a CSV file\n\n"
                 "Every change is saved to the CSV file immediately and all numbers "
                 "and charts are refreshed automatically.")
        ttk.Label(tab, text=guide, font=("Segoe UI", 10), justify="left").pack(anchor="w", pady=12)

        buttons = ttk.Frame(tab)
        buttons.pack(anchor="w")
        for name in ("Sales Records", "Analytics", "Charts", "Data Quality"):
            # lambda with a default argument: each button remembers its own tab name
            ttk.Button(buttons, text=f"Open {name}", width=20,
                       command=lambda n=name: self.notebook.select(self.tabs[n])
                       ).pack(side="left", padx=(0, 8))

    # ------------------------------------------------------ Sales Records tab
    def _build_records_tab(self, tab):
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        # ---------- left: the form ----------
        form = ttk.LabelFrame(tab, text=" Sales Record Form ", padding=12)
        form.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        hints = {"Order Date": "Order Date (YYYY-MM-DD)"}
        for row, field in enumerate(FORM_FIELDS):
            ttk.Label(form, text=hints.get(field, field) + ":").grid(
                row=row, column=0, sticky="w", pady=5)
            if field == "Category":
                widget = ttk.Combobox(form, textvariable=self.vars[field], width=24,
                                      values=list(DEFAULT_CATEGORIES))
            elif field == "Region":
                widget = ttk.Combobox(form, textvariable=self.vars[field], width=24,
                                      values=list(DEFAULT_REGIONS))
            else:
                widget = ttk.Entry(form, textvariable=self.vars[field], width=27)
            widget.grid(row=row, column=1, pady=5, padx=(8, 0))
            self.widgets[field] = widget

        # The amount is calculated automatically while the user types
        for field in ("Quantity", "Unit Price"):
            self.widgets[field].bind("<KeyRelease>", self.update_amount_preview)

        ttk.Label(form, text="Sales Amount:", font=("Segoe UI", 9, "bold")).grid(
            row=len(FORM_FIELDS), column=0, sticky="w", pady=(10, 5))
        ttk.Label(form, textvariable=self.amount_var, foreground=ACCENT,
                  font=("Segoe UI", 12, "bold")).grid(
            row=len(FORM_FIELDS), column=1, sticky="w", padx=(8, 0), pady=(10, 5))

        buttons = ttk.Frame(form)
        buttons.grid(row=len(FORM_FIELDS) + 1, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(buttons, text="Add Record", width=14, command=self.add_record).grid(row=0, column=0, padx=3, pady=3)
        ttk.Button(buttons, text="Update Record", width=14, command=self.update_record).grid(row=0, column=1, padx=3, pady=3)
        ttk.Button(buttons, text="Delete Selected", width=14, command=self.delete_record).grid(row=1, column=0, padx=3, pady=3)
        ttk.Button(buttons, text="Clear Form", width=14, command=self.clear_form).grid(row=1, column=1, padx=3, pady=3)

        ttk.Label(form, justify="left", foreground="#6c757d", font=("Segoe UI", 8),
                  text="Tip: click a row in the table to edit it.\n"
                       "Order ID is locked while editing.").grid(
            row=len(FORM_FIELDS) + 2, column=0, columnspan=2, pady=(12, 0), sticky="w")

        # ---------- right: search + table ----------
        right = ttk.Frame(tab)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        search_bar = ttk.Frame(right)
        search_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(search_bar, text="Search (Order ID or Product Name):").pack(side="left")
        entry = ttk.Entry(search_bar, textvariable=self.search_var, width=28)
        entry.pack(side="left", padx=8)
        entry.bind("<Return>", lambda event: self.search_records())   # Enter key = Search
        ttk.Button(search_bar, text="Search", command=self.search_records).pack(side="left", padx=3)
        ttk.Button(search_bar, text="Show All", command=self.show_all).pack(side="left", padx=3)
        ttk.Label(search_bar, textvariable=self.count_var, foreground="#6c757d").pack(side="right")

        table_frame = ttk.Frame(right)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.table = ttk.Treeview(table_frame, columns=COLUMNS, show="headings",
                                  selectmode="browse")
        for col in COLUMNS:
            # Clicking a heading sorts the table by that column
            self.table.heading(col, text=col, command=lambda c=col: self.sort_table(c))
            anchor = "e" if col in ("Quantity", "Unit Price", "Sales Amount") else "w"
            self.table.column(col, width=COLUMN_WIDTHS[col], anchor=anchor)
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.table.bind("<<TreeviewSelect>>", self.on_row_selected)

    # ---------------------------------------------------------- Analytics tab
    def _build_analytics_tab(self, tab):
        self._make_kpi_cards(tab)

        body = ttk.Frame(tab)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # left: product table
        left = ttk.LabelFrame(body, text=" Product-wise Sales and Revenue ", padding=6)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        columns = ("Product", "Units Sold", "Orders", "Revenue", "Avg Sale")
        self.product_table = ttk.Treeview(left, columns=columns, show="headings")
        for col in columns:
            self.product_table.heading(col, text=col)
            self.product_table.column(col, width=120 if col == "Product" else 90,
                                      anchor="w" if col == "Product" else "e")
        scroll = ttk.Scrollbar(left, orient="vertical", command=self.product_table.yview)
        self.product_table.configure(yscrollcommand=scroll.set)
        self.product_table.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        # right: text report
        right = ttk.LabelFrame(body, text=" Category, Region, Monthly and Statistics ", padding=6)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self.analysis_text = tk.Text(right, wrap="none", font=("Consolas", 9),
                                     bg="white", relief="flat", state="disabled")
        scroll_y = ttk.Scrollbar(right, orient="vertical", command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=scroll_y.set)
        self.analysis_text.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")

    # ------------------------------------------------------------- Charts tab
    def _build_charts_tab(self, tab):
        controls = ttk.Frame(tab)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(controls, text="Chart type:").pack(side="left")
        combo = ttk.Combobox(controls, textvariable=self.chart_var, state="readonly",
                             values=list(CHART_TYPES), width=34)
        combo.pack(side="left", padx=8)
        combo.bind("<<ComboboxSelected>>", lambda event: self.draw_chart())
        ttk.Button(controls, text="Draw Chart", command=self.draw_chart).pack(side="left")

        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=tab)
        toolbar = NavigationToolbar2Tk(self.canvas, tab, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ------------------------------------------------------- Data Quality tab
    def _build_quality_tab(self, tab):
        buttons = ttk.Frame(tab)
        buttons.pack(fill="x", pady=(0, 8))
        ttk.Button(buttons, text="Check Current Data", command=self.check_current_quality).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Inspect a CSV File...", command=self.inspect_csv_file).pack(side="left", padx=6)
        ttk.Button(buttons, text="Clean a CSV File and Export...", command=self.clean_and_export).pack(side="left", padx=6)

        info = ("Inspect = only report problems.   Clean and Export = write a cleaned copy "
                "(rejected rows go to a separate *_rejected.csv file). Your own data is not changed.")
        ttk.Label(tab, text=info, foreground="#6c757d", wraplength=1100).pack(anchor="w", pady=(0, 8))

        frame = ttk.Frame(tab)
        frame.pack(fill="both", expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.quality_text = tk.Text(frame, wrap="word", font=("Consolas", 10),
                                    bg="white", relief="flat", state="disabled", padx=10, pady=8)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.quality_text.yview)
        self.quality_text.configure(yscrollcommand=scroll.set)
        self.quality_text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.set_text(self.quality_text, "Choose one of the buttons above to see a data quality report.")

    # ==================================================================
    # SMALL HELPERS
    # ==================================================================
    def set_status(self, message):
        self.status_var.set(message)

    @staticmethod
    def set_text(widget, content):
        """Replace the text of a read-only Text widget."""
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def _show_load_warnings(self):
        if self.manager.load_warnings:
            messagebox.showwarning("Data File Warning", "\n\n".join(self.manager.load_warnings))

    def show_report_window(self, title, text):
        """Open a window with scrollable text and a 'Save as .txt' button."""
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("760x520")

        buttons = ttk.Frame(window)
        buttons.pack(side="bottom", fill="x", pady=8)
        frame = ttk.Frame(window)
        frame.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        box = tk.Text(frame, wrap="word", font=("Consolas", 10), padx=8, pady=6)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=box.yview)
        box.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        box.pack(side="left", fill="both", expand=True)
        box.insert("1.0", text)
        box.configure(state="disabled")

        def save_text():
            path = filedialog.asksaveasfilename(parent=window, defaultextension=".txt",
                                                filetypes=[("Text file", "*.txt")])
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as file:     # file handling
                        file.write(text)
                except OSError as error:
                    messagebox.showerror("Save Error", f"Could not save the file:\n{error}", parent=window)

        ttk.Button(buttons, text="Save as .txt", command=save_text).pack(side="left", padx=10)
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right", padx=10)

    # ==================================================================
    # FORM HANDLING
    # ==================================================================
    def update_amount_preview(self, event=None):
        """Show Quantity x Unit Price while the user is typing."""
        try:
            quantity = float(self.vars["Quantity"].get())
            price = float(self.vars["Unit Price"].get().replace(",", ""))
            self.amount_var.set(money(quantity * price) if quantity > 0 and price > 0 else "-")
        except ValueError:
            self.amount_var.set("-")

    def clear_form(self):
        """Empty the form and go back to 'add' mode."""
        for field in FORM_FIELDS:
            self.vars[field].set("")
        self.vars["Order Date"].set(datetime.now().strftime(DATE_FORMAT))
        self.amount_var.set("-")
        self.selected_order_id = None
        self.widgets["Order ID"].config(state="normal")
        self.table.selection_remove(*self.table.selection())
        self.widgets["Order ID"].focus_set()

    def read_form(self):
        """Build a SalesRecord from the form. Raises ValueError if anything is invalid."""
        values = {field: self.vars[field].get() for field in FORM_FIELDS}
        return SalesRecord(values["Order ID"], values["Order Date"], values["Product Name"],
                           values["Category"], values["Quantity"], values["Unit Price"],
                           values["Region"])

    def on_row_selected(self, event=None):
        """When a table row is clicked, copy it into the form (edit mode)."""
        selection = self.table.selection()
        if not selection:
            return
        record = self.manager.get_record(selection[0])
        if record is None:
            return
        for field in FORM_FIELDS:
            value = record[field]
            if field == "Unit Price":
                value = f"{float(value):.2f}"
            elif field == "Quantity":
                value = int(value)
            self.vars[field].set(str(value))
        self.selected_order_id = record["Order ID"]
        self.widgets["Order ID"].config(state="readonly")
        self.update_amount_preview()
        self.set_status(f"Editing record {self.selected_order_id}. "
                        "Change the values and click 'Update Record'.")

    # ==================================================================
    # CRUD BUTTONS
    # ==================================================================
    def _run_change(self, action, success_message):
        """
        Run a data-changing action, show errors in a dialog, refresh on success.
        'action' is a function (passed as an argument) that does the real work.
        """
        try:
            action()
        except ValueError as error:
            messagebox.showerror("Invalid Input", str(error))
            return False
        except OSError as error:
            messagebox.showerror("File Error", str(error))
            return False
        self.clear_form()
        self.refresh_all(success_message)
        return True

    def add_record(self):
        if self.selected_order_id is not None:
            messagebox.showinfo("Edit Mode",
                                f"You are editing record {self.selected_order_id}.\n"
                                "Click 'Clear Form' first to add a new record.")
            return

        def action():
            record = self.read_form()
            self.manager.add_record(record)

        self._run_change(action, "Record added and saved.")

    def update_record(self):
        if self.selected_order_id is None:
            messagebox.showwarning("No Record Selected",
                                   "Click a row in the table first, then change its values.")
            return

        def action():
            record = self.read_form()
            self.manager.update_record(record)

        self._run_change(action, f"Record {self.selected_order_id} updated and saved.")

    def delete_record(self):
        if self.selected_order_id is None:
            messagebox.showwarning("No Record Selected", "Click a row in the table to select it first.")
            return
        order_id = self.selected_order_id
        if not messagebox.askyesno("Confirm Delete",
                                   f"Delete record '{order_id}'?\nThis cannot be undone."):
            return
        self._run_change(lambda: self.manager.delete_record(order_id),
                         f"Record {order_id} deleted.")

    # ==================================================================
    # SEARCH AND SORT
    # ==================================================================
    def search_records(self):
        self.visible_df = self.manager.search(self.search_var.get())
        self.populate_table()
        found = len(self.visible_df)
        self.set_status(f"Search found {found} record(s).")
        if found == 0 and self.search_var.get().strip():
            messagebox.showinfo("No Results", "No record matches your search.")

    def show_all(self):
        self.search_var.set("")
        self.visible_df = self.manager.get_all()
        self.populate_table()
        self.set_status("Showing all records.")

    def sort_table(self, column):
        """Sort by the clicked column. Clicking again reverses the order."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column, self.sort_ascending = column, True
        self.populate_table()

    def populate_table(self):
        """Fill the Treeview with the rows of self.visible_df."""
        df = self.visible_df
        if self.sort_column in df.columns and not df.empty:
            df = df.sort_values(self.sort_column, ascending=self.sort_ascending, kind="stable")

        self.table.delete(*self.table.get_children())
        for row in df.to_dict("records"):
            self.table.insert("", "end", iid=row["Order ID"], values=(
                row["Order ID"], row["Order Date"], row["Product Name"], row["Category"],
                int(row["Quantity"]), f"{row['Unit Price']:,.2f}",
                f"{row['Sales Amount']:,.2f}", row["Region"]))
        self.count_var.set(f"Showing {len(df)} of {self.manager.count()} records")

    # ==================================================================
    # REFRESHING THE DASHBOARD
    # ==================================================================
    def refresh_all(self, message=None):
        """Rebuild the analyzer from the latest data and redraw everything."""
        self.analyzer = SalesAnalyzer(self.manager.get_all())
        self.update_choice_lists()
        self.visible_df = self.manager.search(self.search_var.get())
        self.populate_table()
        self.update_kpis()
        self.update_analytics()
        self.draw_chart()
        self.home_info_var.set(f"Records stored: {self.manager.count()}     "
                               f"Data file: {self.manager.csv_path}")
        if message:
            self.set_status(message)

    def refresh_dashboard(self):
        """Toolbar button: reload the CSV file from disk, then redraw everything."""
        self.manager.load()
        self._show_load_warnings()
        self.refresh_all("Dashboard refreshed from the data file.")

    def update_choice_lists(self):
        """Drop-down lists = default values + values already used in the data."""
        df = self.manager.get_all()
        categories = sorted(set(DEFAULT_CATEGORIES) | set(df["Category"].tolist()))   # set union
        regions = sorted(set(DEFAULT_REGIONS) | set(df["Region"].tolist()))
        self.widgets["Category"]["values"] = categories
        self.widgets["Region"]["values"] = regions

    def update_kpis(self):
        cards = self.analyzer.summary_cards()
        for labels in self.kpi_label_sets:
            for name, label in labels.items():
                label.config(text=cards[name])

    def update_analytics(self):
        a = self.analyzer

        # ----- product table -----
        self.product_table.delete(*self.product_table.get_children())
        for product, row in a.product_summary().iterrows():
            self.product_table.insert("", "end", values=(
                product, int(row["Units"]), int(row["Orders"]),
                money(row["Revenue"]), money(row["Avg_Sale"])))

        # ----- text report -----
        if a.is_empty():
            self.set_text(self.analysis_text, "No sales records yet.\nAdd a record or import a CSV file.")
            return

        def section(title, series):
            lines = [title, "-" * 40]
            lines.extend(f"{str(name)[:22]:<22}{money(value):>17}" for name, value in series.items())
            return lines + [""]

        top_name, top_value = a.highest_revenue_product()
        low_name, low_value = a.lowest_revenue_product()
        lines = section("CATEGORY-WISE REVENUE", a.revenue_by_category())
        lines += section("REGION-WISE REVENUE", a.revenue_by_region())
        lines += section("MONTHLY REVENUE", a.monthly_revenue())
        lines += ["PRODUCT EXTREMES", "-" * 40,
                  f"Highest: {top_name} ({money(top_value)})",
                  f"Lowest : {low_name} ({money(low_value)})", ""]
        lines += ["QUANTITY SOLD BY PRODUCT", "-" * 40]
        lines += [f"{str(name)[:22]:<22}{int(units):>17}" for name, units in a.quantity_by_product().items()]
        lines += ["", "ORDER VALUE STATISTICS (NumPy)", "-" * 40,
                  f"Average sales amount: {money(a.average_sales_amount())}"]
        lines += [f"{name:<22}{money(value):>17}" for name, value in a.statistics().items()]
        self.set_text(self.analysis_text, "\n".join(lines))

    def draw_chart(self):
        """Draw the chart chosen in the drop-down on the embedded Figure."""
        draw_function = CHART_TYPES.get(self.chart_var.get())
        self.figure.clear()
        try:
            draw_function(self.analyzer, self.figure)
            self.figure.tight_layout()
        except Exception as error:               # never let a chart crash the application
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.axis("off")
            ax.text(0.5, 0.5, f"This chart could not be drawn:\n{error}",
                    ha="center", va="center", transform=ax.transAxes)
        self.canvas.draw_idle()

    # ==================================================================
    # IMPORT / EXPORT
    # ==================================================================
    def import_csv(self):
        path = filedialog.askopenfilename(title="Select a sales CSV file",
                                          filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        choice = messagebox.askyesnocancel(
            "Import Mode",
            "How should the file be imported?\n\n"
            "YES     = Replace all current records with the file\n"
            "NO      = Add the new records to the current data\n"
            "CANCEL  = Stop")
        if choice is None:
            return
        mode = "replace" if choice else "append"
        try:
            log = self.manager.import_csv(path, mode)
        except ValueError as error:
            messagebox.showerror("Invalid File", str(error))
            return
        except OSError as error:
            messagebox.showerror("File Error", str(error))
            return
        self.clear_form()
        self.refresh_all("CSV file imported.")
        self.show_report_window("Import Report", "\n".join(log))

    def export_csv(self):
        if self.manager.count() == 0:
            messagebox.showwarning("Nothing to Export", "There are no records to export.")
            return
        path = filedialog.asksaveasfilename(title="Export records as CSV", defaultextension=".csv",
                                            initialfile="sales_export.csv",
                                            filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            self.manager.export_csv(path)
        except OSError as error:
            messagebox.showerror("File Error", str(error))
            return
        self.set_status(f"Exported {self.manager.count()} records to {path}")
        messagebox.showinfo("Export Complete", f"{self.manager.count()} records exported.")

    # ==================================================================
    # DATA QUALITY TAB
    # ==================================================================
    def check_current_quality(self):
        self.set_text(self.quality_text, "QUALITY REPORT - CURRENT DATA\n" + "=" * 50
                      + "\n\n" + self.manager.check_quality())
        self.set_status("Quality check finished.")

    def inspect_csv_file(self):
        path = filedialog.askopenfilename(title="Select a CSV file to inspect",
                                          filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            report = DataCleaner().inspect(DataCleaner.read_raw_csv(path))
        except ValueError as error:
            messagebox.showerror("Invalid File", str(error))
            return
        self.set_text(self.quality_text, f"QUALITY REPORT - {path}\n" + "=" * 50 + "\n\n" + report)
        self.set_status("File inspected. Nothing was changed.")

    def clean_and_export(self):
        source = filedialog.askopenfilename(title="Select the CSV file to clean",
                                            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not source:
            return
        target = filedialog.asksaveasfilename(title="Save the cleaned file as",
                                              defaultextension=".csv",
                                              initialfile="sales_cleaned.csv",
                                              filetypes=[("CSV files", "*.csv")])
        if not target:
            return
        try:
            log = DataCleaner().clean_csv_file(source, target)
        except ValueError as error:
            messagebox.showerror("Invalid File", str(error))
            return
        except OSError as error:
            messagebox.showerror("File Error", str(error))
            return
        self.set_text(self.quality_text, "CLEANING REPORT\n" + "=" * 50 + "\n\n" + "\n".join(log))
        self.set_status("Cleaned file exported.")
