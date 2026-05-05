import tkinter as tk
from tkinter import ttk, messagebox
from dbManager import DatabaseManager
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class Reports(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        self.current_user = None
        
        self.configure(padx=20, pady=20)
        self.access_denied_label = tk.Label(self, text="Admin Access Required", font=("Helvetica", 16, "bold"), fg="red")

        # Variables for charts to prevent memory leaks on redraw
        self.trend_canvas = None
        self.pie_canvas = None

    def set_user(self, user):
        self.current_user = user
        for widget in self.winfo_children():
            widget.destroy()

        if user and user['role'] == 'Admin':
            self.create_widgets()
            self.generate_reports()
        else:
            self.access_denied_label = tk.Label(self, text="Access Denied. Administrator privileges required.", font=("Helvetica", 16, "bold"), fg="red")
            self.access_denied_label.pack(expand=True)

    def create_widgets(self):
        # --- Header & Filter ---
        header_frame = tk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(header_frame, text="Business Reports & Analytics", font=("Helvetica", 16, "bold"), fg="#2C3E50").pack(side="left")

        filter_frame = tk.Frame(header_frame)
        filter_frame.pack(side="right")
        
        tk.Label(filter_frame, text="Date Range:").pack(side="left", padx=5)
        self.date_var = tk.StringVar(value="This Month")
        date_cb = ttk.Combobox(filter_frame, textvariable=self.date_var, state="readonly", width=15)
        date_cb['values'] = ("All Time", "Today", "Last 7 Days", "This Month", "This Year")
        date_cb.pack(side="left", padx=5)
        date_cb.bind("<<ComboboxSelected>>", lambda e: self.generate_reports())

        # --- Tabbed Interface ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_tab, text=" Financial Summary & Trends ")

        self.service_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.service_tab, text=" Service & Add-on Performance ")

        self.build_summary_tab()
        self.build_service_tab()

    def build_summary_tab(self):
        # Top Stats Frame
        self.stats_frame = tk.Frame(self.summary_tab)
        self.stats_frame.pack(fill="x", pady=10, padx=10)
        
        for i in range(3): self.stats_frame.columnconfigure(i, weight=1)

        self.stat_vars = {
            "Finished Transactions": tk.StringVar(),
            "Total Sales Expected": tk.StringVar(),
            "Average Transaction Value": tk.StringVar(),
            "Unclaimed Transactions": tk.StringVar(),
            "Unpaid Orders": tk.StringVar(),
            "Voided Transactions": tk.StringVar()
        }

        # Row 0
        self.create_stat_card(self.stats_frame, "Finished (Claimed)", self.stat_vars["Finished Transactions"], "#27AE60", 0, 0)
        self.create_stat_card(self.stats_frame, "Total Sales (Gross)", self.stat_vars["Total Sales Expected"], "#2980B9", 0, 1)
        self.create_stat_card(self.stats_frame, "Avg. Transaction", self.stat_vars["Average Transaction Value"], "#8E44AD", 0, 2)
        # Row 1
        self.create_stat_card(self.stats_frame, "Unclaimed Orders", self.stat_vars["Unclaimed Transactions"], "#F39C12", 1, 0)
        self.create_stat_card(self.stats_frame, "Unpaid Orders", self.stat_vars["Unpaid Orders"], "#D35400", 1, 1)
        self.create_stat_card(self.stats_frame, "Voided Transactions", self.stat_vars["Voided Transactions"], "#C0392B", 1, 2)

        # Charts Frame
        self.charts_frame = tk.Frame(self.summary_tab)
        self.charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.charts_frame.columnconfigure(0, weight=2) # Line Chart gets more space
        self.charts_frame.columnconfigure(1, weight=1) # Pie Chart gets less

        self.trend_frame = tk.LabelFrame(self.charts_frame, text="Sales Trend", padx=5, pady=5)
        self.trend_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.pie_frame = tk.LabelFrame(self.charts_frame, text="Payment Analysis (Amount)", padx=5, pady=5)
        self.pie_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    def build_service_tab(self):
        # Layout for Services and Addons performance (Side by side Treeviews)
        self.service_tab.columnconfigure(0, weight=1)
        self.service_tab.columnconfigure(1, weight=1)

        # Top Services
        srv_frame = tk.LabelFrame(self.service_tab, text="Top Performing Services", padx=10, pady=10)
        srv_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        cols = ("rank", "name", "usage", "income")
        self.perf_srv_tree = ttk.Treeview(srv_frame, columns=cols, show="headings", height=15)
        self.perf_srv_tree.heading("rank", text="#")
        self.perf_srv_tree.heading("name", text="Service")
        self.perf_srv_tree.heading("usage", text="Times Used")
        self.perf_srv_tree.heading("income", text="Total Income Generated")
        
        self.perf_srv_tree.column("rank", width=40, anchor="center")
        self.perf_srv_tree.column("name", width=150)
        self.perf_srv_tree.column("usage", width=80, anchor="center")
        self.perf_srv_tree.column("income", width=120, anchor="e")
        self.perf_srv_tree.pack(fill="both", expand=True)

        # Top Addons
        add_frame = tk.LabelFrame(self.service_tab, text="Top Performing Add-ons", padx=10, pady=10)
        add_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.perf_add_tree = ttk.Treeview(add_frame, columns=cols, show="headings", height=15)
        self.perf_add_tree.heading("rank", text="#")
        self.perf_add_tree.heading("name", text="Add-on")
        self.perf_add_tree.heading("usage", text="Times Used")
        self.perf_add_tree.heading("income", text="Total Income Generated")

        self.perf_add_tree.column("rank", width=40, anchor="center")
        self.perf_add_tree.column("name", width=150)
        self.perf_add_tree.column("usage", width=80, anchor="center")
        self.perf_add_tree.column("income", width=120, anchor="e")
        self.perf_add_tree.pack(fill="both", expand=True)

    def create_stat_card(self, parent, title, variable, color, row, col):
        card = tk.Frame(parent, bg=color, bd=0, padx=10, pady=10)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        tk.Label(card, text=title, font=("Helvetica", 10), bg=color, fg="white").pack(anchor="w")
        tk.Label(card, textvariable=variable, font=("Helvetica", 16, "bold"), bg=color, fg="white").pack(anchor="w", pady=(2, 0))

    def get_date_condition(self, column="created_at"):
        time_filter = self.date_var.get()
        if time_filter == "Today":
            return f"DATE({column}) = CURDATE()"
        elif time_filter == "Last 7 Days":
            return f"{column} >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif time_filter == "This Month":
            return f"MONTH({column}) = MONTH(CURDATE()) AND YEAR({column}) = YEAR(CURDATE())"
        elif time_filter == "This Year":
            return f"YEAR({column}) = YEAR(CURDATE())"
        return "1=1" # All time
    
    def generate_reports(self):
        # We define two conditions: one for created dates and one for voided dates
        date_cond_created = self.get_date_condition("created_at")
        date_cond_voided = self.get_date_condition("void_at")
        
        try:
            # === SUMMARY STATS ===
            # We remove the WHERE clause from the main query and move the date filters 
            # inside the CASE statements for absolute accuracy.
            stats = self.db.fetch_one(f"""
                SELECT 
                    COUNT(CASE WHEN status = 'Claimed' AND void_status = 'Active' AND {date_cond_created} THEN 1 END) as finished_count,
                    SUM(CASE WHEN void_status = 'Active' AND {date_cond_created} THEN total_amount ELSE 0 END) as total_sales,
                    COUNT(CASE WHEN void_status = 'Active' AND {date_cond_created} THEN 1 END) as active_count,
                    COUNT(CASE WHEN status != 'Claimed' AND void_status = 'Active' AND {date_cond_created} THEN 1 END) as unclaimed_count,
                    COUNT(CASE WHEN payment_status = 'Unpaid' AND void_status = 'Active' AND {date_cond_created} THEN 1 END) as unpaid_count,
                    COUNT(CASE WHEN void_status = 'Voided' AND {date_cond_voided} THEN 1 END) as voided_count
                FROM Transactions 
                WHERE ({date_cond_created}) OR ({date_cond_voided})
            """)

            t_sales = float(stats['total_sales'] or 0)
            a_count = int(stats['active_count'] or 0)
            avg_val = (t_sales / a_count) if a_count > 0 else 0.0

            self.stat_vars["Finished Transactions"].set(str(stats['finished_count']))
            self.stat_vars["Total Sales Expected"].set(f"₱{t_sales:,.2f}")
            self.stat_vars["Average Transaction Value"].set(f"₱{avg_val:,.2f}")
            self.stat_vars["Unclaimed Transactions"].set(str(stats['unclaimed_count']))
            self.stat_vars["Unpaid Orders"].set(str(stats['unpaid_count']))
            self.stat_vars["Voided Transactions"].set(str(stats['voided_count']))

            # === CHARTS & PERFORMANCE ===
            # Pass the creation date condition to the other methods
            self.draw_sales_trend(date_cond_created)
            self.draw_payment_pie(date_cond_created)
            self.load_service_performance(date_cond_created)

        except Exception as e:
            print(f"Report Generation Error: {e}")

    def draw_sales_trend(self, date_cond):
        query = f"""
            SELECT DATE(created_at) as t_date, SUM(total_amount) as daily_total
            FROM Transactions 
            WHERE void_status = 'Active' AND {date_cond}
            GROUP BY DATE(created_at)
            ORDER BY t_date ASC
        """
        data = self.db.fetch_all(query)
        
        dates = [row['t_date'].strftime("%b %d") for row in data]
        totals = [float(row['daily_total']) for row in data]

        fig = Figure(figsize=(5, 3), dpi=100)
        ax = fig.add_subplot(111)
        
        if dates:
            ax.plot(dates, totals, marker='o', color='#2980B9', linestyle='-', linewidth=2)
            ax.fill_between(dates, totals, color='#2980B9', alpha=0.1)
            ax.set_ylabel("Sales (₱)")
            ax.tick_params(axis='x', rotation=45, labelsize=8)
        else:
            ax.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center')
        
        fig.tight_layout()

        if self.trend_canvas:
            self.trend_canvas.get_tk_widget().destroy()
        
        self.trend_canvas = FigureCanvasTkAgg(fig, master=self.trend_frame)
        self.trend_canvas.draw()
        self.trend_canvas.get_tk_widget().pack(fill="both", expand=True)

    def draw_payment_pie(self, date_cond):
        query = f"""
            SELECT payment_status, SUM(total_amount) as sum_amount
            FROM Transactions 
            WHERE void_status = 'Active' AND {date_cond}
            GROUP BY payment_status
        """
        data = self.db.fetch_all(query)
        
        labels = []
        sizes = []
        colors = []
        
        for row in data:
            if row['sum_amount'] > 0:
                labels.append(row['payment_status'])
                sizes.append(float(row['sum_amount']))
                colors.append('#27AE60' if row['payment_status'] == 'Paid' else '#E74C3C')

        fig = Figure(figsize=(4, 3), dpi=100)
        ax = fig.add_subplot(111)

        if sizes:
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 9})
            ax.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.
        else:
            ax.text(0.5, 0.5, "No data available", horizontalalignment='center', verticalalignment='center')

        fig.tight_layout()

        if self.pie_canvas:
            self.pie_canvas.get_tk_widget().destroy()
            
        self.pie_canvas = FigureCanvasTkAgg(fig, master=self.pie_frame)
        self.pie_canvas.draw()
        self.pie_canvas.get_tk_widget().pack(fill="both", expand=True)

    def load_service_performance(self, date_cond):
        # For Services and Addons, we alias the date condition to match the joined tables
        # t.created_at is required because the date filter applies to the Transaction.
        date_cond_joined = date_cond.replace("created_at", "t.created_at")

        # 1. Services
        srv_query = f"""
            SELECT s.service_name, COUNT(b.batch_id) as usage_count, SUM(b.subtotal) as total_income
            FROM Services s
            JOIN Transaction_Batches b ON s.service_id = b.service_id
            JOIN Transactions t ON b.transaction_id = t.transaction_id
            WHERE t.void_status = 'Active' AND {date_cond_joined}
            GROUP BY s.service_id
            ORDER BY total_income DESC, usage_count DESC
        """
        for item in self.perf_srv_tree.get_children(): self.perf_srv_tree.delete(item)
        for rank, row in enumerate(self.db.fetch_all(srv_query), 1):
            self.perf_srv_tree.insert("", "end", values=(
                rank, row['service_name'], row['usage_count'], f"₱{row['total_income']:,.2f}"
            ))

        # 2. Add-ons
        add_query = f"""
            SELECT a.addon_name, COUNT(ba.batch_addon_id) as usage_count, SUM(ba.subtotal) as total_income
            FROM Addons a
            JOIN Batch_Addons ba ON a.addon_id = ba.addon_id
            JOIN Transaction_Batches b ON ba.batch_id = b.batch_id
            JOIN Transactions t ON b.transaction_id = t.transaction_id
            WHERE t.void_status = 'Active' AND {date_cond_joined}
            GROUP BY a.addon_id
            ORDER BY total_income DESC, usage_count DESC
        """
        for item in self.perf_add_tree.get_children(): self.perf_add_tree.delete(item)
        for rank, row in enumerate(self.db.fetch_all(add_query), 1):
            self.perf_add_tree.insert("", "end", values=(
                rank, row['addon_name'], row['usage_count'], f"₱{row['total_income']:,.2f}"
            ))