import tkinter as tk
from tkinter import ttk, messagebox
from dbManager import DatabaseManager
from Validator import validate_password_complexity

class UserManagement(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        self.current_user = None
        self.configure(padx=20, pady=20)

    def set_user(self, user):
        self.current_user = user
        for widget in self.winfo_children(): widget.destroy()
        if user and user['role'] == 'Admin':
            self.create_widgets()
            self.load_data()
        else:
            tk.Label(self, text="Admin Access Required", fg="red", font=("Arial", 14)).pack(expand=True)

    def create_widgets(self):
        header_frame = tk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 15))
        tk.Label(header_frame, text="User Management", font=("Helvetica", 16, "bold"), fg="#2C3E50").pack(side="left")

        stats_frame = tk.Frame(self)
        stats_frame.pack(fill="x", pady=(0, 15))
        for i in range(4): stats_frame.columnconfigure(i, weight=1)

        self.total_users_var = tk.StringVar(value="0")
        self.active_users_var = tk.StringVar(value="0")
        self.admin_count_var = tk.StringVar(value="0")
        self.staff_count_var = tk.StringVar(value="0")

        self.create_stat_card(stats_frame, "Total Users", self.total_users_var, "#34495E", 0)
        self.create_stat_card(stats_frame, "Active Users", self.active_users_var, "#27AE60", 1)
        self.create_stat_card(stats_frame, "Total Admins", self.admin_count_var, "#8E44AD", 2)
        self.create_stat_card(stats_frame, "Total Staff", self.staff_count_var, "#2980B9", 3)

        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True)
        columns = ("id", "username", "full_name", "role", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns: self.tree.heading(col, text=col.replace("_", " ").title())
        self.tree.pack(fill="both", expand=True)

        actions_frame = tk.Frame(self)
        actions_frame.pack(fill="x", pady=(15, 0))
        tk.Button(actions_frame, text="Add New User", bg="#27AE60", fg="white", width=15, command=lambda: self.user_form()).pack(side="left", padx=(0, 10))
        tk.Button(actions_frame, text="Edit Details", bg="#F39C12", fg="white", width=15, command=lambda: self.user_form(is_edit=True)).pack(side="left", padx=10)

    def create_stat_card(self, parent, title, variable, color, col):
        card = tk.Frame(parent, bg=color, bd=0, padx=15, pady=15)
        card.grid(row=0, column=col, padx=5, sticky="nsew")
        tk.Label(card, text=title, font=("Helvetica", 10), bg=color, fg="white").pack(anchor="w")
        tk.Label(card, textvariable=variable, font=("Helvetica", 18, "bold"), bg=color, fg="white").pack(anchor="w", pady=(5, 0))

    def load_data(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        try:
            users = self.db.fetch_all("SELECT * FROM users ORDER BY role ASC")
            for u in users:
                self.tree.insert("", "end", values=(u['user_id'], u['username'], u['full_name'], u['role'], u['status']))
            self.total_users_var.set(str(len(users)))
            self.active_users_var.set(str(sum(1 for u in users if u['status'] == 'Active')))
            self.admin_count_var.set(str(sum(1 for u in users if u['role'] == 'Admin')))
            self.staff_count_var.set(str(sum(1 for u in users if u['role'] == 'Staff')))
        except Exception as e: messagebox.showerror("Error", str(e))

    def user_form(self, is_edit=False):
        selected_id = None
        user_data = None
        if is_edit:
            selected = self.tree.selection()
            if not selected: return
            selected_id = self.tree.item(selected[0])['values'][0]
            user_data = self.db.fetch_one("SELECT * FROM users WHERE user_id = %s", (selected_id,))

        top = tk.Toplevel(self)
        top.title("User Details Form")
        top.geometry("400x500")
        top.grab_set()

        tk.Label(top, text="Username").pack(pady=(10,0))
        u_ent = tk.Entry(top); u_ent.pack()
        if is_edit: u_ent.insert(0, user_data['username'])

        tk.Label(top, text="Full Name").pack(pady=(10,0))
        fn_ent = tk.Entry(top); fn_ent.pack()
        if is_edit: fn_ent.insert(0, user_data['full_name'])

        tk.Label(top, text="Email").pack(pady=(10,0))
        e_ent = tk.Entry(top); e_ent.pack()
        if is_edit: e_ent.insert(0, user_data.get('email') or "")

        tk.Label(top, text="Password").pack(pady=(10,0))
        p_ent = tk.Entry(top, show="*"); p_ent.pack()

        tk.Label(top, text="Role").pack(pady=(10,0))
        r_cb = ttk.Combobox(top, values=("Admin", "Staff"))
        r_cb.pack(); r_cb.set(user_data['role'] if is_edit else "Staff")

        tk.Label(top, text="Status").pack(pady=(10,0))
        s_cb = ttk.Combobox(top, values=("Active", "Inactive"))
        s_cb.pack(); s_cb.set(user_data['status'] if is_edit else "Active")

        def save():
            pwd = p_ent.get().strip()
            
            # Constraint check
            if not is_edit or (is_edit and pwd):
                error_msg = validate_password_complexity(pwd)
                if error_msg:
                    messagebox.showwarning("Weak Password", error_msg, parent=top)
                    return
                else:
                    # Optional success message specifically for the password check
                    messagebox.showinfo("Success", "Password meets security requirements.", parent=top)

            try:
                if is_edit:
                    if pwd:
                        self.db.execute_query("UPDATE users SET username=%s, full_name=%s, email=%s, password=%s, role=%s, status=%s WHERE user_id=%s",
                                            (u_ent.get(), fn_ent.get(), e_ent.get(), pwd, r_cb.get(), s_cb.get(), selected_id))
                    else:
                        self.db.execute_query("UPDATE users SET username=%s, full_name=%s, email=%s, role=%s, status=%s WHERE user_id=%s",
                                            (u_ent.get(), fn_ent.get(), e_ent.get(), r_cb.get(), s_cb.get(), selected_id))
                else:
                    self.db.execute_query("INSERT INTO users (username, password, full_name, email, role, status) VALUES (%s, %s, %s, %s, %s, %s)",
                                        (u_ent.get(), pwd, fn_ent.get(), e_ent.get(), r_cb.get(), s_cb.get()))
                
                messagebox.showinfo("Saved", "User details updated successfully.", parent=top)
                self.load_data()
                top.destroy()
            except Exception as e: messagebox.showerror("Error", str(e), parent=top)

        tk.Button(top, text="Save User", bg="#2980B9", fg="white", width=20, command=save).pack(pady=30)