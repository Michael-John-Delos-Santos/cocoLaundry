import tkinter as tk
from tkinter import ttk, messagebox
from dbManager import DatabaseManager
from datetime import datetime
from EmailHelper import EmailHelper
import threading
import math

class Orders(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        self.current_user = None

        # Column sort state: tracks current sort column and direction per column
        self.sort_col = "date"
        self.sort_directions = {
            "id": "DESC", "display_id": "DESC", "customer": "ASC",
            "status": "ASC", "payment": "ASC", "amount": "DESC", "date": "DESC"
        }
        # Map treeview column names to SQL column names
        self.col_to_sql = {
            "id": "transaction_id",
            "display_id": "display_id",
            "customer": "customer_name",
            "status": "status",
            "payment": "payment_status",
            "amount": "total_amount",
            "date": "created_at"
        }

        self.services_data = {}; self.addons_data = {}
        self.configure(padx=20, pady=20); self.create_widgets()

    def set_user(self, user):
        self.current_user = user
        self.load_orders(); self.load_reference_data()

    def load_reference_data(self):
        services = self.db.fetch_all("SELECT * FROM Services WHERE status='Active'")
        self.services_data = {s['service_name']: s for s in services}
        addons = self.db.fetch_all("SELECT * FROM Addons WHERE status='Active'")
        self.addons_data = {a['addon_name']: a for a in addons}

    def create_widgets(self):
        header_frame = tk.Frame(self); header_frame.pack(fill="x", pady=(0, 10))
        tk.Label(header_frame, text="Active Orders Management", font=("Helvetica", 16, "bold"), fg="#2C3E50").pack(side="left")

        filter_frame = tk.LabelFrame(self, text="Search", padx=10, pady=10)
        filter_frame.pack(fill="x", pady=(0, 15))

        self.search_ent = tk.Entry(filter_frame, width=40); self.search_ent.pack(side="left", padx=5)
        tk.Button(filter_frame, text="Search/Refresh", command=self.load_orders).pack(side="left")

        columns = ("id", "display_id", "customer", "status", "payment", "amount", "date")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)

        col_labels = {
            "id": "ID", "display_id": "Order ID", "customer": "Customer",
            "status": "Status", "payment": "Payment", "amount": "Amount", "date": "Date"
        }
        for col in columns:
            self.tree.heading(
                col,
                text=col_labels[col],
                command=lambda c=col: self.sort_by_column(c)
            )

        self.tree.column("id", width=0, stretch=tk.NO)
        self.tree.column("display_id", width=100, anchor="center")
        self.tree.column("customer", width=180)
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("payment", width=100, anchor="center")
        self.tree.column("amount", width=110, anchor="e")
        self.tree.column("date", width=150, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.update_button_states())

        # Update heading arrows for default sort column
        self._update_heading_arrows()

        # ACTIONS BAR
        actions_frame = tk.Frame(self); actions_frame.pack(fill="x", pady=(10, 0))
        self.btn_edit = tk.Button(actions_frame, text="View/Edit Details", bg="#3498DB", fg="white", width=15, command=self.view_details)
        self.btn_edit.pack(side="left", padx=(0, 10))
        self.btn_pay = tk.Button(actions_frame, text="Mark as Paid", bg="#27AE60", fg="white", width=15, command=self.mark_as_paid)
        self.btn_pay.pack(side="left", padx=10)
        self.btn_ready = tk.Button(actions_frame, text="Move to Ready", bg="#F39C12", fg="white", width=15, command=lambda: self.update_status("Ready to Claim"))
        self.btn_ready.pack(side="left", padx=10)
        self.btn_claim = tk.Button(actions_frame, text="Mark Claimed", bg="#8E44AD", fg="white", width=15, command=lambda: self.update_status("Claimed"))
        self.btn_claim.pack(side="left", padx=10)

    def sort_by_column(self, col):
        """Toggle sort direction for the clicked column, then reload."""
        if self.sort_col == col:
            # Same column — flip direction
            self.sort_directions[col] = "ASC" if self.sort_directions[col] == "DESC" else "DESC"
        else:
            # New column — keep that column's last direction (default is set in __init__)
            self.sort_col = col
        self._update_heading_arrows()
        self.load_orders()

    def _update_heading_arrows(self):
        """Refresh all column heading labels to show sort arrow on active column."""
        col_labels = {
            "id": "ID", "display_id": "Order ID", "customer": "Customer",
            "status": "Status", "payment": "Payment", "amount": "Amount", "date": "Date"
        }
        for col, label in col_labels.items():
            if col == self.sort_col:
                arrow = " ▲" if self.sort_directions[col] == "ASC" else " ▼"
                self.tree.heading(col, text=label + arrow)
            else:
                self.tree.heading(col, text=label)

    def update_button_states(self):
        sel = self.tree.selection()
        if not sel or not self.current_user: return
        item = self.tree.item(sel[0])['values']
        status, payment = item[3], item[4]; is_admin = self.current_user['role'] == 'Admin'

        self.btn_pay.config(state="normal" if is_admin or payment == "Unpaid" else "disabled")
        self.btn_ready.config(state="normal" if payment == "Paid" else "disabled")
        self.btn_claim.config(state="normal" if payment == "Paid" else "disabled")
        self.btn_edit.config(state="normal" if is_admin or payment == "Unpaid" else "disabled")

    def load_orders(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        search = f"%{self.search_ent.get()}%"
        sql_col = self.col_to_sql[self.sort_col]
        direction = self.sort_directions[self.sort_col]
        query = (
            f"SELECT * FROM Transactions "
            f"WHERE void_status='Active' AND status != 'Claimed' AND customer_name LIKE %s "
            f"ORDER BY {sql_col} {direction}"
        )
        records = self.db.fetch_all(query, (search,))
        for r in records:
            self.tree.insert("", "end", values=(
                r['transaction_id'], r['display_id'], r['customer_name'],
                r['status'], r['payment_status'],
                f"₱{r['total_amount']:,.2f}", r['created_at']
            ))

    def get_selected_order_id(self):
        sel = self.tree.selection()
        return self.tree.item(sel[0])['values'][0] if sel else None

    def mark_as_paid(self):
        trans_id = self.get_selected_order_id()
        if not trans_id or not messagebox.askyesno("Confirm", "Are you sure you want to update payment status?"): return
        new_status = "Paid" if self.tree.item(self.tree.selection()[0])['values'][4] == "Unpaid" else "Unpaid"
        self.db.execute_query("UPDATE Transactions SET payment_status = %s WHERE transaction_id = %s", (new_status, trans_id))
        self.db.log_audit(self.current_user['user_id'], 'UPDATE', 'Transaction', trans_id, f"Payment: {new_status}")
        self.load_orders()

    def update_status(self, new_status):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])['values']
        trans_id, current_status = item[0], item[3]

        if current_status == new_status: return messagebox.showinfo("No Change", "Order is already in this status.")
        if not messagebox.askyesno("Confirm", f"Move status to {new_status}?"): return

        self.db.execute_query("UPDATE Transactions SET status = %s WHERE transaction_id = %s", (new_status, trans_id))
        self.db.log_audit(self.current_user['user_id'], 'UPDATE', 'Transaction', trans_id, f"Status: {new_status}")

        if new_status == "Ready to Claim":
            order = self.db.fetch_one("SELECT * FROM Transactions WHERE transaction_id = %s", (trans_id,))
            if order and order.get('customer_email'):
                threading.Thread(target=self.run_email_thread, args=(order,), daemon=True).start()
        self.load_orders()

    def run_email_thread(self, order):
        EmailHelper.send_email(
            db=self.db, receiver=order['customer_email'],
            subject_key='pickup_ready_subject', body_key='pickup_ready_body',
            placeholders={'{customer}': order['customer_name'], '{order_id}': order['display_id']}
        )

    # ================= DETAIL & EDIT WINDOW =================
    def view_details(self):
        trans_id = self.get_selected_order_id()
        if not trans_id: return
        trans = self.db.fetch_one("SELECT * FROM Transactions WHERE transaction_id = %s", (trans_id,))

        self.detail_win = tk.Toplevel(self)
        self.detail_win.title(f"Order - {trans['display_id']}")
        self.detail_win.geometry("950x750")
        self.detail_win.grab_set()
        tabs = ttk.Notebook(self.detail_win); tabs.pack(fill="both", expand=True, padx=10, pady=10)

        # TAB 1: RECEIPT
        view_tab = ttk.Frame(tabs); tabs.add(view_tab, text=" Receipt ")
        self.receipt_text = tk.Text(view_tab, font=("Courier", 10), padx=20, pady=20)
        self.receipt_text.pack(fill="both", expand=True)
        self.refresh_receipt(trans_id)

        # TAB 2: EDIT
        edit_tab = ttk.Frame(tabs); tabs.add(edit_tab, text=" Edit Order ")
        paned = tk.PanedWindow(edit_tab, orient="horizontal", sashwidth=4); paned.pack(fill="both", expand=True)
        left_form = tk.Frame(paned, padx=10, pady=10); paned.add(left_form, width=400)

        tk.Label(left_form, text="Batch Editor", font=("bold")).pack(anchor="w")
        tk.Label(left_form, text="Service").pack(anchor="w", pady=(10, 0))
        self.edit_srv_cb = ttk.Combobox(left_form, state="readonly", values=list(self.services_data.keys()))
        self.edit_srv_cb.pack(fill="x")
        tk.Label(left_form, text="Weight (kg)").pack(anchor="w", pady=(10, 0))
        self.edit_w_ent = tk.Entry(left_form); self.edit_w_ent.pack(fill="x")

        addon_frame = tk.LabelFrame(left_form, text="Add-on", padx=10, pady=10); addon_frame.pack(fill="x", pady=15)
        self.edit_add_cb = ttk.Combobox(addon_frame, state="readonly", values=["None"] + list(self.addons_data.keys()))
        self.edit_add_cb.set("None"); self.edit_add_cb.pack(fill="x")
        self.edit_qty_var = tk.IntVar(value=1)
        tk.Label(addon_frame, text="Qty:").pack(side="left")
        tk.Entry(addon_frame, textvariable=self.edit_qty_var, width=5).pack(side="left", padx=5)

        self.batch_btn = tk.Button(left_form, text="Add/Update Batch", bg="#3498DB", fg="white",
                                   command=lambda: self.save_batch_action(trans_id))
        self.batch_btn.pack(fill="x", pady=10)

        right_list = tk.Frame(paned, padx=10, pady=10); paned.add(right_list, width=450)
        self.edit_tree = ttk.Treeview(right_list, columns=("id", "srv", "w", "sub"), show="headings", height=12)
        self.edit_tree.heading("id", text="ID"); self.edit_tree.heading("srv", text="Service")
        self.edit_tree.heading("w", text="Kg"); self.edit_tree.heading("sub", text="Subtotal")
        self.edit_tree.column("id", width=40); self.edit_tree.pack(fill="both", expand=True)
        self.edit_tree.bind("<<TreeviewSelect>>", self.load_batch_to_form)
        self.refresh_edit_list(trans_id)

    def refresh_receipt(self, trans_id):
        trans = self.db.fetch_one("SELECT * FROM Transactions WHERE transaction_id = %s", (trans_id,))
        batches = self.db.fetch_all(
            "SELECT b.*, s.service_name, c.name as cat_name FROM Transaction_Batches b "
            "JOIN Services s ON b.service_id = s.service_id "
            "JOIN Category c ON b.category_id = c.category_id "
            "WHERE transaction_id = %s", (trans_id,)
        )
        self.receipt_text.config(state="normal"); self.receipt_text.delete("1.0", tk.END)
        res = (f"COCO BUBBLE WASH\nID: {trans['display_id']}\nCUSTOMER: {trans['customer_name']}\n"
               f"TYPE: {batches[0]['cat_name'] if batches else 'N/A'}\n" + "-" * 40 + "\n")
        for b in batches:
            res += f"{b['service_name']} ({b['weight']}kg - {b['load_count']} Load/s) : ₱{b['subtotal']:,.2f}\n"
            addons = self.db.fetch_all(
                "SELECT a.addon_name, ba.quantity FROM Batch_Addons ba "
                "JOIN Addons a ON ba.addon_id = a.addon_id WHERE ba.batch_id = %s", (b['batch_id'],)
            )
            for a in addons: res += f"  + {a['addon_name']} x{a['quantity']}\n"
        res += "-" * 40 + f"\nTOTAL: ₱{trans['total_amount']:,.2f}\nSTATUS: {trans['status']} | {trans['payment_status']}"
        self.receipt_text.insert("1.0", res); self.receipt_text.config(state="disabled")

    def refresh_edit_list(self, trans_id):
        for i in self.edit_tree.get_children(): self.edit_tree.delete(i)
        batches = self.db.fetch_all(
            "SELECT b.*, s.service_name FROM Transaction_Batches b "
            "JOIN Services s ON b.service_id = s.service_id WHERE transaction_id = %s", (trans_id,)
        )
        for b in batches:
            self.edit_tree.insert("", "end", values=(b['batch_id'], b['service_name'], b['weight'], f"₱{b['subtotal']:.2f}"))

    def load_batch_to_form(self, event):
        sel = self.edit_tree.selection()
        if not sel: return
        b_id = self.edit_tree.item(sel[0])['values'][0]
        self.editing_id = b_id
        batch = self.db.fetch_one(
            "SELECT b.*, s.service_name FROM Transaction_Batches b "
            "JOIN Services s ON b.service_id = s.service_id WHERE b.batch_id = %s", (b_id,)
        )
        self.edit_srv_cb.set(batch['service_name'])
        self.edit_w_ent.delete(0, tk.END); self.edit_w_ent.insert(0, batch['weight'])
        self.batch_btn.config(text="Update Batch", bg="#F39C12")

    def save_batch_action(self, trans_id):
        srv_name, w_str = self.edit_srv_cb.get(), self.edit_w_ent.get()
        if not srv_name or not w_str or not messagebox.askyesno("Confirm", "Update this order details?"): return

        try:
            w = float(w_str)
            limit = float(self.db.fetch_one(
                "SELECT config_value FROM system_config WHERE config_key = 'kg_per_load'"
            )['config_value'])
            loads = math.ceil(w / limit)

            existing = self.db.fetch_all(
                "SELECT weight FROM Transaction_Batches WHERE transaction_id = %s", (trans_id,)
            )
            if existing and w != existing[0]['weight']:
                return messagebox.showerror("Weight Error", f"Weight must match other items: {existing[0]['weight']}kg")

            srv = self.services_data[srv_name]; sub = loads * float(srv['price_per_load'])
            if hasattr(self, 'editing_id') and self.editing_id:
                self.db.execute_query(
                    "UPDATE Transaction_Batches SET service_id=%s, weight=%s, load_count=%s, subtotal=%s WHERE batch_id=%s",
                    (srv['service_id'], w, loads, sub, self.editing_id)
                )
            else:
                self.db.execute_query(
                    "INSERT INTO Transaction_Batches (transaction_id, service_id, category_id, weight, load_count, price_per_unit, subtotal) VALUES (%s,%s,1,%s,%s,%s,%s)",
                    (trans_id, srv['service_id'], w, loads, srv['price_per_load'], sub)
                )

            self.update_trans_total(trans_id)
            self.refresh_edit_list(trans_id)
            self.refresh_receipt(trans_id)
            self.load_orders()
            messagebox.showinfo("Success", "Record updated.")
            self.editing_id = None
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_trans_total(self, trans_id):
        res = self.db.fetch_one(
            "SELECT SUM(subtotal) as total FROM Transaction_Batches WHERE transaction_id=%s", (trans_id,)
        )
        self.db.execute_query(
            "UPDATE Transactions SET total_amount=%s WHERE transaction_id=%s", (res['total'] or 0, trans_id)
        )