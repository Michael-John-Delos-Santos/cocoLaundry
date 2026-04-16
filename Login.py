import tkinter as tk
from tkinter import messagebox
from dbManager import DatabaseManager

class Login(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        
        self.configure(padx=40, pady=40)
        self.create_widgets()

    def create_widgets(self):
        # --- Header ---
        tk.Label(self, text="Coco Bubble Wash", font=("Helvetica", 24, "bold"), fg="#2C3E50").pack(pady=(10, 5))
        tk.Label(self, text="Laundry Management System", font=("Helvetica", 10), fg="#7F8C8D").pack(pady=(0, 20))
        tk.Label(self, text="Hello! Welcome back, please log in to continue.", font=("Helvetica", 12, "italic"), fg="#3498DB").pack(pady=(0, 30))

        # --- Form Container ---
        form_frame = tk.Frame(self)
        form_frame.pack()

        # Username
        tk.Label(form_frame, text="Username", font=("Helvetica", 10, "bold"), fg="#2C3E50").pack(anchor="w")
        self.username_entry = tk.Entry(form_frame, font=("Helvetica", 12), width=30)
        self.username_entry.pack(pady=(5, 15))

        # Password
        tk.Label(form_frame, text="Password", font=("Helvetica", 10, "bold"), fg="#2C3E50").pack(anchor="w")
        self.password_entry = tk.Entry(form_frame, font=("Helvetica", 12), width=30, show="*")
        self.password_entry.pack(pady=(5, 5))

        # --- Show Password Toggle ---
        self.show_pass_var = tk.BooleanVar(value=False)
        self.show_pass_btn = tk.Checkbutton(
            form_frame, 
            text="Show Password", 
            variable=self.show_pass_var,
            command=self.toggle_password,
            font=("Helvetica", 9),
            fg="#7F8C8D",
            cursor="hand2"
        )
        self.show_pass_btn.pack(anchor="w", pady=(0, 15))

        # Login Button
        self.login_btn = tk.Button(
            form_frame, 
            text="LOG IN", 
            font=("Helvetica", 12, "bold"), 
            bg="#3498DB", 
            fg="white",
            width=28,
            activebackground="#2980B9",
            cursor="hand2",
            command=self.handle_login
        )
        self.login_btn.pack(pady=10)
        
        # Forgot Password Link
        tk.Button(
            form_frame, 
            text="Forgot Password?", 
            font=("Helvetica", 10, "underline"), 
            fg="#3498DB", 
            bg=self.cget("bg"),
            bd=0,
            cursor="hand2",
            activeforeground="#2980B9",
            command=lambda: self.controller.show_forgot_password()
        ).pack(pady=5)
        
        self.password_entry.bind('<Return>', lambda event: self.handle_login())
        self.username_entry.bind('<Return>', lambda event: self.handle_login())

    def toggle_password(self):
        """Switches the password entry between hidden and visible."""
        if self.show_pass_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password.", parent=self)
            return

        try:
            query = "SELECT user_id, username, full_name, role, status FROM Users WHERE username = %s AND password = %s"
            user = self.db.fetch_one(query, (username, password))

            if user:
                if user['status'] == 'Inactive':
                    messagebox.showerror("Access Denied", "Your account is inactive.", parent=self)
                    return

                # Update last login
                self.db.execute_query("UPDATE Users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s", (user['user_id'],))
                self.db.log_audit(user['user_id'], 'LOGIN', 'User', user['user_id'], f"Successful login")

                # Clear entries
                self.username_entry.delete(0, tk.END)
                self.password_entry.delete(0, tk.END)
                self.show_pass_var.set(False)
                self.password_entry.config(show="*")

                if self.controller:
                    self.controller.show_dashboard(current_user=user)
            else:
                messagebox.showerror("Login Failed", "Invalid username or password.", parent=self)
                
        except Exception as e:
            messagebox.showerror("System Error", f"Database connection error:\n{e}", parent=self)