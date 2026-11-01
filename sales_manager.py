"""
sales_manager.py
----------------
Two classes:

  DataCleaner  - checks and cleans raw data (used when loading / importing).
  SalesManager - the "database layer": add, update, delete, search,
                 load, save, import and export. Data lives in a Pandas
                 DataFrame and is saved to a CSV file after every change.

Design rule: the manager never touches the screen. It only raises errors
(ValueError / OSError) and the GUI decides how to show them.
"""

import os
from collections import Counter
from datetime import datetime

import numpy as np
import pandas as pd

from config import (COLUMNS, REQUIRED_INPUT_COLUMNS, DATA_FILE, REJECTED_FILE,
                    DATE_FORMAT, ACCEPTED_DATE_FORMATS, MISSING_TOKENS)
from models import SalesRecord


# ======================================================================
# Small helper functions
# ======================================================================

def empty_sales_frame():
    """An empty DataFrame that already has the right columns and data types."""
    frame = pd.DataFrame(columns=COLUMNS)
    return frame.astype({"Quantity": "int64", "Unit Price": "float64",
                         "Sales Amount": "float64"})


def parse_date_text(text):
    """
    Convert date text to 'YYYY-MM-DD'. Returns '' if the date is invalid.
    Tries each accepted format one by one (loop + exception handling).
    """
    text = str(text).strip().split(" ")[0]       # ignore a time part like '10:30:00'
    for date_format in ACCEPTED_DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).strftime(DATE_FORMAT)
        except ValueError:
            continue
    return ""


def write_csv_file(df, path):
    """Write a DataFrame to a CSV file with friendly error messages."""
    try:
        df.to_csv(path, index=False, encoding="utf-8")
    except PermissionError:
        raise OSError(f"Cannot write to '{os.path.basename(path)}'. "
                      "If the file is open in Excel, close it and try again.")
    except OSError as error:
        raise OSError(f"Could not save '{os.path.basename(path)}': {error}")


# ======================================================================
# DataCleaner
# ======================================================================

class DataCleaner:
    """
    Inspects and cleans raw sales data.

    ASSUMPTIONS (printed in every report so nothing is hidden):
      1. Important fields (Order ID, Date, Product, Quantity, Unit Price)
         are never guessed. A row with a missing/invalid important field is
         REJECTED and reported - it is not silently repaired.
      2. Missing Category or Region is filled with 'Unknown' (reported).
      3. Sales Amount is a derived value, so it is always recalculated as
         Quantity x Unit Price. Rows where the file's value differed are counted.
      4. For duplicate Order IDs the first row is kept, later copies rejected.
      5. Dates like 15/03/2025 are read as day/month/year.
      6. Category/Region written fully in lower or UPPER case are changed to
         Title Case ('north' -> 'North'). Mixed case is left unchanged.
    """

    ASSUMPTIONS = [
        "Rows with a missing/invalid Order ID, Date, Product, Quantity or Unit Price "
        "are rejected, not guessed.",
        "Missing Category / Region -> 'Unknown'.",
        "Sales Amount is recalculated as Quantity x Unit Price.",
        "Duplicate Order IDs: first row kept, later copies rejected.",
        "dd/mm/yyyy dates are read as day-first.",
        "all-lower or ALL-UPPER Category/Region text is changed to Title Case.",
    ]

    # ------------------------------------------------------------ reading
    @staticmethod
    def read_raw_csv(path):
        """
        Read a CSV file with EVERYTHING as text (dtype=str). Reading as text means
        Pandas never guesses types, so bad values such as 'abc' are not hidden.
        """
        last_error = None
        for encoding in ("utf-8-sig", "cp1252"):      # Excel files are often cp1252
            try:
                return pd.read_csv(path, dtype=str, keep_default_na=False,
                                   encoding=encoding)
            except FileNotFoundError:
                raise ValueError("The selected file could not be found.")
            except PermissionError:
                raise ValueError("Permission denied. Close the file if it is open in Excel.")
            except pd.errors.EmptyDataError:
                raise ValueError("The file is empty.")
            except pd.errors.ParserError:
                raise ValueError("The file is not a properly formatted CSV file.")
            except UnicodeDecodeError as error:
                last_error = error
        raise ValueError(f"The file could not be read as text: {last_error}")

    # --------------------------------------------------------- preparing
    @staticmethod
    def _prepare(raw_df):
        """Check the columns, trim spaces and mark missing values as ''."""
        df = raw_df.copy()
        df.columns = [str(col).strip() for col in df.columns]

        if df.columns.duplicated().any():
            raise ValueError("The file has repeated column names.")
        missing = [col for col in REQUIRED_INPUT_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError("The file is missing required column(s):\n  - "
                             + "\n  - ".join(missing)
                             + "\n\nRequired columns: " + ", ".join(REQUIRED_INPUT_COLUMNS))
        if "Sales Amount" not in df.columns:
            df["Sales Amount"] = ""

        df = df[COLUMNS].reset_index(drop=True)
        for col in COLUMNS:
            df[col] = df[col].fillna("").astype(str).str.strip()
            df.loc[df[col].str.lower().isin(MISSING_TOKENS), col] = ""
        return df

    def _evaluate(self, raw_df):
        """
        Find every problem WITHOUT changing the data.
        Returns a dictionary with the prepared text table, one 'reason' per
        row ('' means the row is fine) and the parsed numbers.
        """
        df = self._prepare(raw_df)
        reasons = pd.Series("", index=df.index, dtype="object")

        def flag(mask, text):
            """Give 'text' as reason to rows that have no reason yet."""
            reasons.loc[mask & (reasons == "")] = text

        flag(df["Order ID"] == "", "Missing Order ID")
        flag(df["Product Name"] == "", "Missing Product Name")

        dates = df["Order Date"].map(parse_date_text)
        flag(dates == "", "Missing or invalid Order Date")

        qty = pd.to_numeric(df["Quantity"], errors="coerce").astype(float)
        qty = qty.replace([np.inf, -np.inf], np.nan)
        flag(qty.isna() | (qty <= 0) | ((qty % 1) != 0),
             "Invalid Quantity (needs a whole number above 0)")

        price = pd.to_numeric(df["Unit Price"], errors="coerce").astype(float)
        price = price.replace([np.inf, -np.inf], np.nan)
        flag(price.isna() | (price <= 0), "Invalid Unit Price (needs a number above 0)")

        # Duplicate Order IDs are checked only among rows that are otherwise fine
        ok = reasons == ""
        if ok.any():
            duplicate = pd.Series(False, index=df.index)
            duplicate[ok] = df.loc[ok, "Order ID"].str.upper().duplicated(keep="first")
            flag(duplicate, "Duplicate Order ID (later copy)")

        return {"df": df, "reasons": reasons, "dates": dates, "qty": qty, "price": price}

    # ----------------------------------------------------------- inspect
    def inspect(self, raw_df):
        """Return a text report about data quality. Nothing is changed."""
        ev = self._evaluate(raw_df)
        df, reasons = ev["df"], ev["reasons"]
        rejected = int((reasons != "").sum())

        lines = [f"Rows checked: {len(df)}", "", "Missing values per column:"]
        for col in COLUMNS:
            count = int((df[col] == "").sum())
            note = "   (will be calculated)" if col == "Sales Amount" and count else ""
            lines.append(f"  {col:<14}: {count}{note}")

        lines.extend(["", "Problems found:"])
        counts = Counter(reasons[reasons != ""])           # counts each reason
        if counts:
            for reason, count in counts.items():
                lines.append(f"  {count:>4} row(s) - {reason}")
        else:
            lines.append("  No rejected rows.")
        lines.append(f"  Exact duplicate rows : {int(df.duplicated().sum())}")

        good = reasons == ""
        amount = pd.to_numeric(df.loc[good, "Sales Amount"], errors="coerce")
        calc = ev["qty"][good] * ev["price"][good]
        mismatch = int((amount.notna() & ((amount - calc).abs() > 0.01)).sum())
        lines.append(f"  Sales Amount differs from Quantity x Unit Price: {mismatch}")
        lines.append(f"  Missing Category/Region (-> 'Unknown'): "
                     f"{int((df.loc[good, 'Category'] == '').sum() + (df.loc[good, 'Region'] == '').sum())}")

        lines.extend(["", f"Result: {len(df) - rejected} row(s) usable, "
                          f"{rejected} row(s) would be rejected.", "",
                      "Cleaning assumptions:"])
        lines.extend(f"  - {text}" for text in self.ASSUMPTIONS)
        return "\n".join(lines)

    # ------------------------------------------------------------- clean
    @staticmethod
    def _standardise_case(series):
        """'north' / 'NORTH' -> 'North'. Mixed case such as 'North East' is untouched."""
        needs = series.str.islower() | series.str.isupper()
        fixed = series.copy()
        fixed[needs] = series[needs].str.title()
        return fixed

    def clean(self, raw_df):
        """
        Clean the data. Returns (clean_df, rejected_df, log_lines).
        Rejected rows are returned, never thrown away silently.
        """
        ev = self._evaluate(raw_df)
        df, reasons = ev["df"], ev["reasons"]
        keep = reasons == ""

        good = df[keep].copy()
        good["Order Date"] = ev["dates"][keep]
        good["Quantity"] = ev["qty"][keep].astype("int64")
        good["Unit Price"] = ev["price"][keep].round(2).astype(float)

        # Sales Amount: always recalculated; count how many differed
        given = pd.to_numeric(good["Sales Amount"], errors="coerce")
        calculated = (good["Quantity"] * good["Unit Price"]).round(2)
        changed_amounts = int((given.notna() & ((given - calculated).abs() > 0.01)).sum())
        missing_amounts = int(given.isna().sum())
        good["Sales Amount"] = calculated.astype(float)

        # Category / Region: fix case, then fill missing with 'Unknown'
        case_fixed = 0
        filled = 0
        for col in ("Category", "Region"):
            fixed = self._standardise_case(good[col])
            case_fixed += int((fixed != good[col]).sum())
            good[col] = fixed
            empty = good[col] == ""
            filled += int(empty.sum())
            good.loc[empty, col] = "Unknown"

        good = good[COLUMNS].reset_index(drop=True)

        rejected = df[~keep].copy()
        rejected.insert(0, "Row", rejected.index + 2)       # +2 = CSV line number
        rejected["Reason"] = reasons[~keep]

        # ---- log ----
        log = [f"Rows read           : {len(df)}",
               f"Rows accepted       : {len(good)}",
               f"Rows rejected       : {len(rejected)}"]
        for reason, count in Counter(rejected["Reason"]).items():
            log.append(f"     {count} x {reason}")
        log.append(f"Missing Category/Region filled with 'Unknown': {filled}")
        log.append(f"Sales Amount calculated (was missing)        : {missing_amounts}")
        log.append(f"Sales Amount corrected (did not match)       : {changed_amounts}")
        log.append(f"Category/Region case standardised            : {case_fixed}")
        if not rejected.empty:
            log.append("")
            log.append("First rejected rows (CSV line number):")
            for _, row in rejected.head(10).iterrows():
                log.append(f"  line {row['Row']}: {row['Order ID'] or '(no ID)'} - {row['Reason']}")
        log.append("")
        log.append("Assumptions used:")
        log.extend(f"  - {text}" for text in self.ASSUMPTIONS)
        return good, rejected, log

    def clean_csv_file(self, source_path, output_path):
        """Clean a CSV file and write the result. Rejected rows go to *_rejected.csv."""
        raw = self.read_raw_csv(source_path)
        cleaned, rejected, log = self.clean(raw)
        if cleaned.empty:
            raise ValueError("No valid rows were found in this file.\n\n" + "\n".join(log))
        write_csv_file(cleaned, output_path)
        log.insert(0, f"Cleaned file saved: {output_path}")
        if not rejected.empty:
            rejected_path = os.path.splitext(output_path)[0] + "_rejected.csv"
            write_csv_file(rejected, rejected_path)
            log.insert(1, f"Rejected rows saved: {rejected_path}")
        return log


# ======================================================================
# SalesManager
# ======================================================================

class SalesManager:
    """Stores all sales records and keeps the CSV file in sync."""

    def __init__(self, csv_path=DATA_FILE):          # default argument
        self.csv_path = csv_path
        self._df = empty_sales_frame()               # protected: use the methods below
        self.load_warnings = []                      # messages for the GUI to show
        self.load()

    # ----------------------------------------------------------- helpers
    def _commit(self, new_df):
        """
        Save first, then update memory. If saving fails (for example the file
        is open in Excel) memory is NOT changed, so screen and file stay equal.
        """
        write_csv_file(new_df[COLUMNS], self.csv_path)
        self._df = new_df.reset_index(drop=True)

    def _row_mask(self, order_id):
        """True for the row(s) having this Order ID (not case sensitive)."""
        return self._df["Order ID"].str.upper() == str(order_id).strip().upper()

    @staticmethod
    def _join(frame_a, frame_b):
        """Stack two DataFrames (skips empty ones to avoid Pandas warnings)."""
        if frame_a.empty:
            return frame_b.copy()
        if frame_b.empty:
            return frame_a.copy()
        return pd.concat([frame_a, frame_b], ignore_index=True)

    # ------------------------------------------------------------ loading
    def load(self):
        """Load saved records at start-up. Bad rows are reported, not hidden."""
        self.load_warnings = []
        if not os.path.exists(self.csv_path):
            self._df = empty_sales_frame()
            return
        try:
            raw = DataCleaner.read_raw_csv(self.csv_path)
            cleaned, rejected, _ = DataCleaner().clean(raw)
        except ValueError as error:
            self._df = empty_sales_frame()
            self.load_warnings.append(f"Could not load '{os.path.basename(self.csv_path)}': {error}")
            return
        self._df = cleaned
        if not rejected.empty:
            try:
                write_csv_file(rejected, REJECTED_FILE)
                where = f"They were saved to '{os.path.basename(REJECTED_FILE)}'."
            except OSError:
                where = "They could not be saved to a separate file."
            self.load_warnings.append(
                f"{len(rejected)} row(s) in '{os.path.basename(self.csv_path)}' were invalid "
                f"and skipped. {where}")

    # --------------------------------------------------------------- read
    def get_all(self):
        """Return a COPY of all records (so outside code cannot damage ours)."""
        return self._df.copy()

    def count(self):
        return len(self._df)

    def get_record(self, order_id):
        """Return one record as a dictionary, or None if not found."""
        found = self._df[self._row_mask(order_id)]
        return None if found.empty else found.iloc[0].to_dict()

    def search(self, keyword):
        """Records whose Order ID or Product Name contains the keyword."""
        keyword = str(keyword).strip()
        if not keyword:
            return self.get_all()
        mask = (self._df["Order ID"].str.contains(keyword, case=False, regex=False)
                | self._df["Product Name"].str.contains(keyword, case=False, regex=False))
        return self._df[mask].copy()

    # ------------------------------------------------------ add/update/delete
    def add_record(self, record):
        """Add a SalesRecord. Rejects a duplicate Order ID."""
        if self._row_mask(record.order_id).any():
            raise ValueError(f"Order ID '{record.order_id}' already exists. "
                             "Order IDs must be unique.")
        new_row = pd.DataFrame([record.to_dict()])[COLUMNS]
        self._commit(self._join(self._df, new_row))

    def update_record(self, record):
        """Replace the stored record that has the same Order ID."""
        mask = self._row_mask(record.order_id)
        if not mask.any():
            raise ValueError(f"Order ID '{record.order_id}' was not found. "
                             "The Order ID of an existing record cannot be changed.")
        new_df = self._df.copy()
        for column, value in record.to_dict().items():
            new_df.loc[mask, column] = value
        self._commit(new_df)

    def delete_record(self, order_id):
        """Delete the record with this Order ID."""
        mask = self._row_mask(order_id)
        if not mask.any():
            raise ValueError(f"Order ID '{order_id}' was not found.")
        self._commit(self._df[~mask])

    # ------------------------------------------------------- import / export
    def import_csv(self, path, mode="append"):
        """
        Import a CSV file after cleaning it. mode = 'append' or 'replace'.
        Returns the cleaning log (list of text lines).
        """
        raw = DataCleaner.read_raw_csv(path)
        cleaned, rejected, log = DataCleaner().clean(raw)
        if cleaned.empty:
            raise ValueError("No valid records were found in this file.\n\n" + "\n".join(log))

        if mode == "replace":
            new_df = cleaned
            log.insert(0, f"Imported {len(cleaned)} record(s). All previous records were replaced.")
        else:
            existing_ids = set(self._df["Order ID"].str.upper())          # set
            already_there = cleaned["Order ID"].str.upper().isin(existing_ids)
            new_df = self._join(self._df, cleaned[~already_there])
            log.insert(0, f"Imported {int((~already_there).sum())} new record(s); "
                          f"skipped {int(already_there.sum())} whose Order ID already exists.")
        self._commit(new_df)
        return log

    def export_csv(self, path):
        """Write all current records to a CSV file chosen by the user."""
        write_csv_file(self._df[COLUMNS], path)

    def check_quality(self):
        """Quality report for the data currently stored."""
        return DataCleaner().inspect(self._df.astype(str))
