import tkinter as tk
from tkinter import messagebox
import random
import datetime
from EmailHelper import EmailHelper
from Validator import validate_password_complexity
import threading
import smtplib
from email.message import EmailMessage
class ForgotPasswordFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.target_email = None
        self.verified_user_id = None
        self.active_reset_id = None

        tk.Label(self, text="Password Recovery", font=("Arial", 20, "bold")).pack(pady=20)
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(pady=10, padx=20)
        self.show_email_view()

    def show_email_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Enter registered email:").pack()
        self.email_ent = tk.Entry(self.content_frame, width=35)
        self.email_ent.pack(pady=10)
        self.request_btn = tk.Button(self.content_frame, text="Request OTP", bg="#3498db", fg="white", width=20, command=self.handle_otp_request)
        self.request_btn.pack(pady=5)
        tk.Button(self.content_frame, text="Cancel", bg="#E74C3C", fg="white", width=20, command=self.controller.show_login, cursor="hand2").pack(pady=(10, 0))

    def handle_otp_request(self):
        email = self.email_ent.get().strip()
        if not email: return
        
        user = self.controller.db.fetch_one("SELECT user_id FROM users WHERE email = %s AND status = 'Active'", (email,))
        if not user:
            messagebox.showerror("Not Found", "Account not found.")
            return

        otp = str(random.randint(100000, 999999))
        expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
        self.controller.db.execute_query("INSERT INTO password_resets (user_id, otp_code, expiry) VALUES (%s, %s, %s)", (user['user_id'], otp, expiry))
        
        self.target_email = email
        self.request_btn.config(text="Sending...", state="disabled")
        self.update_idletasks() # Refresh UI to show "Sending..."

        # Synchronous send
        success, error = EmailHelper.send_email(
            db=self.controller.db,
            receiver=email,
            subject_key='otp_subject',
            body_key='otp_body',
            placeholders={'{otp}': otp}
        )

        if success:
            messagebox.showinfo("Success", f"OTP has been sent to {email}")
            self.show_otp_view()
        else:
            self.request_btn.config(text="Request OTP", state="normal")
            messagebox.showerror("Email Error", f"Failed: {error}")

    def show_otp_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text=f"OTP sent to: {self.target_email}", fg="#27ae60").pack(pady=5)
        self.otp_ent = tk.Entry(self.content_frame, width=15, justify="center", font=("Arial", 14))
        self.otp_ent.pack(pady=10)
        self.otp_ent.focus_set()
        tk.Button(self.content_frame, text="Verify Code", bg="#f39c12", fg="white", width=20, command=self.handle_otp_verification).pack(pady=(0, 10))
        tk.Button(self.content_frame, text="Cancel / Back to Login", bg="#E74C3C", fg="white", width=20, command=self.cancel_reset, cursor="hand2").pack(pady=(0, 5))

    def show_new_password_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Identity Verified", fg="#27ae60", font=("Arial", 10, "bold")).pack(pady=5)
        
        tk.Label(self.content_frame, text="New Password:").pack(pady=(10, 0))
        self.new_pass_ent = tk.Entry(self.content_frame, width=35, show="*")
        self.new_pass_ent.pack(pady=5)

        tk.Label(self.content_frame, text="Confirm New Password:").pack(pady=(10, 0))
        self.confirm_pass_ent = tk.Entry(self.content_frame, width=35, show="*")
        self.confirm_pass_ent.pack(pady=5)

        tk.Button(self.content_frame, text="Update Password", bg="#2ecc71", fg="white", width=20, command=self.handle_password_reset).pack(pady=(20, 10))
        tk.Button(self.content_frame, text="Cancel / Back to Login", bg="#E74C3C", fg="white", width=20, command=self.cancel_reset, cursor="hand2").pack(pady=(0, 5))

    def handle_otp_request(self):
        email = self.email_ent.get().strip()
        if not email: return
        try:
            user = self.controller.db.fetch_one("SELECT user_id FROM users WHERE email = %s AND status = 'Active'", (email,))
            if user:
                otp = str(random.randint(100000, 999999))
                expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
                self.controller.db.execute_query("INSERT INTO password_resets (user_id, otp_code, expiry) VALUES (%s, %s, %s)", (user['user_id'], otp, expiry))
                self.target_email = email
                self.request_btn.config(text="Sending...", state="disabled")
                threading.Thread(target=self.send_email_thread, args=(email, otp), daemon=True).start()
            else:
                messagebox.showerror("Not Found", "Account not found.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def cancel_reset(self):
        self.target_email = None
        self.verified_user_id = None
        self.active_reset_id = None
        self.show_email_view()
        if self.controller and hasattr(self.controller, "show_login"):
            self.controller.show_login()

    def send_email_thread(self, receiver, otp):
        try:
            # FETCH LIVE CONFIG FROM DB
            settings = self.controller.db.fetch_all("SELECT * FROM system_config")
            config = {item['config_key']: item['config_value'] for item in settings}
            
            admin_email = config.get('admin_email')
            app_password = config.get('gmail_app_password')
            subject = config.get('otp_subject')
            body = config.get('otp_body', '').replace("{otp}", otp)

            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = admin_email
            msg['To'] = receiver

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(admin_email, app_password)
                server.send_message(msg)
            
            self.after(0, self.show_otp_view)
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda m=error_msg: self.handle_email_error(m))

    def handle_email_error(self, err):
        self.request_btn.config(text="Request OTP", state="normal")
        messagebox.showerror("Email Error", f"Failed: {err}")

    def handle_otp_verification(self):
        sql = "SELECT r.reset_id, r.user_id FROM password_resets r JOIN users u ON r.user_id = u.user_id WHERE u.email = %s AND r.otp_code = %s AND r.is_used = FALSE AND r.expiry > NOW()"
        result = self.controller.db.fetch_one(sql, (self.target_email, self.otp_ent.get().strip()))
        if result:
            self.active_reset_id, self.verified_user_id = result['reset_id'], result['user_id']
            self.show_new_password_view()
        else: messagebox.showerror("Invalid", "Invalid or expired OTP.")

    def handle_password_reset(self):
        new_pw = self.new_pass_ent.get().strip()
        if new_pw != self.confirm_pass_ent.get().strip():
            messagebox.showerror("Error", "Passwords do not match.")
            return

        # Use the Validator for password complexity
        error_msg = validate_password_complexity(new_pw)
        if error_msg:
            messagebox.showwarning("Weak Password", error_msg)
            return

        try:
            self.controller.db.execute_query("UPDATE users SET password = %s WHERE user_id = %s", (new_pw, self.verified_user_id))
            self.controller.db.execute_query("UPDATE password_resets SET is_used = TRUE WHERE reset_id = %s", (self.active_reset_id,))
            messagebox.showinfo("Success", "Password updated!")
            self.show_email_view()
            self.controller.show_login()
        except Exception as e: messagebox.showerror("Error", str(e))

    def clear_content(self):
        for widget in self.content_frame.winfo_children(): widget.destroy()