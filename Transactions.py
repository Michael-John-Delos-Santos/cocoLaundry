import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from dbManager import DatabaseManager
from datetime import datetime, timedelta

class Transactions(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        self.current_user = None
        
        self.configure(padx=20, pady=20)
        self.create_widgets()

    def set_user(self, user):
        self.current_user = user
        self.load_data()

    def create_widgets(self):
        # --- Header ---
        header_frame = tk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 10))
        tk.Label(header_frame, text="Transactions History", font=("Helvetica", 16, "bold"), fg="#2C3E50").pack(side="left")

        # --- Statistics Cards ---
        stats_frame = tk.Frame(self)
        stats_frame.pack(fill="x", pady=(0, 15))
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)

        self.trans_count_var = tk.StringVar(value="0")
        self.paid_var = tk.StringVar(value="₱0.00")
        self.unpaid_var = tk.StringVar(value="₱0.00")
        self.unclaimed_var = tk.StringVar(value="0")

        self.create_stat_card(stats_frame, "Total Transactions", self.trans_count_var, "#34495E", 0)
        self.create_stat_card(stats_frame, "Total Paid Amount", self.paid_var, "#27AE60", 1)
        self.create_stat_card(stats_frame, "Total Unpaid Balance", self.unpaid_var, "#E74C3C", 2)
        self.create_stat_card(stats_frame, "Unclaimed Orders", self.unclaimed_var, "#F39C12", 3)

        # --- Filters & Search ---
        filter_frame = tk.LabelFrame(self, text="Search & Filters", font=("Helvetica", 10, "bold"), padx=10, pady=10)
        filter_frame.pack(fill="x", pady=(0, 15))

        tk.Label(filter_frame, text="Search (Name/ID):").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        tk.Entry(filter_frame, textvariable=self.search_var, width=20).pack(side="left", padx=5)

        tk.Label(filter_frame, text="Time Filter:").pack(side="left", padx=(15, 5))
        self.time_var = tk.StringVar(value="All Time")
        time_cb = ttk.Combobox(filter_frame, textvariable=self.time_var, state="readonly", width=15)
        time_cb['values'] = ("All Time", "Today", "Last 7 Days", "This Month")
        time_cb.pack(side="left", padx=5)

        tk.Label(filter_frame, text="Item Filter:").pack(side="left", padx=(15, 5))
        self.item_var = tk.StringVar(value="All")
        item_cb = ttk.Combobox(filter_frame, textvariable=self.item_var, state="readonly", width=15)
        item_cb['values'] = ("All", "Services Only", "Add-ons Only")
        item_cb.pack(side="left", padx=5)

        tk.Button(filter_frame, text="Search & Apply", bg="#2980B9", fg="white", command=self.load_data).pack(side="left", padx=(20, 0))

        # --- Transaction List ---
        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True)

        scroll_y = tk.Scrollbar(table_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        columns = ("id", "display_id", "customer", "status", "payment", "amount", "date", "void")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tree.yview)

        self.tree.heading("id", text="ID")
        self.tree.heading("display_id", text="Order ID")
        self.tree.heading("customer", text="Customer Name")
        self.tree.heading("status", text="Order Status")
        self.tree.heading("payment", text="Payment")
        self.tree.heading("amount", text="Total Amount")
        self.tree.heading("date", text="Date Created")
        self.tree.heading("void", text="Void Status")

        self.tree.column("id", width=0, stretch=tk.NO)
        self.tree.column("display_id", width=100, anchor="center")
        self.tree.column("customer", width=180)
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("payment", width=100, anchor="center")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("date", width=150, anchor="center")
        self.tree.column("void", width=100, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

        # Bind double-click to view receipt
        self.tree.bind("<Double-1>", lambda event: self.view_receipt())

        # --- Actions ---
        actions_frame = tk.Frame(self)
        actions_frame.pack(fill="x", pady=(10, 0))

        tk.Button(actions_frame, text="View Receipt", bg="#16A085", fg="white", width=15, 
                  command=self.view_receipt).pack(side="left", padx=(0, 10))
        tk.Button(actions_frame, text="Void Transaction", bg="#C0392B", fg="white", width=15,
                  command=self.void_transaction).pack(side="left")

    def create_stat_card(self, parent, title, variable, color, col):
        card = tk.Frame(parent, bg=color, bd=0, padx=15, pady=15)
        card.grid(row=0, column=col, padx=5, sticky="nsew")
        tk.Label(card, text=title, font=("Helvetica", 10), bg=color, fg="white").pack(anchor="w")
        tk.Label(card, textvariable=variable, font=("Helvetica", 18, "bold"), bg=color, fg="white").pack(anchor="w", pady=(5, 0))

    def load_data(self):
        # 1. Build Query & Params
        search = self.search_var.get().strip()
        time_f = self.time_var.get()
        item_f = self.item_var.get()

        base_query = "SELECT * FROM Transactions WHERE 1=1"
        params = []

        if search:
            base_query += " AND (customer_name LIKE %s OR display_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        if time_f == "Today":
            base_query += " AND DATE(created_at) = CURDATE()"
        elif time_f == "Last 7 Days":
            base_query += " AND created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif time_f == "This Month":
            base_query += " AND MONTH(created_at) = MONTH(CURDATE()) AND YEAR(created_at) = YEAR(CURDATE())"

        # Item filter subqueries
        if item_f == "Services Only":
            base_query += " AND transaction_id IN (SELECT transaction_id FROM Transaction_Batches)"
            base_query += " AND transaction_id NOT IN (SELECT b.transaction_id FROM Batch_Addons ba JOIN Transaction_Batches b ON ba.batch_id = b.batch_id)"
        elif item_f == "Add-ons Only":
            base_query += " AND transaction_id IN (SELECT b.transaction_id FROM Batch_Addons ba JOIN Transaction_Batches b ON ba.batch_id = b.batch_id)"
            base_query += " AND transaction_id NOT IN (SELECT transaction_id FROM Transaction_Batches WHERE service_id IS NOT NULL)" # Simplified logic

        base_query += " ORDER BY created_at DESC"

        records = self.db.fetch_all(base_query, tuple(params))

        # 2. Update Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in records:
            amt = f"₱{row['total_amount']:,.2f}"
            dt = row['created_at'].strftime("%Y-%m-%d %H:%M")
            self.tree.insert("", "end", values=(
                row['transaction_id'], row['display_id'], row['customer_name'], 
                row['status'], row['payment_status'], amt, dt, row['void_status']
            ))

        # 3. Update Statistics (Based on current filtered set, excluding Voided for financials)
        total_trans = len(records)
        paid = sum(r['total_amount'] for r in records if r['payment_status'] == 'Paid' and r['void_status'] == 'Active')
        unpaid = sum(r['total_amount'] for r in records if r['payment_status'] == 'Unpaid' and r['void_status'] == 'Active')
        unclaimed = sum(1 for r in records if r['status'] != 'Claimed' and r['void_status'] == 'Active')

        self.trans_count_var.set(str(total_trans))
        self.paid_var.set(f"₱{paid:,.2f}")
        self.unpaid_var.set(f"₱{unpaid:,.2f}")
        self.unclaimed_var.set(str(unclaimed))

    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a transaction.", parent=self)
            return None
        return self.tree.item(selected[0])['values'][0]

    def void_transaction(self):
        trans_id = self.get_selected_id()
        if not trans_id: return

        # Check if already voided
        trans = self.db.fetch_one("SELECT void_status, display_id FROM Transactions WHERE transaction_id = %s", (trans_id,))
        if trans['void_status'] == 'Voided':
            messagebox.showinfo("Info", "This transaction is already voided.", parent=self)
            return

        reason = simpledialog.askstring("Void Transaction", f"Reason for voiding {trans['display_id']}:", parent=self)
        if reason: # If user didn't click Cancel and typed something
            try:
                query = """
                    UPDATE Transactions 
                    SET void_status = 'Voided', void_reason = %s, void_at = CURRENT_TIMESTAMP 
                    WHERE transaction_id = %s
                """
                self.db.execute_query(query, (reason, trans_id))
                
                user_id = self.current_user['user_id'] if self.current_user else None
                self.db.log_audit(user_id, 'VOID', 'Transaction', trans_id, f"Voided {trans['display_id']}. Reason: {reason}")
                
                messagebox.showinfo("Success", "Transaction successfully voided.", parent=self)
                self.load_data()
            except Exception as e:
                messagebox.showerror("Error", f"Could not void transaction:\n{e}", parent=self)
        elif reason == "":
            messagebox.showwarning("Required", "A reason is required to void a transaction.", parent=self)

    def view_receipt(self):
        trans_id = self.get_selected_id()
        if not trans_id: return

        trans = self.db.fetch_one("SELECT * FROM Transactions WHERE transaction_id = %s", (trans_id,))
        
        top = tk.Toplevel(self)
        top.title(f"Receipt - {trans['display_id']}")
        top.geometry("400x600")
        top.transient(self)
        top.grab_set()

        receipt_text = tk.Text(top, font=("Courier", 10), padx=20, pady=20)
        receipt_text.pack(fill="both", expand=True)

        # Build Receipt Content
        content =  "========================================\n"
        content += "           COCO BUBBLE WASH             \n"
        content += "========================================\n"
        content += f"Order ID: {trans['display_id']}\n"
        content += f"Date: {trans['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        content += f"Customer: {trans['customer_name']}\n"
        content += f"Status: {trans['status']} | {trans['payment_status']}\n"
        if trans['void_status'] == 'Voided':
            content += f"\n*** VOIDED ON {trans['void_at']} ***\nReason: {trans['void_reason']}\n"
        content += "----------------------------------------\n"

        batches = self.db.fetch_all("""
            SELECT b.batch_id, s.service_name, b.weight, b.subtotal 
            FROM Transaction_Batches b JOIN Services s ON b.service_id = s.service_id 
            WHERE b.transaction_id = %s
        """, (trans_id,))

        for b in batches:
            content += f"{b['service_name']} ({b['weight']}kg)\n"
            content += f"  Subtotal: ₱{b['subtotal']:,.2f}\n"
            
            addons = self.db.fetch_all("""
                SELECT a.addon_name, ba.subtotal FROM Batch_Addons ba 
                JOIN Addons a ON ba.addon_id = a.addon_id WHERE ba.batch_id = %s
            """, (b['batch_id'],))
            for a in addons:
                content += f"  + Add-on: {a['addon_name']} (₱{a['subtotal']:,.2f})\n"
            content += "\n"

        content += "----------------------------------------\n"
        content += f"TOTAL AMOUNT:          ₱{trans['total_amount']:,.2f}\n"
        content += "========================================\n"
        
        receipt_text.insert("1.0", content)
        receipt_text.config(state="disabled") # Make uneditable

# Testing Block
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test - Transactions")
    root.geometry("900x600")
    app = Transactions(parent=root)
    app.pack(expand=True, fill="both")
    app.set_user({'user_id': 1, 'full_name': 'Test Admin'})
    root.mainloop()