import tkinter as tk
from tkinter import ttk, messagebox
from dbManager import DatabaseManager

class Config(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.db = DatabaseManager()
        self.current_user = None
        
        self.configure(padx=30, pady=30)
        
    def set_user(self, user):
        """Standard check for admin access."""
        self.current_user = user
        for widget in self.winfo_children():
            widget.destroy()

        if user and user['role'] == 'Admin':
            self.create_widgets()
            self.load_settings()
        else:
            tk.Label(self, text="Access Denied. Admins Only.", font=("Arial", 16), fg="red").pack(expand=True)

    def create_widgets(self):
        # --- Top Header & Action Bar ---
        top_bar = tk.Frame(self)
        top_bar.pack(fill="x", pady=(0, 20))

        # Save Button moved to Top Left
        tk.Button(top_bar, text="Save Configurations", bg="#27AE60", fg="white", 
                  font=("Arial", 10, "bold"), width=25, command=self.save_settings).pack(side="right")

        tk.Label(top_bar, text="System Configuration", font=("Helvetica", 18, "bold"), fg="#2C3E50").pack(side="left")

        # --- Gmail Setup ---
        gmail_frame = tk.LabelFrame(self, text="Gmail SMTP Setup", padx=15, pady=15)
        gmail_frame.pack(fill="x", pady=10)

        tk.Label(gmail_frame, text="Admin Gmail:").grid(row=0, column=0, sticky="e")
        self.email_ent = tk.Entry(gmail_frame, width=40)
        self.email_ent.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(gmail_frame, text="App Password:").grid(row=1, column=0, sticky="e")
        self.pass_ent = tk.Entry(gmail_frame, width=40, show="*")
        self.pass_ent.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(gmail_frame, text="Note: Use a 16-character Google App Password (no spaces).", 
                 font=("Arial", 8), fg="gray").grid(row=2, column=1, sticky="w")

        # --- Email Content ---
        content_frame = tk.LabelFrame(self, text="OTP Email Template", padx=15, pady=15)
        content_frame.pack(fill="both", expand=True, pady=10)

        tk.Label(content_frame, text="Subject:").pack(anchor="w")
        self.subject_ent = tk.Entry(content_frame, width=60)
        self.subject_ent.pack(fill="x", pady=(0, 10))

        tk.Label(content_frame, text="Body Content:").pack(anchor="w")
        tk.Label(content_frame, text="Use {otp} as a placeholder for the generated code.", 
                 font=("Arial", 8, "italic"), fg="#3498db").pack(anchor="w")
        
        self.body_txt = tk.Text(content_frame, height=6)
        self.body_txt.pack(fill="both", expand=True, pady=5)

        # --- Pickup Ready Content ---
        pickup_frame = tk.LabelFrame(self, text="Pickup Ready Email Template", padx=15, pady=15)
        pickup_frame.pack(fill="both", expand=True, pady=10)

        tk.Label(pickup_frame, text="Subject:").pack(anchor="w")
        self.pickup_subject_ent = tk.Entry(pickup_frame, width=60)
        self.pickup_subject_ent.pack(fill="x", pady=(0, 10))

        tk.Label(pickup_frame, text="Body Content:").pack(anchor="w")
        tk.Label(pickup_frame, text="Use {customer} and {order_id} as placeholders.", 
                 font=("Arial", 8, "italic"), fg="#3498db").pack(anchor="w")
        
        self.pickup_body_txt = tk.Text(pickup_frame, height=4)
        self.pickup_body_txt.pack(fill="both", expand=True, pady=5)

    def load_settings(self):
        """Fetch values from database and fill the form."""
        try:
            settings = self.db.fetch_all("SELECT * FROM system_config")
            data = {item['config_key']: item['config_value'] for item in settings}
            
            self.email_ent.insert(0, data.get('admin_email', ''))
            self.pass_ent.insert(0, data.get('gmail_app_password', ''))
            self.subject_ent.insert(0, data.get('otp_subject', ''))
            self.body_txt.insert("1.0", data.get('otp_body', ''))
            self.pickup_subject_ent.insert(0, data.get('pickup_ready_subject', ''))
            self.pickup_body_txt.insert("1.0", data.get('pickup_ready_body', ''))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {e}")

    def save_settings(self):
        email = self.email_ent.get().strip()
        pwd = self.pass_ent.get().strip()
        subject = self.subject_ent.get().strip()
        body = self.body_txt.get("1.0", tk.END).strip()
        pickup_subject = self.pickup_subject_ent.get().strip()
        pickup_body = self.pickup_body_txt.get("1.0", tk.END).strip()

        if not all([email, pwd, subject, body, pickup_subject, pickup_body]):
            messagebox.showwarning("Validation", "All configuration fields are required.")
            return

        try:
            queries = [
                ("UPDATE system_config SET config_value = %s WHERE config_key = 'admin_email'", (email,)),
                ("UPDATE system_config SET config_value = %s WHERE config_key = 'gmail_app_password'", (pwd,)),
                ("UPDATE system_config SET config_value = %s WHERE config_key = 'otp_subject'", (subject,)),
                ("UPDATE system_config SET config_value = %s WHERE config_key = 'otp_body'", (body,)),
                ("UPDATE system_config SET config_value = %s WHERE config_key = 'pickup_ready_subject'", (pickup_subject,)),
                ("UPDATE system_config SET config_value = %s WHERE config_key = 'pickup_ready_body'", (pickup_body,))
            ]
            
            for sql, params in queries:
                self.db.execute_query(sql, params)
            
            self.db.log_audit(self.current_user['user_id'], 'UPDATE', 'SystemConfig', 0, "Updated system email settings")
            messagebox.showinfo("Success", "System configurations updated successfully!")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))