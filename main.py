import tkinter as tk
from tkinter import messagebox

# Import all the modules we created
from Login import Login
from ForgotPassword import ForgotPasswordFrame
from Dashboard import Dashboard
from CreateOrder import CreateOrder
from Orders import Orders
from Transactions import Transactions
from Services import Services
from Reports import Reports
from UserManagement import UserManagement
from Settings import Config
from dbManager import DatabaseManager

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.title("Coco Bubble Wash - Management System")
        self.configure(bg="#ECF0F1")
        self.minsize(900, 600)
        
        # --- Launch at User's Current Resolution ---
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        
        try:
            self.state('zoomed')
        except Exception:
            pass 
        
        # State variables
        self.current_user = None
        self.frames = {}

        self.create_layout()
        self.init_frames()
        
        # Start the app by showing the login screen
        self.show_login()

    def create_layout(self):
        """Creates the base layout with a hidden sidebar and a main container."""
        # --- Sidebar (Hidden by default) ---
        self.sidebar = tk.Frame(self, bg="#2C3E50", width=220)
        self.sidebar.pack_propagate(False) 
        
        tk.Label(self.sidebar, text="COCO BUBBLE", font=("Helvetica", 16, "bold"), bg="#2C3E50", fg="white").pack(pady=(20, 0))
        tk.Label(self.sidebar, text="WASH", font=("Helvetica", 14), bg="#2C3E50", fg="#3498DB").pack(pady=(0, 20))
        
        self.user_info_lbl = tk.Label(self.sidebar, text="", bg="#2C3E50", fg="#BDC3C7", font=("Helvetica", 10))
        self.user_info_lbl.pack(pady=(0, 20))

        # Navigation Buttons
        self.nav_btns = []
        self.create_nav_button("Dashboard", "Dashboard")
        self.create_nav_button("Create Order", "CreateOrder")
        self.create_nav_button("Active Orders", "Orders")
        self.create_nav_button("Past Transactions", "Transactions")
        
        # Admin-only separator
        self.admin_lbl = tk.Label(self.sidebar, text="ADMINISTRATION", bg="#2C3E50", fg="#7F8C8D", font=("Helvetica", 8, "bold"))
        self.admin_lbl.pack(pady=(20, 5), anchor="w", padx=10)
        
        self.create_nav_button("Services & Add-ons", "Services", is_admin=True)
        self.create_nav_button("Reports", "Reports", is_admin=True)
        self.create_nav_button("User Management", "UserManagement", is_admin=True)
        
        # This string "Config" must match the class name in init_frames
        self.create_nav_button("System Config", "Config", is_admin=True) 

        tk.Button(self.sidebar, text="Logout", bg="#C0392B", fg="white", bd=0, font=("Helvetica", 10, "bold"),
                  command=self.logout, cursor="hand2").pack(side="bottom", fill="x", pady=20, padx=10)

        # --- Main Content Container ---
        self.container = tk.Frame(self, bg="#ECF0F1")
        self.container.pack(side="left", fill="both", expand=True)
        
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def create_nav_button(self, text, frame_name, is_admin=False):
        """Helper to create sidebar navigation buttons."""
        btn = tk.Button(self.sidebar, text=text, bg="#34495E", fg="white", bd=0, 
                        font=("Helvetica", 11), anchor="w", padx=20, pady=10,
                        activebackground="#2980B9", activeforeground="white", cursor="hand2",
                        command=lambda: self.show_frame(frame_name))
        btn.frame_name = frame_name 
        btn.is_admin = is_admin
        self.nav_btns.append(btn)
        btn.pack(fill="x", pady=2)

    def init_frames(self):
        """Initializes all the module views."""
        # 1. Check that Config is included in this list
        # 2. Check that in Config.py, the class is actually named 'Config'
        frame_classes = (
            Login, ForgotPasswordFrame, Dashboard, CreateOrder, Orders, 
            Transactions, Services, Reports, UserManagement, Config
        )

        for F in frame_classes:
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, page_name):
        """Brings the requested frame to the top."""
        if page_name not in self.frames:
            messagebox.showerror("Error", f"Frame '{page_name}' not found in internal registry.")
            return

        frame = self.frames[page_name]
        frame.tkraise()
        
        if hasattr(frame, 'set_user'):
            frame.set_user(self.current_user)

    def show_login(self):
        self.sidebar.pack_forget()
        self.container.pack(side="left", fill="both", expand=True)
        self.show_frame("Login")

    def show_forgot_password(self):
        self.sidebar.pack_forget()
        self.container.pack(side="left", fill="both", expand=True)
        self.show_frame("ForgotPasswordFrame")

    def show_dashboard(self, current_user):
        self.current_user = current_user
        self.user_info_lbl.config(text=f"{current_user['full_name']}\nRole: {current_user['role']}")
        
        if current_user['role'] == 'Admin':
            self.admin_lbl.pack(pady=(20, 5), anchor="w", padx=10) 
            for btn in self.nav_btns:
                if btn.is_admin:
                    btn.pack(fill="x", pady=2)
        else:
            self.admin_lbl.pack_forget()
            for btn in self.nav_btns:
                if btn.is_admin:
                    btn.pack_forget()

        self.container.pack_forget()
        self.sidebar.pack(side="left", fill="y")
        self.container.pack(side="left", fill="both", expand=True)
        self.show_frame("Dashboard")

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.current_user = None
            self.show_login()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()