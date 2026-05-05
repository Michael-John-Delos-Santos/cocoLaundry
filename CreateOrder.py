import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from dbManager import DatabaseManager
from datetime import datetime
import time
import math

class CreateOrder(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        self.current_user = None
        
        # Data storage
        self.services_data = {}
        self.categories_data = {}
        self.addons_data = {}
        
        # Current batch state
        self.temp_addons = {} 
        self.current_batches = [] 
        self.order_weight = None  # To establish weight consistency
        
        self.configure(padx=20, pady=20)
        self.create_widgets()

    def set_user(self, user):
        self.current_user = user
        self.refresh_form()

    def refresh_form(self):
        self.load_reference_data()
        self.load_customer_emails()
        self.clear_form()

    def load_reference_data(self):
        services = self.db.fetch_all("SELECT * FROM Services WHERE status = 'Active'")
        self.services_data = {s['service_name']: s for s in services}
        self.service_cb['values'] = list(self.services_data.keys())

        categories = self.db.fetch_all("SELECT * FROM Category")
        self.categories_data = {c['name']: c for c in categories}
        self.category_cb['values'] = list(self.categories_data.keys())

        addons = self.db.fetch_all("SELECT * FROM Addons WHERE status = 'Active'")
        self.addons_data = {a['addon_name']: a for a in addons}
        self.addon_selection_cb['values'] = list(self.addons_data.keys())

    def load_customer_emails(self):
        query = "SELECT DISTINCT customer_email FROM Transactions WHERE customer_email IS NOT NULL AND customer_email != ''"
        results = self.db.fetch_all(query)
        self.cust_email_cb['values'] = [r['customer_email'] for r in results]

    def create_widgets(self):
        self.order_id_var = tk.StringVar()
        
        header_frame = tk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 10))
        tk.Label(header_frame, text="Create New Order", font=("Helvetica", 16, "bold"), fg="#2C3E50").pack(side="left")
        tk.Label(header_frame, textvariable=self.order_id_var, font=("Helvetica", 12, "bold"), fg="#E74C3C").pack(side="right")

        main_paned = tk.PanedWindow(self, orient="horizontal", sashwidth=5)
        main_paned.pack(fill="both", expand=True)

        left_frame = tk.Frame(main_paned); right_frame = tk.Frame(main_paned)
        main_paned.add(left_frame, minsize=450, stretch="always")
        main_paned.add(right_frame, minsize=350, stretch="always")

        # 1. Customer Details
        cust_frame = tk.LabelFrame(left_frame, text="Customer Details", font=("Helvetica", 10, "bold"), padx=10, pady=10)
        cust_frame.pack(fill="x", pady=(0, 10))

        vcmd = (self.register(self.validate_name), '%S')
        tk.Label(cust_frame, text="Name *").grid(row=0, column=0, sticky="w")
        self.cust_name = tk.Entry(cust_frame, width=30, validate='key', validatecommand=vcmd)
        self.cust_name.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(cust_frame, text="Email").grid(row=1, column=0, sticky="w")
        self.cust_email_cb = ttk.Combobox(cust_frame, width=28)
        self.cust_email_cb.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(cust_frame, text="Pickup Date").grid(row=0, column=2, padx=(10,0))
        self.pickup_date = DateEntry(cust_frame, width=15, date_pattern='yyyy-mm-dd', mindate=datetime.now().date())
        self.pickup_date.grid(row=0, column=3, padx=5)

        # 2. Add Batch Form
        batch_frame = tk.LabelFrame(left_frame, text="Add Batch Details", font=("Helvetica", 10, "bold"), padx=10, pady=10)
        batch_frame.pack(fill="both", expand=True)

        tk.Label(batch_frame, text="Service *").grid(row=0, column=0, sticky="w")
        self.service_cb = ttk.Combobox(batch_frame, state="readonly", width=25)
        self.service_cb.grid(row=0, column=1, pady=5, sticky="w")
        
        tk.Label(batch_frame, text="Category *").grid(row=1, column=0, sticky="w")
        self.category_cb = ttk.Combobox(batch_frame, state="readonly", width=25)
        self.category_cb.grid(row=1, column=1, pady=5, sticky="w")

        tk.Label(batch_frame, text="Weight (kg) *").grid(row=2, column=0, sticky="w")
        self.weight_entry = tk.Entry(batch_frame, width=28)
        self.weight_entry.grid(row=2, column=1, pady=5, sticky="w")
        self.weight_entry.bind("<KeyRelease>", lambda e: self.update_load_display())

        self.load_info_var = tk.StringVar(value="Loads: 0")
        tk.Label(batch_frame, textvariable=self.load_info_var, font=("Helvetica", 10, "italic"), fg="#2980B9").grid(row=2, column=2, sticky="w")

        addon_labelframe = tk.LabelFrame(batch_frame, text="Select Add-ons", pady=10, padx=10)
        addon_labelframe.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")

        self.addon_selection_cb = ttk.Combobox(addon_labelframe, state="readonly", width=35)
        self.addon_selection_cb.pack(pady=5)

        qty_ctrl_frame = tk.Frame(addon_labelframe); qty_ctrl_frame.pack()
        self.temp_qty_var = tk.IntVar(value=1)
        tk.Button(qty_ctrl_frame, text="-", width=3, command=lambda: self.adjust_temp_qty(-1)).pack(side="left")
        tk.Label(qty_ctrl_frame, textvariable=self.temp_qty_var, width=5, font=("bold")).pack(side="left", padx=10)
        tk.Button(qty_ctrl_frame, text="+", width=3, command=lambda: self.adjust_temp_qty(1)).pack(side="left")

        tk.Button(addon_labelframe, text="Apply Add-on to Batch", bg="#34495E", fg="white", command=self.apply_addon_to_temp).pack(pady=10)
        self.applied_addons_lbl = tk.Label(addon_labelframe, text="Applied: None", fg="#7F8C8D", wraplength=350, justify="left")
        self.applied_addons_lbl.pack()

        tk.Button(batch_frame, text="ADD BATCH TO ORDER", bg="#3498DB", fg="white", font=("bold"), command=self.add_batch_to_order).grid(row=4, column=0, columnspan=2, pady=10)

        # 3. Order Summary
        summary_frame = tk.LabelFrame(right_frame, text="Order Summary", padx=10, pady=10)
        summary_frame.pack(fill="both", expand=True)

        self.cart_tree = ttk.Treeview(summary_frame, columns=("service", "weight", "subtotal"), show="headings", height=12)
        self.cart_tree.heading("service", text="Service"); self.cart_tree.heading("weight", text="Kg"); self.cart_tree.heading("subtotal", text="Subtotal")
        self.cart_tree.column("weight", width=80, anchor="center")
        self.cart_tree.pack(fill="both", expand=True)

        self.total_var = tk.StringVar(value="Total: ₱0.00")
        tk.Label(summary_frame, textvariable=self.total_var, font=("Helvetica", 14, "bold"), fg="#27AE60").pack(pady=10)
        tk.Button(summary_frame, text="SUBMIT FINAL ORDER", bg="#2ECC71", fg="white", font=("bold"), command=self.submit_order).pack(fill="x")

    def validate_name(self, char):
        return not char.isdigit()

    def get_kg_per_load(self):
        res = self.db.fetch_one("SELECT config_value FROM system_config WHERE config_key = 'kg_per_load'")
        return float(res['config_value']) if res else 7.0

    def calculate_loads(self, weight):
        limit = self.get_kg_per_load()
        return math.ceil(weight / limit) if weight > 0 else 0

    def update_load_display(self):
        try:
            w = float(self.weight_entry.get())
            self.load_info_var.set(f"Loads: {self.calculate_loads(w)}")
        except: self.load_info_var.set("Loads: 0")

    def adjust_temp_qty(self, amt):
        new_val = self.temp_qty_var.get() + amt
        if new_val >= 1: self.temp_qty_var.set(new_val)

    def apply_addon_to_temp(self):
        name = self.addon_selection_cb.get()
        if not name: return
        addon_id = self.addons_data[name]['addon_id']
        self.temp_addons[addon_id] = self.temp_addons.get(addon_id, 0) + self.temp_qty_var.get()
        summary = [f"{self.addons_data[n]['addon_name']} (x{q})" for n, info in self.addons_data.items() for aid, q in self.temp_addons.items() if info['addon_id'] == aid]
        self.applied_addons_lbl.config(text=f"Applied: {', '.join(summary)}")
        self.temp_qty_var.set(1); self.addon_selection_cb.set('')

    def add_batch_to_order(self):
        s_name = self.service_cb.get(); c_name = self.category_cb.get(); w_val = self.weight_entry.get()
        if not all([s_name, c_name, w_val]):
            return messagebox.showwarning("Input Error", "Fill all required fields.")

        try:
            weight = float(w_val)
            loads = self.calculate_loads(weight)
            if loads <= 0: return messagebox.showwarning("Input Error", "At least one load is required.")
            
            # --- WEIGHT SYNC CHECK ---
            if self.order_weight is not None and weight != self.order_weight:
                messagebox.showerror("Weight Mismatch", f"Weight must match established order weight: {self.order_weight}kg")
                return
            
            if self.order_weight is None:
                self.order_weight = weight
        except: return messagebox.showerror("Error", "Invalid weight.")

        service = self.services_data[s_name]; category = self.categories_data[c_name]
        subtotal = loads * float(service['price_per_load'])
        
        final_addons = []; addon_desc = []
        for aid, qty in self.temp_addons.items():
            addon = next(item for item in self.addons_data.values() if item['addon_id'] == aid)
            u_price = float(addon['price']) * (weight if addon['pricing_type'] == 'Per Kg' else 1)
            subtotal += (u_price * qty)
            final_addons.append({'addon_id': aid, 'quantity': qty, 'unit_price': u_price, 'total_price': u_price * qty})
            addon_desc.append(f"{addon['addon_name']} x{qty}")

        batch = {'service_id': service['service_id'], 'service_name': s_name, 'category_id': category['category_id'], 
                 'weight': weight, 'loads': loads, 'price_per_unit': service['price_per_load'], 'subtotal': subtotal, 
                 'addons': final_addons, 'addon_text': ", ".join(addon_desc)}
        
        self.current_batches.append(batch)
        self.cart_tree.insert("", "end", values=(s_name, f"{weight}kg", f"₱{subtotal:,.2f}"))
        self.update_total()
        self.temp_addons = {}; self.applied_addons_lbl.config(text="Applied: None")
        self.service_cb.set('')

    def update_total(self):
        total = sum(b['subtotal'] for b in self.current_batches)
        self.total_var.set(f"Total: ₱{total:,.2f}")

    def submit_order(self):
        name = self.cust_name.get().strip(); email = self.cust_email_cb.get().strip()
        if not name or not self.current_batches: return messagebox.showwarning("Error", "Incomplete details.")
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to submit this order?"): return

        display_id = f"ORD-{int(time.time())}"; u_id = self.current_user['user_id'] if self.current_user else None
        try:
            t_id = self.db.execute_query("INSERT INTO Transactions (display_id, customer_name, customer_email, pickup_date, total_amount, created_by) VALUES (%s,%s,%s,%s,%s,%s)", 
                                       (display_id, name, email or None, self.pickup_date.get(), sum(b['subtotal'] for b in self.current_batches), u_id))
            for b in self.current_batches:
                b_id = self.db.execute_query("INSERT INTO Transaction_Batches (transaction_id, service_id, category_id, weight, load_count, price_per_unit, subtotal) VALUES (%s,%s,%s,%s,%s,%s,%s)", 
                                           (t_id, b['service_id'], b['category_id'], b['weight'], b['loads'], b['price_per_unit'], b['subtotal']))
                for a in b['addons']:
                    self.db.execute_query("INSERT INTO Batch_Addons (batch_id, addon_id, quantity, price, subtotal) VALUES (%s,%s,%s,%s,%s)", (b_id, a['addon_id'], a['quantity'], a['unit_price'], a['total_price']))
            
            messagebox.showinfo("Success", f"Order {display_id} saved!"); self.load_customer_emails(); self.clear_form()
        except Exception as e: messagebox.showerror("DB Error", str(e))

    def clear_form(self):
        self.cust_name.delete(0, tk.END); self.cust_email_cb.set(''); self.current_batches = []; self.order_weight = None
        for i in self.cart_tree.get_children(): self.cart_tree.delete(i)
        self.update_total(); self.order_id_var.set(f"ORD-{int(time.time())}")