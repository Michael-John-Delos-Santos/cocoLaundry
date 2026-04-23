import tkinter as tk
from tkinter import ttk, messagebox
from dbManager import DatabaseManager
from datetime import datetime
from EmailHelper import EmailHelper
import threading
import time

class Orders(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        self.current_user = None
        
        self.services_data = {}
        self.addons_data = {}
        
        self.configure(padx=20, pady=20)
        self.create_widgets()

    def set_user(self, user):
        self.current_user = user
        self.load_orders()
        self.load_reference_data()

    def load_reference_data(self):
        services = self.db.fetch_all("SELECT * FROM Services WHERE status='Active'")
        self.services_data = {s['service_name']: s for s in services}
        addons = self.db.fetch_all("SELECT * FROM Addons WHERE status='Active'")
        self.addons_data = {a['addon_name']: a for a in addons}

    def create_widgets(self):
        header_frame = tk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 10))
        tk.Label(header_frame, text="Active Orders Management", font=("Helvetica", 16, "bold"), fg="#2C3E50").pack(side="left")

        filter_frame = tk.LabelFrame(self, text="Search Orders", padx=10, pady=10)
        filter_frame.pack(fill="x", pady=(0, 15))
        self.search_ent = tk.Entry(filter_frame, width=40)
        self.search_ent.pack(side="left", padx=5)
        tk.Button(filter_frame, text="Search/Refresh", command=self.load_orders).pack(side="left")

        columns = ("id", "display_id", "customer", "status", "payment", "amount", "date")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
        
        self.tree.column("id", width=0, stretch=tk.NO)
        self.tree.pack(fill="both", expand=True)

        actions_frame = tk.Frame(self)
        actions_frame.pack(fill="x", pady=(10, 0))

        tk.Button(actions_frame, text="View Details", bg="#3498DB", fg="white", width=15, command=self.view_details).pack(side="left", padx=(0, 10))
        tk.Button(actions_frame, text="Mark as Paid", bg="#27AE60", fg="white", width=15, command=self.mark_as_paid).pack(side="left", padx=10)
        tk.Button(actions_frame, text="Move to Ready", bg="#F39C12", fg="white", width=15, command=lambda: self.update_status("Ready to Claim")).pack(side="left", padx=10)
        tk.Button(actions_frame, text="Mark Claimed", bg="#8E44AD", fg="white", width=15, command=lambda: self.update_status("Claimed")).pack(side="left", padx=10)

    def load_orders(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        search_term = f"%{self.search_ent.get()}%"
        query = "SELECT * FROM Transactions WHERE void_status='Active' AND status != 'Claimed' AND customer_name LIKE %s ORDER BY created_at DESC"
        records = self.db.fetch_all(query, (search_term,))
        for row in records:
            self.tree.insert("", "end", values=(row['transaction_id'], row['display_id'], row['customer_name'], row['status'], row['payment_status'], f"₱{row['total_amount']:,.2f}", row['created_at']))

    def get_selected_order_id(self):
        sel = self.tree.selection()
        return self.tree.item(sel[0])['values'][0] if sel else None

    def mark_as_paid(self):
        trans_id = self.get_selected_order_id()
        if trans_id and messagebox.askyesno("Confirm", "Mark as Paid?"):
            self.db.execute_query("UPDATE Transactions SET payment_status = 'Paid' WHERE transaction_id = %s", (trans_id,))
            self.db.log_audit(self.current_user['user_id'], 'UPDATE', 'Transaction', trans_id, "Marked as Paid")
            self.load_orders()

    def update_status(self, new_status):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection", "Please select an order from the list.")
            return

        # 2. Extract current values (ID is index 0, Status is index 3)
        item_values = self.tree.item(sel[0])['values']
        trans_id = item_values[0]
        current_status = item_values[3]

        # 3. Validation: Prevent updating if the status is already the same
        if current_status == new_status:
            messagebox.showinfo("No Change", f"This order is already marked as '{new_status}'.")
            return

        # 4. Proceed with confirmation and update if it's a new status
        if messagebox.askyesno("Confirm", f"Change status from '{current_status}' to '{new_status}'?"):
            try:
                # Update the database
                self.db.execute_query("UPDATE Transactions SET status = %s WHERE transaction_id = %s", (new_status, trans_id))
                self.db.log_audit(self.current_user['user_id'], 'UPDATE', 'Transaction', trans_id, f"Status: {new_status}")
                
                # Use threading for background email sending for specific status
                if new_status == "Ready to Claim":
                    order = self.db.fetch_one("SELECT * FROM Transactions WHERE transaction_id = %s", (trans_id,))
                    if order and order.get('customer_email'):
                        threading.Thread(target=self.run_email_thread, args=(order,), daemon=True).start()
                
                # Refresh the list to reflect changes
                self.load_orders()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update status: {e}")

    def run_email_thread(self, order):
        success, error = EmailHelper.send_email(
            db=self.db,
            receiver=order['customer_email'],
            subject_key='pickup_ready_subject',
            body_key='pickup_ready_body',
            placeholders={'{customer}': order['customer_name'], '{order_id}': order['display_id']}
        )
        if not success:
            self.after(0, lambda: messagebox.showwarning("Email Warning", f"Order updated, but email failed: {error}"))

    def view_details(self):
        trans_id = self.get_selected_order_id()
        if not trans_id: return
        trans = self.db.fetch_one("SELECT * FROM Transactions WHERE transaction_id = %s", (trans_id,))
        
        self.detail_win = tk.Toplevel(self)
        self.detail_win.title(f"Order Manager - {trans['display_id']}")
        self.detail_win.geometry("950x750")
        self.detail_win.grab_set()

        tabs = ttk.Notebook(self.detail_win)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)

        # TAB 1: RECEIPT
        view_tab = ttk.Frame(tabs)
        tabs.add(view_tab, text=" View Receipt ")
        self.receipt_text = tk.Text(view_tab, font=("Courier", 10), padx=20, pady=20)
        self.receipt_text.pack(fill="both", expand=True)
        self.refresh_receipt(trans_id)

        # TAB 2: EDIT
        edit_tab = ttk.Frame(tabs)
        tabs.add(edit_tab, text=" Edit Order Details ")
        paned = tk.PanedWindow(edit_tab, orient="horizontal", sashwidth=4)
        paned.pack(fill="both", expand=True)

        left_form = tk.Frame(paned, padx=10, pady=10)
        paned.add(left_form, width=400)

        tk.Label(left_form, text="Batch Editor", font=("bold")).pack(anchor="w")
        tk.Label(left_form, text="Service").pack(anchor="w", pady=(10,0))
        self.edit_srv_cb = ttk.Combobox(left_form, state="readonly", values=list(self.services_data.keys()))
        self.edit_srv_cb.pack(fill="x")

        tk.Label(left_form, text="Weight (kg)").pack(anchor="w", pady=(10,0))
        self.edit_w_ent = tk.Entry(left_form)
        self.edit_w_ent.pack(fill="x")

        addon_frame = tk.LabelFrame(left_form, text="Add-on", padx=10, pady=10)
        addon_frame.pack(fill="x", pady=15)
        self.edit_add_cb = ttk.Combobox(addon_frame, state="readonly", values=["None"] + list(self.addons_data.keys()))
        self.edit_add_cb.set("None")
        self.edit_add_cb.pack(fill="x")

        qty_ctrl = tk.Frame(addon_frame)
        qty_ctrl.pack(pady=5)
        self.edit_qty_var = tk.IntVar(value=1)
        tk.Button(qty_ctrl, text="-", width=3, command=lambda: self.edit_qty_var.set(max(1, self.edit_qty_var.get()-1))).pack(side="left")
        tk.Label(qty_ctrl, textvariable=self.edit_qty_var, width=5, font=("bold")).pack(side="left", padx=10)
        tk.Button(qty_ctrl, text="+", width=3, command=lambda: self.edit_qty_var.set(self.edit_qty_var.get()+1)).pack(side="left")

        self.batch_btn = tk.Button(left_form, text="Add/Update Batch", bg="#3498DB", fg="white", command=lambda: self.save_batch_action(trans_id))
        self.batch_btn.pack(fill="x", pady=10)
        tk.Button(left_form, text="Reset Form", command=self.reset_editor).pack(fill="x")

        right_list = tk.Frame(paned, padx=10, pady=10)
        paned.add(right_list, width=450)
        self.edit_tree = ttk.Treeview(right_list, columns=("id", "srv", "w", "sub"), show="headings", height=12)
        self.edit_tree.heading("id", text="ID"); self.edit_tree.heading("srv", text="Service")
        self.edit_tree.heading("w", text="Kg"); self.edit_tree.heading("sub", text="Subtotal")
        self.edit_tree.column("id", width=40); self.edit_tree.column("w", width=50)
        self.edit_tree.pack(fill="both", expand=True)
        self.edit_tree.bind("<<TreeviewSelect>>", self.load_batch_to_form)

        tk.Button(right_list, text="Remove Batch", bg="#C0392B", fg="white", command=lambda: self.delete_batch_action(trans_id)).pack(fill="x", pady=10)
        self.refresh_edit_list(trans_id)

    def refresh_receipt(self, trans_id):
        trans = self.db.fetch_one("SELECT * FROM Transactions WHERE transaction_id = %s", (trans_id,))
        batches = self.db.fetch_all("SELECT b.*, s.service_name FROM Transaction_Batches b JOIN Services s ON b.service_id = s.service_id WHERE transaction_id = %s", (trans_id,))
        self.receipt_text.config(state="normal")
        self.receipt_text.delete("1.0", tk.END)
        res = f"RECEIPT: {trans['display_id']}\nCUSTOMER: {trans['customer_name']}\n" + "-"*40 + "\n"
        for b in batches:
            res += f"{b['service_name']} ({b['weight']}kg) : ₱{b['subtotal']:,.2f}\n"
            addons = self.db.fetch_all("SELECT a.addon_name, ba.quantity FROM Batch_Addons ba JOIN Addons a ON ba.addon_id = a.addon_id WHERE ba.batch_id = %s", (b['batch_id'],))
            for a in addons: res += f"  + {a['addon_name']} x{a['quantity']}\n"
        res += "-"*40 + f"\nTOTAL: ₱{trans['total_amount']:,.2f}"
        self.receipt_text.insert("1.0", res)
        self.receipt_text.config(state="disabled")

    def refresh_edit_list(self, trans_id):
        for i in self.edit_tree.get_children(): self.edit_tree.delete(i)
        batches = self.db.fetch_all("SELECT b.*, s.service_name FROM Transaction_Batches b JOIN Services s ON b.service_id = s.service_id WHERE transaction_id = %s", (trans_id,))
        for b in batches:
            self.edit_tree.insert("", "end", values=(b['batch_id'], b['service_name'], b['weight'], f"₱{b['subtotal']:.2f}"))

    def load_batch_to_form(self, event):
        sel = self.edit_tree.selection()
        if not sel: return
        b_id = self.edit_tree.item(sel[0])['values'][0]
        self.editing_id = b_id
        batch = self.db.fetch_one("SELECT b.*, s.service_name FROM Transaction_Batches b JOIN Services s ON b.service_id = s.service_id WHERE b.batch_id = %s", (b_id,))
        self.edit_srv_cb.set(batch['service_name'])
        self.edit_w_ent.delete(0, tk.END); self.edit_w_ent.insert(0, batch['weight'])
        addon = self.db.fetch_one("SELECT a.addon_name, ba.quantity FROM Batch_Addons ba JOIN Addons a ON ba.addon_id = a.addon_id WHERE ba.batch_id = %s", (b_id,))
        if addon:
            self.edit_add_cb.set(addon['addon_name']); self.edit_qty_var.set(addon['quantity'])
        else:
            self.edit_add_cb.set("None"); self.edit_qty_var.set(1)
        self.batch_btn.config(text="Update Batch", bg="#F39C12")

    def reset_editor(self):
        self.editing_id = None
        self.edit_srv_cb.set(""); self.edit_w_ent.delete(0, tk.END)
        self.edit_add_cb.set("None"); self.edit_qty_var.set(1)
        self.batch_btn.config(text="Add Batch to List", bg="#3498DB")

    def save_batch_action(self, trans_id):
        srv_name = self.edit_srv_cb.get()
        w_str = self.edit_w_ent.get()
        if not srv_name or not w_str: 
            messagebox.showwarning("Error", "Required fields missing", parent=self.detail_win)
            return
            
        try:
            w = float(w_str)
            srv = self.services_data[srv_name]
            sub = (w * float(srv['price_per_kg'])) + float(srv['base_price'])
            add_name = self.edit_add_cb.get(); addon_obj = None
            if add_name != "None":
                a = self.addons_data[add_name]
                qty = self.edit_qty_var.get()
                u_p = float(a['price']) * (w if a['pricing_type'] == 'Per Kg' else 1)
                sub += (u_p * qty); addon_obj = (a['addon_id'], qty, u_p, u_p * qty)

            if hasattr(self, 'editing_id') and self.editing_id:
                # Update logic
                self.db.execute_query("UPDATE Transaction_Batches SET service_id=%s, weight=%s, subtotal=%s WHERE batch_id=%s", (srv['service_id'], w, sub, self.editing_id))
                self.db.execute_query("DELETE FROM Batch_Addons WHERE batch_id=%s", (self.editing_id,))
                if addon_obj: self.db.execute_query("INSERT INTO Batch_Addons (batch_id, addon_id, quantity, price, subtotal) VALUES (%s,%s,%s,%s,%s)", (self.editing_id, *addon_obj))
            else:
                # Add New logic
                b_id = self.db.execute_query("INSERT INTO Transaction_Batches (transaction_id, service_id, category_id, weight, price_per_unit, subtotal) VALUES (%s, %s, 1, %s, %s, %s)", (trans_id, srv['service_id'], w, srv['price_per_kg'], sub))
                if addon_obj: self.db.execute_query("INSERT INTO Batch_Addons (batch_id, addon_id, quantity, price, subtotal) VALUES (%s,%s,%s,%s,%s)", (b_id, *addon_obj))

            self.update_trans_total(trans_id)
            self.refresh_edit_list(trans_id)
            self.refresh_receipt(trans_id)
            self.load_orders()
            self.reset_editor()
            
            # This keeps the focus on the Order Manager window
            messagebox.showinfo("Success", "Record updated successfully.", parent=self.detail_win)
            
        except Exception as e: 
            messagebox.showerror("Error", str(e), parent=self.detail_win)

    def delete_batch_action(self, trans_id):
        sel = self.edit_tree.selection()
        if not sel: return
        b_id = self.edit_tree.item(sel[0])['values'][0]
        
        # Adding parent here ensures the confirmation box stays on top of the popup
        if messagebox.askyesno("Confirm", "Delete batch?", parent=self.detail_win):
            self.db.execute_query("DELETE FROM Transaction_Batches WHERE batch_id=%s", (b_id,))
            self.update_trans_total(trans_id)
            self.refresh_edit_list(trans_id)
            self.refresh_receipt(trans_id)
            self.load_orders()
            self.reset_editor()

    def update_trans_total(self, trans_id):
        res = self.db.fetch_one("SELECT SUM(subtotal) as total FROM Transaction_Batches WHERE transaction_id=%s", (trans_id,))
        self.db.execute_query("UPDATE Transactions SET total_amount=%s WHERE transaction_id=%s", (res['total'] or 0, trans_id))

# ==========================================
# Testing Block
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test - Orders Module")
    root.geometry("900x600")
    
    app = Orders(parent=root)
    app.pack(expand=True, fill="both")
    app.set_user({'user_id': 1, 'full_name': 'Test Admin'}) 
    
    root.mainloop()