import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageTk
import serial
import serial.tools.list_ports
import threading
import time
import json
import sqlite3  # <--- ADDED SQLITE
from datetime import datetime
import csv
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Set appearance mode and color theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class AttemptDanceUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AttemptDance - Automatic Temperature Attendance")

        # Start in full screen
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.resizable(False, False)

        # Track window state
        self.is_fullscreen = True

        # Bind keys
        self.bind('<Escape>', self.exit_application)
        self.bind('<F11>', self.toggle_fullscreen)

        # Serial connection variables
        self.serial_connection = None
        self.is_connected = False
        self.data_buffer = ""
        self.reconnect_flag = False

        # Data storage
        self.attendance_data = []
        self.temperature_history = []
        self.rfid_users = {}  # We keep this for fast UI lookups

        # Default settings
        self.fever_threshold = 37.5
        self.auto_save = True

        # Initialize Database
        self.init_database()  # <--- NEW DATABASE INIT

        self.setup_ui()
        self.load_existing_data()  # Modified to load from DB
        self.load_user_database()  # Modified to load from DB
        self.setup_serial_monitor()

    def init_database(self):
        """Initialize SQLite Database and Tables"""
        try:
            self.conn = sqlite3.connect('attemptdance.db', check_same_thread=False)
            self.cursor = self.conn.cursor()

            # Create Users Table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    rfid_uid TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    department TEXT,
                    email TEXT
                )
            ''')

            try:
                self.cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
                self.conn.commit()
            except:
                pass

            # Create Attendance Table
            # We include name/dept here too so historical logs stay valid even if user changes
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    rfid_uid TEXT,
                    name TEXT,
                    department TEXT,
                    temperature TEXT,
                    status TEXT,
                    is_synced INTEGER DEFAULT 0
                )
            ''')
            self.conn.commit()
            print("Database initialized successfully")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to init database: {e}")

    def toggle_fullscreen(self, event=None):
        """Toggle between full screen and zoomed mode"""
        if self.is_fullscreen:
            self.attributes('-fullscreen', False)
            self.state('zoomed')
            self.attributes('-topmost', False)
            self.is_fullscreen = False
        else:
            self.state('normal')
            self.attributes('-fullscreen', True)
            self.attributes('-topmost', True)
            self.is_fullscreen = True

    def exit_application(self, event=None):
        """Exit the application with confirmation"""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            if hasattr(self, 'conn'):
                self.conn.close()  # Close DB connection
            self.destroy()

    def setup_ui(self):
        self.setup_background()
        self.setup_navigation()
        self.setup_dashboard_section()
        self.setup_log_section()
        self.setup_user_management_section()
        self.setup_settings_section()
        self.setup_stats_section()
        self.show_section('dashboard')

    # [BACKGROUND AND NAVIGATION CODE REMAINS EXACTLY THE SAME]
    def setup_background(self):
        try:
            bg_img1 = ctk.CTkImage(light_image=Image.open("Bg1.png"), size=(1920, 1080))
            self.bg_label = ctk.CTkLabel(self, image=bg_img1, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            self.bg_label = ctk.CTkLabel(self, text="", fg_color="#194f59")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.connection_status1 = ctk.CTkLabel(self, text="Disconnected", text_color="white",
                                               font=("Arial", 27, "bold"), fg_color='#4692a0', bg_color='#4692a0')
        self.connection_status1.place(x=340, y=1017)

        self.status_display1 = ctk.CTkLabel(self, text="Ready", text_color="white", font=("Arial", 27, "bold"),
                                            fg_color='#4692a0', bg_color='#4692a0')
        self.status_display1.place(x=905, y=1017)

    def setup_navigation(self):
        nav_frame = ctk.CTkFrame(self, width=400, height=500, fg_color="#194f59", bg_color='#194f59', corner_radius=40)
        nav_frame.place(x=1500, y=250)

        self.dashboard_btn = ctk.CTkButton(nav_frame, text="Dashboard", command=lambda: self.show_section('dashboard'),
                                           width=350, height=70, font=ctk.CTkFont(size=30, weight="bold"),
                                           corner_radius=20, text_color='black', fg_color='#fcd016',
                                           hover_color='#806400', border_width=5, border_color='#c6a220')
        self.dashboard_btn.place(relx=0.5, y=70, anchor='center')

        self.log_btn = ctk.CTkButton(nav_frame, text="Attendance Log", command=lambda: self.show_section('log'),
                                     width=350, height=70, font=ctk.CTkFont(size=30, weight="bold"), corner_radius=20,
                                     text_color='black', fg_color='#fcd016', hover_color='#806400', border_width=5,
                                     border_color='#c6a220')
        self.log_btn.place(relx=0.5, y=160, anchor='center')

        self.users_btn = ctk.CTkButton(nav_frame, text="User Management", command=lambda: self.show_section('users'),
                                       width=350, height=70, font=ctk.CTkFont(size=30, weight="bold"), corner_radius=20,
                                       text_color='black', fg_color='#fcd016', hover_color='#806400', border_width=5,
                                       border_color='#c6a220')
        self.users_btn.place(relx=0.5, y=250, anchor='center')

        self.settings_btn = ctk.CTkButton(nav_frame, text="Settings", command=lambda: self.show_section('settings'),
                                          width=350, height=70, font=ctk.CTkFont(size=30, weight="bold"),
                                          corner_radius=20, text_color='black', fg_color='#fcd016',
                                          hover_color='#806400', border_width=5, border_color='#c6a220')
        self.settings_btn.place(relx=0.5, y=340, anchor='center')

        self.stats_btn = ctk.CTkButton(nav_frame, text="Statistics", command=lambda: self.show_section('stats'),
                                       width=350, height=70, font=ctk.CTkFont(size=30, weight="bold"), corner_radius=20,
                                       text_color='black', fg_color='#fcd016', hover_color='#806400', border_width=5,
                                       border_color='#c6a220')
        self.stats_btn.place(relx=0.5, y=430, anchor='center')

    # [DASHBOARD SETUP REMAINS SAME]
    def setup_dashboard_section(self):
        self.dashboard_frame = ctk.CTkFrame(self, width=1100, height=680, fg_color="white", bg_color="#194f59",
                                            corner_radius=20)
        connection_frame = ctk.CTkFrame(self.dashboard_frame, width=1090, height=240, fg_color="#5fafea",
                                        bg_color="white", corner_radius=15)
        connection_frame.place(x=5, y=5)
        (ctk.CTkLabel(connection_frame, text="ESP-32 CONNECTION", font=("Intro Rust Base", 30, "bold"),
                      text_color='white').place(relx=0.5, y=25, anchor='center'))
        ctk.CTkLabel(connection_frame, text="COM Port:", font=("Arial", 20, "bold"), text_color='white').place(x=20,
                                                                                                               y=68)

        self.port_combobox = ctk.CTkComboBox(connection_frame, values=self.get_available_ports(), width=180, height=40,
                                             font=("Arial", 20, "bold"), text_color='black', fg_color='white',
                                             button_color='white', border_color='white', border_width=1,
                                             button_hover_color='#606060', dropdown_fg_color='white',
                                             dropdown_text_color='black', dropdown_hover_color='light gray')
        self.port_combobox.place(x=130, y=60)

        self.refresh_ports_btn = ctk.CTkButton(connection_frame, text="Refresh Ports", command=self.refresh_ports,
                                               width=180, height=40, font=("Arial", 20, "bold"), text_color='white',
                                               fg_color='#044ec3', bg_color='#5fafea')
        self.refresh_ports_btn.place(x=320, y=60)

        self.connect_btn = ctk.CTkButton(connection_frame, text="Connect", command=self.connect_serial,
                                         fg_color="green", hover_color="dark green", width=180, height=40,
                                         font=("Arial", 20, "bold"), text_color='white')
        self.connect_btn.place(x=680, y=60)

        self.disconnect_btn = ctk.CTkButton(connection_frame, text="Disconnect", command=self.disconnect_serial,
                                            fg_color="red", hover_color="dark red", width=180, height=40,
                                            font=("Arial", 20, "bold"), text_color='white', state="disabled")
        self.disconnect_btn.place(x=880, y=60)

        self.connection_status = ctk.CTkLabel(connection_frame, text="🔴 Disconnected", text_color="red",
                                              font=("Arial", 20, "bold"))
        self.connection_status.place(relx=0.5, y=130, anchor='center')

        ctk.CTkLabel(connection_frame, text="Debug Console:", font=("Arial", 20, "bold"), text_color='white').place(
            x=20, y=130)

        self.debug_text = ctk.CTkTextbox(connection_frame, width=1040, height=75, corner_radius=10)
        self.debug_text.place(x=20, y=160)
        self.debug_text.insert("1.0", "System started. Database Ready.\n")
        self.debug_text.configure(state="disabled")

        main_display_frame = ctk.CTkFrame(self.dashboard_frame, width=1090, height=425, corner_radius=15,
                                          bg_color='white', fg_color='#557f87')
        main_display_frame.place(x=5, y=250)

        current_scan_frame = ctk.CTkFrame(main_display_frame, width=520, height=400, corner_radius=20,
                                          bg_color='#557f87', fg_color='#557f87')
        current_scan_frame.place(x=10, y=5)

        ctk.CTkLabel(current_scan_frame, text="Current Scan", font=("Arial", 35, "bold"), text_color='white').place(
            x=20, y=10)
        self.user_display = ctk.CTkLabel(current_scan_frame, text="Waiting for scan...", font=("Arial", 20),
                                         text_color='white')
        self.user_display.place(x=20, y=60)
        self.temp_display = ctk.CTkLabel(current_scan_frame, text="--.- °C", font=ctk.CTkFont(size=48, weight="bold"),
                                         text_color="white")
        self.temp_display.place(x=200, y=100)
        self.status_display = ctk.CTkLabel(current_scan_frame, text="Ready", font=ctk.CTkFont(size=30, weight="bold"),
                                           text_color="white", corner_radius=5, width=180, height=50,
                                           fg_color='#73bd00')
        self.status_display.place(x=180, y=170)
        self.rfid_display = ctk.CTkLabel(current_scan_frame, text="RFID: --", font=ctk.CTkFont(size=20),
                                         text_color="light blue")
        self.rfid_display.place(x=20, y=260)

        stats_frame = ctk.CTkFrame(main_display_frame, width=520, height=400, corner_radius=20, border_width=2,
                                   border_color='white')
        stats_frame.place(x=540, y=10)

        ctk.CTkLabel(stats_frame, text="Today's Summary", font=ctk.CTkFont(size=20, weight="bold")).place(x=20, y=20)
        self.total_scans_label = self.create_stat_label(stats_frame, "Total Scans", "0", 70)
        self.normal_temp_label = self.create_stat_label(stats_frame, "Normal", "0", 150)
        self.fever_cases_label = self.create_stat_label(stats_frame, "Fever Cases", "0", 230)
        self.avg_temp_label = self.create_stat_label(stats_frame, "Avg Temp", "-- °C", 310)

    def create_stat_label(self, parent, title, value, y_pos):
        frame = ctk.CTkFrame(parent, width=480, height=60)
        frame.place(x=20, y=y_pos)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=12)).place(x=20, y=10)
        label = ctk.CTkLabel(frame, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color="light blue")
        label.place(x=20, y=35)
        return label

    # [LOG SECTION REMAINS SAME]
    def setup_log_section(self):
        self.log_frame = ctk.CTkFrame(self, width=1100, height=700, fg_color="white", bg_color="#194f59",
                                      corner_radius=20)
        controls_frame = ctk.CTkFrame(self.log_frame, width=1090, height=60, fg_color="#5fafea", bg_color="white",
                                      corner_radius=15)
        controls_frame.place(x=5, y=5)

        self.search_entry = ctk.CTkEntry(controls_frame, placeholder_text="Search by RFID, Name, or Department...",
                                         width=320, height=40, font=("Arial", 20, "bold"), corner_radius=15,
                                         text_color='black', fg_color='white')
        self.search_entry.place(x=10, y=10)
        self.search_entry.bind("<KeyRelease>", self.search_log)

        ctk.CTkLabel(controls_frame, text="Sort by:", font=("Arial", 20, "bold"), text_color='white').place(x=335, y=15)
        self.sort_combobox = ctk.CTkComboBox(controls_frame,
                                             values=["Show Today (Default)", "Show All History","Timestamp (Newest)", "Timestamp (Oldest)", "Name (A-Z)",
                                                     "Name (Z-A)", "Temperature (High-Low)", "Temperature (Low-High)",
                                                     "Status", "Department"], width=200, height=40,
                                             font=("Arial", 14, "bold"), corner_radius=10, text_color='black',
                                             fg_color='white', button_color='#044ec3', button_hover_color='#00296a',
                                             dropdown_fg_color='white', dropdown_text_color='black',
                                             dropdown_hover_color='light gray')
        self.sort_combobox.set("Show Today (Default)")
        self.sort_combobox.place(x=420, y=10)
        self.sort_combobox.configure(command=self.sort_log)

        self.clear_log_btn = ctk.CTkButton(controls_frame, text="Clear Log", command=self.clear_log, fg_color="orange",
                                           hover_color="#ff5806", width=140, height=40, font=("Arial", 16, "bold"),
                                           text_color='white', corner_radius=10, border_width=2, border_color='black')
        self.clear_log_btn.place(x=630, y=10)

        self.export_btn = ctk.CTkButton(controls_frame, text="Export CSV", command=self.export_data, width=140,
                                        height=40, font=("Arial", 16, "bold"), text_color='white', corner_radius=10,
                                        fg_color='#044ec3', bg_color='#5fafea', hover_color='#00296a', border_width=2,
                                        border_color='black')
        self.export_btn.place(x=780, y=10)

        self.refresh_log_btn = ctk.CTkButton(controls_frame, text="Refresh", command=self.refresh_log, width=140,
                                             height=40, font=("Arial", 16, "bold"), text_color='white',
                                             corner_radius=10, fg_color='green', hover_color='dark green',
                                             border_width=2, border_color='black')
        self.refresh_log_btn.place(x=930, y=10)

        table_frame = ctk.CTkFrame(self.log_frame, width=1090, height=625, corner_radius=20, bg_color='white',
                                   fg_color='#557f87')
        table_frame.place(x=5, y=70)

        columns = ("Timestamp", "RFID", "Name", "Department", "Temperature", "Status")
        self.log_tree = ttk.Treeview(self.log_frame, columns=columns, show="headings", height=25)

        for col in columns:
            self.log_tree.heading(col, text=col)
            if col == "Timestamp":
                self.log_tree.column(col, width=150)
            elif col == "RFID":
                self.log_tree.column(col, width=100)
            elif col == "Name":
                self.log_tree.column(col, width=280)
            elif col == "Department":
                self.log_tree.column(col, width=140)
            elif col == "Temperature":
                self.log_tree.column(col, width=110)
            elif col == "Status":
                self.log_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(self.log_frame, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)
        self.log_tree.place(x=20, y=100, width=1040, height=580)
        scrollbar.place(x=1060, y=100, height=580)

    def sort_log(self, event=None):
        """Unified function for Filtering and Sorting"""
        sort_option = self.sort_combobox.get()
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 1. Start with ALL data from memory
        filtered_data = list(self.attendance_data)

        # 2. FILTER LOGIC: "Show Today" is stricter
        if sort_option == "Show Today (Default)":
            # Only keep rows that start with today's date
            filtered_data = [row for row in filtered_data if row[0].startswith(today_str)]
            filtered_data.sort(key=lambda x: x[0], reverse=True)

        elif sort_option == "Show All History":
            # No filtering, just default sort
            filtered_data.sort(key=lambda x: x[0], reverse=True)

        # 3. SORT LOGIC
        elif sort_option == "Name (A-Z)":
            filtered_data.sort(key=lambda x: x[2].lower())  # Name is index 2
        elif sort_option == "Name (Z-A)":
            filtered_data.sort(key=lambda x: x[2].lower(), reverse=True)
        elif sort_option == "Timestamp (Newest)":
            filtered_data.sort(key=lambda x: x[0], reverse=True)
        elif sort_option == "Timestamp (Oldest)":
            filtered_data.sort(key=lambda x: x[0])
        elif sort_option == "Temperature (High-Low)":
            filtered_data.sort(key=lambda x: float(x[4].replace(' °C', '').replace('C', '')), reverse=True)
        elif sort_option == "Temperature (Low-High)":
            filtered_data.sort(key=lambda x: float(x[4].replace(' °C', '').replace('C', '')))
        elif sort_option == "Status":
            filtered_data.sort(key=lambda x: x[5])
        elif sort_option == "Department":
            filtered_data.sort(key=lambda x: x[3])
        
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)

        for row in filtered_data:
            self.log_tree.insert("", "end", values=row)

        # 5. Update the "Stats" box to reflect what we are currently seeing
        self.update_stats_for_view(filtered_data)

    def refresh_log(self):
        for item in self.log_tree.get_children(): self.log_tree.delete(item)
        for entry in self.attendance_data: self.log_tree.insert("", "end", values=entry)
        if self.attendance_data: self.sort_log()
        self.sort_log()

    def update_stats_for_view(self, data_list):
        if not hasattr(self, 'total_scans_label'): return

        total = len(data_list)
        fever = sum(1 for x in data_list if "FEVER" in str(x[5]).upper())
        normal = total - fever

        self.total_scans_label.configure(text=str(total))
        self.fever_cases_stat.configure(text=str(fever))
        self.normal_cases_stat.configure(text=str(normal))

    def setup_user_management_section(self):
        self.users_frame = ctk.CTkFrame(self, width=1100, height=700, fg_color="white", bg_color="#194f59",
                                        corner_radius=20)
        add_frame = ctk.CTkFrame(self.users_frame, width=1090, height=255, fg_color="#5fafea", bg_color="white",
                                 corner_radius=15)
        add_frame.place(x=5, y=5)

        ctk.CTkLabel(add_frame, text="Add New User", font=("Intro Rust Base", 30, "bold"), text_color='white').place(
            relx=0.5, y=25, anchor='center')
        ctk.CTkLabel(add_frame, text="RFID UID:", font=("Arial", 20, "bold"), text_color='white').place(x=20, y=57)
        self.new_rfid_entry = ctk.CTkEntry(add_frame, placeholder_text="Enter RFID UID...", width=360, height=40,
                                           font=("Arial", 20, "bold"), corner_radius=15, text_color='black',
                                           fg_color='white')
        self.new_rfid_entry.place(x=150, y=50)

        ctk.CTkLabel(add_frame, text="Name:", font=("Arial", 20, "bold"), text_color='white').place(x=20, y=110)
        self.new_name_entry = ctk.CTkEntry(add_frame, placeholder_text="Last Name, First Name MI.", width=360,
                                           height=40, font=("Arial", 20, "bold"), corner_radius=15, text_color='black',
                                           fg_color='white')
        self.new_name_entry.place(x=150, y=100)

        ctk.CTkLabel(add_frame, text="Email:", font=("Arial", 20, "bold"), text_color='white').place(x=20, y=158)
        self.new_email_entry = ctk.CTkEntry(add_frame, placeholder_text="Parent/Guardian Email...", width=360,
                                            height=40, font=("Arial", 20, "bold"), corner_radius=15, text_color='black',
                                            fg_color='white')
        self.new_email_entry.place(x=150, y=150)

        ctk.CTkLabel(add_frame, text="Department:", font=("Arial", 20, "bold"), text_color='white').place(x=20, y=206)
        department_options = ["BSCPE-1D", "BSCPE-2D", "BSCPE-3D", "BSCPE-4D"]
        self.new_dept_combobox = ctk.CTkComboBox(add_frame, values=department_options, width=200, height=40,
                                                 font=("Arial", 20, "bold"), corner_radius=15, text_color='black',
                                                 fg_color='white', button_color='gray', button_hover_color='dark gray',
                                                 dropdown_fg_color='white', dropdown_text_color='black')
        self.new_dept_combobox.set("BSCPE-1D")
        self.new_dept_combobox.place(x=150, y=200)

        add_btn = ctk.CTkButton(add_frame, text="Add User", command=self.add_user, fg_color="green", height=40,
                                font=("Arial", 20, "bold"), text_color='White', corner_radius=15, border_width=2,
                                border_color='black')
        add_btn.place(x=370, y=200)

        ctk.CTkLabel(add_frame, text="Search & Delete User:", font=("Arial", 20, "bold"), text_color='white').place(
            x=700, y=65)
        self.search_user_entry = ctk.CTkEntry(add_frame, placeholder_text="Search by RFID or Name...", width=360,
                                              height=40, font=("Arial", 20, "bold"), corner_radius=15,
                                              text_color='black', fg_color='white')
        self.search_user_entry.place(x=700, y=100)

        self.search_user_btn = ctk.CTkButton(add_frame, text="Search", command=self.search_user, height=40, width=170,
                                             font=("Arial", 20, "bold"), text_color='White', corner_radius=15,
                                             border_width=2, border_color='black')
        self.search_user_btn.place(x=700, y=150)

        self.delete_user_btn = ctk.CTkButton(add_frame, text="Delete User", command=self.delete_user, width=170,
                                             fg_color="red", hover_color="dark red", height=40,
                                             font=("Arial", 20, "bold"), text_color='White', corner_radius=15,
                                             border_width=2, border_color='black', state="disabled")
        self.delete_user_btn.place(x=890, y=150)

        list_frame = ctk.CTkFrame(self.users_frame, width=1090, height=430, corner_radius=20, bg_color='white',
                                  fg_color='#557f87')
        list_frame.place(x=5, y=265)

        ctk.CTkLabel(list_frame, text="Registered Users", font=("Arial", 20, "bold"), text_color='white').place(x=20,
                                                                                                                y=20)

        columns = ("RFID", "Name", "Department","Parent/Guardian Email")
        self.users_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.users_tree.heading(col, text=col)
            if col == "RFID":
                self.users_tree.column(col, width=150, anchor='center')
            elif col == "Name":
                self.users_tree.column(col, width=300, anchor='center')
            elif col == "Parent/Guardian Email":
                self.users_tree.column(col, width=300, anchor='center')
            else:
                self.users_tree.column(col, width=200, anchor='center')

        style = ttk.Style()
        style.configure("Treeview", font=('Arial', 14), rowheight=30, background="white", fieldbackground="white",
                        foreground="black")
        style.configure("Treeview.Heading", font=('Arial', 16, 'bold'), background='#5fafea', foreground='black')

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        self.users_tree.place(x=20, y=60, width=1040, height=350)
        scrollbar.place(x=1060, y=60, height=350)
        self.users_tree.bind('<<TreeviewSelect>>', self.on_user_select)
        self.refresh_users_list()

    def search_user(self):
        search_term = self.search_user_entry.get().strip().lower()
        if not search_term:
            messagebox.showwarning("Search", "Please enter RFID or Name to search")
            return

        for item in self.users_tree.selection():
            self.users_tree.selection_remove(item)

        found_item = None

        for item in self.users_tree.get_children():
            values = self.users_tree.item(item)['values']

            current_rfid = str(values[0]).lower()
            current_name = str(values[1]).lower()

            if search_term in current_rfid or search_term in current_name:
                found_item = item
                break

        if found_item:
            self.users_tree.selection_set(found_item)
            self.users_tree.focus(found_item)

            self.users_tree.see(found_item)

            self.delete_user_btn.configure(state="normal")

        else:
            messagebox.showinfo("Search", "No user found with that Name or RFID.")
            self.delete_user_btn.configure(state="disabled")



    def delete_user(self):
        """Delete user from SQLite DB"""
        selected_items = self.users_tree.selection()
        if not selected_items: return

        selected_item = selected_items[0]
        values = self.users_tree.item(selected_item)['values']
        rfid = str(values[0])
        name = values[1]

        if not messagebox.askyesno("Confirm Delete", f"Delete user:\n{name} (RFID: {rfid})?"): return

        try:
            # SQLite Delete
            self.cursor.execute("DELETE FROM users WHERE rfid_uid = ?", (rfid,))
            self.conn.commit()

            # Update local cache
            if rfid in self.rfid_users:
                del self.rfid_users[rfid]

            dept_key = f"{rfid}_dept"
            if dept_key in self.rfid_users:
                del self.rfid_users[dept_key]

            self.users_tree.delete(selected_item)

            self.search_user_entry.delete(0, 'end')
            self.delete_user_btn.configure(state="disabled")
            messagebox.showinfo("Success", "User deleted successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete user: {e}")

    def on_user_select(self, event):
        selected_items = self.users_tree.selection()
        if selected_items:
            self.delete_user_btn.configure(state="normal")
        else:
            self.delete_user_btn.configure(state="disabled")

    def setup_settings_section(self):
        self.settings_frame = ctk.CTkFrame(self, width=1100, height=700, fg_color="white", bg_color="#194f59",
                                           corner_radius=20)

        # --- Threshold Frame ---
        temp_frame = ctk.CTkFrame(self.settings_frame, width=1090, height=130, fg_color="#5fafea", bg_color="white",
                                  corner_radius=15)
        temp_frame.place(x=5, y=5)

        ctk.CTkLabel(
            temp_frame,
            text="Temperature Settings",
            font=("Intro Rust Base", 30, "bold"),
            text_color='White'
        ).place(relx=0.5, y=25, anchor='center')

        ctk.CTkLabel(
            temp_frame,
            text="Fever Threshold:",
            font=("Arial", 20, "bold"),
            text_color='white'
        ).place(x=20, y=70)

        self.threshold_var = ctk.StringVar(value=str(self.fever_threshold))
        ctk.CTkEntry(temp_frame, textvariable=self.threshold_var, width=100, height=40, font=("Arial", 20, "bold"),
                     corner_radius=15, text_color='black', fg_color='white', justify='center').place(x=190, y=63)
        ctk.CTkLabel(
            temp_frame,
            text="°C",
            font=("Arial", 20, "bold"),
            text_color='white'
        ).place(x=300, y=70)

        ctk.CTkButton(
            temp_frame,
            text="Update Threshold",
            command=self.update_threshold,
            width=170,
            fg_color="red",
            hover_color="dark red",
            height=40,
            font=("Arial", 20, "bold"),
            text_color='White',
            corner_radius=15,
            border_width=2,
            border_color='black'
        ).place(x=350, y=65)

        # --- Device Controls Frame ---
        device_frame = ctk.CTkFrame(self.settings_frame, width=1090, height=470, corner_radius=20, bg_color='white',
                                    fg_color='#557f87')
        device_frame.place(x=5, y=140)

        ctk.CTkLabel(device_frame, text="Device Controls", font=("Intro Rust Base", 30, "bold"),
                     text_color='white').place(relx=0.5, y=30, anchor='center')

        # Place buttons side by side with spacing
        ctk.CTkButton(
            device_frame,
            text="Test Buzzer",
            command=self.test_buzzer,
            fg_color="blue",
            hover_color="dark blue",
            height=50,
            width=250,
            font=("Arial", 20, "bold"),
            text_color='White',
            corner_radius=15,
            border_width=2,
            border_color='black'
        ).place(relx=0.35, y=90, anchor='center')  # Left side

        ctk.CTkButton(
            device_frame,
            text="Test LCD",
            command=self.test_lcd,
            fg_color="blue",
            hover_color="dark blue",
            height=50,
            width=250,
            font=("Arial", 20, "bold"),
            text_color='White',
            corner_radius=15,
            border_width=2,
            border_color='black'
        ).place(relx=0.65, y=90, anchor='center')  # Right side

        ctk.CTkLabel(device_frame, text="Debug Console:", font=("Arial", 20, "bold"), text_color='white').place(x=20, y=130)

        self.debug_text = ctk.CTkTextbox(device_frame, width=1040, height=160, corner_radius=10)
        self.debug_text.place(x=20, y=165)
        self.debug_text.insert("1.0", "System started. Database Ready.\n")
        self.debug_text.configure(state="disabled")

        # --- NEW CALIBRATION SECTION ---
        ctk.CTkLabel(device_frame, text="--- Sensor Calibration ---", font=("Arial", 20, "bold"),
                     text_color='white').place(relx=0.5, y=350, anchor='center')

        # Place label, entry, and button side by side
        ctk.CTkLabel(device_frame,
                     text="Offset Value (Add to reading):",
                     font=("Arial", 20, "bold"),
                     text_color='white').place(relx=0.3, y=410, anchor='center')

        self.offset_var = ctk.StringVar(value="3.0")
        self.offset_entry = ctk.CTkEntry(
            device_frame,
            textvariable=self.offset_var,
            width=100, height=40, font=("Arial", 20, "bold"),
            corner_radius=15, text_color='black', fg_color='white', justify='center')
        self.offset_entry.place(relx=0.5, y=410, anchor='center')

        ctk.CTkButton(
            device_frame,
            text="Set Calibration",
            command=self.update_offset,
            fg_color="blue",
            hover_color="dark blue",
            height=50,
            width=250,
            font=("Arial", 20, "bold"),
            text_color='White',
            corner_radius=15,
            border_width=2,
            border_color='black'
        ).place(relx=0.75, y=410, anchor='center')

        # Auto save checkbox at bottom
        system_frame = ctk.CTkFrame(self.settings_frame, width=1090, height=80, corner_radius=20, bg_color='white')
        system_frame.place(x=5, y=615)
        self.auto_save_var = ctk.BooleanVar(value=self.auto_save)
        ctk.CTkCheckBox(system_frame, text="Auto-save attendance data", variable=self.auto_save_var,
                        font=("Arial", 25, "bold"), text_color='white', fg_color='#73bd00').place(x=20, y=25)

    def setup_stats_section(self):
        self.stats_frame = ctk.CTkFrame(self, width=1100, height=700, bg_color="#194f59", fg_color='white',
                                        corner_radius=20, border_width=5, border_color='white')
        ctk.CTkLabel(self.stats_frame, text="Attendance Statistics", font=("Arial", 30, "bold"),
                     text_color='white').place(relx=0.5, y=30, anchor='center')

        stats_grid_frame = ctk.CTkFrame(self.stats_frame, width=1090, height=200, fg_color="#5fafea", corner_radius=15,
                                        bg_color='white')
        stats_grid_frame.place(x=5, y=5)

        self.total_scans_stat = self.create_stat_display(stats_grid_frame, "Total Scans", "0", 100, 20)
        self.fever_cases_stat = self.create_stat_display(stats_grid_frame, "Fever Cases", "0", 100, 100)
        self.normal_cases_stat = self.create_stat_display(stats_grid_frame, "Normal Cases", "0", 450, 20)
        self.avg_temp_stat = self.create_stat_display(stats_grid_frame, "Average Temp", "-- °C", 450, 100)
        self.highest_temp_stat = self.create_stat_display(stats_grid_frame, "Highest Temp", "-- °C", 800, 20)
        self.lowest_temp_stat = self.create_stat_display(stats_grid_frame, "Lowest Temp", "-- °C", 800, 100)

        charts_frame = ctk.CTkFrame(self.stats_frame, width=1090, height=400, fg_color="#557f87", corner_radius=15,
                                    bg_color='white')
        charts_frame.place(x=5, y=210)
        ctk.CTkLabel(charts_frame, text="Temperature Distribution", font=("Arial", 20, "bold"),
                     text_color='white').place(relx=0.5, y=25, anchor='center')
        self.chart_label = ctk.CTkLabel(charts_frame, text="Temperature chart will appear here", font=("Arial", 16),
                                        text_color='white', justify='center')
        self.chart_label.place(relx=0.5, y=200, anchor='center')

        refresh_frame = ctk.CTkFrame(self.stats_frame, width=1090, height=80, corner_radius=15, bg_color='white')
        refresh_frame.place(x=5, y=615)
        self.refresh_stats_btn = ctk.CTkButton(refresh_frame, text="Refresh Statistics",
                                               command=self.update_stats_display, width=200, height=40,
                                               font=("Arial", 16, "bold"), fg_color='green', hover_color='dark green')
        self.refresh_stats_btn.place(relx=0.5, rely=0.5, anchor='center')

    def create_stat_display(self, parent, title, value, x, y):
        frame = ctk.CTkFrame(parent, width=200, height=60, fg_color="#194f59")
        frame.place(x=x, y=y)
        ctk.CTkLabel(frame, text=title, font=("Arial", 14), text_color='white').place(relx=0.5, y=15, anchor='center')
        value_label = ctk.CTkLabel(frame, text=value, font=("Arial", 18, "bold"), text_color='light blue')
        value_label.place(relx=0.5, y=40, anchor='center')
        return value_label

    def update_stats_display(self):
        if not self.attendance_data:
            self.total_scans_stat.configure(text="0")
            self.fever_cases_stat.configure(text="0")
            self.normal_cases_stat.configure(text="0")
            self.avg_temp_stat.configure(text="-- °C")
            self.highest_temp_stat.configure(text="-- °C")
            self.lowest_temp_stat.configure(text="-- °C")
            return

        total_scans = len(self.attendance_data)
        fever_cases = sum(1 for entry in self.attendance_data if "FEVER" in entry[5])
        normal_cases = total_scans - fever_cases

        if self.temperature_history:
            avg_temp = sum(self.temperature_history) / len(self.temperature_history)
            highest_temp = max(self.temperature_history)
            lowest_temp = min(self.temperature_history)
        else:
            avg_temp = highest_temp = lowest_temp = 0

        self.total_scans_stat.configure(text=str(total_scans))
        self.fever_cases_stat.configure(text=str(fever_cases))
        self.normal_cases_stat.configure(text=str(normal_cases))
        self.avg_temp_stat.configure(text=f"{avg_temp:.1f} °C")
        self.highest_temp_stat.configure(text=f"{highest_temp:.1f} °C")
        self.lowest_temp_stat.configure(text=f"{lowest_temp:.1f} °C")

        if self.temperature_history:
            self.chart_label.configure(
                text=f"Data available: {total_scans} scans\nTemperature range: {lowest_temp:.1f}°C - {highest_temp:.1f}°C\nFever rate: {(fever_cases / total_scans * 100):.1f}%")

    def show_section(self, section_name):
        for frame in [self.dashboard_frame, self.log_frame, self.users_frame, self.settings_frame, self.stats_frame]:
            frame.place_forget()

        if section_name == 'dashboard':
            self.dashboard_frame.place(x=300, y=250)
            self.highlight_button(self.dashboard_btn)
        elif section_name == 'log':
            self.log_frame.place(x=300, y=250)
            self.highlight_button(self.log_btn)
        elif section_name == 'users':
            self.users_frame.place(x=300, y=250)
            self.highlight_button(self.users_btn)
        elif section_name == 'settings':
            self.settings_frame.place(x=300, y=250)
            self.highlight_button(self.settings_btn)
        elif section_name == 'stats':
            self.stats_frame.place(x=300, y=250)
            self.highlight_button(self.stats_btn)
            self.update_stats_display()

    def highlight_button(self, active_button):
        buttons = [self.dashboard_btn, self.log_btn, self.users_btn, self.settings_btn, self.stats_btn]
        for button in buttons:
            if button == active_button:
                button.configure(fg_color="#a93800", text_color='white')
            else:
                button.configure(fg_color=["#806400", "#fcd016"], text_color='black')

    def setup_serial_monitor(self):
        self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
        self.serial_thread.start()

    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def refresh_ports(self):
        ports = self.get_available_ports()
        self.port_combobox.configure(values=ports)
        if ports: self.port_combobox.set(ports[0])

    def connect_serial(self):
        port = self.port_combobox.get()
        if not port:
            messagebox.showerror("Error", "Please select a COM port")
            return
        try:
            self.serial_connection = serial.Serial(port=port, baudrate=115200, timeout=1, write_timeout=1, rtscts=False,
                                                   dsrdtr=False)
            time.sleep(2)
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            self.is_connected = True
            self.connection_status.configure(text="🟢 Connected", text_color="green")
            self.connection_status1.configure(text="Connected", text_color="white")
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.add_debug_message(f"Connected to {port}")
            self.after(1000, self.send_threshold_to_arduino)
            messagebox.showinfo("Success", f"Connected to {port}")
        except Exception as e:
            self.add_debug_message(f"Connection failed: {str(e)}")
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")

    def disconnect_serial(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.is_connected = False
        self.connection_status.configure(text="🔴 Disconnected", text_color="red")
        self.connection_status1.configure(text="Disconnected", text_color="white")
        self.connect_btn.configure(state="normal")
        self.disconnect_btn.configure(state="disabled")
        self.add_debug_message("Disconnected from ESP32")

    def read_serial_data(self):
        while True:
            if self.is_connected and self.serial_connection and self.serial_connection.is_open:
                try:
                    if self.serial_connection.in_waiting:
                        line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            self.add_debug_message(f"Received: {line}")
                            self.process_serial_data(line)
                except Exception as e:
                    self.is_connected = False
                    print(f"Device disconnected unexpectedly: {e}")
                    self.after(0, self.handle_serial_error)
            time.sleep(0.1)

    def process_serial_data(self, data):
        try:
            if data.startswith('{') and data.endswith('}'):
                sensor_data = json.loads(data)
                self.after(0, self.update_ui_with_data, sensor_data)
            elif "DEBUG:" in data:
                pass
            elif "BUZZER_TEST_COMPLETE" in data:
                self.add_debug_message("Buzzer test completed successfully")
            elif "LCD_TEST_COMPLETE" in data:
                self.add_debug_message("LCD test completed successfully")
            elif "AttemptDance System Ready" in data:
                self.add_debug_message("ESP32 is ready and initialized")
            else:
                self.add_debug_message(f"Raw data: {data}")
        except json.JSONDecodeError as e:
            self.add_debug_message(f"JSON decode error: {e}")

    def update_ui_with_data(self, data):
        rfid_uid = data.get('rfid', 'Unknown')
        temperature = data.get('temperature', 0.0)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today_date = datetime.now().strftime("%Y-%m-%d")

        user_name = self.rfid_users.get(rfid_uid, "Unknown User")
        department = self.rfid_users.get(f"{rfid_uid}_dept", "Unknown Department")
        email = self.rfid_users.get(f"{rfid_uid}_email", "")

        # CHECK DB FOR DUPLICATE
        if self.has_user_logged_today(rfid_uid, today_date):
            if self.is_connected and self.serial_connection:
                self.serial_connection.write(b"ALREADY_LOGGED\n")

            self.user_display.configure(text=user_name)
            self.temp_display.configure(text=f"{temperature:.1f} °C")
            self.rfid_display.configure(text=f"RFID: {rfid_uid}")
            self.status_display.configure(text="ALREADY LOGGED", text_color="white")
            self.status_display1.configure(text="WAIT", text_color='white')
            return
        else:
            if self.is_connected and self.serial_connection:
                self.serial_connection.write(b"PROCEED\n")

        if self.is_connected and self.serial_connection:
            time.sleep(0.1)
            self.serial_connection.write(f"USER_NAME:{user_name}\n".encode())
            time.sleep(0.1)
            self.serial_connection.write(f"USER_DEPT:{department}\n".encode())
            time.sleep(0.1)
            self.serial_connection.write(f"USER_TIME:{timestamp}\n".encode())
            time.sleep(0.1)
            self.serial_connection.write(f"USER_EMAIL:{email}\n".encode())
            time.sleep(0.1)

        self.user_display.configure(text=user_name)
        self.temp_display.configure(text=f"{temperature:.1f} °C")
        self.rfid_display.configure(text=f"RFID: {rfid_uid}")

        threshold = float(self.threshold_var.get())
        if temperature >= threshold:
            status_text = "FEVER"
            status_color = "red"
            status_text1 = "WAIT"
            self.trigger_fever_alert()
        else:
            status_text = "NORMAL"
            status_color = "green"
            status_text1 = "WAIT"
            self.trigger_success_beep()

        self.status_display.configure(text=status_text, text_color=status_color)
        self.status_display1.configure(text=status_text1, text_color='white')

        log_entry = (timestamp, rfid_uid, user_name, department, f"{temperature:.1f} °C", status_text.split(' - ')[0])
        self.attendance_data.append(log_entry)
        self.temperature_history.append(temperature)
        self.update_statistics()

        if hasattr(self, 'stats_frame') and self.stats_frame.winfo_ismapped():
            self.update_stats_display()

        if self.auto_save_var.get():
            self.save_attendance_data(log_entry)

        self.refresh_log()

    # --- REPLACED LOGIC WITH SQLITE ---
    def has_user_logged_today(self, rfid_uid, today_date):
        """Check DB for today's login"""
        try:
            # Query SQLite for today's date
            query = "SELECT count(*) FROM attendance WHERE rfid_uid = ? AND date(timestamp) = date('now', 'localtime')"
            self.cursor.execute(query, (rfid_uid,))
            count = self.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            print(f"DB Check Error: {e}")
            return False

    def send_threshold_to_arduino(self):
        if self.is_connected:
            try:
                threshold = self.threshold_var.get()
                command = f"THRESHOLD:{threshold}\n"
                self.serial_connection.write(command.encode())
                self.add_debug_message(f"Sent threshold: {threshold}")
            except Exception as e:
                self.add_debug_message(f"Error sending threshold: {e}")

    def trigger_fever_alert(self):
        if self.is_connected: self.serial_connection.write(b"FEVER_ALERT\n")

    def trigger_success_beep(self):
        if self.is_connected: self.serial_connection.write(b"SUCCESS_BEEP\n")

    def test_buzzer(self):
        if self.is_connected:
            self.serial_connection.write(b"BUZZER_TEST\n")
        else:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")

    def test_lcd(self):
        if self.is_connected:
            self.serial_connection.write(b"LCD_TEST\n")
        else:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")

    def calibrate_sensor(self):
        if self.is_connected:
            self.serial_connection.write(b"CALIBRATE\n")
        else:
            messagebox.showwarning("Not Connected", "Please connect to ESP32 first")

    def update_threshold(self):
        try:
            threshold = float(self.threshold_var.get())
            self.fever_threshold = threshold
            self.send_threshold_to_arduino()
            messagebox.showinfo("Success", f"Threshold updated to {threshold}°C")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    def update_offset(self):
        try:
            offset_val = float(self.offset_var.get())
            if self.is_connected:
                # Send command to Arduino: "OFFSET:3.5"
                command = f"OFFSET:{offset_val}\n"
                self.serial_connection.write(command.encode())
                self.add_debug_message(f"Sent Offset: {offset_val}")
                messagebox.showinfo("Success", f"Calibration Offset set to {offset_val}°C")
            else:
                messagebox.showerror("Error", "Not connected to ESP32")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number (e.g., 2.5)")

    # --- REPLACED LOGIC WITH SQLITE ---
    def add_user(self):
        rfid = self.new_rfid_entry.get().strip().upper()
        name = self.new_name_entry.get().strip()
        dept = self.new_dept_combobox.get()
        email = self.new_email_entry.get().strip()

        if not rfid or not name:
            messagebox.showerror("Error", "RFID and Name are required")
            return

        try:
            # Insert into SQLite
            self.cursor.execute('''
                INSERT OR REPLACE INTO users (rfid_uid, name, department, email)
                VALUES (?, ?, ?, ?)
            ''', (rfid, name, dept, email))
            self.conn.commit()

            # Update local dictionary cache for UI speed
            self.rfid_users[rfid] = name
            self.rfid_users[f"{rfid}_dept"] = dept
            self.rfid_users[f"{rfid}_email"] = email

            self.new_rfid_entry.delete(0, 'end')
            self.new_name_entry.delete(0, 'end')
            self.new_email_entry.delete(0, 'end')
            self.new_dept_combobox.set("BSCPE-1D")
            self.refresh_users_list()
            messagebox.showinfo("Success", f"User {name} added successfully")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not add user: {e}")

    def refresh_users_list(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        # We iterate the dictionary cache for speed, which is synced with DB
        for rfid, name in self.rfid_users.items():
            if not rfid.endswith('_dept') and not rfid.endswith('_email'):
                dept = self.rfid_users.get(f"{rfid}_dept", "")
                email = self.rfid_users.get(f"{rfid}_email", "")
                self.users_tree.insert("", "end", values=(rfid, name, dept, email))

    def update_statistics(self):
        if not hasattr(self, 'total_scans_label') or self.total_scans_label is None: return
        if not self.attendance_data:
            self.total_scans_label.configure(text="0")
            self.normal_temp_label.configure(text="0")
            self.fever_cases_label.configure(text="0")
            self.avg_temp_label.configure(text="-- °C")
            return
        total_scans = len(self.attendance_data)
        fever_cases = sum(1 for entry in self.attendance_data if "FEVER" in entry[5])
        normal_cases = total_scans - fever_cases
        avg_temp = sum(self.temperature_history) / len(self.temperature_history) if self.temperature_history else 0
        self.total_scans_label.configure(text=str(total_scans))
        self.normal_temp_label.configure(text=str(normal_cases))
        self.fever_cases_label.configure(text=str(fever_cases))
        self.avg_temp_label.configure(text=f"{avg_temp:.1f} °C")

    def export_data(self):
        try:
            data_to_export = []
            for item in self.log_tree.get_children():
                values = self.log_tree.item(item)['values']
                data_to_export.append(values)
            total_records = len(data_to_export)
            default_name = f"attendance_data_{datetime.now().strftime('%Y-%m-%d')}_{total_records}_records.csv"
            filename = filedialog.asksaveasfilename(title="Export Data", defaultextension=".csv",
                                                    filetypes=[("CSV files", "*.csv")], initialfile=default_name)
            if not filename: return
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "RFID", "Name", "Department", "Temperature", "Status"])
                writer.writerows(data_to_export)
            messagebox.showinfo("Export Successful", f"Saved to {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {e}")

    def clear_log(self):
        if messagebox.askyesno("Confirm", "Clear the log? This deletes history from database."):
            try:
                self.cursor.execute("DELETE FROM attendance")
                self.conn.commit()
                self.attendance_data.clear()
                self.temperature_history.clear()
                self.refresh_log()
                self.update_statistics()
            except Exception as e:
                messagebox.showerror("Error", f"Database clear failed: {e}")

    def search_log(self, event=None):
        search_term = self.search_entry.get().lower()
        for item in self.log_tree.get_children():
            values = self.log_tree.item(item)['values']
            if (search_term in str(values[1]).lower() or search_term in str(values[2]).lower() or search_term in str(
                    values[3]).lower()):
                self.log_tree.selection_set(item)
                self.log_tree.focus(item)
            else:
                self.log_tree.selection_remove(item)

    # --- REPLACED LOGIC WITH SQLITE ---
    def save_attendance_data(self, entry):
        """Save new scan to SQLite"""
        try:
            # entry format: (timestamp, rfid, name, dept, temp, status)
            self.cursor.execute('''
                INSERT INTO attendance (timestamp, rfid_uid, name, department, temperature, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', entry)
            self.conn.commit()
        except Exception as e:
            print(f"Error saving data to DB: {e}")

    # --- REPLACED LOGIC WITH SQLITE ---
    def load_existing_data(self):
        """Load history from DB and trigger default view"""
        try:
            self.attendance_data.clear()
            # Get everything from DB
            self.cursor.execute(
                "SELECT timestamp, rfid_uid, name, department, temperature, status FROM attendance ORDER BY id DESC")
            rows = self.cursor.fetchall()

            for row in rows:
                self.attendance_data.append(row)
                try:
                    # Keep history for charts
                    temp_str = row[4].replace(' °C', '')
                    self.temperature_history.append(float(temp_str))
                except:
                    pass

            # --- CRITICAL FIX: Trigger the view immediately ---
            self.sort_log()

        except Exception as e:
            print(f"Error loading DB data: {e}")

    # --- REPLACED LOGIC WITH SQLITE ---
    def load_user_database(self):
        """Load users from SQLite into local cache dictionary"""
        try:
            self.cursor.execute("SELECT rfid_uid, name, department, email FROM users")
            rows = self.cursor.fetchall()

            self.rfid_users.clear()
            for row in rows:
                rfid = row[0]
                self.rfid_users[row[0]] = row[1]
                self.rfid_users[f"{row[0]}_dept"] = row[2]
                self.rfid_users[f"{row[0]}_email"] = row[3]  # <--- NEW


            print(f"Loaded {len(rows)} users from database")
        except Exception as e:
            print(f"Error loading users DB: {e}")
            self.rfid_users = {}

        if hasattr(self, 'users_tree'):
            self.refresh_users_list()

    def handle_serial_error(self):
        # If we are already disconnected, don't do anything (prevents duplicate errors)
        if self.serial_connection is None:
            return

        self.add_debug_message("Connection lost.")

        # Close the connection safely
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
        except:
            pass

        self.serial_connection = None
        self.is_connected = False

        # Reset UI buttons
        self.connection_status.configure(text="🔴 Disconnected", text_color="red")
        self.connection_status1.configure(text="Disconnected", text_color="white")
        self.connect_btn.configure(state="normal")
        self.disconnect_btn.configure(state="disabled")

        # Show ONE pop-up only
        messagebox.showerror("Connection Lost", "Device was unplugged or connection failed.")

    def add_debug_message(self, message):
        self.debug_text.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_text.insert("end", f"[{timestamp}] {message}\n")
        self.debug_text.see("end")
        self.debug_text.configure(state="disabled")

    def on_closing(self):
        self.disconnect_serial()
        if hasattr(self, 'conn'):
            self.conn.close()
        self.destroy()


if __name__ == "__main__":
    app = AttemptDanceUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()