import tkinter as tk
from tkinter import messagebox
import random
import datetime

class ForgotPasswordFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.target_email = None

        tk.Label(self, text="Password Recovery", font=("Arial", 20, "bold")).pack(pady=20)

        # Dynamic content container
        self.content_frame = tk.Frame(self)
        self.content_frame.pack(pady=10, padx=20)

        self.show_email_view()

    def show_email_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Enter your registered email address:", font=("Arial", 10)).pack()
        self.email_ent = tk.Entry(self.content_frame, width=35)
        self.email_ent.pack(pady=10)
        
        tk.Button(self.content_frame, text="Request OTP", bg="#3498db", fg="white", 
                  width=20, command=self.handle_otp_request).pack(pady=5)
        
        tk.Button(self.content_frame, text="Cancel", relief="flat", 
                  command=self.controller.show_login).pack()

    def show_reset_view(self):
        self.clear_content()
        tk.Label(self.content_frame, text=f"OTP sent to: {self.target_email}", fg="#27ae60").pack(pady=5)
        
        tk.Label(self.content_frame, text="6-Digit OTP:").pack(pady=(10, 0))
        self.otp_ent = tk.Entry(self.content_frame, width=15, justify="center", font=("Arial", 12))
        self.otp_ent.pack(pady=5)

        tk.Label(self.content_frame, text="New Password:").pack(pady=(10, 0))
        self.new_pass_ent = tk.Entry(self.content_frame, width=35, show="*")
        self.new_pass_ent.pack(pady=5)

        tk.Button(self.content_frame, text="Reset Password", bg="#2ecc71", fg="white", 
                  width=20, command=self.handle_password_reset).pack(pady=20)

    def handle_otp_request(self):
        email = self.email_ent.get().strip()
        if not email:
            messagebox.showwarning("Input Error", "Email is required.")
            return

        try:
            # Check if user exists
            query = "SELECT user_id FROM users WHERE email = %s AND status = 'Active'"
            user = self.controller.db.fetch_one(query, (email,))

            if user:
                user_id = user['user_id']
                otp = str(random.randint(100000, 999999))
                # Set expiry for 10 minutes from now
                expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)

                # Save OTP to the password_resets table
                sql = "INSERT INTO password_resets (user_id, otp_code, expiry) VALUES (%s, %s, %s)"
                self.controller.db.execute_query(sql, (user_id, otp, expiry))

                # DEBUG: In a real app, you'd send this via smtplib
                print(f"[SYSTEM] OTP for {email}: {otp}")
                
                self.target_email = email
                self.show_reset_view()
            else:
                messagebox.showerror("Not Found", "No active account associated with this email.")
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to process request: {e}")

    def handle_password_reset(self):
        otp = self.otp_ent.get().strip()
        new_pw = self.new_pass_ent.get().strip()

        if not otp or not new_pw:
            messagebox.showwarning("Input Error", "Please fill in all fields.")
            return

        try:
            # Validate OTP from the separate table
            sql = """
                SELECT r.reset_id, r.user_id FROM password_resets r
                JOIN users u ON r.user_id = u.user_id
                WHERE u.email = %s AND r.otp_code = %s AND r.is_used = FALSE AND r.expiry > NOW()
            """
            result = self.controller.db.fetch_one(sql, (self.target_email, otp))

            if result:
                reset_id = result['reset_id']
                user_id = result['user_id']
                # 1. Update User Password
                self.controller.db.execute_query("UPDATE users SET password = %s WHERE user_id = %s", (new_pw, user_id))
                # 2. Mark OTP as used
                self.controller.db.execute_query("UPDATE password_resets SET is_used = TRUE WHERE reset_id = %s", (reset_id,))
                
                messagebox.showinfo("Success", "Password updated! You can now log in.")
                self.controller.show_login()
            else:
                messagebox.showerror("Invalid", "Invalid or expired OTP.")
        except Exception as e:
            messagebox.showerror("Error", f"Reset failed: {e}")

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()