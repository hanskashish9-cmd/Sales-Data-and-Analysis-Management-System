"""
visualizations.py
-----------------
Every chart is a function with the same signature:

        chart_name(analyzer, fig)

  analyzer : a SalesAnalyzer holding the current data
  fig      : an EMPTY Matplotlib Figure to draw on

The GUI puts the Figure inside a Tkinter window. If there is no data, the
function writes a message on the figure instead of crashing.
All charts are collected in the CHART_TYPES dictionary (name -> function),
which the GUI uses to fill its drop-down list.
"""

import seaborn as sns

from config import CURRENCY, money

sns.set_theme(style="whitegrid")   # clean look for every chart


def _show_message(fig, text):
    """Write a centred message on the figure (used when a chart cannot be drawn)."""
    ax = fig.add_subplot(111)
    ax.axis("off")
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=13,
            color="gray", transform=ax.transAxes)


def _title(ax, text):
    ax.set_title(text, fontsize=14, fontweight="bold")


# ---------------------------------------------------------------- bar charts
def chart_product_revenue(analyzer, fig):
    """Horizontal bar chart: top 10 products by revenue."""
    revenue = analyzer.revenue_by_product().head(10)
    if revenue.empty:
        return _show_message(fig, "No sales data to display.")
    data = revenue.reset_index()
    data.columns = ["Product", "Revenue"]
    ax = fig.add_subplot(111)
    sns.barplot(data=data, y="Product", x="Revenue", hue="Product",
                palette="crest", legend=False, ax=ax)
    for bars in ax.containers:
        ax.bar_label(bars, labels=[money(b.get_width()) for b in bars], padding=3, fontsize=8)
    _title(ax, "Revenue by Product (Top 10)")
    ax.set_xlabel(f"Total Revenue ({CURRENCY})")
    ax.set_ylabel("Product")
    ax.margins(x=0.22)


def chart_category_revenue(analyzer, fig):
    """Bar chart: revenue of each category."""
    revenue = analyzer.revenue_by_category()
    if revenue.empty:
        return _show_message(fig, "No sales data to display.")
    data = revenue.reset_index()
    data.columns = ["Category", "Revenue"]
    ax = fig.add_subplot(111)
    sns.barplot(data=data, x="Category", y="Revenue", hue="Category",
                palette="viridis", legend=False, ax=ax)
    for bars in ax.containers:
        ax.bar_label(bars, labels=[money(b.get_height()) for b in bars], padding=3, fontsize=8)
    _title(ax, "Revenue by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel(f"Total Revenue ({CURRENCY})")
    ax.tick_params(axis="x", rotation=20)
    ax.margins(y=0.15)


def chart_region_revenue(analyzer, fig):
    """Bar chart: revenue of each region."""
    revenue = analyzer.revenue_by_region()
    if revenue.empty:
        return _show_message(fig, "No sales data to display.")
    data = revenue.reset_index()
    data.columns = ["Region", "Revenue"]
    ax = fig.add_subplot(111)
    sns.barplot(data=data, x="Region", y="Revenue", hue="Region",
                palette="mako", legend=False, ax=ax)
    for bars in ax.containers:
        ax.bar_label(bars, labels=[money(b.get_height()) for b in bars], padding=3, fontsize=8)
    _title(ax, "Revenue by Region")
    ax.set_xlabel("Region")
    ax.set_ylabel(f"Total Revenue ({CURRENCY})")
    ax.margins(y=0.15)


# ---------------------------------------------------------------- line chart
def chart_monthly_trend(analyzer, fig):
    """Line chart: revenue month by month."""
    monthly = analyzer.monthly_revenue()
    if monthly.empty:
        return _show_message(fig, "No dated sales data to display.")
    ax = fig.add_subplot(111)
    ax.plot(monthly.index, monthly.values, marker="o", linewidth=2,
            color="#2a6f97", label="Monthly Revenue")
    peak = monthly.idxmax()
    ax.annotate(f"Peak: {peak}", xy=(peak, monthly.max()), xytext=(0, 14),
                textcoords="offset points", ha="center",
                arrowprops=dict(arrowstyle="->"))
    _title(ax, "Monthly Sales Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel(f"Total Revenue ({CURRENCY})")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    ax.margins(y=0.2)


# ----------------------------------------------------------------- pie chart
def chart_category_pie(analyzer, fig):
    """Pie chart: share of each category in total revenue."""
    revenue = analyzer.revenue_by_category()
    if revenue.empty or revenue.sum() <= 0:
        return _show_message(fig, "No sales data to display.")
    ax = fig.add_subplot(111)
    wedges, _, _ = ax.pie(revenue.values, autopct="%1.1f%%", startangle=90,
                          colors=sns.color_palette("pastel", len(revenue)),
                          wedgeprops=dict(edgecolor="white"))
    ax.legend(wedges, revenue.index, title="Category", loc="center left",
              bbox_to_anchor=(1, 0.5))
    _title(ax, "Category-wise Revenue Distribution")
    ax.axis("equal")


# ----------------------------------------------------------------- histogram
def chart_order_histogram(analyzer, fig):
    """Histogram: how are order values spread?"""
    values = analyzer.order_values()
    if values.size == 0:
        return _show_message(fig, "No sales data to display.")
    ax = fig.add_subplot(111)
    # The smooth KDE curve needs enough different values to work
    use_kde = values.size >= 5 and len(set(values.tolist())) > 1
    sns.histplot(values, bins=min(15, max(5, values.size // 3)), kde=use_kde,
                 color="#e07a5f", ax=ax)
    mean_value = analyzer.average_sales_amount()
    ax.axvline(mean_value, color="black", linestyle="--", label=f"Mean = {money(mean_value)}")
    _title(ax, "Distribution of Order Values")
    ax.set_xlabel(f"Sales Amount ({CURRENCY})")
    ax.set_ylabel("Number of Orders")
    ax.legend()


# ------------------------------------------------------------- scatter plot
def chart_quantity_scatter(analyzer, fig):
    """Scatter plot: quantity sold versus sales amount."""
    if analyzer.is_empty():
        return _show_message(fig, "No sales data to display.")
    ax = fig.add_subplot(111)
    sns.scatterplot(data=analyzer.data, x="Quantity", y="Sales Amount",
                    hue="Category", s=70, alpha=0.85, ax=ax)
    _title(ax, "Quantity vs Sales Amount")
    ax.set_xlabel("Quantity Sold")
    ax.set_ylabel(f"Sales Amount ({CURRENCY})")
    ax.legend(title="Category", fontsize=8)


# ------------------------------------------------------------------- heatmap
def chart_correlation_heatmap(analyzer, fig):
    """Seaborn heatmap: correlation between the numeric columns."""
    if analyzer.is_empty() or len(analyzer.data) < 3:
        return _show_message(fig, "At least 3 records are needed\nto calculate correlations.")
    ax = fig.add_subplot(111)
    sns.heatmap(analyzer.correlation(), annot=True, fmt=".2f", cmap="coolwarm",
                vmin=-1, vmax=1, linewidths=0.5,
                cbar_kws={"label": "Correlation (-1 to +1)"}, ax=ax)
    _title(ax, "Correlation between Numeric Fields")


# Name shown in the drop-down  ->  function that draws it
CHART_TYPES = {
    "Bar - Revenue by Product":      chart_product_revenue,
    "Bar - Revenue by Category":     chart_category_revenue,
    "Bar - Revenue by Region":       chart_region_revenue,
    "Line - Monthly Sales Trend":    chart_monthly_trend,
    "Pie - Category Revenue Share":  chart_category_pie,
    "Histogram - Order Values":      chart_order_histogram,
    "Scatter - Quantity vs Sales":   chart_quantity_scatter,
    "Heatmap - Correlation":         chart_correlation_heatmap,
}
