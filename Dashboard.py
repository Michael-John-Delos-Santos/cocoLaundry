import tkinter as tk
from tkinter import ttk, messagebox
from dbManager import DatabaseManager
from datetime import datetime

class Dashboard(tk.Frame):
    def __init__(self, parent, controller=None):
        """
        Initialize the Dashboard Frame.
        :param parent: The parent widget.
        :param controller: Reference to the main app to handle navigation.
        """
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        self.current_user = None
        
        self.configure(padx=20, pady=20)
        self.create_widgets()

    def set_user(self, user):
        """Sets the current user and refreshes the dashboard data."""
        self.current_user = user
        self.welcome_label.config(text=f"Welcome back, {user['full_name']}!")
        self.refresh_data()

    def create_widgets(self):
        # --- Header Section ---
        header_frame = tk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 20))
        
        self.welcome_label = tk.Label(header_frame, text="Welcome back!", font=("Helvetica", 18, "bold"), fg="#2C3E50")
        self.welcome_label.pack(side="left")
        
        refresh_btn = tk.Button(header_frame, text="Refresh Data", bg="#27AE60", fg="white", command=self.refresh_data)
        refresh_btn.pack(side="right")

        # --- Summary Cards Section ---
        cards_frame = tk.Frame(self)
        cards_frame.pack(fill="x", pady=(0, 20))
        
        # Configure grid for cards
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)

        # Pending Orders Card
        self.pending_var = tk.StringVar(value="0")
        self.create_card(cards_frame, "Pending Orders (In-queue)", self.pending_var, "#F39C12", 0)

        # Ready for Pickup Card
        self.ready_var = tk.StringVar(value="0")
        self.create_card(cards_frame, "Ready for Pickup", self.ready_var, "#3498DB", 1)

        # Total Sales Today Card
        self.sales_var = tk.StringVar(value="₱0.00")
        self.create_card(cards_frame, "Total Sales (Today)", self.sales_var, "#2ECC71", 2)

        # --- Quick Actions Section ---
        actions_frame = tk.LabelFrame(self, text="Quick Actions", font=("Helvetica", 12, "bold"), padx=10, pady=10)
        actions_frame.pack(fill="x", pady=(0, 20))

        tk.Button(actions_frame, text="Create Order", bg="#2980B9", fg="white", width=20, 
                  command=lambda: self.navigate("CreateOrder")).pack(side="left", padx=10)
        tk.Button(actions_frame, text="View Pending Orders", bg="#8E44AD", fg="white", width=20,
                  command=lambda: self.navigate("Orders")).pack(side="left", padx=10)
        tk.Button(actions_frame, text="Reports", bg="#16A085", fg="white", width=20,
                  command=lambda: self.navigate("Reports")).pack(side="left", padx=10)

        # --- Recent Activity Section ---
        activity_frame = tk.LabelFrame(self, text="Recent Activity (Last 5 Orders)", font=("Helvetica", 12, "bold"), padx=10, pady=10)
        activity_frame.pack(fill="both", expand=True)

        columns = ("display_id", "customer", "status", "payment", "amount", "date")
        self.tree = ttk.Treeview(activity_frame, columns=columns, show="headings", height=5)
        
        self.tree.heading("display_id", text="Order ID")
        self.tree.heading("customer", text="Customer Name")
        self.tree.heading("status", text="Order Status")
        self.tree.heading("payment", text="Payment")
        self.tree.heading("amount", text="Total Amount")
        self.tree.heading("date", text="Date Created")
        
        self.tree.column("display_id", width=100, anchor="center")
        self.tree.column("customer", width=200)
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("payment", width=100, anchor="center")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("date", width=150, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

    def create_card(self, parent, title, variable, color, col):
        """Helper to create summary statistic cards."""
        card = tk.Frame(parent, bg=color, bd=0, relief="flat", padx=15, pady=15)
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        
        tk.Label(card, text=title, font=("Helvetica", 10), bg=color, fg="white").pack(anchor="w")
        tk.Label(card, textvariable=variable, font=("Helvetica", 24, "bold"), bg=color, fg="white").pack(anchor="w", pady=(5, 0))

    def navigate(self, page_name):
        """Navigates to another module via the controller."""
        if self.controller and hasattr(self.controller, 'show_frame'):
            self.controller.show_frame(page_name)
        else:
            print(f"Navigation to {page_name} requested. (Controller not fully implemented)")

    def refresh_data(self):
        """Fetches the latest data from the database to update the dashboard."""
        try:
            # 1. Get Pending Orders Count
            pending_query = "SELECT COUNT(*) as count FROM Transactions WHERE status = 'In-queue' AND void_status = 'Active'"
            pending_res = self.db.fetch_one(pending_query)
            self.pending_var.set(str(pending_res['count']) if pending_res else "0")

            # 2. Get Ready for Pickup Count
            ready_query = "SELECT COUNT(*) as count FROM Transactions WHERE status = 'Ready to Claim' AND void_status = 'Active'"
            ready_res = self.db.fetch_one(ready_query)
            self.ready_var.set(str(ready_res['count']) if ready_res else "0")

            # 3. Get Total Sales Today (Only active, paid or unpaid doesn't matter for 'recorded sales', but we can adjust if you only want 'Paid')
            sales_query = """
                SELECT SUM(total_amount) as total 
                FROM Transactions 
                WHERE DATE(created_at) = CURDATE() AND void_status = 'Active'
            """
            sales_res = self.db.fetch_one(sales_query)
            total_sales = sales_res['total'] if sales_res and sales_res['total'] else 0.00
            self.sales_var.set(f"₱{total_sales:,.2f}")

            # 4. Get Recent Activity (Last 5 orders)
            activity_query = """
                SELECT display_id, customer_name, status, payment_status, total_amount, created_at 
                FROM Transactions 
                ORDER BY created_at DESC LIMIT 5
            """
            recent_orders = self.db.fetch_all(activity_query)
            
            # Clear existing treeview data
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Populate treeview
            for order in recent_orders:
                amount = f"₱{order['total_amount']:,.2f}"
                date_str = order['created_at'].strftime("%Y-%m-%d %H:%M") if order['created_at'] else "N/A"
                self.tree.insert("", "end", values=(
                    order['display_id'], 
                    order['customer_name'], 
                    order['status'], 
                    order['payment_status'], 
                    amount, 
                    date_str
                ))

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load dashboard data:\n{e}", parent=self)

# ==========================================
# Testing Block
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test - Dashboard Module")
    root.geometry("800x600")
    
    class MockController:
        def show_frame(self, page_name):
            print(f"Switching to {page_name}")
            
    app = Dashboard(parent=root, controller=MockController())
    app.pack(expand=True, fill="both")
    
    # Mock a user login
    mock_user = {'user_id': 1, 'username': 'admin', 'full_name': 'System Admin', 'role': 'Admin'}
    app.set_user(mock_user)
    
    root.mainloop()