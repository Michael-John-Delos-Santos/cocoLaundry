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
        self._update_action_buttons()
        self.load_data()

    def _is_admin(self):
        if not self.current_user:
            return False
        role = self.current_user.get('role', '').strip().lower()
        return role == 'admin'

    def _update_action_buttons(self):
        """Show or hide admin-only buttons based on the current user's role."""
        if self._is_admin():
            self.void_btn.pack(side="left", padx=(0, 10))
            self.revert_btn.pack(side="left")
        else:
            self.void_btn.pack_forget()
            self.revert_btn.pack_forget()

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

        row1 = tk.Frame(filter_frame)
        row1.pack(fill="x", pady=2)

        tk.Label(row1, text="Search (Name/ID):").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.search_var, width=30).pack(side="left", padx=5)

        tk.Label(row1, text="Time Filter:").pack(side="left", padx=(15, 5))
        self.time_var = tk.StringVar(value="All Time")
        time_cb = ttk.Combobox(row1, textvariable=self.time_var, state="readonly", width=15)
        time_cb['values'] = ("All Time", "Today", "Last 7 Days", "This Month")
        time_cb.pack(side="left", padx=5)

        row2 = tk.Frame(filter_frame)
        row2.pack(fill="x", pady=5)

        tk.Label(row2, text="Order Status:").pack(side="left", padx=(0, 5))
        self.status_var = tk.StringVar(value="All")
        status_cb = ttk.Combobox(row2, textvariable=self.status_var, state="readonly", width=15)
        status_cb['values'] = ("All", "In-queue", "Ready to Claim", "Claimed")
        status_cb.pack(side="left", padx=5)

        tk.Label(row2, text="Payment:").pack(side="left", padx=(15, 5))
        self.pay_filter_var = tk.StringVar(value="All")
        pay_cb = ttk.Combobox(row2, textvariable=self.pay_filter_var, state="readonly", width=12)
        pay_cb['values'] = ("All", "Paid", "Unpaid")
        pay_cb.pack(side="left", padx=5)

        tk.Label(row2, text="Void Status:").pack(side="left", padx=(15, 5))
        self.void_filter_var = tk.StringVar(value="Active Only")
        void_cb = ttk.Combobox(row2, textvariable=self.void_filter_var, state="readonly", width=12)
        void_cb['values'] = ("All", "Active Only", "Voided Only")
        void_cb.pack(side="left", padx=5)

        tk.Button(row2, text="Apply Filters", bg="#2980B9", fg="white", font=("bold"), command=self.load_data).pack(side="left", padx=(10, 5))

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
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("payment", width=100, anchor="center")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("date", width=150, anchor="center")
        self.tree.column("void", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda event: self.view_receipt())

        # --- Actions ---
        actions_frame = tk.Frame(self)
        actions_frame.pack(fill="x", pady=(10, 0))

        tk.Button(
            actions_frame, text="View Receipt", bg="#16A085", fg="white", width=15,
            command=self.view_receipt
        ).pack(side="left", padx=(0, 10))

        # Admin-only buttons (hidden until set_user is called)
        self.void_btn = tk.Button(
            actions_frame, text="Void Transaction", bg="#C0392B", fg="white", width=15,
            command=self.void_transaction
        )
        self.revert_btn = tk.Button(
            actions_frame, text="Revert Void", bg="#8E44AD", fg="white", width=15,
            command=self.revert_void
        )
        # Buttons are packed in _update_action_buttons() after role is known

    def create_stat_card(self, parent, title, variable, color, col):
        card = tk.Frame(parent, bg=color, bd=0, padx=15, pady=15)
        card.grid(row=0, column=col, padx=5, sticky="nsew")
        tk.Label(card, text=title, font=("Helvetica", 10), bg=color, fg="white").pack(anchor="w")
        tk.Label(card, textvariable=variable, font=("Helvetica", 18, "bold"), bg=color, fg="white").pack(anchor="w", pady=(5, 0))

    def load_data(self):
        search = self.search_var.get().strip()
        time_f = self.time_var.get()
        status_f = self.status_var.get()
        pay_f = self.pay_filter_var.get()
        void_f = self.void_filter_var.get()

        query = "SELECT * FROM Transactions WHERE 1=1"
        params = []

        if search:
            query += " AND (customer_name LIKE %s OR display_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        if time_f == "Today":
            query += " AND DATE(created_at) = CURDATE()"
        elif time_f == "Last 7 Days":
            query += " AND created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif time_f == "This Month":
            query += " AND MONTH(created_at) = MONTH(CURDATE()) AND YEAR(created_at) = YEAR(CURDATE())"

        if status_f != "All":
            query += " AND status = %s"
            params.append(status_f)

        if pay_f != "All":
            query += " AND payment_status = %s"
            params.append(pay_f)

        if void_f == "Active Only":
            query += " AND void_status = 'Active'"
        elif void_f == "Voided Only":
            query += " AND void_status = 'Voided'"

        query += " ORDER BY created_at DESC"
        records = self.db.fetch_all(query, tuple(params))

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in records:
            amt = f"₱{row['total_amount']:,.2f}"
            dt = row['created_at'].strftime("%Y-%m-%d %H:%M")
            self.tree.insert("", "end", values=(
                row['transaction_id'], row['display_id'], row['customer_name'],
                row['status'], row['payment_status'], amt, dt, row['void_status']
            ))

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

    # ------------------------------------------------------------------
    # Void Transaction
    # ------------------------------------------------------------------
    def void_transaction(self):
        if not self._is_admin():
            messagebox.showerror("Access Denied", "Only admins can void transactions.", parent=self)
            return

        trans_id = self.get_selected_id()
        if not trans_id:
            return

        trans = self.db.fetch_one(
            "SELECT void_status, display_id FROM Transactions WHERE transaction_id = %s",
            (trans_id,)
        )

        if trans['void_status'] == 'Voided':
            messagebox.showinfo("Already Voided", f"Order {trans['display_id']} is already voided.\nUse 'Revert Void' to undo.", parent=self)
            return

        # Step 1 — Require a reason (loop until one is provided or user cancels)
        reason = None
        while not reason:
            reason = simpledialog.askstring(
                "Void Reason Required",
                f"Enter the reason for voiding order {trans['display_id']}:\n(Cannot be left blank)",
                parent=self
            )
            if reason is None:
                # User pressed Cancel — abort entirely
                return
            reason = reason.strip()
            if not reason:
                messagebox.showwarning(
                    "Reason Required",
                    "A reason is required to void a transaction. Please enter a reason.",
                    parent=self
                )

        # Step 2 — Final confirmation
        confirmed = messagebox.askyesno(
            "Confirm Void",
            f"Are you sure you want to void order {trans['display_id']}?\n\nReason: {reason}\n\nThis action will be logged.",
            parent=self
        )
        if not confirmed:
            return

        try:
            self.db.execute_query(
                "UPDATE Transactions SET void_status = 'Voided', void_reason = %s, void_at = CURRENT_TIMESTAMP WHERE transaction_id = %s",
                (reason, trans_id)
            )
            user_id = self.current_user['user_id'] if self.current_user else None
            self.db.log_audit(user_id, 'VOID', 'Transaction', trans_id, f"Voided {trans['display_id']}. Reason: {reason}")
            messagebox.showinfo("Success", f"Order {trans['display_id']} has been voided.", parent=self)
            self.load_data()
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self)

    # ------------------------------------------------------------------
    # Revert Void (admin only)
    # ------------------------------------------------------------------
    def revert_void(self):
        if not self._is_admin():
            messagebox.showerror("Access Denied", "Only admins can revert voided transactions.", parent=self)
            return

        trans_id = self.get_selected_id()
        if not trans_id:
            return

        trans = self.db.fetch_one(
            "SELECT void_status, display_id FROM Transactions WHERE transaction_id = %s",
            (trans_id,)
        )

        if trans['void_status'] != 'Voided':
            messagebox.showinfo("Not Voided", f"Order {trans['display_id']} is not voided.", parent=self)
            return

        confirmed = messagebox.askyesno(
            "Confirm Revert",
            f"Are you sure you want to revert the void on order {trans['display_id']}?\n\nThis will restore it to Active status.",
            parent=self
        )
        if not confirmed:
            return

        try:
            self.db.execute_query(
                "UPDATE Transactions SET void_status = 'Active', void_reason = NULL, void_at = NULL WHERE transaction_id = %s",
                (trans_id,)
            )
            user_id = self.current_user['user_id'] if self.current_user else None
            self.db.log_audit(user_id, 'REVERT_VOID', 'Transaction', trans_id, f"Reverted void on {trans['display_id']}.")
            messagebox.showinfo("Success", f"Order {trans['display_id']} has been restored to Active.", parent=self)
            self.load_data()
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self)

    # ------------------------------------------------------------------
    # View Receipt
    # ------------------------------------------------------------------
    def view_receipt(self):
        trans_id = self.get_selected_id()
        if not trans_id:
            return

        trans = self.db.fetch_one("SELECT * FROM Transactions WHERE transaction_id = %s", (trans_id,))
        top = tk.Toplevel(self)
        top.title(f"Receipt - {trans['display_id']}")
        top.geometry("400x600")

        receipt_text = tk.Text(top, font=("Courier", 10), padx=20, pady=20)
        receipt_text.pack(fill="both", expand=True)

        content  = "========================================\n"
        content += "           COCO BUBBLE WASH             \n"
        content += "========================================\n"
        content += f"Order ID: {trans['display_id']}\n"
        content += f"Date: {trans['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        content += f"Customer: {trans['customer_name']}\n"
        content += f"Status: {trans['status']} | {trans['payment_status']}\n"
        if trans['void_status'] == 'Voided':
            content += f"\n*** VOIDED ON {trans['void_at']} ***\nReason: {trans['void_reason']}\n"
        content += "----------------------------------------\n"

        batches = self.db.fetch_all(
            "SELECT b.*, s.service_name FROM Transaction_Batches b "
            "JOIN Services s ON b.service_id = s.service_id WHERE b.transaction_id = %s",
            (trans_id,)
        )
        for b in batches:
            content += f"{b['service_name']} ({b['weight']}kg)\n"
            content += f"  Subtotal: ₱{b['subtotal']:,.2f}\n"
            addons = self.db.fetch_all(
                "SELECT a.addon_name, ba.subtotal FROM Batch_Addons ba "
                "JOIN Addons a ON ba.addon_id = a.addon_id WHERE ba.batch_id = %s",
                (b['batch_id'],)
            )
            for a in addons:
                content += f"  + Add-on: {a['addon_name']} (₱{a['subtotal']:,.2f})\n"
            content += "\n"

        content += "----------------------------------------\n"
        content += f"TOTAL AMOUNT:          ₱{trans['total_amount']:,.2f}\n"
        content += "========================================\n"

        receipt_text.insert("1.0", content)
        receipt_text.config(state="disabled")