import tkinter as tk
from tkinter import ttk, messagebox
from dbManager import DatabaseManager

class Services(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        self.current_user = None
        
        self.configure(padx=20, pady=20)
        
        # We will create widgets only after verifying the user is an admin
        self.access_denied_label = tk.Label(self, text="Admin Access Required", font=("Helvetica", 16, "bold"), fg="red")

    def set_user(self, user):
        self.current_user = user
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        if user and user['role'] == 'Admin':
            self.create_widgets()
            self.load_data()
        else:
            self.access_denied_label = tk.Label(self, text="Access Denied. Administrator privileges required.", font=("Helvetica", 16, "bold"), fg="red")
            self.access_denied_label.pack(expand=True)

    def create_widgets(self):
        # --- Header & Filters ---
        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(top_frame, text="Services & Add-ons Management", font=("Helvetica", 16, "bold"), fg="#2C3E50").pack(side="left")

        filter_frame = tk.Frame(top_frame)
        filter_frame.pack(side="right")
        
        tk.Label(filter_frame, text="Stats Time Filter:").pack(side="left", padx=5)
        self.time_var = tk.StringVar(value="All Time")
        time_cb = ttk.Combobox(filter_frame, textvariable=self.time_var, state="readonly", width=15)
        time_cb['values'] = ("All Time", "This Month", "This Year")
        time_cb.pack(side="left", padx=5)
        time_cb.bind("<<ComboboxSelected>>", lambda e: self.update_statistics())

        # --- Statistics Cards ---
        stats_frame = tk.Frame(self)
        stats_frame.pack(fill="x", pady=(0, 15))
        for i in range(4): stats_frame.columnconfigure(i, weight=1)

        self.top_service_var = tk.StringVar(value="Loading...")
        self.top_addon_var = tk.StringVar(value="Loading...")
        self.active_count_var = tk.StringVar(value="0")
        self.inactive_count_var = tk.StringVar(value="0")

        self.create_stat_card(stats_frame, "Top Used Service", self.top_service_var, "#2980B9", 0)
        self.create_stat_card(stats_frame, "Top Used Add-on", self.top_addon_var, "#8E44AD", 1)
        self.create_stat_card(stats_frame, "Total Active (Srv/Add)", self.active_count_var, "#27AE60", 2)
        self.create_stat_card(stats_frame, "Total Inactive", self.inactive_count_var, "#7F8C8D", 3)

        # --- Tabbed Interface ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.create_services_tab()
        self.create_addons_tab()

    def create_stat_card(self, parent, title, variable, color, col):
        card = tk.Frame(parent, bg=color, bd=0, padx=10, pady=10)
        card.grid(row=0, column=col, padx=5, sticky="nsew")
        tk.Label(card, text=title, font=("Helvetica", 10), bg=color, fg="white").pack(anchor="w")
        tk.Label(card, textvariable=variable, font=("Helvetica", 14, "bold"), bg=color, fg="white").pack(anchor="w", pady=(5, 0))

    def create_services_tab(self):
        self.srv_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.srv_tab, text=" Manage Services ")

        columns = ("id", "name", "desc", "price", "base_price", "duration", "status")
        self.srv_tree = ttk.Treeview(self.srv_tab, columns=columns, show="headings", height=10)
        
        self.srv_tree.heading("id", text="ID")
        self.srv_tree.heading("name", text="Service Name")
        self.srv_tree.heading("desc", text="Description")
        self.srv_tree.heading("price", text="Price/kg")
        self.srv_tree.heading("base_price", text="Base Price")
        self.srv_tree.heading("duration", text="Est. Duration")
        self.srv_tree.heading("status", text="Status")

        self.srv_tree.column("id", width=50, anchor="center")
        self.srv_tree.column("name", width=150)
        self.srv_tree.column("desc", width=250)
        self.srv_tree.column("price", width=80, anchor="e")
        self.srv_tree.column("base_price", width=80, anchor="e")
        self.srv_tree.column("duration", width=100)
        self.srv_tree.column("status", width=80, anchor="center")
        
        self.srv_tree.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(self.srv_tab)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        tk.Button(btn_frame, text="Add Service", bg="#27AE60", fg="white", width=12, command=lambda: self.service_form()).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Edit Service", bg="#F39C12", fg="white", width=12, command=lambda: self.service_form(is_edit=True)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Service", bg="#C0392B", fg="white", width=12, command=self.delete_service).pack(side="left", padx=5)

    def create_addons_tab(self):
        self.add_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.add_tab, text=" Manage Add-ons ")

        columns = ("id", "name", "desc", "price", "pricing_type", "status")
        self.add_tree = ttk.Treeview(self.add_tab, columns=columns, show="headings", height=10)
        
        self.add_tree.heading("id", text="ID")
        self.add_tree.heading("name", text="Add-on Name")
        self.add_tree.heading("desc", text="Description")
        self.add_tree.heading("price", text="Price")
        self.add_tree.heading("pricing_type", text="Pricing Type")
        self.add_tree.heading("status", text="Status")

        self.add_tree.column("id", width=50, anchor="center")
        self.add_tree.column("name", width=150)
        self.add_tree.column("desc", width=250)
        self.add_tree.column("price", width=80, anchor="e")
        self.add_tree.column("pricing_type", width=100, anchor="center")
        self.add_tree.column("status", width=80, anchor="center")
        
        self.add_tree.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(self.add_tab)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        tk.Button(btn_frame, text="Add Add-on", bg="#27AE60", fg="white", width=12, command=lambda: self.addon_form()).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Edit Add-on", bg="#F39C12", fg="white", width=12, command=lambda: self.addon_form(is_edit=True)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Add-on", bg="#C0392B", fg="white", width=12, command=self.delete_addon).pack(side="left", padx=5)

    def load_data(self):
        self.update_tables()
        self.update_statistics()

    def update_tables(self):
        # Update Services Table
        for item in self.srv_tree.get_children(): self.srv_tree.delete(item)
        for srv in self.db.fetch_all("SELECT * FROM Services ORDER BY service_id"):
            self.srv_tree.insert("", "end", values=(
                srv['service_id'], srv['service_name'], srv['description'],
                f"₱{srv['price_per_kg']:.2f}", f"₱{srv['base_price']:.2f}",
                srv['estimated_duration'], srv['status']
            ))

        # Update Add-ons Table
        for item in self.add_tree.get_children(): self.add_tree.delete(item)
        for add in self.db.fetch_all("SELECT * FROM Addons ORDER BY addon_id"):
            self.add_tree.insert("", "end", values=(
                add['addon_id'], add['addon_name'], add['description'],
                f"₱{add['price']:.2f}", add['pricing_type'], add['status']
            ))

    def update_statistics(self):
        time_filter = self.time_var.get()
        date_cond = ""
        
        if time_filter == "This Month":
            date_cond = "AND MONTH(t.created_at) = MONTH(CURDATE()) AND YEAR(t.created_at) = YEAR(CURDATE())"
        elif time_filter == "This Year":
            date_cond = "AND YEAR(t.created_at) = YEAR(CURDATE())"

        try:
            # 1. Top Service
            srv_query = f"""
                SELECT s.service_name, COUNT(b.batch_id) as usage_count 
                FROM Services s 
                LEFT JOIN Transaction_Batches b ON s.service_id = b.service_id
                LEFT JOIN Transactions t ON b.transaction_id = t.transaction_id {date_cond}
                GROUP BY s.service_id ORDER BY usage_count DESC LIMIT 1
            """
            top_srv = self.db.fetch_one(srv_query)
            self.top_service_var.set(f"{top_srv['service_name']} ({top_srv['usage_count']})" if top_srv and top_srv['usage_count'] > 0 else "None")

            # 2. Top Add-on
            add_query = f"""
                SELECT a.addon_name, COUNT(ba.batch_addon_id) as usage_count 
                FROM Addons a 
                LEFT JOIN Batch_Addons ba ON a.addon_id = ba.addon_id
                LEFT JOIN Transaction_Batches b ON ba.batch_id = b.batch_id
                LEFT JOIN Transactions t ON b.transaction_id = t.transaction_id {date_cond}
                GROUP BY a.addon_id ORDER BY usage_count DESC LIMIT 1
            """
            top_add = self.db.fetch_one(add_query)
            self.top_addon_var.set(f"{top_add['addon_name']} ({top_add['usage_count']})" if top_add and top_add['usage_count'] > 0 else "None")

            # 3. Active/Inactive Counts
            srv_status = self.db.fetch_all("SELECT status, COUNT(*) as count FROM Services GROUP BY status")
            add_status = self.db.fetch_all("SELECT status, COUNT(*) as count FROM Addons GROUP BY status")
            
            active = sum(row['count'] for row in srv_status + add_status if row['status'] == 'Active')
            inactive = sum(row['count'] for row in srv_status + add_status if row['status'] == 'Inactive')
            
            self.active_count_var.set(str(active))
            self.inactive_count_var.set(str(inactive))

        except Exception as e:
            print(f"Stats Error: {e}")

    # ================= CRUD Dialogs =================
    
    def service_form(self, is_edit=False):
        selected_id = None
        if is_edit:
            selected = self.srv_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select a service to edit.", parent=self)
                return
            selected_id = self.srv_tree.item(selected[0])['values'][0]

        top = tk.Toplevel(self)
        top.title("Edit Service" if is_edit else "Add Service")
        top.geometry("400x350")
        top.grab_set()

        # Form Fields
        tk.Label(top, text="Service Name:").grid(row=0, column=0, sticky="e", padx=10, pady=5)
        name_ent = tk.Entry(top, width=30)
        name_ent.grid(row=0, column=1, pady=5)

        tk.Label(top, text="Description:").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        desc_ent = tk.Entry(top, width=30)
        desc_ent.grid(row=1, column=1, pady=5)

        tk.Label(top, text="Price per kg (₱):").grid(row=2, column=0, sticky="e", padx=10, pady=5)
        price_ent = tk.Entry(top, width=15)
        price_ent.grid(row=2, column=1, sticky="w", pady=5)

        tk.Label(top, text="Base Price (₱):").grid(row=3, column=0, sticky="e", padx=10, pady=5)
        base_ent = tk.Entry(top, width=15)
        base_ent.grid(row=3, column=1, sticky="w", pady=5)
        base_ent.insert(0, "0.00")

        tk.Label(top, text="Est. Duration:").grid(row=4, column=0, sticky="e", padx=10, pady=5)
        dur_ent = tk.Entry(top, width=15)
        dur_ent.grid(row=4, column=1, sticky="w", pady=5)

        tk.Label(top, text="Status:").grid(row=5, column=0, sticky="e", padx=10, pady=5)
        status_cb = ttk.Combobox(top, values=("Active", "Inactive"), state="readonly", width=12)
        status_cb.set("Active")
        status_cb.grid(row=5, column=1, sticky="w", pady=5)

        if is_edit:
            srv = self.db.fetch_one("SELECT * FROM Services WHERE service_id = %s", (selected_id,))
            name_ent.insert(0, srv['service_name'])
            if srv['description']: desc_ent.insert(0, srv['description'])
            price_ent.insert(0, srv['price_per_kg'])
            base_ent.delete(0, tk.END)
            base_ent.insert(0, srv['base_price'])
            if srv['estimated_duration']: dur_ent.insert(0, srv['estimated_duration'])
            status_cb.set(srv['status'])

        def save():
            try:
                pkg = float(price_ent.get())
                base = float(base_ent.get() or 0)
                
                if is_edit:
                    query = "UPDATE Services SET service_name=%s, description=%s, price_per_kg=%s, base_price=%s, estimated_duration=%s, status=%s WHERE service_id=%s"
                    self.db.execute_query(query, (name_ent.get(), desc_ent.get(), pkg, base, dur_ent.get(), status_cb.get(), selected_id))
                    self.db.log_audit(self.current_user['user_id'], 'UPDATE', 'Service', selected_id, f"Updated service {name_ent.get()}")
                else:
                    query = "INSERT INTO Services (service_name, description, price_per_kg, base_price, estimated_duration, status) VALUES (%s, %s, %s, %s, %s, %s)"
                    new_id = self.db.execute_query(query, (name_ent.get(), desc_ent.get(), pkg, base, dur_ent.get(), status_cb.get()))
                    self.db.log_audit(self.current_user['user_id'], 'CREATE', 'Service', new_id, f"Created service {name_ent.get()}")
                
                self.load_data()
                top.destroy()
                messagebox.showinfo("Success", "Service saved successfully.", parent=self)
            except ValueError:
                messagebox.showerror("Error", "Prices must be valid numbers.", parent=top)

        tk.Button(top, text="Save", bg="#2980B9", fg="white", width=15, command=save).grid(row=6, column=0, columnspan=2, pady=20)

    def addon_form(self, is_edit=False):
        selected_id = None
        if is_edit:
            selected = self.add_tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Select an add-on to edit.", parent=self)
                return
            selected_id = self.add_tree.item(selected[0])['values'][0]

        top = tk.Toplevel(self)
        top.title("Edit Add-on" if is_edit else "Add Add-on")
        top.geometry("400x300")
        top.grab_set()

        tk.Label(top, text="Add-on Name:").grid(row=0, column=0, sticky="e", padx=10, pady=5)
        name_ent = tk.Entry(top, width=30)
        name_ent.grid(row=0, column=1, pady=5)

        tk.Label(top, text="Description:").grid(row=1, column=0, sticky="e", padx=10, pady=5)
        desc_ent = tk.Entry(top, width=30)
        desc_ent.grid(row=1, column=1, pady=5)

        tk.Label(top, text="Price (₱):").grid(row=2, column=0, sticky="e", padx=10, pady=5)
        price_ent = tk.Entry(top, width=15)
        price_ent.grid(row=2, column=1, sticky="w", pady=5)

        tk.Label(top, text="Pricing Type:").grid(row=3, column=0, sticky="e", padx=10, pady=5)
        type_cb = ttk.Combobox(top, values=("Fixed", "Per Kg"), state="readonly", width=12)
        type_cb.set("Fixed")
        type_cb.grid(row=3, column=1, sticky="w", pady=5)

        tk.Label(top, text="Status:").grid(row=4, column=0, sticky="e", padx=10, pady=5)
        status_cb = ttk.Combobox(top, values=("Active", "Inactive"), state="readonly", width=12)
        status_cb.set("Active")
        status_cb.grid(row=4, column=1, sticky="w", pady=5)

        if is_edit:
            add = self.db.fetch_one("SELECT * FROM Addons WHERE addon_id = %s", (selected_id,))
            name_ent.insert(0, add['addon_name'])
            if add['description']: desc_ent.insert(0, add['description'])
            price_ent.insert(0, add['price'])
            type_cb.set(add['pricing_type'])
            status_cb.set(add['status'])

        def save():
            try:
                price = float(price_ent.get())
                if is_edit:
                    query = "UPDATE Addons SET addon_name=%s, description=%s, price=%s, pricing_type=%s, status=%s WHERE addon_id=%s"
                    self.db.execute_query(query, (name_ent.get(), desc_ent.get(), price, type_cb.get(), status_cb.get(), selected_id))
                    self.db.log_audit(self.current_user['user_id'], 'UPDATE', 'Addon', selected_id, f"Updated addon {name_ent.get()}")
                else:
                    query = "INSERT INTO Addons (addon_name, description, price, pricing_type, status) VALUES (%s, %s, %s, %s, %s)"
                    new_id = self.db.execute_query(query, (name_ent.get(), desc_ent.get(), price, type_cb.get(), status_cb.get()))
                    self.db.log_audit(self.current_user['user_id'], 'CREATE', 'Addon', new_id, f"Created addon {name_ent.get()}")
                
                self.load_data()
                top.destroy()
                messagebox.showinfo("Success", "Add-on saved successfully.", parent=self)
            except ValueError:
                messagebox.showerror("Error", "Price must be a valid number.", parent=top)

        tk.Button(top, text="Save", bg="#2980B9", fg="white", width=15, command=save).grid(row=5, column=0, columnspan=2, pady=20)

    def delete_service(self):
        selected = self.srv_tree.selection()
        if not selected: return
        srv_id = self.srv_tree.item(selected[0])['values'][0]
        
        # Dependency check
        check = self.db.fetch_one("SELECT COUNT(*) as cnt FROM Transaction_Batches WHERE service_id = %s", (srv_id,))
        if check['cnt'] > 0:
            messagebox.showerror("Cannot Delete", "This Service is linked to past transactions. Consider setting its Status to 'Inactive' instead.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to permanently delete this Service?", parent=self):
            self.db.execute_query("DELETE FROM Services WHERE service_id = %s", (srv_id,))
            self.db.log_audit(self.current_user['user_id'], 'DELETE', 'Service', srv_id, "Deleted a service")
            self.load_data()

    def delete_addon(self):
        selected = self.add_tree.selection()
        if not selected: return
        add_id = self.add_tree.item(selected[0])['values'][0]
        
        # Dependency check
        check = self.db.fetch_one("SELECT COUNT(*) as cnt FROM Batch_Addons WHERE addon_id = %s", (add_id,))
        if check['cnt'] > 0:
            messagebox.showerror("Cannot Delete", "This Add-on is linked to past transactions. Consider setting its Status to 'Inactive' instead.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to permanently delete this Add-on?", parent=self):
            self.db.execute_query("DELETE FROM Addons WHERE addon_id = %s", (add_id,))
            self.db.log_audit(self.current_user['user_id'], 'DELETE', 'Addon', add_id, "Deleted an add-on")
            self.load_data()

# Testing Block
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test - Services (Admin)")
    root.geometry("900x600")
    app = Services(parent=root)
    app.pack(expand=True, fill="both")
    # Simulate an Admin user login
    app.set_user({'user_id': 1, 'role': 'Admin', 'full_name': 'Test Admin'})
    root.mainloop()