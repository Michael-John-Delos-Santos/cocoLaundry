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
        self.access_denied_label = tk.Label(self, text="Admin Access Required", font=("Helvetica", 16, "bold"), fg="red")

    def set_user(self, user):
        self.current_user = user
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
        
        tk.Label(top_frame, text="Services & Inventory Management", font=("Helvetica", 16, "bold"), fg="#2C3E50").pack(side="left")

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
        self.create_stat_card(stats_frame, "Total Active Items", self.active_count_var, "#27AE60", 2)
        self.create_stat_card(stats_frame, "Total Inactive", self.inactive_count_var, "#7F8C8D", 3)

        # --- Tabbed Interface ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.create_services_tab()
        self.create_addons_tab()
        self.create_categories_tab() # New Tab

    def create_stat_card(self, parent, title, variable, color, col):
        card = tk.Frame(parent, bg=color, bd=0, padx=10, pady=10)
        card.grid(row=0, column=col, padx=5, sticky="nsew")
        tk.Label(card, text=title, font=("Helvetica", 10), bg=color, fg="white").pack(anchor="w")
        tk.Label(card, textvariable=variable, font=("Helvetica", 14, "bold"), bg=color, fg="white").pack(anchor="w", pady=(5, 0))

    # ================= SERVICES TAB =================
    def create_services_tab(self):
        self.srv_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.srv_tab, text=" Manage Services ")

        columns = ("id", "name", "desc", "price", "status")
        self.srv_tree = ttk.Treeview(self.srv_tab, columns=columns, show="headings", height=10)
        self.srv_tree.heading("id", text="ID"); self.srv_tree.heading("name", text="Service Name")
        self.srv_tree.heading("desc", text="Description"); self.srv_tree.heading("price", text="Price/Load")
        self.srv_tree.heading("status", text="Status")
        self.srv_tree.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(self.srv_tab)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Button(btn_frame, text="Add Service", bg="#27AE60", fg="white", width=12, command=lambda: self.service_form()).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Edit Service", bg="#F39C12", fg="white", width=12, command=lambda: self.service_form(is_edit=True)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Service", bg="#C0392B", fg="white", width=12, command=self.delete_service).pack(side="left", padx=5)

    # ================= ADD-ONS TAB =================
    def create_addons_tab(self):
        self.add_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.add_tab, text=" Manage Add-ons ")

        columns = ("id", "name", "desc", "price", "pricing_type", "status")
        self.add_tree = ttk.Treeview(self.add_tab, columns=columns, show="headings", height=10)
        self.add_tree.heading("id", text="ID"); self.add_tree.heading("name", text="Add-on Name")
        self.add_tree.heading("desc", text="Description"); self.add_tree.heading("price", text="Price")
        self.add_tree.heading("pricing_type", text="Type"); self.add_tree.heading("status", text="Status")
        self.add_tree.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(self.add_tab)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Button(btn_frame, text="Add Add-on", bg="#27AE60", fg="white", width=12, command=lambda: self.addon_form()).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Edit Add-on", bg="#F39C12", fg="white", width=12, command=lambda: self.addon_form(is_edit=True)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Add-on", bg="#C0392B", fg="white", width=12, command=self.delete_addon).pack(side="left", padx=5)

    # ================= CATEGORIES TAB (NEW) =================
    def create_categories_tab(self):
        self.cat_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.cat_tab, text=" Manage Categories ")

        columns = ("id", "name", "desc")
        self.cat_tree = ttk.Treeview(self.cat_tab, columns=columns, show="headings", height=10)
        self.cat_tree.heading("id", text="ID"); self.cat_tree.heading("name", text="Category Name")
        self.cat_tree.heading("desc", text="Description")
        self.cat_tree.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(self.cat_tab)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Button(btn_frame, text="Add Category", bg="#27AE60", fg="white", width=12, command=lambda: self.category_form()).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Edit Category", bg="#F39C12", fg="white", width=12, command=lambda: self.category_form(is_edit=True)).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Category", bg="#C0392B", fg="white", width=12, command=self.delete_category).pack(side="left", padx=5)

    def load_data(self):
        self.update_tables()
        self.update_statistics()

    def update_tables(self):
        # Update Services
        for item in self.srv_tree.get_children(): self.srv_tree.delete(item)
        for srv in self.db.fetch_all("SELECT * FROM Services ORDER BY service_id"):
            self.srv_tree.insert("", "end", values=(srv['service_id'], srv['service_name'], srv['description'], f"₱{srv['price_per_load']:.2f}", srv['status']))

        # Update Add-ons
        for item in self.add_tree.get_children(): self.add_tree.delete(item)
        for add in self.db.fetch_all("SELECT * FROM Addons ORDER BY addon_id"):
            self.add_tree.insert("", "end", values=(add['addon_id'], add['addon_name'], add['description'], f"₱{add['price']:.2f}", add['pricing_type'], add['status']))

        # Update Categories
        for item in self.cat_tree.get_children(): self.cat_tree.delete(item)
        for cat in self.db.fetch_all("SELECT * FROM Category ORDER BY category_id"):
            self.cat_tree.insert("", "end", values=(cat['category_id'], cat['name'], cat['description']))

    def update_statistics(self):
        time_filter = self.time_var.get()
        date_cond = ""
        if time_filter == "This Month": date_cond = "AND MONTH(t.created_at) = MONTH(CURDATE()) AND YEAR(t.created_at) = YEAR(CURDATE())"
        elif time_filter == "This Year": date_cond = "AND YEAR(t.created_at) = YEAR(CURDATE())"

        try:
            # Top Service
            srv_q = f"SELECT s.service_name, COUNT(b.batch_id) as usage_count FROM Services s LEFT JOIN Transaction_Batches b ON s.service_id = b.service_id LEFT JOIN Transactions t ON b.transaction_id = t.transaction_id {date_cond} GROUP BY s.service_id ORDER BY usage_count DESC LIMIT 1"
            top_srv = self.db.fetch_one(srv_q)
            self.top_service_var.set(f"{top_srv['service_name']} ({top_srv['usage_count']})" if top_srv and top_srv['usage_count'] > 0 else "None")

            # Top Add-on
            add_q = f"SELECT a.addon_name, COUNT(ba.batch_addon_id) as usage_count FROM Addons a LEFT JOIN Batch_Addons ba ON a.addon_id = ba.addon_id LEFT JOIN Transaction_Batches b ON ba.batch_id = b.batch_id LEFT JOIN Transactions t ON b.transaction_id = t.transaction_id {date_cond} GROUP BY a.addon_id ORDER BY usage_count DESC LIMIT 1"
            top_add = self.db.fetch_one(add_q)
            self.top_addon_var.set(f"{top_add['addon_name']} ({top_add['usage_count']})" if top_add and top_add['usage_count'] > 0 else "None")

            # Active/Inactive
            s_s = self.db.fetch_all("SELECT status, COUNT(*) as count FROM Services GROUP BY status")
            a_s = self.db.fetch_all("SELECT status, COUNT(*) as count FROM Addons GROUP BY status")
            active = sum(row['count'] for row in s_s + a_s if row['status'] == 'Active')
            inactive = sum(row['count'] for row in s_s + a_s if row['status'] == 'Inactive')
            self.active_count_var.set(str(active)); self.inactive_count_var.set(str(inactive))
        except Exception as e: print(f"Stats Error: {e}")

    # ================= FORMS =================

    def service_form(self, is_edit=False):
        selected_id = None
        if is_edit:
            sel = self.srv_tree.selection()
            if not sel: return messagebox.showwarning("Warning", "Select a service to edit.")
            selected_id = self.srv_tree.item(sel[0])['values'][0]

        top = tk.Toplevel(self); top.title("Service Form"); top.geometry("400x300"); top.grab_set()
        tk.Label(top, text="Service Name:").grid(row=0, column=0, pady=10, padx=10, sticky="e")
        name_ent = tk.Entry(top, width=30); name_ent.grid(row=0, column=1)
        tk.Label(top, text="Description:").grid(row=1, column=0, pady=10, padx=10, sticky="e")
        desc_ent = tk.Entry(top, width=30); desc_ent.grid(row=1, column=1)
        tk.Label(top, text="Price/Load:").grid(row=2, column=0, pady=10, padx=10, sticky="e")
        price_ent = tk.Entry(top, width=30); price_ent.grid(row=2, column=1)
        tk.Label(top, text="Status:").grid(row=3, column=0, pady=10, padx=10, sticky="e")
        stat_cb = ttk.Combobox(top, values=("Active", "Inactive"), state="readonly"); stat_cb.grid(row=3, column=1); stat_cb.set("Active")

        if is_edit:
            srv = self.db.fetch_one("SELECT * FROM Services WHERE service_id = %s", (selected_id,))
            name_ent.insert(0, srv['service_name']); desc_ent.insert(0, srv['description'] or "")
            price_ent.insert(0, srv['price_per_load']); stat_cb.set(srv['status'])

        def save():
            try:
                p = float(price_ent.get())
                if is_edit:
                    self.db.execute_query("UPDATE Services SET service_name=%s, description=%s, price_per_load=%s, status=%s WHERE service_id=%s", (name_ent.get(), desc_ent.get(), p, stat_cb.get(), selected_id))
                else:
                    self.db.execute_query("INSERT INTO Services (service_name, description, price_per_load, status) VALUES (%s,%s,%s,%s)", (name_ent.get(), desc_ent.get(), p, stat_cb.get()))
                self.load_data(); top.destroy()
            except: messagebox.showerror("Error", "Check inputs.")
        tk.Button(top, text="Save", bg="#2980B9", fg="white", width=15, command=save).grid(row=4, column=0, columnspan=2, pady=20)

    def addon_form(self, is_edit=False):
        selected_id = None
        if is_edit:
            sel = self.add_tree.selection()
            if not sel: return messagebox.showwarning("Warning", "Select an add-on.")
            selected_id = self.add_tree.item(sel[0])['values'][0]

        top = tk.Toplevel(self); top.title("Add-on Form"); top.geometry("400x300"); top.grab_set()
        tk.Label(top, text="Name:").grid(row=0, column=0, pady=10, padx=10, sticky="e")
        name_ent = tk.Entry(top, width=30); name_ent.grid(row=0, column=1)
        tk.Label(top, text="Price:").grid(row=1, column=0, pady=10, padx=10, sticky="e")
        price_ent = tk.Entry(top, width=30); price_ent.grid(row=1, column=1)
        tk.Label(top, text="Type:").grid(row=2, column=0, pady=10, padx=10, sticky="e")
        type_cb = ttk.Combobox(top, values=("Fixed", "Per Kg"), state="readonly"); type_cb.grid(row=2, column=1); type_cb.set("Fixed")

        if is_edit:
            a = self.db.fetch_one("SELECT * FROM Addons WHERE addon_id = %s", (selected_id,))
            name_ent.insert(0, a['addon_name']); price_ent.insert(0, a['price']); type_cb.set(a['pricing_type'])

        def save():
            try:
                p = float(price_ent.get())
                if is_edit: self.db.execute_query("UPDATE Addons SET addon_name=%s, price=%s, pricing_type=%s WHERE addon_id=%s", (name_ent.get(), p, type_cb.get(), selected_id))
                else: self.db.execute_query("INSERT INTO Addons (addon_name, price, pricing_type) VALUES (%s,%s,%s)", (name_ent.get(), p, type_cb.get()))
                self.load_data(); top.destroy()
            except: messagebox.showerror("Error", "Check inputs.")
        tk.Button(top, text="Save", bg="#2980B9", fg="white", width=15, command=save).grid(row=3, column=0, columnspan=2, pady=20)

    # ================= CATEGORY FORM (NEW) =================
    def category_form(self, is_edit=False):
        selected_id = None
        if is_edit:
            sel = self.cat_tree.selection()
            if not sel: return messagebox.showwarning("Warning", "Select a category.")
            selected_id = self.cat_tree.item(sel[0])['values'][0]

        top = tk.Toplevel(self); top.title("Category Form"); top.geometry("400x250"); top.grab_set()
        tk.Label(top, text="Category Name:").grid(row=0, column=0, pady=20, padx=10, sticky="e")
        name_ent = tk.Entry(top, width=30); name_ent.grid(row=0, column=1)
        tk.Label(top, text="Description:").grid(row=1, column=0, pady=10, padx=10, sticky="e")
        desc_ent = tk.Entry(top, width=30); desc_ent.grid(row=1, column=1)

        if is_edit:
            c = self.db.fetch_one("SELECT * FROM Category WHERE category_id = %s", (selected_id,))
            name_ent.insert(0, c['name']); desc_ent.insert(0, c['description'] or "")

        def save():
            name = name_ent.get().strip()
            if not name: return messagebox.showerror("Error", "Name required.")
            if is_edit:
                self.db.execute_query("UPDATE Category SET name=%s, description=%s WHERE category_id=%s", (name, desc_ent.get(), selected_id))
            else:
                self.db.execute_query("INSERT INTO Category (name, description) VALUES (%s,%s)", (name, desc_ent.get()))
            self.load_data(); top.destroy()

        tk.Button(top, text="Save", bg="#2980B9", fg="white", width=15, command=save).grid(row=2, column=0, columnspan=2, pady=20)

    # ================= DELETE LOGIC =================
    def delete_service(self):
        sel = self.srv_tree.selection()
        if sel:
            sid = self.srv_tree.item(sel[0])['values'][0]
            if messagebox.askyesno("Confirm", "Delete this Service?"):
                self.db.execute_query("DELETE FROM Services WHERE service_id=%s", (sid,))
                self.load_data()

    def delete_addon(self):
        sel = self.add_tree.selection()
        if sel:
            aid = self.add_tree.item(sel[0])['values'][0]
            if messagebox.askyesno("Confirm", "Delete this Add-on?"):
                self.db.execute_query("DELETE FROM Addons WHERE addon_id=%s", (aid,))
                self.load_data()

    def delete_category(self):
        sel = self.cat_tree.selection()
        if sel:
            cid = self.cat_tree.item(sel[0])['values'][0]
            if messagebox.askyesno("Confirm", "Delete this Category?"):
                try:
                    self.db.execute_query("DELETE FROM Category WHERE category_id=%s", (cid,))
                    self.load_data()
                except: messagebox.showerror("Error", "Category is currently in use.")