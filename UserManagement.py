import tkinter as tk
from tkinter import ttk, messagebox
from dbManager import DatabaseManager

class UserManagement(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        self.current_user = None
        
        self.configure(padx=20, pady=20)
        self.access_denied_label = tk.Label(self, text="Admin Access Required", font=("Helvetica", 16, "bold"), fg="red")

    def set_user(self, user):
        """Sets the current logged-in user and verifies admin access."""
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
        # --- Header ---
        header_frame = tk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 15))
        tk.Label(header_frame, text="User Management", font=("Helvetica", 16, "bold"), fg="#2C3E50").pack(side="left")

        # --- Statistics Cards ---
        stats_frame = tk.Frame(self)
        stats_frame.pack(fill="x", pady=(0, 15))
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)

        self.total_users_var = tk.StringVar(value="0")
        self.active_users_var = tk.StringVar(value="0")
        self.admin_count_var = tk.StringVar(value="0")
        self.staff_count_var = tk.StringVar(value="0")

        self.create_stat_card(stats_frame, "Total Users", self.total_users_var, "#34495E", 0)
        self.create_stat_card(stats_frame, "Active Users", self.active_users_var, "#27AE60", 1)
        self.create_stat_card(stats_frame, "Total Admins", self.admin_count_var, "#8E44AD", 2)
        self.create_stat_card(stats_frame, "Total Staff", self.staff_count_var, "#2980B9", 3)

        # --- User Table ---
        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True)

        scroll_y = tk.Scrollbar(table_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        columns = ("id", "username", "full_name", "role", "status", "last_login")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tree.yview)

        self.tree.heading("id", text="User ID")
        self.tree.heading("username", text="Username")
        self.tree.heading("full_name", text="Full Name")
        self.tree.heading("role", text="Role")
        self.tree.heading("status", text="Status")
        self.tree.heading("last_login", text="Last Login")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("username", width=150)
        self.tree.column("full_name", width=250)
        self.tree.column("role", width=100, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("last_login", width=150, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

        # --- Actions ---
        actions_frame = tk.Frame(self)
        actions_frame.pack(fill="x", pady=(15, 0))

        tk.Button(actions_frame, text="Add New User", bg="#27AE60", fg="white", width=15, 
                  command=lambda: self.user_form()).pack(side="left", padx=(0, 10))
        tk.Button(actions_frame, text="Edit User Details", bg="#F39C12", fg="white", width=15,
                  command=lambda: self.user_form(is_edit=True)).pack(side="left", padx=10)

    def create_stat_card(self, parent, title, variable, color, col):
        card = tk.Frame(parent, bg=color, bd=0, padx=15, pady=15)
        card.grid(row=0, column=col, padx=5, sticky="nsew")
        tk.Label(card, text=title, font=("Helvetica", 10), bg=color, fg="white").pack(anchor="w")
        tk.Label(card, textvariable=variable, font=("Helvetica", 18, "bold"), bg=color, fg="white").pack(anchor="w", pady=(5, 0))

    def load_data(self):
        """Fetches user list and calculates statistics."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            users = self.db.fetch_all("SELECT * FROM Users ORDER BY role ASC, full_name ASC")
            
            # Populate Treeview
            for u in users:
                last_login = u['last_login'].strftime("%Y-%m-%d %H:%M") if u['last_login'] else "Never"
                self.tree.insert("", "end", values=(
                    u['user_id'], u['username'], u['full_name'], 
                    u['role'], u['status'], last_login
                ))

            # Update Statistics
            self.total_users_var.set(str(len(users)))
            self.active_users_var.set(str(sum(1 for u in users if u['status'] == 'Active')))
            self.admin_count_var.set(str(sum(1 for u in users if u['role'] == 'Admin')))
            self.staff_count_var.set(str(sum(1 for u in users if u['role'] == 'Staff')))

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load users:\n{e}", parent=self)

    def user_form(self, is_edit=False):
        selected_id = None
        user_data = None

        if is_edit:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select a user to edit.", parent=self)
                return
            selected_id = self.tree.item(selected[0])['values'][0]
            user_data = self.db.fetch_one("SELECT * FROM Users WHERE user_id = %s", (selected_id,))

        top = tk.Toplevel(self)
        top.title("Edit User" if is_edit else "Create New User")
        top.geometry("400x400")
        top.transient(self)
        top.grab_set()

        # Form Fields
        tk.Label(top, text="Username *").grid(row=0, column=0, sticky="e", padx=10, pady=10)
        username_ent = tk.Entry(top, width=30)
        username_ent.grid(row=0, column=1, pady=10)

        tk.Label(top, text="Full Name *").grid(row=1, column=0, sticky="e", padx=10, pady=10)
        fullname_ent = tk.Entry(top, width=30)
        fullname_ent.grid(row=1, column=1, pady=10)

        # Password logic: Required for new users, optional for editing
        pwd_label_text = "New Password" if is_edit else "Password *"
        tk.Label(top, text=pwd_label_text).grid(row=2, column=0, sticky="e", padx=10, pady=10)
        password_ent = tk.Entry(top, width=30, show="*")
        password_ent.grid(row=2, column=1, pady=10)
        
        if is_edit:
            tk.Label(top, text="(Leave blank to keep current)", font=("Helvetica", 8), fg="gray").grid(row=3, column=1, sticky="w")

        tk.Label(top, text="Role").grid(row=4, column=0, sticky="e", padx=10, pady=10)
        role_cb = ttk.Combobox(top, values=("Admin", "Staff"), state="readonly", width=15)
        role_cb.set("Staff")
        role_cb.grid(row=4, column=1, sticky="w", pady=10)

        tk.Label(top, text="Status").grid(row=5, column=0, sticky="e", padx=10, pady=10)
        status_cb = ttk.Combobox(top, values=("Active", "Inactive"), state="readonly", width=15)
        status_cb.set("Active")
        status_cb.grid(row=5, column=1, sticky="w", pady=10)

        # Pre-fill data if editing
        if is_edit and user_data:
            username_ent.insert(0, user_data['username'])
            fullname_ent.insert(0, user_data['full_name'])
            role_cb.set(user_data['role'])
            status_cb.set(user_data['status'])
            
            # Prevent self-deactivation to avoid locking out the system
            if user_data['user_id'] == self.current_user['user_id']:
                status_cb.config(state="disabled")
                role_cb.config(state="disabled")

        def save_user():
            username = username_ent.get().strip()
            fullname = fullname_ent.get().strip()
            password = password_ent.get().strip()
            role = role_cb.get()
            status = status_cb.get()

            if not username or not fullname:
                messagebox.showwarning("Validation Error", "Username and Full Name are required.", parent=top)
                return

            try:
                # Note: In a production application, passwords MUST be hashed (e.g., using bcrypt or hashlib)
                if is_edit:
                    if password:
                        query = "UPDATE Users SET username=%s, full_name=%s, password=%s, role=%s, status=%s WHERE user_id=%s"
                        params = (username, fullname, password, role, status, selected_id)
                    else:
                        query = "UPDATE Users SET username=%s, full_name=%s, role=%s, status=%s WHERE user_id=%s"
                        params = (username, fullname, role, status, selected_id)
                    
                    self.db.execute_query(query, params)
                    self.db.log_audit(self.current_user['user_id'], 'UPDATE', 'User', selected_id, f"Updated user profile for {username}")
                
                else:
                    if not password:
                        messagebox.showwarning("Validation Error", "Password is required for new users.", parent=top)
                        return
                        
                    # Check for existing username
                    existing = self.db.fetch_one("SELECT user_id FROM Users WHERE username = %s", (username,))
                    if existing:
                        messagebox.showerror("Error", "Username already exists. Please choose another.", parent=top)
                        return

                    query = "INSERT INTO Users (username, password, full_name, role, status) VALUES (%s, %s, %s, %s, %s)"
                    new_id = self.db.execute_query(query, (username, password, fullname, role, status))
                    self.db.log_audit(self.current_user['user_id'], 'CREATE', 'User', new_id, f"Created new user {username}")

                messagebox.showinfo("Success", "User details saved successfully.", parent=top)
                self.load_data()
                top.destroy()

            except Exception as e:
                messagebox.showerror("Database Error", f"An error occurred:\n{e}", parent=top)

        tk.Button(top, text="Save Details", bg="#2980B9", fg="white", width=20, command=save_user).grid(row=6, column=0, columnspan=2, pady=20)

# ==========================================
# Testing Block
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test - User Management (Admin)")
    root.geometry("900x600")
    
    app = UserManagement(parent=root)
    app.pack(expand=True, fill="both")
    
    # Simulate an Admin login
    app.set_user({'user_id': 1, 'role': 'Admin', 'full_name': 'Test Admin'}) 
    
    root.mainloop()