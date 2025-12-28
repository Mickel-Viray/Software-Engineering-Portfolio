import customtkinter as ctk
import sqlite3
from tkinter import messagebox
from PIL import Image, ImageTk
from mysql.connector import Error, connect
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import random
import keyring
from calendar import calendar
from socket import create_connection
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from tkcalendar import DateEntry
import sys
import os
import ctypes

def initialize_database():
    connection = sqlite3.connect('ipes.db')
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT,
        email_verified BOOLEAN DEFAULT 0,
        remember_me_enabled BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT)
    """)
    cursor.execute("SELECT * FROM admin WHERE username = ?", ('ipesadmin',))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO admin (username, password, email) VALUES (?, ?, ?)",
                       ('ipesadmin', '1234', 'mickeljohndviray@gmail.com'))



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        otp TEXT,
        purpose TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        attempts INTEGER DEFAULT 0,
        lockout_time TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id))
        """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        section TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id))
        """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS login_history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    login_time DATETIME NOT NULL,
    email TEXT,
    logout_time DATETIME)
    """)

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_trainees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            hte_name TEXT,
            hte_address TEXT,
            hours_rendered INTEGER,
            supervisor_contact TEXT,
            supervisor_email TEXT,
            training_period TEXT,
            section TEXT)''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            work_attitude_1 INTEGER,
            work_attitude_2 INTEGER,
            work_attitude_3 INTEGER,
            work_attitude_4 INTEGER,
            work_attitude_5 INTEGER,
            work_knowledge_1 INTEGER,
            work_knowledge_2 INTEGER,
            work_knowledge_3 INTEGER,
            work_knowledge_4 INTEGER,
            work_knowledge_5 INTEGER,
            personal_appearance_1 INTEGER,
            personal_appearance_2 INTEGER,
            personal_appearance_3 INTEGER,
            personal_appearance_4 INTEGER,
            personal_appearance_5 INTEGER,
            professional_competence_1 INTEGER,
            professional_competence_2 INTEGER,
            professional_competence_3 INTEGER,
            professional_competence_4 INTEGER,
            professional_competence_5 INTEGER,
            remarks TEXT,
            total_rating INTEGER,
            FOREIGN KEY(student_id) REFERENCES student_trainees(id))
        ''')

    connection.commit()
    connection.close()

initialize_database()

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Enable High DPI awareness
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
except Exception:
    screen_width = 1920
    screen_height = 1080

DESIGN_WIDTH = 1536
DESIGN_HEIGHT = 864

scaling_factor = screen_width / DESIGN_WIDTH

ctk.set_window_scaling(scaling_factor)
ctk.set_widget_scaling(scaling_factor)

# Window configuration
ctk.set_appearance_mode("light")
main = ctk.CTk()
main.title("Intern Performance Evaluation System")
main.configure(bg='#B03052')
main.after(0, lambda: main.state('zoomed'))
main.resizable(True, True)
main.grid_rowconfigure(0, weight=1)
main.grid_columnconfigure(0, weight=1)
current_user_id = None
SERVICE_NAME = "IPES_System_v1"

def resource_path(relative_path):
    """ Get absolute path to resource for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def create_connection():
    try:
        connection = sqlite3.connect('ipes.db')
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to connect: {e}")
        return None

def generate_otp():
    return ''.join(random.choices('0123456789', k=6))

def send_otp_email(receiver_email, otp):
    sender_email = "mickeljohndviray@gmail.com"
    sender_password = "mmmu lgio kzbi veci"

    message = MIMEText(f"Your OTP is {otp}")
    message['Subject'] = "OTP Verification"
    message['From'] = sender_email
    message['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send OTP: {e}")
        return False

def verify_otp_in_db(email, otp, purpose):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""SELECT * FROM otps 
                WHERE email = ? AND otp = ? AND purpose = ? 
                AND created_at >= datetime('now', '-5 minutes')
                ORDER BY created_at DESC LIMIT 1""", (email, otp, purpose))
            result =cursor.fetchone()
            return result is not None
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
            return False
        finally:
            if connection:
                connection.close()
    return False

def open_admin_from_user(loginpage_window):
    loginpage_window.destroy()
    loginAs_admin()

def open_user_from_admin(loginAsAdmin_window):
    loginAsAdmin_window.destroy()
    loginAs_user()

def open_user_from_signup(signuppage_window):
    signuppage_window.destroy()
    loginAs_user()

def open_signup_from_user(loginpage_window):
    loginpage_window.destroy()
    signupAs_user()

def open_forget_from_user(loginpage_window):
    loginpage_window.destroy()
    forget_password()

def open_user_from_forget(forget_pass_window):
    forget_pass_window.destroy()
    loginAs_user()

def loginAs_admin():
    ctk.set_appearance_mode("light")
    loginAsAdmin_window = ctk.CTkToplevel()
    loginAsAdmin_window.title("Intern Performance Evaluation System")
    loginAsAdmin_window.configure(bg='#B03052')
    loginAsAdmin_window.after(0, lambda: loginAsAdmin_window.state('zoomed'))
    loginAsAdmin_window.resizable(True, True)
    loginAsAdmin_window.geometry(f"{main.winfo_screenwidth()}x{main.winfo_screenheight()}+0+0")
    loginAsAdmin_window.grid_rowconfigure(0, weight=1)
    loginAsAdmin_window.grid_columnconfigure(0, weight=1)

    def verify_admin():
        username = usname_admin_box.get().strip()
        password = pass_admin_box.get().strip()


        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                # First select by username only
                cursor.execute("SELECT * FROM admin WHERE username = ?", (username,))
                result = cursor.fetchone()

                if result:
                    # Convert row to dictionary
                    columns = [col[0] for col in cursor.description]
                    admin = dict(zip(columns, result))

                    # Verify password separately
                    if admin['password'] == password:
                        otp = generate_otp()
                        try:
                            cursor.execute(
                                "INSERT INTO otps (email, otp, purpose) VALUES (?, ?, 'admin')",
                                (admin['email'], otp)
                            )
                            connection.commit()

                            if send_otp_email(admin['email'], otp):
                                loginAsAdmin_window.withdraw()
                                otp_send_verification_window(
                                    admin['email'],
                                    'admin',
                                    success_callback=lambda: [
                                        loginAsAdmin_window.destroy(),
                                        homepage_admin()
                                    ]
                                )
                                return  # Success, exit early
                            else:
                                messagebox.showerror("Error", "Failed to send OTP email")
                        except sqlite3.Error as e:
                            messagebox.showerror("Database Error", f"OTP insert failed: {e}")
                    else:
                        messagebox.showerror("Error", "Invalid admin password")
                else:
                    messagebox.showerror("Error", "Admin username not found")

                # Only show credentials error if we reach here
                messagebox.showerror("Error", "Invalid admin credentials")

            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Query failed: {e}")
            finally:
                connection.close()



    admin_bg = ctk.CTkImage(light_image=Image.open(resource_path("loginAsAdmin.png")), size=(1540, 795))
    admin_bg = ctk.CTkLabel(loginAsAdmin_window, image=admin_bg, text='')
    admin_bg.grid(row=0, column=0)

    login_admin_lbl = ctk.CTkLabel(loginAsAdmin_window, text="LOG IN AS ADMIN", font=("Lato", 45, "bold"),
                                   bg_color="#c4d5d7")
    login_admin_lbl.place(x=225, y=200)

    usname_admin_lbl = ctk.CTkLabel(loginAsAdmin_window, text="Username:", font=("Lato", 17, "bold"),
                                    bg_color="#c4d5d7")
    usname_admin_lbl.place(x=210, y=280)

    usname_admin_box_frame = ctk.CTkFrame(loginAsAdmin_window, width=400, height=55, fg_color="#405460",
                                          corner_radius=10, bg_color="#c4d5d7")
    usname_admin_box_frame.place(x=210, y=310)

    usname_admin_box = ctk.CTkEntry(usname_admin_box_frame, width=380, height=38, corner_radius=10, font=("Lato", 14),
                                    fg_color="#c4d5d7"
                                    )
    usname_admin_box.place(x=10, y=9)

    pass_admin_lbl = ctk.CTkLabel(loginAsAdmin_window, text="Password:", font=("Lato", 17, "bold"),
                                  bg_color="#c4d5d7", )
    pass_admin_lbl.place(x=210, y=370)

    pass_admin_box_frame = ctk.CTkFrame(loginAsAdmin_window, width=400, height=55, fg_color="#405460", corner_radius=10,
                                        bg_color="#c4d5d7")
    pass_admin_box_frame.place(x=210, y=400)

    pass_admin_box = ctk.CTkEntry(pass_admin_box_frame, width=380, height=38, corner_radius=10, fg_color="#c4d5d7",
                                  font=("Lato", 14), show="*")
    pass_admin_box.place(x=10, y=9)

    def toggle_pasword():
        if pass_admin_box.cget("show") == "*":
            pass_admin_box.configure(show="")
            admin_showpass.configure(image=hide_icon)
        else:
            pass_admin_box.configure(show="*")
            admin_showpass.configure(image=show_icon)

    show_icon = ctk.CTkImage(light_image=Image.open(resource_path("showpass.png")), size=(20, 20))
    hide_icon = ctk.CTkImage(light_image=Image.open(resource_path("hidepass.png")), size=(20, 20))

    admin_showpass = ctk.CTkButton(pass_admin_box_frame, image=show_icon, text="", width=30, height=30, bg_color="#c4d5d7",
                                  fg_color="#c4d5d7", hover_color="#a0a5aa", command= toggle_pasword
                                  )
    admin_showpass.place(x=347, y=12)

    remember_admin = ctk.CTkCheckBox(loginAsAdmin_window, text="Remember me", font=("Lato", 14),
                                     bg_color="#c4d5d7", checkbox_width=18, checkbox_height=18,
                                     hover_color="#D76C82")
    remember_admin.place(x=210, y=465)

    remember_admin = ctk.CTkLabel(loginAsAdmin_window, text="Forget Password?", font=("Lato", 14), bg_color="#c4d5d7")
    remember_admin.place(x=490, y=465)

    login_btn_admin = ctk.CTkButton(loginAsAdmin_window, text="Log In", width=400, height=40, corner_radius=10,
                                    fg_color="#405460",
                                    bg_color="#c4d5d7", hover_color="#60646B", font=("Lato", 13, "bold"), command= verify_admin)
    login_btn_admin.place(x=210, y=520)

    login_user = ctk.CTkLabel(loginAsAdmin_window, text="Login as User", font=("Lato", 15, "bold"), bg_color="#c4d5d7",)
    login_user.place(x=353, y=586)

    user_login_lbl = ctk.CTkLabel(loginAsAdmin_window, text="User", font=("Lato", 15, "bold"), bg_color="#c4d5d7",
                             text_color="#60646B", cursor="hand2")
    user_login_lbl.place(x=420, y=586)
    user_login_lbl.bind("<Button-1>", lambda event: open_user_from_admin(loginAsAdmin_window))

    loginAsAdmin_window.mainloop()

def loginAs_user():
    main.withdraw()
    ctk.set_appearance_mode("light")
    loginpage_window = ctk.CTkToplevel()
    loginpage_window.title("Intern Performance Evaluation System")
    loginpage_window.configure(bg='#B03052')
    loginpage_window.after(0, lambda: loginpage_window.state('zoomed'))
    loginpage_window.resizable(True, True)
    loginpage_window.geometry(f"{main.winfo_screenwidth()}x{main.winfo_screenheight()}+0+0")
    loginpage_window.grid_rowconfigure(0, weight=1)
    loginpage_window.grid_columnconfigure(0, weight=1)


    def verify_user():
        username = usname_box.get()
        password = pass_box.get()
        remember_me = remember.get()

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user_row = cursor.fetchone()

                if not user_row:
                    messagebox.showerror("Error", "Invalid username or password.")
                    return


                columns = [col[0] for col in cursor.description]
                user = dict(zip(columns, user_row))
                user_id = user['id']

                cursor.execute("SELECT * FROM login_attempts WHERE user_id = ?", (user_id,))
                attempt_row = cursor.fetchone()
                attempt = None

                if attempt_row:
                    columns = [col[0] for col in cursor.description]
                    attempt = dict(zip(columns, attempt_row))
                else:
                    cursor.execute("INSERT INTO login_attempts (user_id, attempts) VALUES (?, 0)", (user_id,))
                    connection.commit()
                    attempt = {'attempts': 0, 'lockout_time': None}

                current_time = datetime.now()
                if attempt['lockout_time']:
                    lockout_time = datetime.strptime(attempt['lockout_time'], "%Y-%m-%d %H:%M:%S")
                    if lockout_time > current_time:
                        remaining = lockout_time - current_time
                        mins = remaining.seconds // 60
                        secs = remaining.seconds % 60
                        messagebox.showerror("Account Locked",
                                             f"Too many failed attempts. Try again in {mins} minutes {secs} seconds.")
                        return
                    else:
                        cursor.execute("UPDATE login_attempts SET attempts = 0, lockout_time = NULL WHERE user_id = ?",
                                       (user_id,))
                        connection.commit()
                        attempt['attempts'] = 0
                        attempt['lockout_time'] = None


                if user_row and check_password_hash(user_row[3], password):
                    cursor.execute("UPDATE login_attempts SET attempts = 0, lockout_time = NULL WHERE user_id = ?", (user_id,))
                    if remember_me:
                        store_credentials(username,password)
                        cursor.execute("UPDATE users SET remember_me_enabled = TRUE WHERE id = ?", (user_id,))
                    else:
                        clear_credentials(username)
                        cursor.execute("UPDATE users SET remember_me_enabled = FALSE WHERE id = ?", (user_id,))

                    connection.commit()
                    cursor.execute(
                        "INSERT INTO login_history (user_id, username, email, login_time) VALUES (?, ?, ?, datetime('now'))",
                        (user_id, user['username'], user['email'])
                    )
                    connection.commit()
                    global current_user_id
                    current_user_id = user_id
                    if user['email_verified']:
                        loginpage_window.destroy()
                        homepage_user(username)
                    else:
                        otp = generate_otp()
                        connection = create_connection()
                        if connection:
                            try:
                                cursor = connection.cursor()
                                cursor.execute("INSERT INTO otps (email, otp, purpose) VALUES (?, ?, 'login')",(user['email'], otp))
                                connection.commit()
                                if send_otp_email(user['email'], otp):
                                    loginpage_window.withdraw()
                                    otp_send_verification_window(user['email'], 'login',
                                    success_callback=lambda: [loginpage_window.destroy(), homepage_user(username)])
                            except sqlite3.Error as e:
                                messagebox.showerror("Error", str(e))
                            finally:
                                connection.close()

                else:
                    new_attempts = attempt['attempts'] + 1
                    if new_attempts >= 3:
                        lockout_time = (datetime.now() + timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute("UPDATE login_attempts SET attempts = ?, lockout_time = ? WHERE user_id = ?", (new_attempts, lockout_time,user_id))
                        connection.commit()
                        messagebox.showerror("Account Locked", "Too many failed attempts. Account locked for 3 minutes.")
                    else:
                        cursor.execute("UPDATE login_attempts SET attempts = ? WHERE user_id = ?", (new_attempts,  user_id))
                        connection.commit()
                        remaining = 3 - new_attempts
                        messagebox.showerror("Error", f"Incorrect password. {remaining} attempts remaining.")

            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"An error occurred: {e}")
            finally:
                if connection:
                    connection.close()





    bg = ctk.CTkImage(light_image=Image.open(resource_path("loginpage.png")), size=(1540, 795))
    login_bg = ctk.CTkLabel(loginpage_window, image=bg, text='')
    login_bg.grid(row=0, column=0)

    login_lbl = ctk.CTkLabel(loginpage_window, text="LOG IN", font=("Lato", 45, "bold"), bg_color="#c4d5d7")
    login_lbl.place(x=1050, y=200)

    usname_lbl = ctk.CTkLabel(loginpage_window, text="Username:", font=("Lato", 17, "bold"), bg_color="#c4d5d7")
    usname_lbl.place(x=930, y=280)

    usname_box_frame = ctk.CTkFrame(loginpage_window, width=400, height=55, fg_color="#405460", corner_radius=10,
                                    bg_color="#c4d5d7")
    usname_box_frame.place(x=930, y=310)

    usname_box = ctk.CTkEntry(usname_box_frame, width=380, height=38, corner_radius=10, font=("Lato", 14),
                              fg_color="#c4d5d7"
                              )
    usname_box.place(x=10, y=9)

    pass_lbl = ctk.CTkLabel(loginpage_window, text="Password:", font=("Lato", 17, "bold"), bg_color="#c4d5d7", )
    pass_lbl.place(x=930, y=370)

    pass_box_frame = ctk.CTkFrame(loginpage_window, width=400, height=55, fg_color="#405460", corner_radius=10,
                                  bg_color="#c4d5d7")
    pass_box_frame.place(x=930, y=400)

    pass_box = ctk.CTkEntry(pass_box_frame, width=380, height=38, corner_radius=10, fg_color="#c4d5d7",
                            font=("Lato", 14), show="*")
    pass_box.place(x=10, y=9)

    def toggle_pasword():
        if pass_box.cget("show") == "*":
            pass_box.configure(show="")
            user_showpass.configure(image=hide_icon)
        else:
            pass_box.configure(show="*")
            user_showpass.configure(image=show_icon)


    show_icon = ctk.CTkImage(light_image=Image.open(resource_path("showpass.png")), size=(20, 20))
    hide_icon = ctk.CTkImage(light_image=Image.open(resource_path("hidepass.png")), size=(20, 20))

    user_showpass = ctk.CTkButton(pass_box_frame, image= show_icon, text= "", width=30, height=30, bg_color=  "#c4d5d7",
                                  fg_color="#c4d5d7",  hover_color="#a0a5aa", command=toggle_pasword
                                  )
    user_showpass.place(x=347, y=12)

    remember = ctk.BooleanVar(value=False)
    remember_checkbox = ctk.CTkCheckBox(loginpage_window, text="Remember me", font=("Lato", 14),
                               bg_color="#c4d5d7", checkbox_width=18, checkbox_height=18, variable= remember,
                               hover_color="#D76C82")
    remember_checkbox.place(x=930, y=465)

    saved_creds = load_saved_credentials()
    if saved_creds:
        usname_box.insert(0, saved_creds.get("username", ""))
        pass_box.insert(0, saved_creds.get("password", ""))
        remember.set(True)

    forget_password_user = ctk.CTkLabel(loginpage_window, text="Forget Password?", font=("Lato", 14), bg_color="#c4d5d7", cursor="hand2",
                            )
    forget_password_user.place(x=1220, y=465)
    forget_password_user.bind("<Button-1>", lambda event: open_forget_from_user(loginpage_window))

    login_btn = ctk.CTkButton(loginpage_window, text="Log In", width=400, height=40, corner_radius=10,
                              fg_color="#405460",
                              bg_color="#c4d5d7", hover_color="#60646B", font=("Lato", 13, "bold"), command=verify_user)
    login_btn.place(x=930, y=520)

    noacc = ctk.CTkLabel(loginpage_window, text="Don't have account?", font=("Lato", 14, "bold"), bg_color="#c4d5d7")
    noacc.place(x=1040, y=580)

    signup_lbl = ctk.CTkLabel(loginpage_window, text="Sign Up", font=("Lato", 14, "bold"), bg_color="#c4d5d7",
                              text_color="#60646B", cursor="hand2")
    signup_lbl.place(x=1190, y=580)
    signup_lbl.bind("<Button-1>", lambda event:open_signup_from_user(loginpage_window) )

    login_admin = ctk.CTkLabel(loginpage_window, text="Login as ", font=("Lato", 14, "bold"), bg_color="#c4d5d7")
    login_admin.place(x=1090, y=610)

    admin_login_lbl = ctk.CTkLabel(loginpage_window, text="Admin", font=("Lato", 14, "bold"), bg_color="#c4d5d7",
                                   text_color="#60646B", cursor="hand2")
    admin_login_lbl.place(x=1155, y=610)
    admin_login_lbl.bind("<Button-1>", lambda event: open_admin_from_user(loginpage_window))

    loginpage_window.mainloop()

def signupAs_user():
    main.withdraw()
    ctk.set_appearance_mode("light")
    signuppage_window = ctk.CTkToplevel()
    signuppage_window.title("Intern Performance Evaluation System")
    signuppage_window.configure(bg='#B03052')
    signuppage_window.after(0, lambda: signuppage_window.state('zoomed'))
    signuppage_window.resizable(True, True)
    signuppage_window.geometry(f"{main.winfo_screenwidth()}x{main.winfo_screenheight()}+0+0")
    signuppage_window.grid_rowconfigure(0, weight=1)
    signuppage_window.grid_columnconfigure(0, weight=1)

    def is_valid_email(email):
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(pattern, email)

    def check_username_exists(username):
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
                return cursor.fetchone() is not None
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))
            finally:
                if connection:
                    connection.close()
        return False

    def check_email_exists(email):
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
                return cursor.fetchone() is not None
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))
            finally:
                if connection:
                    connection.close()
        return False

    def create_account():
        username = username_box.get()
        email = email_box.get()
        password = pass_box.get()
        confirm_pass = conpass_box.get()

        if not all([username, email, password, confirm_pass]):
            messagebox.showerror("Error", "All fields are required!")
            return

        password_pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
        if not re.match(password_pattern, password):
            messagebox.showerror("Error",
                                 "Password must contain:\n"
                                 "- At least 8 characters\n"
                                 "- Letters, numbers, and special symbols")
            return

        if password != confirm_pass:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        if not is_valid_email(email):
            messagebox.showerror("Error", "Please enter a valid email address!")
            return

        if check_username_exists(username):
            messagebox.showerror("Error", "Username already exists!")
            return

        if check_email_exists(email):
            messagebox.showerror("Error", "Email already registered!")
            return

        try:
            hashed_pw = generate_password_hash(password)
            connection = create_connection()
            if connection:
                cursor = connection.cursor()
                insert_query = """INSERT INTO users (username, email, password) 
                                VALUES (?, ?, ?)"""
                cursor.execute(insert_query, (username, email, hashed_pw))
                user_id = cursor.lastrowid
                otp = generate_otp()
                cursor.execute("INSERT INTO otps (email, otp, purpose) VALUES (?, ?, 'signup')",
                               (email, otp))
                connection.commit()
                if send_otp_email(email, otp):
                    signuppage_window.destroy()
                    otp_send_verification_window(email, 'signup', success_callback=lambda: loginAs_user())
                else:
                    messagebox.showerror("Error", "Failed to send OTP. Please try again.")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to create account: {e}")

        finally:
            if connection:
                connection.close()







    signpage_bg = ctk.CTkImage(light_image=Image.open(resource_path("sangupbg.png")), size=(1540, 795))
    sign_bg = ctk.CTkLabel(signuppage_window, image=signpage_bg, text='')
    sign_bg.grid(row=0, column=0)

    signup_lbl = ctk.CTkLabel(signuppage_window, text="SIGN UP", font=("Lato", 45, "bold"), bg_color="#c4d5d7")
    signup_lbl.place(x=1050, y=120)

    username_lbl = ctk.CTkLabel(signuppage_window, text="Username:", font=("Lato", 17, "bold"), bg_color="#c4d5d7")
    username_lbl.place(x=930, y=200)

    username_box_frame = ctk.CTkFrame(signuppage_window, width=400, height=55, fg_color="#405460", corner_radius=10,
                                      bg_color="#c4d5d7")
    username_box_frame.place(x=930, y=230)

    username_box = ctk.CTkEntry(username_box_frame, width=380, height=38, corner_radius=10, font=("Lato", 14),
                                fg_color="#c4d5d7"
                                )
    username_box.place(x=10, y=9)

    email_lbl = ctk.CTkLabel(signuppage_window, text="Email:", font=("Lato", 17, "bold"), bg_color="#c4d5d7")
    email_lbl.place(x=930, y=290)

    email_box_frame = ctk.CTkFrame(signuppage_window, width=400, height=55, fg_color="#405460", corner_radius=10,
                                   bg_color="#c4d5d7")
    email_box_frame.place(x=930, y=320)

    email_box = ctk.CTkEntry(email_box_frame, width=380, height=38, corner_radius=10, font=("Lato", 14),
                             fg_color="#c4d5d7")
    email_box.place(x=10, y=9)

    pass_lbl = ctk.CTkLabel(signuppage_window, text="Password:", font=("Lato", 17, "bold"), bg_color="#c4d5d7", )
    pass_lbl.place(x=930, y=380)

    pass_box_frame = ctk.CTkFrame(signuppage_window, width=400, height=55, fg_color="#405460", corner_radius=10,
                                  bg_color="#c4d5d7")
    pass_box_frame.place(x=930, y=410)

    pass_box = ctk.CTkEntry(pass_box_frame, width=380, height=38, corner_radius=10, fg_color="#c4d5d7",
                            font=("Lato", 14), show="*")
    pass_box.place(x=10, y=9)

    def toggle_password():
        if pass_box.cget("show") == "*":
            pass_box.configure(show="")
            sign_user_showpass.configure(image=hide_icon)
        else:
            pass_box.configure(show="*")
            sign_user_showpass.configure(image=show_icon)

    show_icon = ctk.CTkImage(light_image=Image.open(resource_path("showpass.png")), size=(20, 20))
    hide_icon = ctk.CTkImage(light_image=Image.open(resource_path("hidepass.png")), size=(20, 20))

    sign_user_showpass = ctk.CTkButton(pass_box_frame, image=show_icon, text="", width=30, height=30, bg_color="#c4d5d7",
                                  fg_color="#c4d5d7", hover_color="#a0a5aa", command= toggle_password
                                  )
    sign_user_showpass.place(x=347, y=12)

    conpass_lbl = ctk.CTkLabel(signuppage_window, text="Confirm Password:", font=("Lato", 17, "bold"),
                               bg_color="#c4d5d7")
    conpass_lbl.place(x=930, y=470)

    conpass_box_frame = ctk.CTkFrame(signuppage_window, width=400, height=55, fg_color="#405460", corner_radius=10,
                                     bg_color="#c4d5d7")
    conpass_box_frame.place(x=930, y=500)

    conpass_box = ctk.CTkEntry(conpass_box_frame, width=380, height=38, corner_radius=10, fg_color="#c4d5d7",
                               font=("Lato", 14), show="*")
    conpass_box.place(x=10, y=9)

    def toggle_conpassword():
        if conpass_box.cget("show") == "*":
            conpass_box.configure(show="")
            sign_user_showconpass.configure(image=hide_icon)
        else:
            conpass_box.configure(show="*")
            sign_user_showconpass.configure(image=show_icon)

    sign_user_showconpass = ctk.CTkButton(conpass_box_frame, image=show_icon, text="", width=30, height=30,
                                       bg_color="#c4d5d7",
                                       fg_color="#c4d5d7", hover_color="#a0a5aa", command=toggle_conpassword
                                       )
    sign_user_showconpass.place(x=347, y=12)




    createacc = ctk.CTkButton(signuppage_window, text="Create Account", width=400, height=40, corner_radius=10,
                              fg_color="#405460",
                              bg_color="#c4d5d7", hover_color="#60646B", font=("Lato", 13, "bold"), command=create_account)
    createacc.place(x=930, y=575)

    haveacc = ctk.CTkLabel(signuppage_window, text="Already have an account?", font=("Lato", 14, "bold"),
                           bg_color="#c4d5d7")
    haveacc.place(x=998, y=640)

    haveacc_login_lbl = ctk.CTkLabel(signuppage_window, text="Login Here", font=("Lato", 14, "bold"),
                                     bg_color="#c4d5d7",
                                     text_color="#60646B", cursor="hand2")
    haveacc_login_lbl.place(x=1185, y=640)
    haveacc_login_lbl.bind("<Button-1>", lambda event:open_user_from_signup(signuppage_window))

    signuppage_window.mainloop()

def homepage_user(username):
    ctk.set_appearance_mode("light")
    ipes_users_window = ctk.CTkToplevel()
    ipes_users_window.title("Intern Performance Evaluation System")
    ipes_users_window.configure(bg='#B03052')
    ipes_users_window.after(0, lambda: ipes_users_window.state('zoomed'))
    ipes_users_window.resizable(True, True)
    ipes_users_window.geometry(f"{main.winfo_screenwidth()}x{main.winfo_screenheight()}+0+0")
    ipes_users_window.grid_rowconfigure(0, weight=1)
    ipes_users_window.grid_columnconfigure(0, weight=1)

    def get_user_sections():
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT section FROM user_sections WHERE user_id = ?", (current_user_id,))
                return [row[0] for row in cursor.fetchall()]
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to fetch user sections: {e}")
                return []
            finally:
                if connection:
                    connection.close()
        return []

    def show_homepage():
        clear_dashboard_homepage()
        dashboard_homepage()

    def clear_dashboard_homepage():
        for widget in ipes_homepage_frame.winfo_children():
            widget.destroy()

    def dashboard_homepage():
        welcome_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff", corner_radius=0)
        welcome_frame.place(x=20, y=30)

        welcome_user_lbl = ctk.CTkLabel(welcome_frame, text=f"Welcome back, {username.upper()}!", font=('Arial', 33, 'bold'))
        welcome_user_lbl.place(x=10, y=16)

        ipes_dashboard_bg = ctk.CTkImage(dark_image=Image.open(resource_path('dashboardipes.png')), size=(1300, 700))
        image_ipes_dashboard_bg = ctk.CTkLabel(ipes_homepage_frame, image=ipes_dashboard_bg, text='')
        image_ipes_dashboard_bg.place(x=0, y=100)

        my_prf_btn = ctk.CTkButton(ipes_homepage_frame, height=50, width=180, text="Click to view",
                                   hover_color="#60646b", text_color="#000000",
                                   font=('Arial', 20), fg_color="#c4c9ca", corner_radius=0, command=profile_settings)
        my_prf_btn.place(x=275, y=495)

        performance_btn = ctk.CTkButton(ipes_homepage_frame, height=50, width=180, text="Click to view",
                                        hover_color="#60646b", text_color="#000000",
                                        font=('Arial', 20), fg_color="#c4c9ca", corner_radius=0,
                                        command=performance_tracking)
        performance_btn.place(x=555, y=495)

        my_class_btn = ctk.CTkButton(ipes_homepage_frame, height=50, width=180, text="Click to view",
                                     hover_color="#60646b", text_color="#000000",
                                     font=('Arial', 20), fg_color="#c4c9ca", corner_radius=0, command=my_class)
        my_class_btn.place(x=845, y=495)

    def profile_settings():
        for widget in ipes_homepage_frame.winfo_children():
            widget.destroy()

        def fetch_user_data():
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT username , email FROM users WHERE id = ?", (current_user_id,))
                    columns = [col[0] for col in cursor.description]
                    user_row = cursor.fetchone()
                    user_dict = dict(zip(columns, user_row)) if user_row else None

                    cursor.execute("SELECT section FROM user_sections WHERE user_id = ?", (current_user_id,))
                    sections = [row[0] for row in cursor.fetchall()]

                    return user_dict, sections
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", str(e))
                finally:
                    if connection:
                        connection.close()
            return None, []

        def changing_of_username():
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            def update_username():
                global current_user_id
                new_username = new_username_box.get().strip()
                password = passwo_box.get().strip()

                if not new_username or not password:
                    messagebox.showwarning("Missing Info", "Please fill in all fields.")
                    return

                connection = create_connection()
                if connection:
                    try:
                        cursor = connection.cursor()
                        cursor.execute("SELECT password FROM users WHERE id = ?",(current_user_id,))
                        user_row = cursor.fetchone()

                        if user_row:
                            stored_password = user_row[0]
                            if check_password_hash(stored_password,password):
                                cursor.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, current_user_id))
                                connection.commit()
                                messagebox.showinfo("Success", "Username updated successfully!")
                        else:
                            messagebox.showerror("Authentication Failed", "Incorrect password.")
                    except sqlite3.Error as e:
                        messagebox.showerror("Database Error", str(e))
                    finally:
                        if connection:
                            connection.close()

            change_user_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                             corner_radius=0)
            change_user_frame.place(x=20, y=30)

            change_user_lbl = ctk.CTkLabel(change_user_frame, text="CHANGE USERNAME", font=('Arial', 33, 'bold'))
            change_user_lbl.place(x=10, y=16)

            new_username_lbl = ctk.CTkLabel(ipes_homepage_frame, text="New Username:", font=("Lato", 25, "bold"),
                                            bg_color="#c4d5d7")
            new_username_lbl.place(x=200, y=200)

            new_username_box = ctk.CTkEntry(ipes_homepage_frame, width=380, height=45, corner_radius=0,
                                            font=("Lato", 20), border_color='#000000',
                                            fg_color="#ffffff")
            new_username_box.place(x=400, y=195)

            passwo_lbl = ctk.CTkLabel(ipes_homepage_frame, text="Password:", font=("Lato", 25, "bold"),
                                      bg_color="#c4d5d7")
            passwo_lbl.place(x=260, y=340)

            passwo_box = ctk.CTkEntry(ipes_homepage_frame, width=380, height=45, corner_radius=0, font=("Lato", 20),
                                      border_color='#000000',
                                      fg_color="#ffffff")
            passwo_box.place(x=400, y=335)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=profile_settings)
            back_btn.place(x=50, y=630)

            update_user_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Update User",
                                            hover_color="#60646b", text_color="#ffffff",command=update_username,
                                            font=('Arial', 18), fg_color="#405460", corner_radius=10)
            update_user_btn.place(x=1100, y=630)

        def changing_of_password():
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            def update_password():
                old_pass = old_passwrd_box.get().strip()
                new_pass = new_passwrd_box.get().strip()
                confirm_pass = con_passwrd_box.get().strip()

                if not old_pass or not new_pass or not confirm_pass:
                    messagebox.showwarning("Missing Info", "Please fill in all fields.")
                    return

                if new_pass != confirm_pass:
                    messagebox.showwarning("Mismatch", "New and confirm passwords do not match.")
                    return

                password_pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
                if not re.match(password_pattern, new_pass):
                    messagebox.showerror("Error",
                                         "Password must contain:\n"
                                         "- At least 8 characters\n"
                                         "- Letters, numbers, and special symbols")
                    return

                connection = create_connection()
                if connection:
                    try:
                        cursor = connection.cursor()
                        cursor.execute("SELECT password FROM users WHERE id = ?", (current_user_id,))
                        user_row = cursor.fetchone()

                        if user_row:
                            hashed_new = generate_password_hash(new_pass)
                            stored_password = user_row[0]
                            if check_password_hash(stored_password, old_pass):
                                cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_new, current_user_id))
                                connection.commit()
                                messagebox.showinfo("Success", "Password updated successfully!")
                                profile_settings()
                        else:
                            messagebox.showerror("Authentication Failed", "Old password is incorrect.")
                    except sqlite3.Error as e:
                        messagebox.showerror("Database Error", str(e))
                    finally:
                        if connection:
                            connection.close()

            change_passwrd_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                                corner_radius=0)
            change_passwrd_frame.place(x=20, y=30)

            change_passwrd_lbl = ctk.CTkLabel(change_passwrd_frame, text="CHANGE PASSWORD", font=('Arial', 33, 'bold'))
            change_passwrd_lbl.place(x=10, y=16)

            old_passwrd_lbl = ctk.CTkLabel(ipes_homepage_frame, text="Old Password:", font=("Lato", 25, "bold"),
                                           bg_color="#c4d5d7")
            old_passwrd_lbl.place(x=200, y=200)

            old_passwrd_box = ctk.CTkEntry(ipes_homepage_frame, width=380, height=45, corner_radius=0,
                                           font=("Lato", 20),
                                           border_color='#000000',
                                           fg_color="#ffffff")
            old_passwrd_box.place(x=400, y=195)

            new_passwrd_lbl = ctk.CTkLabel(ipes_homepage_frame, text="New Password:", font=("Lato", 25, "bold"),
                                           bg_color="#c4d5d7")
            new_passwrd_lbl.place(x=200, y=340)

            new_passwrd_box = ctk.CTkEntry(ipes_homepage_frame, width=380, height=45, corner_radius=0,
                                           font=("Lato", 20),
                                           border_color='#000000',
                                           fg_color="#ffffff")
            new_passwrd_box.place(x=400, y=335)

            con_passwrd_lbl = ctk.CTkLabel(ipes_homepage_frame, text="Confirm Password:", font=("Lato", 25, "bold"),
                                           bg_color="#c4d5d7")
            con_passwrd_lbl.place(x=160, y=485)

            con_passwrd_box = ctk.CTkEntry(ipes_homepage_frame, width=380, height=45, corner_radius=0,
                                           font=("Lato", 20),
                                           border_color='#000000',
                                           fg_color="#ffffff")
            con_passwrd_box.place(x=400, y=480)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=profile_settings)
            back_btn.place(x=50, y=630)

            update_pass_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Update Password",
                                            hover_color="#60646b", text_color="#ffffff", command=update_password,
                                            font=('Arial', 18), fg_color="#405460", corner_radius=10)
            update_pass_btn.place(x=1100, y=630)

        def manage_section():
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            sections = []
            current_user_sections = []

            def fetch_user_sections():
                nonlocal current_user_sections
                connection = create_connection()
                if connection:
                    try:
                        cursor = connection.cursor()
                        cursor.execute("SELECT section FROM user_sections WHERE user_id = ?", (current_user_id,))
                        current_user_sections = [row[0] for row in cursor.fetchall()]
                    except sqlite3.Error as e:
                        messagebox.showerror("Database Error", f"Failed to fetch sections: {str(e)}")
                    finally:
                        if connection:
                            connection.close()

            def update_sections():
                selected_sections = [combo.get() for combo in sections if combo.get() != "Select a Section"]

                if not selected_sections:
                    messagebox.showwarning("No Sections", "Please select at least one section")
                    return

                if len(selected_sections) != len(set(selected_sections)):
                    messagebox.showwarning("Duplicate Sections", "You have selected the same section multiple times")
                    return

                connection = create_connection()
                if connection:
                    try:
                        cursor = connection.cursor()
                        cursor.execute("DELETE FROM user_sections WHERE user_id = ?", (current_user_id,))

                        for section in selected_sections:
                            cursor.execute("INSERT INTO user_sections (user_id, section) VALUES (?, ?)",  (current_user_id, section))

                        connection.commit()
                        messagebox.showinfo("Success", "Sections updated successfully!")
                    except sqlite3.Error as e:
                        connection.rollback()
                        messagebox.showerror("Database Error", f"Failed to update sections: {str(e)}")
                    finally:
                        if connection:
                            connection.close()



            def add_section():
                if len(sections) >= 4:
                    messagebox.showwarning("Limit Reached", "You can only add up to 4 sections.")
                    return

                selected_sections = [combo.get() for combo in sections if combo.get() != "Select a Section"]

                if sections and sections[-1].get() == "Select a Section":
                    messagebox.showwarning("Missing Selection", "Please select a section before adding a new one.")
                    return

                y_pos = 245 + (len(sections)) * 45

                section_list = ctk.CTkComboBox(
                    ipes_homepage_frame,
                    values=["4A", "4B", "4C", "4D"],
                    width=300,
                    corner_radius=10,
                    bg_color="#ffffff",
                    fg_color="#ffffff"
                )
                section_list.set("Select a Section")
                section_list.place(x=500, y=y_pos)
                sections.append(section_list)

                update_buttons()

            def remove_section():
                if sections:
                    last_section = sections.pop()
                    last_section.destroy()
                    update_buttons()

            def update_buttons():

                y_pos = 245 + len(sections) * 45 + 10

                add_btn.place(x=500, y=y_pos)

                if len(sections) > 1:
                    rmv_btn.place(x=680, y=y_pos)
                else:
                    rmv_btn.place_forget()


            fetch_user_sections()

            manage_section_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                                corner_radius=0)
            manage_section_frame.place(x=20, y=30)

            manage_section_lbl = ctk.CTkLabel(manage_section_frame, text="Manage Sections", font=('Arial', 25, 'bold'))
            manage_section_lbl.place(x=10, y=20)

            choose_section_bg = ctk.CTkImage(dark_image=Image.open(resource_path('choose.png')), size=(1300, 700))
            image_choose_section_bg = ctk.CTkLabel(ipes_homepage_frame, image=choose_section_bg, text='')
            image_choose_section_bg.place(x=0, y=100)

            section_1_lbl = ctk.CTkLabel(ipes_homepage_frame, text="Section:", font=("Lato", 13, "bold"),
                                         bg_color="#ffffff")
            section_1_lbl.place(x=500, y=220)

            for i, section in enumerate(current_user_sections):
                if i >= 4:  # Don't exceed 4 sections
                    break

                y_pos = 245 + i * 45
                section_list = ctk.CTkComboBox(
                    ipes_homepage_frame,
                    values=["4A", "4B", "4C", "4D"],
                    width=300,
                    corner_radius=10,
                    bg_color="#ffffff",
                    fg_color="#ffffff"
                )
                section_list.set(section)
                section_list.place(x=500, y=y_pos)
                sections.append(section_list)

                if not sections:
                    section_list = ctk.CTkComboBox(
                        ipes_homepage_frame,
                        values=["4A", "4B", "4C", "4D"],
                        width=300,
                        corner_radius=10,
                        bg_color="#ffffff",
                        fg_color="#ffffff"
                    )
                    section_list.set("Select a Section")
                    section_list.place(x=500, y=245)
                    sections.append(section_list)

            add_btn = ctk.CTkButton(ipes_homepage_frame, text="Add Section", width=120, height=30,
                                    hover_color="#60646b", text_color="#ffffff", bg_color="#ffffff",
                                    command=add_section,
                                    font=('Arial', 13), fg_color="#405460", corner_radius=10)

            rmv_btn = ctk.CTkButton(ipes_homepage_frame, text="Remove Section", width=120, height=30,
                                    hover_color="#60646b", text_color="#ffffff", bg_color="#ffffff",
                                    command=remove_section,
                                    font=('Arial', 13), fg_color="#405460", corner_radius=10)

            update_buttons()

            update_btn = ctk.CTkButton(ipes_homepage_frame, text="Update", width=300, height=35, hover_color="#60646b",
                                       text_color="#ffffff", bg_color="#ffffff", command= update_sections,
                                       font=('Arial', 15), fg_color="#405460", corner_radius=10)
            update_btn.place(x=500, y=485)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=profile_settings)
            back_btn.place(x=50, y=630)

        profile_header_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                            corner_radius=0)
        profile_header_frame.place(x=20, y=30)

        profile_set_lbl = ctk.CTkLabel(profile_header_frame, text="PROFILE SETTINGS", font=('Arial', 33, 'bold'))
        profile_set_lbl.place(x=10, y=16)

        change_username_btn = ctk.CTkButton(ipes_homepage_frame, width=400, height=170, text="Change Username",
                                            text_color="#FFFFFF", fg_color="#405460",
                                            font=('Arial', 28, 'bold'), hover_color='#60646b', border_color="#000000",
                                            border_width=4, corner_radius=20,
                                            command=changing_of_username)
        change_username_btn.place(x=250, y=150)

        change_password_btn = ctk.CTkButton(ipes_homepage_frame, width=400, height=170, text="Change Password",
                                            text_color="#FFFFFF", fg_color="#405460",
                                            font=('Arial', 28, 'bold'), hover_color='#60646b', border_color="#000000",
                                            border_width=4, corner_radius=20, command=changing_of_password)
        change_password_btn.place(x=250, y=400)

        view_history_frame = ctk.CTkFrame(ipes_homepage_frame, width=280, height=350, fg_color="#FFFFFF",
                                          corner_radius=0, border_width=3, border_color="#000000")
        view_history_frame.place(x=950, y=290)

        user_data, user_sections = fetch_user_data()
        user_name_lbl = ctk.CTkLabel(view_history_frame, text=user_data['username'] if user_data else "User", font=('Arial', 23, 'bold'))
        user_name_lbl.place(x=80, y=20)

        sections_text = "Section Handle:\n" + ", ".join(user_sections) \
            if user_sections else "No sections assigned"
        section_handled_lbl = ctk.CTkLabel(view_history_frame, text=sections_text,
                                           font=('Arial', 15, 'bold'))
        section_handled_lbl.place(x=90, y=160)

        my_prof_logo = ctk.CTkImage(light_image=Image.open(resource_path('myproficon.png')), size=(170, 170))
        my_prof_image_lbl = ctk.CTkLabel(ipes_homepage_frame, image=my_prof_logo, text='')
        my_prof_image_lbl.place(x=1000, y=110)

        view_manage_section_btn = ctk.CTkButton(view_history_frame, height=50, width=180, text="Manage Section",
                                                hover_color="#60646b", text_color="#000000",
                                                font=('Arial', 20), fg_color="#c4c9ca", corner_radius=0,
                                                command=manage_section)
        view_manage_section_btn.place(x=50, y=280)

        back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                 hover_color="#60646b", text_color="#ffffff",
                                 font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                 command=dashboard_homepage)
        back_btn.place(x=50, y=630)

    def performance_tracking():
        for widget in ipes_homepage_frame.winfo_children():
            widget.destroy()

        def get_performance_by_section(section):
            connection = create_connection()

            if connection:
                try:
                    cursor = connection.cursor()
                    query = """SELECT 
                    st.student_name,
                    -- Sums (for the main performance tracking view)
                    ROUND((se.work_attitude_1 + se.work_attitude_2 + se.work_attitude_3 + 
                          se.work_attitude_4 + se.work_attitude_5)) AS work_attitude,
                    ROUND((se.work_knowledge_1 + se.work_knowledge_2 + se.work_knowledge_3 + 
                          se.work_knowledge_4 + se.work_knowledge_5)) AS work_knowledge,
                    ROUND((se.personal_appearance_1 + se.personal_appearance_2 + 
                          se.personal_appearance_3 + se.personal_appearance_4 + 
                          se.personal_appearance_5)) AS personality,
                    ROUND((se.professional_competence_1 + se.professional_competence_2 + 
                          se.professional_competence_3 + se.professional_competence_4 + 
                          se.professional_competence_5)) AS professional_competence,
                    se.total_rating,
                    se.id as evaluation_id,
                    -- Individual scores (for the detailed view)
                    se.work_attitude_1, se.work_attitude_2, se.work_attitude_3, se.work_attitude_4, se.work_attitude_5,
                    se.work_knowledge_1, se.work_knowledge_2, se.work_knowledge_3, se.work_knowledge_4, se.work_knowledge_5,
                    se.personal_appearance_1, se.personal_appearance_2, se.personal_appearance_3, se.personal_appearance_4, se.personal_appearance_5,
                    se.professional_competence_1, se.professional_competence_2, se.professional_competence_3, se.professional_competence_4, se.professional_competence_5
                FROM student_trainees st
                JOIN student_evaluations se ON st.id = se.student_id
                WHERE st.section = ?
                ORDER BY st.student_name"""

                    cursor.execute(query, (section,))
                    columns = [col[0] for col in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Failed to fetch performance data: {e}")
                    return []
                finally:
                    if connection:
                        connection.close()
            return []

        def see_graph_details(student, back_callback):
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            # Header Frame
            header_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff")
            header_frame.place(x=20, y=30)

            ctk.CTkLabel(header_frame, text=f"Performance Details: {student['student_name']}",
                         font=('Arial', 25, 'bold')).place(x=10, y=20)

            # Main Scrollable Content
            scroll_frame = ctk.CTkScrollableFrame(ipes_homepage_frame, width=1250, height=500)
            scroll_frame.place(x=20, y=110)

            # Verify we have all required data
            required_fields = [
                'work_attitude_1', 'work_attitude_2', 'work_attitude_3', 'work_attitude_4', 'work_attitude_5',
                'work_knowledge_1', 'work_knowledge_2', 'work_knowledge_3', 'work_knowledge_4', 'work_knowledge_5',
                'personal_appearance_1', 'personal_appearance_2', 'personal_appearance_3', 'personal_appearance_4',
                'personal_appearance_5',
                'professional_competence_1', 'professional_competence_2', 'professional_competence_3',
                'professional_competence_4', 'professional_competence_5'
            ]

            if not all(field in student for field in required_fields):
                # If missing data, fetch the complete evaluation record
                connection = create_connection()
                if connection:
                    try:
                        cursor = connection.cursor()
                        query = """SELECT * FROM student_evaluations WHERE id = ?"""
                        cursor.execute(query, (student['evaluation_id'],))
                        detailed_data = cursor.fetchone()
                        student.update(detailed_data)  # Merge the detailed data
                    except sqlite3.Error as e:
                        messagebox.showerror("Database Error", f"Failed to fetch detailed evaluation: {e}")
                        back_callback()
                        return
                    finally:
                        if connection:
                            connection.close()

            for field in required_fields:
                if field not in student:
                    messagebox.showerror("Error", f"Missing data field: {field}")
                    back_callback()
                    return

            # Create plots frame
            plots_frame = ctk.CTkFrame(scroll_frame, fg_color="#ffffff")
            plots_frame.pack(fill='both', expand=True, padx=10, pady=10)

            # Create figure with 5 subplots (1 summary + 4 categories)
            fig = Figure(figsize=(10, 18), dpi=100)

            # 1. Summary Plot
            ax1 = fig.add_subplot(511)
            categories = ['Work Attitude', 'Work Knowledge', 'Personality', 'Professional Competence']
            totals = [
                sum([student[f'work_attitude_{i}'] for i in range(1, 6)]),
                sum([student[f'work_knowledge_{i}'] for i in range(1, 6)]),
                sum([student[f'personal_appearance_{i}'] for i in range(1, 6)]),
                sum([student[f'professional_competence_{i}'] for i in range(1, 6)])
            ]

            bars = ax1.bar(categories, totals, color=['#405460', '#5D7B93', '#7FA3B7', '#A1C4D9'])
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width() / 2, height, f'{height}', ha='center', va='bottom')
            ax1.set_title('Total Scores by Category', pad=20)
            ax1.set_ylim(0, 25)

            # 2. Work Attitude Details
            ax2 = fig.add_subplot(512)
            attitude_scores = [student[f'work_attitude_{i}'] for i in range(1, 6)]
            items = [f'Item {i}' for i in range(1, 6)]
            bars = ax2.bar(items, attitude_scores, color='#405460')
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2, height, f'{height}', ha='center', va='bottom')
            ax2.set_title('Work Attitude Scores', pad=20)
            ax2.set_ylim(0, 5)

            # 3. Work Knowledge Details
            ax3 = fig.add_subplot(513)
            knowledge_scores = [student[f'work_knowledge_{i}'] for i in range(1, 6)]
            bars = ax3.bar(items, knowledge_scores, color='#5D7B93')
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width() / 2, height, f'{height}', ha='center', va='bottom')
            ax3.set_title('Work Knowledge Scores', pad=20)
            ax3.set_ylim(0, 5)

            # 4. Personality Details
            ax4 = fig.add_subplot(514)
            personality_scores = [student[f'personal_appearance_{i}'] for i in range(1, 6)]
            bars = ax4.bar(items, personality_scores, color='#7FA3B7')
            for bar in bars:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width() / 2, height, f'{height}', ha='center', va='bottom')
            ax4.set_title('Personality Scores', pad=20)
            ax4.set_ylim(0, 5)

            # 5. Professional Competence Details
            ax5 = fig.add_subplot(515)
            competence_scores = [student[f'professional_competence_{i}'] for i in range(1, 6)]
            bars = ax5.bar(items, competence_scores, color='#A1C4D9')
            for bar in bars:
                height = bar.get_height()
                ax5.text(bar.get_x() + bar.get_width() / 2, height, f'{height}', ha='center', va='bottom')
            ax5.set_title('Professional Competence Scores', pad=20)
            ax5.set_ylim(0, 5)

            fig.tight_layout(pad=3.0)

            # Embed plot
            canvas = FigureCanvasTkAgg(fig, master=plots_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)

            # Total Rating
            total_frame = ctk.CTkFrame(ipes_homepage_frame, width=350, height=60, fg_color="#f1f5fb")
            total_frame.place(x=550, y=630)
            ctk.CTkLabel(total_frame, text=f"TOTAL RATING: {int(student.get('total_rating', 0))}",
                         font=("Arial", 20, "bold")).pack(pady=15)

            # Back Button
            back_btn = ctk.CTkButton(ipes_homepage_frame, text="Back", width=160, height=40,
                                     fg_color="#405460", font=('Arial', 18),
                                     command=back_callback)
            back_btn.place(x=50, y=630)

        def get_evaluated_student_count(section):
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    query = """SELECT COUNT(*) 
                           FROM student_trainees st
                           JOIN student_evaluations se ON st.id = se.student_id
                           WHERE st.section = ?"""
                    cursor.execute(query, (section,))
                    count = cursor.fetchone()[0]
                    return count
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Failed to get evaluated student count: {e}")
                    return 0
                finally:
                    if connection:
                        connection.close()
            return 0

        def performance_tracking_4A():
            user_sections = get_user_sections()
            if "4A" not in user_sections:
                messagebox.showerror("Access Denied", "You are not assigned to handle this section!")
                performance_tracking()
                return
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            perform_4A_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                            corner_radius=0)
            perform_4A_frame.place(x=20, y=30)

            perform_4A_lbl = ctk.CTkLabel(perform_4A_frame, text="PERFORMANCE TRACKING 4-A", font=('Arial', 33, 'bold'))
            perform_4A_lbl.place(x=10, y=16)

            view_4A_frame = ctk.CTkFrame(ipes_homepage_frame, fg_color="#c4d5d7", width=1275, height=520,
                                         corner_radius=0)
            view_4A_frame.place(x=0, y=110)

            scroll_view_4A_frame = ctk.CTkScrollableFrame(view_4A_frame, width=1200, height=450)
            scroll_view_4A_frame.place(x=33, y=0)

            headers_frame = ctk.CTkFrame(scroll_view_4A_frame, fg_color="#f1f5fb", height=50)
            headers_frame.pack(fill="x", pady=(10, 20))

            ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 14, "bold")).place(x=20, y=10)
            ctk.CTkLabel(headers_frame, text="Work Attitude", width=150, font=("Arial", 14, "bold")).place(x=180, y=10)
            ctk.CTkLabel(headers_frame, text="Work Knowledge", width=150, font=("Arial", 14, "bold")).place(x=355, y=10)
            ctk.CTkLabel(headers_frame, text="Personality", width=150, font=("Arial", 14, "bold")).place(x=530, y=10)
            ctk.CTkLabel(headers_frame, text="Professional Competence", width=160, font=("Arial", 14, "bold")).place(
                x=700, y=10)
            ctk.CTkLabel(headers_frame, text="Total Rating", width=150, font=("Arial", 14, "bold")).place(x=890, y=10)
            ctk.CTkLabel(headers_frame, text="Action", width=120, font=("Arial", 14, "bold")).place(x=1060, y=10)

            performance_data = get_performance_by_section("4A")

            for student in performance_data:
                student_frame = ctk.CTkFrame(scroll_view_4A_frame, fg_color="#ffffff", height=40)
                student_frame.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(student_frame, text=student['student_name'], width=120, font=("Arial", 14)).place(x=20,
                                                                                                               y=5)
                ctk.CTkLabel(student_frame, text=f"{student['work_attitude']}", width=150, font=("Arial", 14)).place(
                    x=165, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['work_knowledge']}", width=150, font=("Arial", 14)).place(
                    x=340, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['personality']}", width=150, font=("Arial", 14)).place(
                    x=515, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['professional_competence']}", width=160,
                             font=("Arial", 14)).place(x=700, y=5)
                int_value = int(student['total_rating'])
                ctk.CTkLabel(student_frame, text=f"{int_value}", width=150, font=("Arial", 14)).place(x=880, y=5)

                see_graph_btn = ctk.CTkButton(student_frame, text="See Graph", width=90, height=27,
                                              corner_radius=8, fg_color="#405460", hover_color="#60646B",
                                              command=lambda s=student: see_graph_details(s, performance_tracking_4A),
                                              font=("Arial", 12))
                see_graph_btn.place(x=1060, y=7)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=performance_tracking)
            back_btn.place(x=50, y=630)

        def performance_tracking_4B():
            user_sections = get_user_sections()
            if "4B" not in user_sections:
                messagebox.showerror("Access Denied", "You are not assigned to handle this section!")
                performance_tracking()
                return

            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            perform_4B_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                            corner_radius=0)
            perform_4B_frame.place(x=20, y=30)

            perform_4B_lbl = ctk.CTkLabel(perform_4B_frame, text="PERFORMANCE TRACKING 4-B", font=('Arial', 33, 'bold'))
            perform_4B_lbl.place(x=10, y=16)

            view_4B_frame = ctk.CTkFrame(ipes_homepage_frame, fg_color="#c4d5d7", width=1275, height=520,
                                         corner_radius=0)
            view_4B_frame.place(x=0, y=110)

            scroll_view_4B_frame = ctk.CTkScrollableFrame(view_4B_frame, width=1200, height=450)
            scroll_view_4B_frame.place(x=33, y=0)

            headers_frame = ctk.CTkFrame(scroll_view_4B_frame, fg_color="#f1f5fb", height=50)
            headers_frame.pack(fill="x", pady=(10, 20))

            ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 14, "bold")).place(x=20, y=10)
            ctk.CTkLabel(headers_frame, text="Work Attitude", width=150, font=("Arial", 14, "bold")).place(x=180, y=10)
            ctk.CTkLabel(headers_frame, text="Work Knowledge", width=150, font=("Arial", 14, "bold")).place(x=355, y=10)
            ctk.CTkLabel(headers_frame, text="Personality", width=150, font=("Arial", 14, "bold")).place(x=530, y=10)
            ctk.CTkLabel(headers_frame, text="Professional Competence", width=160, font=("Arial", 14, "bold")).place(
                x=700, y=10)
            ctk.CTkLabel(headers_frame, text="Total Rating", width=150, font=("Arial", 14, "bold")).place(x=890, y=10)
            ctk.CTkLabel(headers_frame, text="Action", width=120, font=("Arial", 14, "bold")).place(x=1060, y=10)

            performance_data = get_performance_by_section("4B")

            for student in performance_data:
                student_frame = ctk.CTkFrame(scroll_view_4B_frame, fg_color="#ffffff", height=40)
                student_frame.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(student_frame, text=student['student_name'], width=120, font=("Arial", 14)).place(x=20,
                                                                                                               y=5)
                ctk.CTkLabel(student_frame, text=f"{student['work_attitude']}", width=150, font=("Arial", 14)).place(
                    x=165, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['work_knowledge']}", width=150, font=("Arial", 14)).place(
                    x=340, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['personality']}", width=150, font=("Arial", 14)).place(
                    x=515, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['professional_competence']}", width=160,
                             font=("Arial", 14)).place(x=700, y=5)
                int_value = int(student['total_rating'])
                ctk.CTkLabel(student_frame, text=f"{int_value}", width=150, font=("Arial", 14)).place(x=880, y=5)

                see_graph_btn = ctk.CTkButton(student_frame, text="See Graph", width=90, height=27,
                                              corner_radius=8, fg_color="#405460", hover_color="#60646B",
                                              command=lambda s=student: see_graph_details(s, performance_tracking_4B),
                                              font=("Arial", 12))
                see_graph_btn.place(x=1060, y=7)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=performance_tracking)
            back_btn.place(x=50, y=630)

        def performance_tracking_4C():
            user_sections = get_user_sections()
            if "4C" not in user_sections:
                messagebox.showerror("Access Denied", "You are not assigned to handle this section!")
                performance_tracking()
                return
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            perform_4C_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                            corner_radius=0)
            perform_4C_frame.place(x=20, y=30)

            perform_4C_lbl = ctk.CTkLabel(perform_4C_frame, text="PERFORMANCE TRACKING 4-C", font=('Arial', 33, 'bold'))
            perform_4C_lbl.place(x=10, y=16)

            view_4C_frame = ctk.CTkFrame(ipes_homepage_frame, fg_color="#c4d5d7", width=1275, height=520,
                                         corner_radius=0)
            view_4C_frame.place(x=0, y=110)

            scroll_view_4C_frame = ctk.CTkScrollableFrame(view_4C_frame, width=1200, height=450)
            scroll_view_4C_frame.place(x=33, y=0)

            headers_frame = ctk.CTkFrame(scroll_view_4C_frame, fg_color="#f1f5fb", height=50)
            headers_frame.pack(fill="x", pady=(10, 20))

            ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 14, "bold")).place(x=20, y=10)
            ctk.CTkLabel(headers_frame, text="Work Attitude", width=150, font=("Arial", 14, "bold")).place(x=180, y=10)
            ctk.CTkLabel(headers_frame, text="Work Knowledge", width=150, font=("Arial", 14, "bold")).place(x=355, y=10)
            ctk.CTkLabel(headers_frame, text="Personality", width=150, font=("Arial", 14, "bold")).place(x=530, y=10)
            ctk.CTkLabel(headers_frame, text="Professional Competence", width=160, font=("Arial", 14, "bold")).place(
                x=700, y=10)
            ctk.CTkLabel(headers_frame, text="Total Rating", width=150, font=("Arial", 14, "bold")).place(x=890, y=10)
            ctk.CTkLabel(headers_frame, text="Action", width=120, font=("Arial", 14, "bold")).place(x=1060, y=10)

            performance_data = get_performance_by_section("4C")

            for student in performance_data:
                student_frame = ctk.CTkFrame(scroll_view_4C_frame, fg_color="#ffffff", height=40)
                student_frame.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(student_frame, text=student['student_name'], width=120, font=("Arial", 14)).place(x=20,
                                                                                                               y=5)
                ctk.CTkLabel(student_frame, text=f"{student['work_attitude']}", width=150, font=("Arial", 14)).place(
                    x=165, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['work_knowledge']}", width=150, font=("Arial", 14)).place(
                    x=340, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['personality']}", width=150, font=("Arial", 14)).place(
                    x=515, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['professional_competence']}", width=160,
                             font=("Arial", 14)).place(x=700, y=5)
                int_value = int(student['total_rating'])
                ctk.CTkLabel(student_frame, text=f"{int_value}", width=150, font=("Arial", 14)).place(x=880, y=5)

                see_graph_btn = ctk.CTkButton(student_frame, text="See Graph", width=90, height=27,
                                              corner_radius=8, fg_color="#405460", hover_color="#60646B",
                                              command=lambda s=student: see_graph_details(s, performance_tracking_4C),
                                              font=("Arial", 12))
                see_graph_btn.place(x=1060, y=7)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=performance_tracking)
            back_btn.place(x=50, y=630)

        def performance_tracking_4D():
            user_sections = get_user_sections()
            if "4D" not in user_sections:
                messagebox.showerror("Access Denied", "You are not assigned to handle this section!")
                performance_tracking()
                return

            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            perform_4D_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                            corner_radius=0)
            perform_4D_frame.place(x=20, y=30)

            perform_4D_lbl = ctk.CTkLabel(perform_4D_frame, text="PERFORMANCE TRACKING 4-D", font=('Arial', 33, 'bold'))
            perform_4D_lbl.place(x=10, y=16)

            view_4D_frame = ctk.CTkFrame(ipes_homepage_frame, fg_color="#c4d5d7", width=1275, height=520,
                                         corner_radius=0)
            view_4D_frame.place(x=0, y=110)

            scroll_view_4D_frame = ctk.CTkScrollableFrame(view_4D_frame, width=1200, height=450)
            scroll_view_4D_frame.place(x=33, y=0)

            headers_frame = ctk.CTkFrame(scroll_view_4D_frame, fg_color="#f1f5fb", height=50)
            headers_frame.pack(fill="x", pady=(10, 20))

            ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 14, "bold")).place(x=20, y=10)
            ctk.CTkLabel(headers_frame, text="Work Attitude", width=150, font=("Arial", 14, "bold")).place(x=180, y=10)
            ctk.CTkLabel(headers_frame, text="Work Knowledge", width=150, font=("Arial", 14, "bold")).place(x=355, y=10)
            ctk.CTkLabel(headers_frame, text="Personality", width=150, font=("Arial", 14, "bold")).place(x=530, y=10)
            ctk.CTkLabel(headers_frame, text="Professional Competence", width=160, font=("Arial", 14, "bold")).place(
                x=700, y=10)
            ctk.CTkLabel(headers_frame, text="Total Rating", width=150, font=("Arial", 14, "bold")).place(x=890, y=10)
            ctk.CTkLabel(headers_frame, text="Action", width=120, font=("Arial", 14, "bold")).place(x=1060, y=10)

            performance_data = get_performance_by_section("4D")

            for student in performance_data:
                student_frame = ctk.CTkFrame(scroll_view_4D_frame, fg_color="#ffffff", height=40)
                student_frame.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(student_frame, text=student['student_name'], width=120, font=("Arial", 14)).place(x=20,
                                                                                                               y=5)
                ctk.CTkLabel(student_frame, text=f"{student['work_attitude']}", width=150, font=("Arial", 14)).place(
                    x=165, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['work_knowledge']}", width=150, font=("Arial", 14)).place(
                    x=340, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['personality']}", width=150, font=("Arial", 14)).place(
                    x=515, y=5)
                ctk.CTkLabel(student_frame, text=f"{student['professional_competence']}", width=160,
                             font=("Arial", 14)).place(x=700, y=5)
                int_value = int(student['total_rating'])
                ctk.CTkLabel(student_frame, text=f"{int_value}", width=150, font=("Arial", 14)).place(x=880, y=5)

                see_graph_btn = ctk.CTkButton(student_frame, text="See Graph", width=90, height=27,
                                              command=lambda s=student: see_graph_details(s, performance_tracking_4D),
                                              corner_radius=8, fg_color="#405460", hover_color="#60646B",
                                              font=("Arial", 12))
                see_graph_btn.place(x=1060, y=7)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=performance_tracking)
            back_btn.place(x=50, y=630)

        num_stud_4A = get_evaluated_student_count("4A")
        num_stud_4B = get_evaluated_student_count("4B")
        num_stud_4C = get_evaluated_student_count("4C")
        num_stud_4D = get_evaluated_student_count("4D")

        perform_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                     corner_radius=0)
        perform_frame.place(x=20, y=30)

        perform_lbl = ctk.CTkLabel(perform_frame, text="PERFORMANCE TRACKING", font=('Arial', 33, 'bold'))
        perform_lbl.place(x=10, y=16)

        sechandle_bg = ctk.CTkImage(dark_image=Image.open(resource_path('section_performance.png')), size=(1300, 700))
        image_sechandle_bg = ctk.CTkLabel(ipes_homepage_frame, image=sechandle_bg, text='')
        image_sechandle_bg.place(x=0, y=100)

        num_stud_4A_lbl = ctk.CTkLabel(ipes_homepage_frame, text=str(num_stud_4A), font=('Arial', 25, 'bold'),
                                       text_color="#000000",
                                       bg_color="#FFFFFF")
        num_stud_4A_lbl.place(x=650, y=330)

        four_A_lbl = ctk.CTkLabel(ipes_homepage_frame, text="4A", font=("Arial", 20, 'bold'), text_color="#000000",
                                  bg_color="#FFFFFF")
        four_A_lbl.place(x=330, y=330)

        four_A_btn = ctk.CTkButton(ipes_homepage_frame, height=20, width=100, text="View",
                                   hover_color="#60646b", text_color="#ffffff", bg_color="#FFFFFF",
                                   font=('Arial', 15), fg_color="#405460", corner_radius=10,
                                   command=performance_tracking_4A)
        four_A_btn.place(x=930, y=330)

        num_stud_4B_lbl = ctk.CTkLabel(ipes_homepage_frame, text=str(num_stud_4B), font=('Arial', 25, 'bold'),
                                       text_color="#000000",
                                       bg_color="#FFFFFF")
        num_stud_4B_lbl.place(x=650, y=400)

        four_B_lbl = ctk.CTkLabel(ipes_homepage_frame, text="4B", font=("Arial", 20, 'bold'), text_color="#000000",
                                  bg_color="#FFFFFF")
        four_B_lbl.place(x=330, y=400)

        four_B_btn = ctk.CTkButton(ipes_homepage_frame, height=20, width=100, text="View",
                                   hover_color="#60646b", text_color="#ffffff", bg_color="#FFFFFF",
                                   font=('Arial', 15), fg_color="#405460", corner_radius=10,
                                   command=performance_tracking_4B)
        four_B_btn.place(x=930, y=400)

        num_stud_4C_lbl = ctk.CTkLabel(ipes_homepage_frame, text=str(num_stud_4C), font=('Arial', 25, 'bold'),
                                       text_color="#000000",
                                       bg_color="#FFFFFF")
        num_stud_4C_lbl.place(x=650, y=475)

        four_C_lbl = ctk.CTkLabel(ipes_homepage_frame, text="4C", font=("Arial", 20, 'bold'), text_color="#000000",
                                  bg_color="#FFFFFF")
        four_C_lbl.place(x=330, y=475)

        four_C_btn = ctk.CTkButton(ipes_homepage_frame, height=20, width=100, text="View",
                                   hover_color="#60646b", text_color="#ffffff", bg_color="#FFFFFF",
                                   font=('Arial', 15), fg_color="#405460", corner_radius=10,
                                   command=performance_tracking_4C)
        four_C_btn.place(x=930, y=475)

        num_stud_4D_lbl = ctk.CTkLabel(ipes_homepage_frame, text=str(num_stud_4D), font=('Arial', 25, 'bold'),
                                       text_color="#000000",
                                       bg_color="#FFFFFF")
        num_stud_4D_lbl.place(x=650, y=550)

        four_D_lbl = ctk.CTkLabel(ipes_homepage_frame, text="4D", font=("Arial", 20, 'bold'), text_color="#000000",
                                  bg_color="#FFFFFF")
        four_D_lbl.place(x=330, y=550)

        four_D_btn = ctk.CTkButton(ipes_homepage_frame, height=20, width=100, text="View",
                                   hover_color="#60646b", text_color="#ffffff", bg_color="#FFFFFF",
                                   font=('Arial', 15), fg_color="#405460", corner_radius=10,
                                   command=performance_tracking_4D)
        four_D_btn.place(x=930, y=550)

        back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                 hover_color="#60646b", text_color="#ffffff",
                                 font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                 command=dashboard_homepage)
        back_btn.place(x=50, y=630)

    def my_class():
        for widget in ipes_homepage_frame.winfo_children():
            widget.destroy()

        def add_student():
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            def open_calendar():
                top = ctk.CTkToplevel()
                top.title("Select Training Period")
                top.geometry("300x200")
                top.update_idletasks()
                window_width = 300
                window_height = 200
                screen_width = top.winfo_screenwidth()
                screen_height = top.winfo_screenheight()
                x = int((screen_width / 2) - (window_width / 2))
                y = int((screen_height / 2) - (window_height / 2))
                top.geometry(f"{window_width}x{window_height}+{x}+{y}")
                top.lift()
                top.focus_force()
                top.grab_set()

                def save_dates():
                    start = start_cal.get_date()
                    end = end_cal.get_date()
                    training_period_entry.delete(0, "end")
                    training_period_entry.insert(0, f"{start} - {end}")
                    top.destroy()

                start_label = ctk.CTkLabel(top, text="Start Date", font=("Lato", 17))
                start_label.pack(pady=(10, 0))

                start_cal = DateEntry(top, width=20, background='darkblue',
                                      foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
                start_cal.pack(pady=10)

                end_label = ctk.CTkLabel(top, text="End Date", font=("Lato", 17))
                end_label.pack(pady=(10, 0))

                end_cal = DateEntry(top, width=20, background='darkblue',
                                    foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
                end_cal.pack(pady=10)

                save_btn = ctk.CTkButton(top, text="Save", command=save_dates, width=120)
                save_btn.pack(pady=15)

            def save_student_data():
                connection = create_connection()
                if connection:
                    try:
                        cursor = connection.cursor()

                        student_name = complete_name_student.get().strip()
                        hte_name = name_of_HTE.get().strip()
                        hte_address = complete_address_HTE.get().strip()
                        hours_rendered = number_hours_rendered.get().strip()
                        supervisor_contact = contact_number_HTE.get().strip()
                        supervisor_email = email_address_HTE.get().strip()
                        training_period = training_period_entry.get().strip()
                        section = section_cmbbox.get().strip()

                        if not all([student_name, hte_name, hte_address, hours_rendered,
                                    supervisor_contact, supervisor_email, training_period, section]):
                            messagebox.showerror("Error", "Please fill all required fields!")
                            return

                        try:
                            hours_rendered = int(hours_rendered)
                            if hours_rendered <= 0:
                                messagebox.showerror("Error", "Hours rendered must be greater than 0!")
                                return
                        except ValueError:
                            messagebox.showerror("Error", "Hours rendered must be a valid number!")
                            return

                        if supervisor_email and not re.match(r"[^@]+@[^@]+\.[^@]+", supervisor_email):
                            messagebox.showerror("Error", "Invalid email format!")
                            return

                        query = """
                        INSERT INTO student_trainees (student_name, hte_name, hte_address, hours_rendered, supervisor_contact,
                        supervisor_email, training_period, section) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

                        cursor.execute(query, (student_name, hte_name, hte_address, hours_rendered, supervisor_contact,
                                               supervisor_email, training_period, section))
                        connection.commit()
                        messagebox.showinfo("Success", "Student trainee added successfully!")

                        complete_name_student.delete(0, 'end')
                        name_of_HTE.delete(0, 'end')
                        complete_address_HTE.delete(0, 'end')
                        number_hours_rendered.delete(0, 'end')
                        contact_number_HTE.delete(0, 'end')
                        email_address_HTE.delete(0, 'end')
                        training_period_entry.delete(0, 'end')
                        section_cmbbox.set("--Select a Section--")

                    except sqlite3.Error as e:
                        messagebox.showerror("Database Error", f"Failed to save student: {e}")
                    finally:
                        if connection:
                            connection.close()

            evaluate_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                          corner_radius=0)
            evaluate_frame.place(x=20, y=30)

            perform_lbl = ctk.CTkLabel(evaluate_frame, text="CPE-OJT EVALUATION SHEET", font=('Arial', 33, 'bold'))
            perform_lbl.place(x=10, y=16)

            add_klass_bg = ctk.CTkImage(dark_image=Image.open(resource_path('addklass.png')), size=(1300, 700))
            image_add_klass_bg = ctk.CTkLabel(ipes_homepage_frame, image=add_klass_bg, text='')
            image_add_klass_bg.place(x=0, y=100)

            complete_name_student = ctk.CTkEntry(ipes_homepage_frame, width=250, height=40, corner_radius=10,
                                                 font=("Lato", 14),
                                                 fg_color="#ffffff", bg_color="#ffffff")
            complete_name_student.place(x=340, y=215)

            name_of_HTE = ctk.CTkEntry(ipes_homepage_frame, width=250, height=40, corner_radius=10,
                                       font=("Lato", 14),
                                       fg_color="#ffffff", bg_color="#ffffff")
            name_of_HTE.place(x=340, y=290)

            complete_address_HTE = ctk.CTkEntry(ipes_homepage_frame, width=250, height=40, corner_radius=10,
                                                font=("Lato", 14),
                                                fg_color="#ffffff", bg_color="#ffffff")
            complete_address_HTE.place(x=340, y=365)

            number_hours_rendered = ctk.CTkEntry(ipes_homepage_frame, width=250, height=40, corner_radius=10,
                                                 font=("Lato", 14),
                                                 fg_color="#ffffff", bg_color="#ffffff")
            number_hours_rendered.place(x=340, y=444)

            contact_number_HTE = ctk.CTkEntry(ipes_homepage_frame, width=250, height=40, corner_radius=10,
                                              font=("Lato", 14),
                                              fg_color="#ffffff", bg_color="#ffffff")
            contact_number_HTE.place(x=700, y=215)

            email_address_HTE = ctk.CTkEntry(ipes_homepage_frame, width=250, height=40, corner_radius=10,
                                             font=("Lato", 14),
                                             fg_color="#ffffff", bg_color="#ffffff")
            email_address_HTE.place(x=700, y=290)

            section_cmbbox = ctk.CTkComboBox(ipes_homepage_frame, width=250, height=40, values=["4A", "4B", "4C", "4D"],
                                             corner_radius=10, font=("Lato", 14),
                                             fg_color="#ffffff", bg_color="#ffffff")
            section_cmbbox.set("   --Select a Section--  ")
            section_cmbbox.place(x=700, y=444)

            training_period_entry = ctk.CTkEntry(ipes_homepage_frame, width=250, height=40, corner_radius=10,
                                                 font=("Lato", 14), fg_color="#ffffff", bg_color="#ffffff")
            training_period_entry.place(x=700, y=365)

            calendar_btn = ctk.CTkButton(ipes_homepage_frame, text="📅", width=35, height=35, corner_radius=10,
                                         bg_color="#ffffff",
                                         font=("Arial", 16), command=open_calendar)
            calendar_btn.place(x=900, y=367)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=my_class)
            back_btn.place(x=50, y=630)

            save_student_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Save Student",
                                             hover_color="#60646b", text_color="#ffffff",
                                             font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                             command=save_student_data)
            save_student_btn.place(x=1100, y=630)

        def get_students_by_section(section):
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    query = """SELECT id,student_name, hte_name, supervisor_email, hte_address, hours_rendered, training_period 
                                FROM student_trainees 
                                WHERE section = ?
                                ORDER BY student_name"""
                    cursor.execute(query, (section,))
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Failed to fetch students: {e}")
                    return []
                finally:
                    if connection:
                        connection.close()
            return []

        def evaluate_student(student, back_callback):
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            def save_grade_to_db(student_id, ratings, remarks, total_rating):
                connection = create_connection()
                cursor = connection.cursor()

                if len(ratings) != 20:
                    messagebox.showerror("Error", f"Expected 20 ratings, got {len(ratings)}")
                    return

                query = """
                        INSERT INTO student_evaluations 
                        (student_id, 
                         work_attitude_1, work_attitude_2, work_attitude_3, work_attitude_4, work_attitude_5,
                         work_knowledge_1, work_knowledge_2, work_knowledge_3, work_knowledge_4, work_knowledge_5,
                         personal_appearance_1, personal_appearance_2, personal_appearance_3, personal_appearance_4, personal_appearance_5,
                         professional_competence_1, professional_competence_2, professional_competence_3, professional_competence_4, professional_competence_5,
                         remarks, total_rating)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """

                try:
                    params = (
                        student_id,
                        *ratings[:20],  # Ensure exactly 20 ratings
                        remarks,
                        total_rating
                    )
                    cursor.execute(query, params)
                    connection.commit()
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Error saving evaluation: {str(e)}")
                    connection.rollback()
                finally:
                    if connection:
                        connection.close()

            def student_eval_form():
                nonlocal student

                work_att_combos = []
                work_knowledge_combos = []
                personal_appearance_combos = []
                professional_competence_combos = []

                guide_form_bg = ctk.CTkImage(dark_image=Image.open(resource_path('four.png')), size=(1300, 640))
                image_guide_form_bg = ctk.CTkLabel(evaluation_frame, image=guide_form_bg, text='')
                image_guide_form_bg.place(x=0, y=0)

                def work_att_and_habit():
                    nonlocal work_att_combos
                    positions = [(175, 175), (175, 208), (175, 241), (175, 274), (175, 307)]
                    for y in [175, 208, 241, 274, 307]:
                        combo = ctk.CTkComboBox(ipes_homepage_frame, values=["1", "2", "3", "4", "5"],
                                                corner_radius=10, bg_color="#ffffff",
                                                width=170, fg_color="#ffffff")
                        combo.set("--Select the score--")
                        combo.place(x=450, y=y)
                        work_att_combos.append(combo)

                def work_knowledge():
                    nonlocal work_knowledge_combos
                    for y in [178, 210, 242, 274, 306]:
                        combo = ctk.CTkComboBox(ipes_homepage_frame, values=["1", "2", "3", "4", "5"],
                                                corner_radius=10, bg_color="#ffffff",
                                                width=170, fg_color="#ffffff")
                        combo.set("--Select the score--")
                        combo.place(x=1090, y=y)
                        work_knowledge_combos.append(combo)

                def pers_appearance():
                    nonlocal personal_appearance_combos
                    for y in [413, 445, 478, 511, 544]:
                        combo = ctk.CTkComboBox(ipes_homepage_frame, values=["1", "2", "3", "4", "5"],
                                                corner_radius=10, bg_color="#ffffff",
                                                width=170, fg_color="#ffffff")
                        combo.set("--Select the score--")
                        combo.place(x=450, y=y)
                        personal_appearance_combos.append(combo)

                def prof_competence():
                    nonlocal professional_competence_combos
                    for y in [413, 445, 478, 511, 544]:
                        combo = ctk.CTkComboBox(ipes_homepage_frame, values=["1", "2", "3", "4", "5"],
                                                corner_radius=10, bg_color="#ffffff",
                                                width=170, fg_color="#ffffff")
                        combo.set("--Select the score--")
                        combo.place(x=1090, y=y)
                        professional_competence_combos.append(combo)

                def final_grade():
                    nonlocal work_att_combos, work_knowledge_combos, personal_appearance_combos, professional_competence_combos

                    try:
                        all_combos = work_att_combos + work_knowledge_combos + personal_appearance_combos + professional_competence_combos
                        scores = []

                        for combo in all_combos:
                            val = combo.get()
                            if val not in ["1", "2", "3", "4", "5"]:
                                raise ValueError("All fields must have a valid score selected (1-5).")
                            scores.append(int(val))
                    except Exception as e:
                        messagebox.showerror("Error", f"Please complete all fields before continuing.\n{e}")
                        return

                    for widget in ipes_homepage_frame.winfo_children():
                        widget.destroy()

                    evaluation_frame = ctk.CTkFrame(ipes_homepage_frame, fg_color="#c4d5d7", width=1275, height=570,
                                                    corner_radius=0)
                    evaluation_frame.place(x=0, y=110)

                    evaluate_student_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70,
                                                          fg_color="#ffffff",
                                                          corner_radius=0)
                    evaluate_student_frame.place(x=20, y=30)

                    perform_lbl = ctk.CTkLabel(evaluate_student_frame, text=f"Evaluating: {student['student_name']}",
                                               font=('Arial', 25, 'bold'))
                    perform_lbl.place(x=10, y=20)

                    remarks_frame = ctk.CTkFrame(ipes_homepage_frame, width=1000, height=430, fg_color="#ffffff",
                                                 corner_radius=20)
                    remarks_frame.place(x=150, y=130)

                    remarks_comments_lbl = ctk.CTkLabel(remarks_frame, text="Remarks/Comments/Suggestions: ",
                                                        font=("Arial", 15, "bold"), text_color="#000000")
                    remarks_comments_lbl.place(x=20, y=20)

                    remarks_comments_txtbox = ctk.CTkTextbox(remarks_frame, height=370, width=900)
                    remarks_comments_txtbox.place(x=50, y=50)

                    total_rating_frame = ctk.CTkFrame(ipes_homepage_frame, height=60, width=250, fg_color="#ffffff")
                    total_rating_frame.place(x=500, y=600)

                    total_rating_lbl = ctk.CTkLabel(total_rating_frame, text="TOTAL RATING:", font=("Arial", 20),
                                                    text_color="#000000")
                    total_rating_lbl.place(x=20, y=15)

                    def handle_save():

                        try:
                            total_rating = sum(scores)
                            total_rating_lbl.configure(text=f"TOTAL RATING: {total_rating}")
                            remarks = remarks_comments_txtbox.get("1.0", "end-1c").strip()
                            save_grade_to_db(student['id'], scores, remarks, total_rating)
                            messagebox.showinfo("Success", "Evaluation saved successfully.")
                            back_callback()
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to save evaluation: {str(e)}")

                    back_btn = ctk.CTkButton(evaluation_frame, height=40, width=160, text="Back",
                                             hover_color="#60646b", text_color="#ffffff",
                                             font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                             command=back_callback)
                    back_btn.place(x=50, y=520)

                    save_grade_btn = ctk.CTkButton(evaluation_frame, height=40, width=160, text="Save Grade",
                                                   hover_color="#60646b", text_color="#ffffff", command=handle_save,
                                                   font=('Arial', 18), fg_color="#405460", corner_radius=10)
                    save_grade_btn.place(x=1100, y=520)

                back_btn = ctk.CTkButton(evaluation_frame, height=40, width=160, text="Back",
                                         hover_color="#60646b", text_color="#ffffff",
                                         font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                         command=back_callback)
                back_btn.place(x=50, y=520)

                work_att_and_habit()
                work_knowledge()
                pers_appearance()
                prof_competence()

                next_page_btn = ctk.CTkButton(evaluation_frame, height=40, width=160, text="Next Page",
                                              hover_color="#60646b", text_color="#ffffff",
                                              font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                              command=final_grade)
                next_page_btn.place(x=1100, y=520)

            evaluation_frame = ctk.CTkFrame(ipes_homepage_frame, fg_color="#c4d5d7", width=1275, height=570,
                                            corner_radius=0)
            evaluation_frame.place(x=0, y=110)

            guide_form_bg = ctk.CTkImage(dark_image=Image.open(resource_path('guide.png')), size=(1300, 640))
            image_guide_form_bg = ctk.CTkLabel(evaluation_frame, image=guide_form_bg, text='')
            image_guide_form_bg.place(x=0, y=0)

            evaluate_student_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                                  corner_radius=0)
            evaluate_student_frame.place(x=20, y=30)

            perform_lbl = ctk.CTkLabel(evaluate_student_frame, text=f"Evaluating: {student['student_name']}",
                                       font=('Arial', 25, 'bold'))
            perform_lbl.place(x=10, y=20)

            back_btn = ctk.CTkButton(evaluation_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=back_callback)
            back_btn.place(x=50, y=520)

            next_page_btn = ctk.CTkButton(evaluation_frame, height=40, width=160, text="Next Page",
                                          hover_color="#60646b", text_color="#ffffff", command=student_eval_form,
                                          font=('Arial', 18), fg_color="#405460", corner_radius=10)
            next_page_btn.place(x=1100, y=520)

        def has_been_evaluated(student_id):
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    query = "SELECT id FROM student_evaluations WHERE student_id = ?"
                    cursor.execute(query, (student_id,))
                    return cursor.fetchone() is not None
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Failed to check evaluation status: {e}")
                    return False
                finally:
                    if connection:
                        connection.close()
            return False

        def handle_evaluation_click(student, back_callback):
            if has_been_evaluated(student['id']):
                messagebox.showinfo("Already Evaluated", f"{student['student_name']} has already been evaluated.")
            else:
                evaluate_student(student, back_callback)

        def get_student_count(section):
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    query = "SELECT COUNT(*) FROM student_trainees WHERE section = ?"
                    cursor.execute(query, (section,))
                    count = cursor.fetchone()[0]
                    return count
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Failed to get student count: {e}")
                    return 0
                finally:
                    if connection:
                        connection.close()
            return 0

        def my_class_4A():
            user_sections = get_user_sections()
            if "4A" not in user_sections:
                messagebox.showerror("Access Denied", "You are not assigned to handle this section!")
                my_class()
                return

            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            class_4A_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                          corner_radius=0)
            class_4A_frame.place(x=20, y=30)

            class_4A_lbl = ctk.CTkLabel(class_4A_frame, text="SECTION 4-A", font=('Arial', 33, 'bold'))
            class_4A_lbl.place(x=10, y=16)

            view_class_4A_frame = ctk.CTkFrame(ipes_homepage_frame, fg_color="#c4d5d7", width=1275, height=520,
                                               corner_radius=0)
            view_class_4A_frame.place(x=0, y=110)

            scroll_view_4A_frame = ctk.CTkScrollableFrame(view_class_4A_frame, width=1200, height=500)
            scroll_view_4A_frame.place(x=33, y=0)

            headers_frame = ctk.CTkFrame(scroll_view_4A_frame, fg_color="#f1f5fb", height=50)
            headers_frame.pack(fill="x", pady=(10, 20))

            ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 13, "bold")).place(x=20, y=10)
            ctk.CTkLabel(headers_frame, text="Name of HTE", width=200, font=("Arial", 13, "bold")).place(x=150, y=10)
            ctk.CTkLabel(headers_frame, text="Supervisor Email", width=230, font=("Arial", 13, "bold")).place(x=310,
                                                                                                              y=10)
            ctk.CTkLabel(headers_frame, text="HTE Address", width=230, font=("Arial", 13, "bold")).place(x=530, y=10)
            ctk.CTkLabel(headers_frame, text="Number of Hours", width=150, font=("Arial", 13, "bold")).place(x=750,
                                                                                                             y=10)
            ctk.CTkLabel(headers_frame, text="Training Period", width=150, font=("Arial", 13, "bold")).place(x=910,
                                                                                                             y=10)
            ctk.CTkLabel(headers_frame, text="Action", width=120, font=("Arial", 13, "bold")).place(x=1080, y=10)

            students = get_students_by_section("4A")

            for i, student in enumerate(students):
                student_frame = ctk.CTkFrame(scroll_view_4A_frame, fg_color="#ffffff", height=40)
                student_frame.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(student_frame, text=student['student_name'], width=120, anchor="w",
                             font=("Arial", 12)).place(x=20, y=5)
                ctk.CTkLabel(student_frame, text=student['hte_name'], width=200, anchor="w",
                             font=("Arial", 12)).place(x=190, y=5)
                ctk.CTkLabel(student_frame, text=student['supervisor_email'], width=230, anchor="w",
                             font=("Arial", 12)).place(x=340, y=5)
                ctk.CTkLabel(student_frame, text=student['hte_address'], width=230, anchor="w",
                             font=("Arial", 12)).place(x=560, y=5)
                ctk.CTkLabel(student_frame, text=str(student['hours_rendered']), width=100, anchor="w",
                             font=("Arial", 12)).place(x=800, y=5)
                ctk.CTkLabel(student_frame, text=student['training_period'], width=200, anchor="w",
                             font=("Arial", 12)).place(x=910, y=5)

                evaluate_btn = ctk.CTkButton(student_frame, text="evaluate", width=90, height=27,
                                             corner_radius=8, fg_color="#405460", hover_color="#60646B",
                                             command=lambda s=student: handle_evaluation_click(s, my_class_4A),
                                             font=("Arial", 12))
                evaluate_btn.place(x=1080, y=7)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=my_class)
            back_btn.place(x=50, y=630)

        def my_class_4B():
            user_sections = get_user_sections()
            if "4B" not in user_sections:
                messagebox.showerror("Access Denied", "You are not assigned to handle this section!")
                my_class()
                return
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            class_4B_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                          corner_radius=0)
            class_4B_frame.place(x=20, y=30)

            class_4B_lbl = ctk.CTkLabel(class_4B_frame, text="SECTION 4-B", font=('Arial', 33, 'bold'))
            class_4B_lbl.place(x=10, y=16)

            view_class_4B_frame = ctk.CTkFrame(ipes_homepage_frame, fg_color="#c4d5d7", width=1275, height=520,
                                               corner_radius=0)
            view_class_4B_frame.place(x=0, y=110)

            scroll_view_4B_frame = ctk.CTkScrollableFrame(view_class_4B_frame, width=1200, height=500)
            scroll_view_4B_frame.place(x=33, y=0)

            headers_frame = ctk.CTkFrame(scroll_view_4B_frame, fg_color="#f1f5fb", height=50)
            headers_frame.pack(fill="x", pady=(10, 20))

            ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 13, "bold")).place(x=20, y=10)
            ctk.CTkLabel(headers_frame, text="Name of HTE", width=200, font=("Arial", 13, "bold")).place(x=150, y=10)
            ctk.CTkLabel(headers_frame, text="Supervisor Email", width=230, font=("Arial", 13, "bold")).place(x=310,
                                                                                                              y=10)
            ctk.CTkLabel(headers_frame, text="HTE Address", width=230, font=("Arial", 13, "bold")).place(x=530, y=10)
            ctk.CTkLabel(headers_frame, text="Number of Hours", width=150, font=("Arial", 13, "bold")).place(x=750,
                                                                                                             y=10)
            ctk.CTkLabel(headers_frame, text="Training Period", width=150, font=("Arial", 13, "bold")).place(x=910,
                                                                                                             y=10)
            ctk.CTkLabel(headers_frame, text="Action", width=120, font=("Arial", 13, "bold")).place(x=1080, y=10)

            students = get_students_by_section("4B")

            for i, student in enumerate(students):
                student_frame = ctk.CTkFrame(scroll_view_4B_frame, fg_color="#ffffff", height=40)
                student_frame.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(student_frame, text=student['student_name'], width=120, anchor="w",
                             font=("Arial", 12)).place(x=20, y=5)
                ctk.CTkLabel(student_frame, text=student['hte_name'], width=200, anchor="w",
                             font=("Arial", 12)).place(x=190, y=5)
                ctk.CTkLabel(student_frame, text=student['supervisor_email'], width=230, anchor="w",
                             font=("Arial", 12)).place(x=340, y=5)
                ctk.CTkLabel(student_frame, text=student['hte_address'], width=230, anchor="w",
                             font=("Arial", 12)).place(x=560, y=5)
                ctk.CTkLabel(student_frame, text=str(student['hours_rendered']), width=100, anchor="w",
                             font=("Arial", 12)).place(x=800, y=5)
                ctk.CTkLabel(student_frame, text=student['training_period'], width=200, anchor="w",
                             font=("Arial", 12)).place(x=910, y=5)

                evaluate_btn = ctk.CTkButton(student_frame, text="evaluate", width=90, height=27,
                                             corner_radius=8, fg_color="#405460", hover_color="#60646B",
                                             command=lambda s=student: handle_evaluation_click(s, my_class_4B),
                                             font=("Arial", 12))
                evaluate_btn.place(x=1080, y=7)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=my_class)
            back_btn.place(x=50, y=630)

        def my_class_4C():
            user_sections = get_user_sections()
            if "4C" not in user_sections:
                messagebox.showerror("Access Denied", "You are not assigned to handle this section!")
                my_class()
                return
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            class_4C_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                          corner_radius=0)
            class_4C_frame.place(x=20, y=30)

            class_4C_lbl = ctk.CTkLabel(class_4C_frame, text="SECTION 4-C", font=('Arial', 33, 'bold'))
            class_4C_lbl.place(x=10, y=16)

            view_class_4C_frame = ctk.CTkFrame(ipes_homepage_frame, fg_color="#c4d5d7", width=1275, height=520,
                                               corner_radius=0)
            view_class_4C_frame.place(x=0, y=110)

            scroll_view_4C_frame = ctk.CTkScrollableFrame(view_class_4C_frame, width=1200, height=500)
            scroll_view_4C_frame.place(x=33, y=0)

            headers_frame = ctk.CTkFrame(scroll_view_4C_frame, fg_color="#f1f5fb", height=50)
            headers_frame.pack(fill="x", pady=(10, 20))

            ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 13, "bold")).place(x=20, y=10)
            ctk.CTkLabel(headers_frame, text="Name of HTE", width=200, font=("Arial", 13, "bold")).place(x=150, y=10)
            ctk.CTkLabel(headers_frame, text="Supervisor Email", width=230, font=("Arial", 13, "bold")).place(x=310,
                                                                                                              y=10)
            ctk.CTkLabel(headers_frame, text="HTE Address", width=230, font=("Arial", 13, "bold")).place(x=530, y=10)
            ctk.CTkLabel(headers_frame, text="Number of Hours", width=150, font=("Arial", 13, "bold")).place(x=750,
                                                                                                             y=10)
            ctk.CTkLabel(headers_frame, text="Training Period", width=150, font=("Arial", 13, "bold")).place(x=910,
                                                                                                             y=10)
            ctk.CTkLabel(headers_frame, text="Action", width=120, font=("Arial", 13, "bold")).place(x=1080, y=10)

            students = get_students_by_section("4C")

            for i, student in enumerate(students):
                student_frame = ctk.CTkFrame(scroll_view_4C_frame, fg_color="#ffffff", height=40)
                student_frame.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(student_frame, text=student['student_name'], width=120, anchor="w",
                             font=("Arial", 12)).place(x=20, y=5)
                ctk.CTkLabel(student_frame, text=student['hte_name'], width=200, anchor="w",
                             font=("Arial", 12)).place(x=190, y=5)
                ctk.CTkLabel(student_frame, text=student['supervisor_email'], width=230, anchor="w",
                             font=("Arial", 12)).place(x=340, y=5)
                ctk.CTkLabel(student_frame, text=student['hte_address'], width=230, anchor="w",
                             font=("Arial", 12)).place(x=560, y=5)
                ctk.CTkLabel(student_frame, text=str(student['hours_rendered']), width=100, anchor="w",
                             font=("Arial", 12)).place(x=800, y=5)
                ctk.CTkLabel(student_frame, text=student['training_period'], width=200, anchor="w",
                             font=("Arial", 12)).place(x=910, y=5)

                evaluate_btn = ctk.CTkButton(student_frame, text="evaluate", width=90, height=27,
                                             corner_radius=8, fg_color="#405460", hover_color="#60646B",
                                             command=lambda s=student: handle_evaluation_click(s, my_class_4C),
                                             font=("Arial", 12))
                evaluate_btn.place(x=1080, y=7)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=my_class)
            back_btn.place(x=50, y=630)

        def my_class_4D():
            user_sections = get_user_sections()
            if "4D" not in user_sections:
                messagebox.showerror("Access Denied", "You are not assigned to handle this section!")
                my_class()
                return
            for widget in ipes_homepage_frame.winfo_children():
                widget.destroy()

            class_4D_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                          corner_radius=0)
            class_4D_frame.place(x=20, y=30)

            class_4D_lbl = ctk.CTkLabel(class_4D_frame, text="SECTION 4-D", font=('Arial', 33, 'bold'))
            class_4D_lbl.place(x=10, y=16)

            view_class_4D_frame = ctk.CTkFrame(ipes_homepage_frame, fg_color="#c4d5d7", width=1275, height=520,
                                               corner_radius=0)
            view_class_4D_frame.place(x=0, y=110)

            scroll_view_4D_frame = ctk.CTkScrollableFrame(view_class_4D_frame, width=1200, height=500)
            scroll_view_4D_frame.place(x=33, y=0)

            headers_frame = ctk.CTkFrame(scroll_view_4D_frame, fg_color="#f1f5fb", height=50)
            headers_frame.pack(fill="x", pady=(10, 20))

            ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 13, "bold")).place(x=20, y=10)
            ctk.CTkLabel(headers_frame, text="Name of HTE", width=200, font=("Arial", 13, "bold")).place(x=150, y=10)
            ctk.CTkLabel(headers_frame, text="Supervisor Email", width=230, font=("Arial", 13, "bold")).place(x=310,
                                                                                                              y=10)
            ctk.CTkLabel(headers_frame, text="HTE Address", width=230, font=("Arial", 13, "bold")).place(x=530, y=10)
            ctk.CTkLabel(headers_frame, text="Number of Hours", width=150, font=("Arial", 13, "bold")).place(x=750,
                                                                                                             y=10)
            ctk.CTkLabel(headers_frame, text="Training Period", width=150, font=("Arial", 13, "bold")).place(x=910,
                                                                                                             y=10)
            ctk.CTkLabel(headers_frame, text="Action", width=120, font=("Arial", 13, "bold")).place(x=1080, y=10)

            students = get_students_by_section("4D")

            for i, student in enumerate(students):
                student_frame = ctk.CTkFrame(scroll_view_4D_frame, fg_color="#ffffff", height=40)
                student_frame.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(student_frame, text=student['student_name'], width=120, anchor="w",
                             font=("Arial", 12)).place(x=20, y=5)
                ctk.CTkLabel(student_frame, text=student['hte_name'], width=200, anchor="w",
                             font=("Arial", 12)).place(x=190, y=5)
                ctk.CTkLabel(student_frame, text=student['supervisor_email'], width=230, anchor="w",
                             font=("Arial", 12)).place(x=340, y=5)
                ctk.CTkLabel(student_frame, text=student['hte_address'], width=230, anchor="w",
                             font=("Arial", 12)).place(x=560, y=5)
                ctk.CTkLabel(student_frame, text=str(student['hours_rendered']), width=100, anchor="w",
                             font=("Arial", 12)).place(x=800, y=5)
                ctk.CTkLabel(student_frame, text=student['training_period'], width=200, anchor="w",
                             font=("Arial", 12)).place(x=910, y=5)

                evaluate_btn = ctk.CTkButton(student_frame, text="evaluate", width=90, height=27,
                                             corner_radius=8, fg_color="#405460", hover_color="#60646B",
                                             command=lambda s=student: handle_evaluation_click(s, my_class_4D),
                                             font=("Arial", 12))
                evaluate_btn.place(x=1080, y=7)

            back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                     hover_color="#60646b", text_color="#ffffff",
                                     font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                     command=my_class)
            back_btn.place(x=50, y=630)

        stud_num_4A = get_student_count("4A")
        stud_num_4B = get_student_count("4B")
        stud_num_4C = get_student_count("4C")
        stud_num_4D = get_student_count("4D")

        myklass_frame = ctk.CTkFrame(ipes_homepage_frame, width=1220, height=70, fg_color="#ffffff",
                                     corner_radius=0)
        myklass_frame.place(x=20, y=30)

        myklass_frame_lbl = ctk.CTkLabel(myklass_frame, text="MY CLASS", font=('Arial', 33, 'bold'))
        myklass_frame_lbl.place(x=10, y=16)

        myklass_bg = ctk.CTkImage(dark_image=Image.open(resource_path('section_performance.png')), size=(1300, 700))
        image_myklass_bg = ctk.CTkLabel(ipes_homepage_frame, image=myklass_bg, text='')
        image_myklass_bg.place(x=0, y=100)

        stud_num_4A_lbl = ctk.CTkLabel(ipes_homepage_frame, text=str(stud_num_4A), font=('Arial', 25, 'bold'),
                                       text_color="#000000",
                                       bg_color="#FFFFFF")
        stud_num_4A_lbl.place(x=650, y=330)

        four_A_lbl = ctk.CTkLabel(ipes_homepage_frame, text="4A", font=("Arial", 20, 'bold'), text_color="#000000",
                                  bg_color="#FFFFFF")
        four_A_lbl.place(x=330, y=330)

        four_A_btn = ctk.CTkButton(ipes_homepage_frame, height=20, width=100, text="View",
                                   hover_color="#60646b", text_color="#ffffff", bg_color="#FFFFFF",
                                   font=('Arial', 15), fg_color="#405460", corner_radius=10, command=my_class_4A)
        four_A_btn.place(x=930, y=330)

        stud_num_4B_lbl = ctk.CTkLabel(ipes_homepage_frame, text=str(stud_num_4B), font=('Arial', 25, 'bold'),
                                       text_color="#000000",
                                       bg_color="#FFFFFF")
        stud_num_4B_lbl.place(x=650, y=400)

        four_B_lbl = ctk.CTkLabel(ipes_homepage_frame, text="4B", font=("Arial", 20, 'bold'), text_color="#000000",
                                  bg_color="#FFFFFF")
        four_B_lbl.place(x=330, y=400)

        four_B_btn = ctk.CTkButton(ipes_homepage_frame, height=20, width=100, text="View",
                                   hover_color="#60646b", text_color="#ffffff", bg_color="#FFFFFF",
                                   font=('Arial', 15), fg_color="#405460", corner_radius=10, command=my_class_4B)
        four_B_btn.place(x=930, y=400)

        stud_num_4C_lbl = ctk.CTkLabel(ipes_homepage_frame, text=str(stud_num_4C), font=('Arial', 25, 'bold'),
                                       text_color="#000000",
                                       bg_color="#FFFFFF")
        stud_num_4C_lbl.place(x=650, y=475)

        four_C_lbl = ctk.CTkLabel(ipes_homepage_frame, text="4C", font=("Arial", 20, 'bold'), text_color="#000000",
                                  bg_color="#FFFFFF")
        four_C_lbl.place(x=330, y=475)

        four_C_btn = ctk.CTkButton(ipes_homepage_frame, height=20, width=100, text="View",
                                   hover_color="#60646b", text_color="#ffffff", bg_color="#FFFFFF",
                                   font=('Arial', 15), fg_color="#405460", corner_radius=10, command=my_class_4C)
        four_C_btn.place(x=930, y=475)

        stud_num_4D_lbl = ctk.CTkLabel(ipes_homepage_frame, text=str(stud_num_4D), font=('Arial', 25, 'bold'),
                                       text_color="#000000",
                                       bg_color="#FFFFFF")
        stud_num_4D_lbl.place(x=650, y=550)

        four_D_lbl = ctk.CTkLabel(ipes_homepage_frame, text="4D", font=("Arial", 20, 'bold'), text_color="#000000",
                                  bg_color="#FFFFFF")
        four_D_lbl.place(x=330, y=550)

        four_D_btn = ctk.CTkButton(ipes_homepage_frame, height=20, width=100, text="View",
                                   hover_color="#60646b", text_color="#ffffff", bg_color="#FFFFFF",
                                   font=('Arial', 15), fg_color="#405460", corner_radius=10, command=my_class_4D)
        four_D_btn.place(x=930, y=550)

        back_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Back",
                                 hover_color="#60646b", text_color="#ffffff",
                                 font=('Arial', 18), fg_color="#405460", corner_radius=10,
                                 command=dashboard_homepage)
        back_btn.place(x=50, y=630)

        add_student_btn = ctk.CTkButton(ipes_homepage_frame, height=40, width=160, text="Add student",
                                        hover_color="#60646b", text_color="#ffffff",
                                        font=('Arial', 18), fg_color="#405460", corner_radius=10, command=add_student)
        add_student_btn.place(x=1100, y=630)

    ipes_header_frame = ctk.CTkFrame(ipes_users_window, width=1920, height=95, fg_color="#405460", corner_radius=0)
    ipes_header_frame.place(x=0, y=0)

    ipes_navigation_frame = ctk.CTkFrame(ipes_users_window, width=240, height=800, corner_radius=0, fg_color="#60646b")
    ipes_navigation_frame.place(x=0, y=95)

    dashboard_btn = ctk.CTkButton(ipes_navigation_frame, width=230, height=50, text="DASHBOARD", text_color="#FFFFFF",
                                  fg_color="#60646b",
                                  font=('Arial', 15, 'bold'), hover_color='#405460', command=show_homepage)
    dashboard_btn.place(x=5, y=150)

    prof_setting = ctk.CTkButton(ipes_navigation_frame, width=230, height=50, text="MY PROFILE", text_color="#FFFFFF",
                                 fg_color="#60646b",
                                 font=('Arial', 15, 'bold'), hover_color='#405460', command=profile_settings)
    prof_setting.place(x=5, y=200)

    perf_track = ctk.CTkButton(ipes_navigation_frame, width=230, height=50, text="PERFORMANCE TRACKING",
                               text_color="#FFFFFF", fg_color="#60646b",
                               font=('Arial', 15, 'bold'), hover_color='#405460', command=performance_tracking)
    perf_track.place(x=5, y=250)

    myklas = ctk.CTkButton(ipes_navigation_frame, width=230, height=50, text="MY CLASS", text_color="#FFFFFF",
                           fg_color="#60646b",
                           font=('Arial', 15, 'bold'), hover_color='#405460', command=my_class)
    myklas.place(x=5, y=300)

    logo = ctk.CTkImage(light_image=Image.open(resource_path('DHVSU-LOGO.png')), size=(80, 80))
    image_lbl = ctk.CTkLabel(ipes_header_frame, image=logo, text='')
    image_lbl.place(x=0, y=7)

    cea_logo = ctk.CTkImage(light_image=Image.open(resource_path('logocea1.png')), size=(100, 80))
    cea_image_lbl = ctk.CTkLabel(ipes_header_frame, image=cea_logo, text='')
    cea_image_lbl.place(x=100, y=7)

    title_lbl = ctk.CTkLabel(ipes_header_frame, text="IPES: INTERN PERFORMANCE EVALUATION SYSTEM ",
                             font=("Arial", 25, "bold"), text_color="#ffffff")
    title_lbl.place(x=210, y=33)

    ipes_homepage_frame = ctk.CTkFrame(ipes_users_window, width=1297, height=800, fg_color="#c4d5d7", corner_radius=0)
    ipes_homepage_frame.place(x=240, y=95)

    def logout_user():
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT username, remember_me_enabled FROM users WHERE id = ?",
                                   (current_user_id,))
                    user = cursor.fetchone()
                    if user and not user[1]:
                        clear_credentials(user[0])
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", str(e))
                finally:
                    if connection:
                        connection.close()
            ipes_users_window.destroy()
            main.deiconify()

    logout_admin_btn = ctk.CTkButton(ipes_navigation_frame, width=230, height=50, text="Log Out", text_color="#FFFFFF",
                                     fg_color="#60646b", command=logout_user,
                                     font=('Arial', 15, 'bold'), hover_color='#405460')
    logout_admin_btn.place(x=5, y=600)

    show_homepage()

    ipes_users_window.grid_rowconfigure(0, weight=0)
    ipes_users_window.grid_rowconfigure(1, weight=0)
    ipes_users_window.grid_rowconfigure(2, weight=1)
    ipes_users_window.grid_columnconfigure(0, weight=1)
    ipes_users_window.mainloop()

def homepage_admin():
    ctk.set_appearance_mode("light")
    ipes_admin_window = ctk.CTkToplevel()
    ipes_admin_window.title("Intern Performance Evaluation System")
    ipes_admin_window.configure(bg='#B03052')
    ipes_admin_window.after(0, lambda: ipes_admin_window.state('zoomed'))
    ipes_admin_window.resizable(True, True)
    ipes_admin_window.geometry(f"{main.winfo_screenwidth()}x{main.winfo_screenheight()}+0+0")
    ipes_admin_window.grid_rowconfigure(0, weight=1)
    ipes_admin_window.grid_columnconfigure(0, weight=1)

    def show_homepage():
        clear_dashboard_homepage()
        admin_dashboard()

    def clear_dashboard_homepage():
        for widget in admin_homepage_frame.winfo_children():
            widget.destroy()

    def admin_dashboard():
        for widget in admin_homepage_frame.winfo_children():
            widget.destroy()

        admin_bg = ctk.CTkImage(dark_image=Image.open(resource_path('adminbg.png')), size=(1300, 680))
        image_admin_bg = ctk.CTkLabel(admin_homepage_frame, image=admin_bg, text='')
        image_admin_bg.grid(row=2, column=0, sticky="nsew")

        total_enrollees = ctk.CTkLabel(admin_homepage_frame, text="0", bg_color="#ffffff",
                                       font=("Arial", 40, "bold"))
        total_enrollees.place(x=390, y=180)

        active_user_lbl = ctk.CTkLabel(admin_homepage_frame, text="0", bg_color="#ffffff",
                                       font=("Arial", 40, "bold"))
        active_user_lbl.place(x=900, y=180)

        evaluation_pending_lbl = ctk.CTkLabel(admin_homepage_frame, text="0", bg_color="#ffffff",
                                              font=("Arial", 40, "bold"))
        evaluation_pending_lbl.place(x=390, y=450)

        evaluated_student_lbl = ctk.CTkLabel(admin_homepage_frame, text="0", bg_color="#ffffff",
                                             font=("Arial", 40, "bold"))
        evaluated_student_lbl.place(x=900, y=450)

        admin_homepage_frame.total_enrollees = total_enrollees
        admin_homepage_frame.active_user_lbl = active_user_lbl
        admin_homepage_frame.evaluation_pending_lbl = evaluation_pending_lbl
        admin_homepage_frame.evaluated_student_lbl = evaluated_student_lbl

        def fetch_counts():
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT COUNT(*) as count FROM student_trainees")
                    total_enrollees = cursor.fetchone()['count']

                    cursor.execute("SELECT COUNT(*) as count FROM users")
                    active_users = cursor.fetchone()['count']

                    cursor.execute("""SELECT COUNT(*) as count 
                        FROM student_trainees st
                        LEFT JOIN student_evaluations se ON st.id = se.student_id
                        WHERE se.id IS NULL""")
                    pending_evaluations = cursor.fetchone()['count']

                    cursor.execute("""SELECT COUNT(DISTINCT st.id) as count 
                                        FROM student_trainees st
                                        JOIN student_evaluations se ON st.id = se.student_id
                                    """)
                    evaluated_students = cursor.fetchone()['count']

                    return {
                        'total_enrollees': total_enrollees,
                        'active_users': active_users,
                        'pending_evaluations': pending_evaluations,
                        'evaluated_students': evaluated_students
                    }
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Failed to fetch dashboard data: {e}")
                    return None
                finally:
                    if connection:
                        connection.close()
            return None

        def update_dashboard():
            if not admin_homepage_frame.winfo_exists():
                return

            counts = fetch_counts()
            if counts:
                if admin_homepage_frame.total_enrollees.winfo_exists():
                    admin_homepage_frame.total_enrollees.configure(text=str(counts['total_enrollees']))
                if admin_homepage_frame.active_user_lbl.winfo_exists():
                    admin_homepage_frame.active_user_lbl.configure(text=str(counts['active_users']))
                if admin_homepage_frame.evaluation_pending_lbl.winfo_exists():
                    admin_homepage_frame.evaluation_pending_lbl.configure(text=str(counts['pending_evaluations']))
                if admin_homepage_frame.evaluated_student_lbl.winfo_exists():
                    admin_homepage_frame.evaluated_student_lbl.configure(text=str(counts['evaluated_students']))

            if admin_homepage_frame.winfo_exists():
                admin_homepage_frame.after(3000, update_dashboard)

        refresh_btn = ctk.CTkButton(admin_homepage_frame, text="Refresh", width=120, height=40,
                                    fg_color="#405460", font=('Arial', 15), corner_radius=10,
                                    command=update_dashboard)
        refresh_btn.place(x=1100, y=630)

        update_dashboard()

    def create_user():
        for widget in admin_homepage_frame.winfo_children():
            widget.destroy()

        def validate_and_create_user():
            username = username_box.get().strip()
            email = email_box.get().strip()
            password = pass_box.get()
            confirm_password = conpass_box.get()

            if not all([username, email, password, confirm_password]):
                messagebox.showerror("Error", "All fields are required!")
                return

            if password != confirm_password:
                messagebox.showerror("Error", "Passwords do not match!")
                return

            if len(password) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters long!")
                return

            password_pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
            if not re.match(password_pattern, password):
                messagebox.showerror("Error",
                                     "Password must contain:\n"
                                     "- At least 8 characters\n"
                                     "- Letters, numbers, and special symbols")
                return

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                messagebox.showerror("Error", "Invalid email format!")
                return

            hashed_password = generate_password_hash(password)

            try:
                connection = create_connection()
                if connection:
                    cursor = connection.cursor()

                    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))

                    if cursor.fetchone():
                        messagebox.showerror("Error", "Username or email already exists!")
                        return

                    query = """INSERT INTO users (username, email, password) 
                                    VALUES (?, ?, ?)"""
                    cursor.execute(query, (username, email, hashed_password))
                    connection.commit()

                    messagebox.showinfo("Success", "User created successfully!")

                    username_box.delete(0, 'end')
                    email_box.delete(0, 'end')
                    pass_box.delete(0, 'end')
                    conpass_box.delete(0, 'end')
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"Failed to create user: {e}")
            finally:
                if connection:
                    connection.close()

        create_user_bg = ctk.CTkImage(dark_image=Image.open(resource_path('createuser.png')), size=(1300, 680))
        image_create_user_bg = ctk.CTkLabel(admin_homepage_frame, image=create_user_bg, text='')
        image_create_user_bg.grid(row=2, column=0, sticky="nsew")

        username_box = ctk.CTkEntry(admin_homepage_frame, width=300, height=36, corner_radius=10, font=("Lato", 14),
                                    fg_color="#e7e6ec")
        username_box.place(x=490, y=185)

        email_box = ctk.CTkEntry(admin_homepage_frame, width=300, height=36, corner_radius=10, font=("Lato", 14),
                                 fg_color="#e7e6ec")
        email_box.place(x=490, y=255)

        pass_box = ctk.CTkEntry(admin_homepage_frame, width=300, height=36, corner_radius=10, font=("Lato", 14),
                                fg_color="#e7e6ec")
        pass_box.place(x=490, y=320)

        conpass_box = ctk.CTkEntry(admin_homepage_frame, width=300, height=36, corner_radius=10, font=("Lato", 14),
                                   fg_color="#e7e6ec")
        conpass_box.place(x=490, y=390)

        create_user_acc = ctk.CTkButton(admin_homepage_frame, text="Create User", width=250, height=36,
                                        corner_radius=10,
                                        fg_color="#405460",
                                        bg_color="#c4d5d7", hover_color="#60646B", font=("Lato", 13, "bold"),
                                        command=validate_and_create_user)
        create_user_acc.place(x=520, y=445)

    def active_user():
        for widget in admin_homepage_frame.winfo_children():
            widget.destroy()

        title_label = ctk.CTkLabel(admin_homepage_frame, text="Active Users",
                                   font=("Arial", 35, "bold"))
        title_label.place(x=520, y=20)

        history_frame = ctk.CTkFrame(admin_homepage_frame, fg_color="#f1f5fb", width=1275, height=720, corner_radius=0)
        history_frame.place(x=0, y=68)

        scroll_frame = ctk.CTkScrollableFrame(history_frame, width=1200, height=550, fg_color="#e4e5e7")
        scroll_frame.place(x=33, y=0)

        headers_frame = ctk.CTkFrame(scroll_frame, fg_color="#f1f5fb", height=50)
        headers_frame.pack(fill="x", pady=(10, 20))

        ctk.CTkLabel(headers_frame, text="User ID", width=100, font=("Arial", 14, "bold")).place(x=20, y=10)
        ctk.CTkLabel(headers_frame, text="Username", width=100, font=("Arial", 14, "bold")).place(x=250, y=10)
        ctk.CTkLabel(headers_frame, text="Email", width=200, font=("Arial", 14, "bold")).place(x=500, y=10)
        ctk.CTkLabel(headers_frame, text="Login Time", width=300, font=("Arial", 14, "bold")).place(x=880, y=10)

        try:
            connection = create_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("""
                    SELECT user_id, username, email, login_time 
                    FROM login_history 
                    WHERE DATE(login_time) = DATE('now')
                    ORDER BY login_time DESC
                """)
                records = cursor.fetchall()

                if not records:
                    no_records_label = ctk.CTkLabel(scroll_frame,
                                                    text="No logins recorded today",
                                                    font=("Arial", 14))
                    no_records_label.pack(pady=50)

                for i, row in enumerate(records):
                    user_id, username, email, login_time = row

                    user_frame = ctk.CTkFrame(scroll_frame, fg_color="#ffffff", height=40)
                    user_frame.pack(fill="x", padx=10, pady=5)

                    ctk.CTkLabel(user_frame, text=str(user_id), width=100, anchor="w", font=("Arial", 13)).place(x=50,
                                                                                                                 y=5)
                    ctk.CTkLabel(user_frame, text=username, width=150, anchor="w", font=("Arial", 13)).place(x=270, y=5)
                    ctk.CTkLabel(user_frame, text=email, width=250, anchor="w", font=("Arial", 13)).place(x=520, y=5)
                    ctk.CTkLabel(user_frame, text=str(login_time), width=300, anchor="w", font=("Arial", 13)).place(
                        x=965, y=5)
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch active users: {e}")
        finally:
            if connection:
                connection.close()

        refresh_btn = ctk.CTkButton(history_frame, text="Refresh", width=120, height=36,
                                    corner_radius=10, fg_color="#405460",
                                    hover_color="#60646B", font=("Lato", 13, "bold"),
                                    command=active_user)
        refresh_btn.place(x=1100, y=570)

    def user_management():
        for widget in admin_homepage_frame.winfo_children():
            widget.destroy()

        def open_update_user_window(user):
            for widget in admin_homepage_frame.winfo_children():
                widget.destroy()

            def is_valid_email(email):
                pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                return re.match(pattern, email)

            def update_user():
                new_username = username_box.get().strip()
                new_email = email_box.get().strip()
                new_password = pass_box.get().strip()
                new_sections_text = sections_box.get().strip()

                if not all([new_username, new_email, new_sections_text]):
                    messagebox.showwarning("Input Error", "Username, Email, and Section are required.")
                    return

                if not is_valid_email(new_email):
                    messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
                    return

                new_sections = [sec.strip() for sec in new_sections_text.split(",") if sec.strip()]
                if not new_sections:
                    messagebox.showwarning("Input Error", "Please enter at least one valid section.")
                    return

                allowed_sections = {"4A", "4B", "4C", "4D"}
                if any(sec not in allowed_sections for sec in new_sections):
                    messagebox.showwarning("Invalid Section", f"Sections must be from {sorted(allowed_sections)}.")
                    return

                if new_password:
                    password_pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
                    if not re.match(password_pattern, new_password):
                        messagebox.showerror("Error",
                                             "Password must contain:\n"
                                             "- At least 8 characters\n"
                                             "- Letters, numbers, and special symbols")
                        return

                connection = create_connection()
                if connection:
                    try:
                        cursor = connection.cursor()

                        # Update users table
                        if new_password:
                            hashed_pw = generate_password_hash(new_password)
                            cursor.execute("""UPDATE users SET username=?, 
                                            email=?, password=? WHERE id=?""",
                                           (new_username, new_email, hashed_pw, user['id']))
                        else:
                            cursor.execute("""UPDATE users SET username=?, 
                                            email=? WHERE id=?""",
                                           (new_username, new_email, user['id']))

                        cursor.execute("DELETE FROM user_sections WHERE user_id = ?", (user['id'],))
                        for section in new_sections:
                            cursor.execute("""INSERT INTO user_sections 
                                              (user_id, section) 
                                              VALUES (?, ?)""", (user['id'], section))

                        connection.commit()
                        messagebox.showinfo("Success", "User updated successfully.")
                        user_management()

                    except sqlite3.Error as e:
                        connection.rollback()
                        messagebox.showerror("Error", f"Database error: {e}")
                    finally:
                        if connection:
                            connection.close()

            def delete_user():
                confirm = messagebox.askyesno("Confirm Delete",
                                              f"Are you sure you want to delete user ID {user['id']}?")
                if confirm:
                    connection = create_connection()
                    if connection:
                        try:
                            cursor = connection.cursor()
                            cursor.execute("DELETE FROM user_sections WHERE user_id = ?", (user['id'],))
                            cursor.execute("DELETE FROM users WHERE id = ?", (user['id'],))
                            connection.commit()
                            messagebox.showinfo("Deleted", "User deleted successfully.")
                            user_management()

                        except sqlite3.Error as e:
                            connection.rollback()
                            messagebox.showerror("Error", f"Could not delete user: {e}")
                        finally:
                            if connection:
                                connection.close()

            create_user_bg = ctk.CTkImage(dark_image=Image.open(resource_path('updateuser.png')), size=(1300, 680))
            image_create_user_bg = ctk.CTkLabel(admin_homepage_frame, image=create_user_bg, text='')
            image_create_user_bg.grid(row=2, column=0, sticky="nsew")

            ctk.CTkLabel(admin_homepage_frame, text=f"{user['id']}", fg_color="#FFFFFF",
                         font=("Arial", 26, "bold")).place(x=755, y=105)

            username_box = ctk.CTkEntry(admin_homepage_frame, width=300, height=36, corner_radius=10, font=("Lato", 14),
                                        fg_color="#e7e6ec")
            username_box.insert(0, user['username'])
            username_box.place(x=490, y=185)

            email_box = ctk.CTkEntry(admin_homepage_frame, width=300, height=36, corner_radius=10, font=("Lato", 14),
                                     fg_color="#e7e6ec")
            email_box.insert(0, user['email'])
            email_box.place(x=490, y=255)

            show_icon = ctk.CTkImage(light_image=Image.open(resource_path("showpass.png")), size=(20, 20))
            hide_icon = ctk.CTkImage(light_image=Image.open(resource_path("hidepass.png")), size=(20, 20))

            pass_box = ctk.CTkEntry(admin_homepage_frame, width=300, height=36, corner_radius=10, font=("Lato", 14),
                                    fg_color="#e7e6ec", show="**")
            pass_box.place(x=490, y=320)

            def toggle_password():
                if pass_box.cget("show") == "*":
                    pass_box.configure(show="")
                    showpass.configure(image=hide_icon)
                else:
                    pass_box.configure(show="*")
                    showpass.configure(image=show_icon)

            showpass = ctk.CTkButton(admin_homepage_frame, image=show_icon, text="", width=30, height=30,
                                     bg_color="#e7e6ec",
                                     fg_color="#e7e6ec", hover_color="#a0a5aa", command=toggle_password
                                     )
            showpass.place(x=748, y=322)

            # Get current section from user_sections table
            current_section = []
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT section FROM user_sections WHERE user_id = ?", (user['id'],))
                    results = cursor.fetchall()
                    if results:
                        current_section = [row[0] for row in results]
                except sqlite3.Error as e:
                    messagebox.showerror("Error", f"Could not fetch user section: {e}")
                finally:
                    if connection:
                        connection.close()

            sections_box = ctk.CTkEntry(admin_homepage_frame, width=300, height=36, corner_radius=10,
                                        font=("Lato", 14), fg_color="#e7e6ec")
            sections_box.insert(0, ", ".join(current_section))
            sections_box.place(x=490, y=390)

            ctk.CTkButton(admin_homepage_frame, text="Update", width=120, height=36,
                          corner_radius=10, fg_color="#405460", command=update_user,
                          hover_color="#60646B", font=("Lato", 13, "bold")).place(x=455, y=470)

            ctk.CTkButton(admin_homepage_frame, text="Cancel", width=120, height=36,
                          corner_radius=10, fg_color="#405460", command=user_management,
                          hover_color="#60646B", font=("Lato", 13, "bold")).place(x=590, y=470)

            ctk.CTkButton(admin_homepage_frame, text="Delete", width=120, height=36,
                          corner_radius=10, fg_color="#405460", command=delete_user,
                          hover_color="#60646B", font=("Lato", 13, "bold")).place(x=725, y=470)

        title_label = ctk.CTkLabel(admin_homepage_frame, text="User Management",
                                   font=("Arial", 35, "bold"))
        title_label.place(x=500, y=20)

        history_frame = ctk.CTkFrame(admin_homepage_frame, fg_color="#f1f5fb", width=1275, height=720, corner_radius=0)
        history_frame.place(x=0, y=68)

        scroll_frame = ctk.CTkScrollableFrame(history_frame, width=1200, height=550)
        scroll_frame.place(x=33, y=0)

        headers_frame = ctk.CTkFrame(scroll_frame, fg_color="#f1f5fb", height=50)
        headers_frame.pack(fill="x", pady=(10, 20))

        ctk.CTkLabel(headers_frame, text="ID", width=50, font=("Arial", 14, "bold")).place(x=10, y=10)
        ctk.CTkLabel(headers_frame, text="Username", width=120, font=("Arial", 14, "bold")).place(x=60, y=10)
        ctk.CTkLabel(headers_frame, text="Email", width=200, font=("Arial", 14, "bold")).place(x=170, y=10)
        ctk.CTkLabel(headers_frame, text="Section", width=50, font=("Arial", 14, "bold")).place(x=450, y=10)
        ctk.CTkLabel(headers_frame, text="Password", width=50, font=("Arial", 14, "bold")).place(x=640, y=10)
        ctk.CTkLabel(headers_frame, text="Created At", width=100, font=("Arial", 14, "bold")).place(x=880, y=10)
        ctk.CTkLabel(headers_frame, text="Action", width=250, font=("Arial", 14, "bold")).place(x=1000, y=10)

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("""SELECT u.id, u.username, u.email, GROUP_CONCAT(us.section, ', ') AS sections,
                                u.password, u.created_at 
                                FROM users u
                                LEFT JOIN user_sections us ON u.id = us.user_id
                                GROUP BY u.id""")
                rows = cursor.fetchall()

                if not rows:
                    no_users_label = ctk.CTkLabel(scroll_frame, text="No users found", font=("Arial", 14))
                    no_users_label.pack(pady=50)
                else:
                    # Get column names
                    columns = [col[0] for col in cursor.description]

                    for row in rows:
                        user = dict(zip(columns, row))
                        user_frame = ctk.CTkFrame(scroll_frame, fg_color="#ffffff", height=50)
                        user_frame.pack(fill="x", pady=5, padx=10)
                        ctk.CTkLabel(user_frame, text=user['id'], width=50, anchor="w", font=("Arial", 13)).place(x=20,
                                                                                                                  y=10)
                        ctk.CTkLabel(user_frame, text=user['username'], width=120, anchor="w", font=("Arial", 13)).place(
                            x=90,
                            y=10)
                        ctk.CTkLabel(user_frame, text=user['email'], width=250, anchor="w", font=("Arial", 13)).place(x=190,
                                                                                                                      y=10)
                        ctk.CTkLabel(user_frame, text=user['sections'], width=50, anchor="w",
                                     font=("Arial", 13)).place(x=455, y=10)
                        hashed_pw = user['password']
                        shortened_pw = hashed_pw[:20] + '...' if len(hashed_pw) > 20 else hashed_pw
                        ctk.CTkLabel(user_frame, text=shortened_pw, width=50, anchor="w", font=("Arial", 13)).place(x=600,
                                                                                                                    y=10)
                        ctk.CTkLabel(user_frame, text=str(user['created_at']), width=200, anchor="w",
                                     font=("Arial", 13)).place(
                            x=860, y=10)
                        update_button = ctk.CTkButton(user_frame, text="Update", width=100, height=30,
                                                      corner_radius=8, fg_color="#405460", hover_color="#60646B",
                                                      font=("Arial", 12, "bold"),
                                                      command=lambda u=user: open_update_user_window(u))
                        update_button.place(x=1070, y=10)

            except sqlite3.Error as e:
                messagebox.showerror("Database Error", f"An error occurred: {e}")
            finally:
                if connection:
                    connection.close()

    def evaluated_student():
        for widget in admin_homepage_frame.winfo_children():
            widget.destroy()

        def get_evaluated_student():
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    query = """SELECT st.id, st.student_name, st.hte_name, st.hte_address, st.hours_rendered,
                    st.supervisor_contact, st.supervisor_email, st.training_period, st.section, se.total_rating
                    FROM student_trainees st
                    JOIN student_evaluations se ON st.id = student_id
                    ORDER BY st.student_name"""

                    cursor.execute(query)
                    return cursor.fetchall()
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Failed to fetch evaluated students: {e}")

                    return []
                finally:
                    if connection:
                        connection.close()
            return []

        title_label = ctk.CTkLabel(admin_homepage_frame, text="Evaluated Student",
                                   font=("Arial", 35, "bold"))
        title_label.place(x=520, y=20)

        history_frame = ctk.CTkFrame(admin_homepage_frame, fg_color="#f1f5fb", width=1275, height=720, corner_radius=0)
        history_frame.place(x=0, y=68)

        scroll_frame = ctk.CTkScrollableFrame(history_frame, width=1200, height=550)
        scroll_frame.place(x=33, y=0)

        headers_frame = ctk.CTkFrame(scroll_frame, fg_color="#f1f5fb", height=50)
        headers_frame.pack(fill="x", pady=(10, 20))

        ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 13, "bold")).place(x=20, y=10)
        ctk.CTkLabel(headers_frame, text="Name of HTE", width=200, font=("Arial", 13, "bold")).place(x=150, y=10)
        ctk.CTkLabel(headers_frame, text="Supervisor Email", width=230, font=("Arial", 13, "bold")).place(x=310, y=10)
        ctk.CTkLabel(headers_frame, text="Rating", width=230, font=("Arial", 13, "bold")).place(x=520, y=10)
        ctk.CTkLabel(headers_frame, text="Number of Hours", width=150, font=("Arial", 13, "bold")).place(x=750, y=10)
        ctk.CTkLabel(headers_frame, text="Training Period", width=150, font=("Arial", 13, "bold")).place(x=910, y=10)
        ctk.CTkLabel(headers_frame, text="Section", width=120, font=("Arial", 13, "bold")).place(x=1080, y=10)

        students = get_evaluated_student()

        for i, student in enumerate(students):
            student_frame = ctk.CTkFrame(scroll_frame, fg_color="#ffffff", height=40)
            student_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(student_frame, text=student['student_name'], width=120, anchor="w",
                         font=("Arial", 12)).place(x=20, y=5)
            ctk.CTkLabel(student_frame, text=student['hte_name'], width=200, anchor="w",
                         font=("Arial", 12)).place(x=190, y=5)
            ctk.CTkLabel(student_frame, text=student['supervisor_email'], width=230, anchor="w",
                         font=("Arial", 12)).place(x=340, y=5)
            int_value = int(student['total_rating'])
            ctk.CTkLabel(student_frame, text=f"{int_value}", width=230, anchor="w",
                         font=("Arial", 12)).place(x=620, y=5)
            ctk.CTkLabel(student_frame, text=str(student['hours_rendered']), width=100, anchor="w",
                         font=("Arial", 12)).place(x=800, y=5)
            ctk.CTkLabel(student_frame, text=student['training_period'], width=200, anchor="w",
                         font=("Arial", 12)).place(x=910, y=5)
            ctk.CTkLabel(student_frame, text=student['section'], width=200, anchor="w",
                         font=("Arial", 12)).place(x=1125, y=7)

    def evaluation_pending():
        for widget in admin_homepage_frame.winfo_children():
            widget.destroy()

        def get_pending_evaluations():
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    query = """SELECT st.* 
                    FROM student_trainees st
                    LEFT JOIN student_evaluations se ON st.id = se.student_id
                    WHERE se.id IS NULL
                    ORDER BY st.student_name"""

                    cursor.execute(query)
                    return cursor.fetchall()
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Failed to fetch pending evaluations: {e}")
                    return []
                finally:
                    if connection:
                        connection.close()
            return []

        title_label = ctk.CTkLabel(admin_homepage_frame, text="Evaluation Pending",
                                   font=("Arial", 35, "bold"))
        title_label.place(x=520, y=20)

        history_frame = ctk.CTkFrame(admin_homepage_frame, fg_color="#f1f5fb", width=1275, height=720, corner_radius=0)
        history_frame.place(x=0, y=68)

        scroll_frame = ctk.CTkScrollableFrame(history_frame, width=1200, height=550)
        scroll_frame.place(x=33, y=0)

        headers_frame = ctk.CTkFrame(scroll_frame, fg_color="#f1f5fb", height=50)
        headers_frame.pack(fill="x", pady=(10, 20))

        ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 13, "bold")).place(x=20, y=10)
        ctk.CTkLabel(headers_frame, text="Name of HTE", width=200, font=("Arial", 13, "bold")).place(x=150, y=10)
        ctk.CTkLabel(headers_frame, text="Supervisor Email", width=230, font=("Arial", 13, "bold")).place(x=310, y=10)
        ctk.CTkLabel(headers_frame, text="HTE Address", width=230, font=("Arial", 13, "bold")).place(x=530, y=10)
        ctk.CTkLabel(headers_frame, text="Number of Hours", width=150, font=("Arial", 13, "bold")).place(x=750, y=10)
        ctk.CTkLabel(headers_frame, text="Training Period", width=150, font=("Arial", 13, "bold")).place(x=910, y=10)
        ctk.CTkLabel(headers_frame, text="Section", width=120, font=("Arial", 13, "bold")).place(x=1080, y=10)

        students = get_pending_evaluations()
        for student in students:
            student_frame = ctk.CTkFrame(scroll_frame, fg_color="#ffffff", height=40)
            student_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(student_frame, text=student['student_name'], width=120, font=("Arial", 12)).place(x=20, y=5)
            ctk.CTkLabel(student_frame, text=student['hte_name'], width=200, font=("Arial", 12)).place(x=150, y=5)
            ctk.CTkLabel(student_frame, text=student['supervisor_email'], width=230, font=("Arial", 12)).place(x=310,
                                                                                                               y=5)
            ctk.CTkLabel(student_frame, text=student['hte_address'], width=230, font=("Arial", 12)).place(x=530, y=5)
            ctk.CTkLabel(student_frame, text=str(student['hours_rendered']), width=150, font=("Arial", 12)).place(x=750,
                                                                                                                  y=5)
            ctk.CTkLabel(student_frame, text=student['training_period'], width=150, font=("Arial", 12)).place(x=910,
                                                                                                              y=5)
            ctk.CTkLabel(student_frame, text=student['section'], width=120, font=("Arial", 12)).place(x=1080, y=5)

    def total_enrollees():
        for widget in admin_homepage_frame.winfo_children():
            widget.destroy()

        def get_all_enrollees():
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    query = """SELECT * FROM student_trainees
                    ORDER BY student_name"""
                    cursor.execute(query)
                    return cursor.fetchall()
                except sqlite3.Error as e:
                    messagebox.showerror("Database Error", f"Failed to fetch enrollees: {e}")
                    return []
                finally:
                    if connection:
                        connection.close()
            return []

        title_label = ctk.CTkLabel(admin_homepage_frame, text="Evaluation Pending",
                                   font=("Arial", 35, "bold"))
        title_label.place(x=520, y=20)

        history_frame = ctk.CTkFrame(admin_homepage_frame, fg_color="#f1f5fb", width=1275, height=720, corner_radius=0)
        history_frame.place(x=0, y=68)

        scroll_frame = ctk.CTkScrollableFrame(history_frame, width=1200, height=550)
        scroll_frame.place(x=33, y=0)

        headers_frame = ctk.CTkFrame(scroll_frame, fg_color="#f1f5fb", height=50)
        headers_frame.pack(fill="x", pady=(10, 20))

        ctk.CTkLabel(headers_frame, text="Student Trainee", width=120, font=("Arial", 13, "bold")).place(x=20, y=10)
        ctk.CTkLabel(headers_frame, text="Name of HTE", width=200, font=("Arial", 13, "bold")).place(x=150, y=10)
        ctk.CTkLabel(headers_frame, text="Supervisor Email", width=230, font=("Arial", 13, "bold")).place(x=310, y=10)
        ctk.CTkLabel(headers_frame, text="HTE Address", width=230, font=("Arial", 13, "bold")).place(x=530, y=10)
        ctk.CTkLabel(headers_frame, text="Number of Hours", width=150, font=("Arial", 13, "bold")).place(x=750, y=10)
        ctk.CTkLabel(headers_frame, text="Training Period", width=150, font=("Arial", 13, "bold")).place(x=910, y=10)
        ctk.CTkLabel(headers_frame, text="Section", width=120, font=("Arial", 13, "bold")).place(x=1080, y=10)

        students = get_all_enrollees()
        for student in students:
            student_frame = ctk.CTkFrame(scroll_frame, fg_color="#ffffff", height=40)
            student_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(student_frame, text=student['student_name'], width=120, font=("Arial", 12)).place(x=20, y=5)
            ctk.CTkLabel(student_frame, text=student['hte_name'], width=200, font=("Arial", 12)).place(x=150, y=5)
            ctk.CTkLabel(student_frame, text=student['supervisor_email'], width=230, font=("Arial", 12)).place(x=310,
                                                                                                               y=5)
            ctk.CTkLabel(student_frame, text=student['hte_address'], width=230, font=("Arial", 12)).place(x=530, y=5)
            ctk.CTkLabel(student_frame, text=str(student['hours_rendered']), width=150, font=("Arial", 12)).place(x=750,
                                                                                                                  y=5)
            ctk.CTkLabel(student_frame, text=student['training_period'], width=150, font=("Arial", 12)).place(x=910,
                                                                                                              y=5)
            ctk.CTkLabel(student_frame, text=student['section'], width=120, font=("Arial", 12)).place(x=1080, y=5)

        # Back button

    admin_navigation_frame = ctk.CTkFrame(ipes_admin_window, width=260, height=800, corner_radius=0, fg_color="#19202e")
    admin_navigation_frame.place(x=0, y=0)

    admin_header_frame = ctk.CTkFrame(ipes_admin_window, width=1920, height=110, corner_radius=0, fg_color="#ffffff")
    admin_header_frame.place(x=260, y=0)

    admin_homepage_frame = ctk.CTkFrame(ipes_admin_window, width=1297, height=800, fg_color="#f1f5fb", corner_radius=0)
    admin_homepage_frame.place(x=260, y=115)

    logo = ctk.CTkImage(light_image=Image.open(resource_path('DHVSU-LOGO.png')), size=(80, 80))
    image_lbl = ctk.CTkLabel(admin_header_frame, image=logo, text='')
    image_lbl.place(x=200, y=14)

    cea_logo = ctk.CTkImage(light_image=Image.open(resource_path('logocea1.png')), size=(100, 80))
    cea_image_lbl = ctk.CTkLabel(admin_header_frame, image=cea_logo, text='')
    cea_image_lbl.place(x=300, y=14)

    title_lbl = ctk.CTkLabel(admin_header_frame, text="IPES: INTERN PERFORMANCE EVALUATION SYSTEM ",
                             font=("Arial", 28, "bold"), text_color="#000000")
    title_lbl.place(x=410, y=40)

    admin_logo = ctk.CTkImage(light_image=Image.open(resource_path('Admin.png')), size=(120, 120))
    admin_logo_image_lbl = ctk.CTkLabel(admin_navigation_frame, image=admin_logo, text='')
    admin_logo_image_lbl.place(x=75, y=50)

    admin_lbl = ctk.CTkLabel(admin_navigation_frame, width=230, height=50, text="ADMIN", text_color="#FFFFFF",
                             fg_color="#19202e",
                             font=('Arial', 15, 'bold'))
    admin_lbl.place(x=15, y=150)

    dashboard_logo = ctk.CTkImage(light_image=Image.open(resource_path('Dashboard (1).png')), size=(40, 40))
    dashboard_btn = ctk.CTkButton(admin_navigation_frame, width=259, height=50, image=dashboard_logo, text="Dashboard",
                                  text_color="#FFFFFF", fg_color="#19202e",
                                  font=('Arial', 15, 'bold'), hover_color='#405460', command=show_homepage)
    dashboard_btn.place(x=0, y=220)

    active_user_logo = ctk.CTkImage(light_image=Image.open(resource_path('Active User.png')), size=(40, 40))
    active_user_btn = ctk.CTkButton(admin_navigation_frame, width=259, height=50, image=active_user_logo,
                                    text="Active User", text_color="#FFFFFF", fg_color="#19202e",
                                    font=('Arial', 15, 'bold'), hover_color='#405460', command=active_user)
    active_user_btn.place(x=0, y=280)

    create_user_logo = ctk.CTkImage(light_image=Image.open(resource_path('Create User.png')), size=(40, 40))
    create_user_btn = ctk.CTkButton(admin_navigation_frame, width=259, height=50, image=create_user_logo,
                                    text="Create User", text_color="#FFFFFF", fg_color="#19202e",
                                    font=('Arial', 15, 'bold'), hover_color='#405460', command=create_user)
    create_user_btn.place(x=0, y=340)

    user_management_logo = ctk.CTkImage(light_image=Image.open(resource_path('User Management.png')), size=(40, 40))
    user_management_btn = ctk.CTkButton(admin_navigation_frame, width=259, height=50, image=user_management_logo,
                                        text="User\nManagement", text_color="#FFFFFF", fg_color="#19202e",
                                        font=('Arial', 15, 'bold'), hover_color='#405460', command=user_management)
    user_management_btn.place(x=0, y=400)

    evaluated_student_logo = ctk.CTkImage(light_image=Image.open(resource_path('Evaluated Student.png')), size=(40, 40))
    evaluated_student_btn = ctk.CTkButton(admin_navigation_frame, width=259, height=50, image=evaluated_student_logo,
                                          text="Evaluated\nStudent", text_color="#FFFFFF", fg_color="#19202e",
                                          font=('Arial', 15, 'bold'), hover_color='#405460', command=evaluated_student)
    evaluated_student_btn.place(x=0, y=460)

    evaluation_pending_logo = ctk.CTkImage(light_image=Image.open(resource_path('pending.png')), size=(40, 40))
    evaluation_pending_btn = ctk.CTkButton(admin_navigation_frame, width=259, height=50, image=evaluation_pending_logo,
                                           text="Evaluation\nPending", text_color="#FFFFFF", fg_color="#19202e",
                                           font=('Arial', 15, 'bold'), hover_color='#405460',
                                           command=evaluation_pending)
    evaluation_pending_btn.place(x=0, y=520)

    total_enrollees_logo = ctk.CTkImage(light_image=Image.open(resource_path('total.png')), size=(40, 40))
    total_enrollees_btn = ctk.CTkButton(admin_navigation_frame, width=259, height=50, image=total_enrollees_logo,
                                        text="Total\nEnrollees", text_color="#FFFFFF", fg_color="#19202e",
                                        font=('Arial', 15, 'bold'), hover_color='#405460', command=total_enrollees)
    total_enrollees_btn.place(x=0, y=580)

    def logout_admin():
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            ipes_admin_window.destroy()
            main.deiconify()



    logout_admin_logo = ctk.CTkImage(light_image=Image.open(resource_path('logout.png')), size=(40, 40))
    logout_admin_btn = ctk.CTkButton(admin_navigation_frame, width=259, height=50, image=logout_admin_logo,
                                     text="Log Out", text_color="#FFFFFF", fg_color="#19202e", command=logout_admin,
                                     font=('Arial', 15, 'bold'), hover_color='#405460')
    logout_admin_btn.place(x=0, y=700)

    show_homepage()

    ipes_admin_window.grid_rowconfigure(0, weight=0)
    ipes_admin_window.grid_rowconfigure(1, weight=0)
    ipes_admin_window.grid_rowconfigure(2, weight=1)
    ipes_admin_window.grid_columnconfigure(0, weight=1)
    ipes_admin_window.mainloop()

def otp_send_verification_window(email, purpose, success_callback):
    ctk.set_appearance_mode("light")
    otp_send_window = ctk.CTkToplevel()
    otp_send_window.title("Intern Performance Evaluation System")
    otp_send_window.configure(bg='#B03052')
    otp_send_window.state('zoomed')  # Start in maximized state
    otp_send_window.resizable(True, True)
    otp_send_window.geometry(f"{main.winfo_screenwidth()}x{main.winfo_screenheight()}+0+0")
    otp_send_window.grid_rowconfigure(0, weight=1)
    otp_send_window.grid_columnconfigure(0, weight=1)
    otp_send_window.grab_set()

    homepage_bg = ctk.CTkImage(dark_image=Image.open(resource_path('verificationbg.png')), size=(1540, 795))
    image_homepage = ctk.CTkLabel(otp_send_window, image=homepage_bg, text='')
    image_homepage.grid(row=2, column=0, sticky="nsew")

    verify_label = ctk.CTkLabel(otp_send_window, text="Verification", font=("Arial", 45, "bold"), bg_color="#c4d5d7")
    verify_label.place(x=1000, y=140)

    codeveri_label = ctk.CTkLabel(otp_send_window, text="Enter Verification code:", font=("Arial", 25, "bold"),
                                  bg_color="#c4d5d7")
    codeveri_label.place(x=870, y=235)

    code_frame = ctk.CTkFrame(otp_send_window, bg_color="#c4d5d7", fg_color="#c4d5d7")
    code_frame.place(relx=0.728, rely=0.4, anchor='center')

    otp_entries = []

    def on_key(event, index):
        entry = otp_entries[index]
        value = entry.get()

        if len(value) > 1:
            entry.delete(1, "end")

        if event.keysym not in ("BackSpace", "Left", "Right") and value:
            if index < 5:
                otp_entries[index + 1].focus()

        elif event.keysym == "BackSpace" and not value:
            if index > 0:
                otp_entries[index - 1].focus()

    for i in range(6):
        entry = ctk.CTkEntry(code_frame, width=50, height=60, font=("Arial", 20, "bold"), fg_color="#c4d5d7",
                             justify="center",
                             border_width=4, border_color="#405460", corner_radius=30)

        entry.grid(row=0, column=i, padx=5)
        entry.bind("<KeyRelease>", lambda event, idx=i: on_key(event, idx))
        otp_entries.append(entry)

    def on_verify():
        entered_otp = ''.join([entry.get() for entry in otp_entries])
        if verify_otp_in_db(email, entered_otp, purpose):
            if purpose == 'login':
                messagebox.showinfo("Success", "Successful login!")
                otp_send_window.destroy()
                success_callback()
            elif purpose == 'admin':
                messagebox.showinfo("Success", "WELCOME ADMIN!")
                otp_send_window.destroy()
                success_callback()
            elif purpose == 'signup':
                messagebox.showinfo("Success", "Account created successfully!")
                otp_send_window.destroy()
                success_callback()
            elif purpose == 'password_reset':
                messagebox.showinfo("Success", "OTP verified! Please set your new password.")
                otp_send_window.destroy()
                success_callback()

        else:
            messagebox.showerror("Error", "Invalid or expired OTP")

    def resend_otp():
        new_otp = generate_otp()
        if send_otp_email(email, new_otp):
            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    cursor.execute("INSERT INTO otps (email, otp, purpose) VALUES (?, ?, ?)",
                                   (email, new_otp, purpose))
                    connection.commit()
                    messagebox.showinfo("Resent", "New OTP sent to your email")
                except sqlite3.Error as e:
                    messagebox.showerror("Error", str(e))
                finally:
                    if connection:
                        connection.close()


    rsend = ctk.CTkLabel(otp_send_window, text="If you didn’t receive a code!", font=("Lato", 14, "bold"),
                         bg_color="#c4d5d7")
    rsend.place(x=990, y=400)

    resend_lbl = ctk.CTkLabel(otp_send_window, text="Resend", font=("Lato", 14, "bold"), bg_color="#c4d5d7",
                              text_color="#60646B", cursor="hand2")
    resend_lbl.place(x=1190, y=400)
    resend_lbl.bind("<Button-1>", lambda e: resend_otp())

    verify_button = ctk.CTkButton(otp_send_window, text="Verify", font=("Arial", 20, "bold"), width=500, height=40,
                                  corner_radius=20, bg_color="#c4d5d7", fg_color="#405460", hover_color="#005A9E",
                                  text_color="#c4d5d7", command=on_verify)
    verify_button.place(x=875, y=450)


    otp_send_window.grid_rowconfigure(0, weight=0)
    otp_send_window.grid_rowconfigure(1, weight=0)
    otp_send_window.grid_rowconfigure(2, weight=1)
    otp_send_window.grid_columnconfigure(0, weight=1)
    return otp_send_window

def forget_password():
    main.withdraw()
    ctk.set_appearance_mode("light")
    forget_pass_window = ctk.CTkToplevel()
    forget_pass_window.title("Intern Performance Evaluation System")
    forget_pass_window.configure(bg='#B03052')
    forget_pass_window.geometry(f"{main.winfo_screenwidth()}x{main.winfo_screenheight()}+0+0")
    forget_pass_window.state('zoomed')  # Start in maximized state
    forget_pass_window.resizable(True, True)
    forget_pass_window.grid_rowconfigure(0, weight=1)
    forget_pass_window.grid_columnconfigure(0, weight=1)

    veribg = ctk.CTkImage(light_image=Image.open(resource_path("verificationbg.png")), size=(1540, 795))
    image_veribg = ctk.CTkLabel(forget_pass_window, image=veribg, text='')
    image_veribg.grid(row=0, column=0, sticky="nsew")

    def send_reset_otp():
        email = usname_fp_box.get().strip()
        if not email:
            messagebox.showerror("Error", "Please enter your email address")
            return

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ? ", (email,))
                if not cursor.fetchone():
                    messagebox.showerror("Error", "Email not registered")
                    return

                otp = generate_otp()
                cursor.execute("INSERT INTO otps (email, otp, purpose) VALUES (?, ?, 'password_reset')",
                               (email, otp))
                connection.commit()

                if send_otp_email(email,otp):
                    forget_pass_window.withdraw()
                    otp_send_verification_window(email, 'password_reset', success_callback=lambda:
                    [forget_pass_window.destroy(), new_password_window(email)])

                else:
                    messagebox.showerror("Error", "Failed to send OTP")
            except sqlite3.Error as e:
                messagebox.showerror("Database Error", str(e))
            finally:
                if connection:
                    connection.close()

    forget_pass_lbl = ctk.CTkLabel(forget_pass_window, text="Forgot Password", font=("Lato", 45, "bold"),
                                   bg_color="#c4d5d7")
    forget_pass_lbl.place(x=940, y=200)

    usname_forgotpass_lbl = ctk.CTkLabel(forget_pass_window, text="Enter Email Address:", font=("Lato", 20, "bold"),
                                         bg_color="#c4d5d7")
    usname_forgotpass_lbl.place(x=885, y=310)

    usname_fp_box_frame = ctk.CTkFrame(forget_pass_window, width=500, height=55, fg_color="#405460",
                                       corner_radius=10, bg_color="#c4d5d7")
    usname_fp_box_frame.place(x=880, y=350)

    usname_fp_box = ctk.CTkEntry(usname_fp_box_frame, width=477, height=38, corner_radius=10,
                                 placeholder_text="example@gmail.com", fg_color="#c5d7d8", font=("Lato", 14), )
    usname_fp_box.place(x=10, y=8)

    send_btn_fp = ctk.CTkButton(forget_pass_window, text="Send", width=500, height=40, corner_radius=20,
                                text_color="#c4d5d7", command=send_reset_otp,
                                fg_color="#405460", bg_color="#c4d5d7", hover_color="#60646B",
                                font=("Lato", 20, "bold"))
    send_btn_fp.place(x=880, y=440)

    btsi_btn_fp = ctk.CTkLabel(forget_pass_window, text="Back to", bg_color="#c4d5d7",
                               font=("Lato", 14, "bold"))
    btsi_btn_fp.place(x=1070, y=650)

    btli_btn_fp = ctk.CTkLabel(forget_pass_window, text="Log in", bg_color="#c4d5d7",
                               text_color="#44545d", font=("Lato", 14, "bold"), cursor="hand2")
    btli_btn_fp.place(x=1127, y=650)
    btli_btn_fp.bind("<Button-1>", lambda event: open_user_from_forget(forget_pass_window))

    forget_pass_window.grid_rowconfigure(0, weight=0)
    forget_pass_window.grid_rowconfigure(1, weight=0)
    forget_pass_window.grid_rowconfigure(2, weight=1)
    forget_pass_window.grid_columnconfigure(0, weight=1)
    forget_pass_window.mainloop()

def new_password_window(email):
    main.withdraw()
    ctk.set_appearance_mode("light")
    new_pass_window = ctk.CTkToplevel()
    new_pass_window.title("Intern Performance Evaluation System")
    new_pass_window.configure(bg='#B03052')
    new_pass_window.state('zoomed')  # Start in maximized state
    new_pass_window.resizable(True, True)
    new_pass_window.geometry(f"{main.winfo_screenwidth()}x{main.winfo_screenheight()}+0+0")
    new_pass_window.grid_rowconfigure(0, weight=1)
    new_pass_window.grid_columnconfigure(0, weight=1)

    newpassbg = ctk.CTkImage(light_image=Image.open(resource_path("verificationbg.png")), size=(1540, 795))
    image_newpassbg = ctk.CTkLabel(new_pass_window, image=newpassbg, text='')
    image_newpassbg.grid(row=0, column=0, sticky="nsew")

    def update_password():
        new_password = newpass_box.get()
        confirm_password = connewpass_box.get()

        if not new_password or not confirm_password:
            messagebox.showerror("Error", "All fields are required!")
            return

        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        password_pattern = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
        if not re.match(password_pattern, new_password):
            messagebox.showerror("Error",
                                 "Password must contain:\n"
                                 "- At least 8 characters\n"
                                 "- Letters, numbers, and special symbols")
            return

        try:
            hashed_pw = generate_password_hash(new_password)
            connection = create_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_pw, email))
                connection.commit()
                messagebox.showinfo("Success", "Password updated successfully!")
                new_pass_window.destroy()
                loginAs_user()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            if connection:
                connection.close()

    newpass_lbl = ctk.CTkLabel(new_pass_window, text="NEW PASSWORD", font=("Lato", 35, "bold"), bg_color="#c4d5d7")
    newpass_lbl.place(x=980, y=200)

    ent_newpass_lbl = ctk.CTkLabel(new_pass_window, text="Enter New Password:", font=("Lato", 17, "bold"),
                                   bg_color="#c4d5d7")
    ent_newpass_lbl.place(x=935, y=290)

    ent_newpass_box_frame = ctk.CTkFrame(new_pass_window, width=400, height=55, fg_color="#405460", corner_radius=10,
                                         bg_color="#c4d5d7")
    ent_newpass_box_frame.place(x=930, y=320)

    newpass_box = ctk.CTkEntry(ent_newpass_box_frame, width=380, height=38, corner_radius=10, font=("Lato", 14),
                               placeholder_text="At least 8 characters incl. numbers & symbols", fg_color="#c4d5d7"
                               )
    newpass_box.place(x=10, y=9)

    confirm_newpass_lbl = ctk.CTkLabel(new_pass_window, text="Confirm New Password:", font=("Lato", 17, "bold"),
                                       bg_color="#c4d5d7")
    confirm_newpass_lbl.place(x=935, y=380)

    confirm_newpass_box_frame = ctk.CTkFrame(new_pass_window, width=400, height=55, fg_color="#405460",
                                             corner_radius=10,
                                             bg_color="#c4d5d7")
    confirm_newpass_box_frame.place(x=930, y=410)

    connewpass_box = ctk.CTkEntry(confirm_newpass_box_frame, width=380, height=38, corner_radius=10, font=("Lato", 14),
                                  fg_color="#c4d5d7")
    connewpass_box.place(x=10, y=9)

    submit_btn = ctk.CTkButton(new_pass_window, text="Submit", width=400, height=40, corner_radius=20,
                               text_color="#c4d5d7", command=update_password,
                               fg_color="#405460", bg_color="#c4d5d7", hover_color="#60646B", font=("Lato", 20, "bold"))
    submit_btn.place(x=930, y=500)

    new_pass_window.grid_rowconfigure(0, weight=0)
    new_pass_window.grid_rowconfigure(1, weight=0)
    new_pass_window.grid_rowconfigure(2, weight=1)
    new_pass_window.grid_columnconfigure(0, weight=1)
    new_pass_window.mainloop()

def store_credentials(username, password):
    try:
        keyring.set_password(SERVICE_NAME, username, password)
    except Exception as e:
        messagebox.showerror("Error", f"Could not save credentials: {str(e)}")

def load_saved_credentials():
    try:
        creds = keyring.get_credential(SERVICE_NAME, None)
        if creds:
            return {"username": creds.username, "password": creds.password}
    except:
        pass
    return {}

def clear_credentials(username):
    try:
        keyring.delete_password(SERVICE_NAME, username)
    except:
        pass



homepage_bg = ctk.CTkImage(dark_image= Image.open(resource_path('homepagebg.png')), size =(1540,690))
image_homepage =ctk.CTkLabel(main, image = homepage_bg, text ='')
image_homepage.grid(row=2, column=0,  sticky="nsew")

homepage_frame =ctk.CTkFrame(main, height=100,fg_color="#c4c9ca", corner_radius=0)
homepage_frame.grid(row = 0 , column = 0, sticky="nsew")

homepage_hr = ctk.CTkFrame(main, height = 5, fg_color="#3e4045", corner_radius=0)
homepage_hr.grid(row=1, column=0, sticky="ew")

logo = ctk.CTkImage(light_image= Image.open(resource_path('DHVSU-LOGO.png')), size = (99,99))
image_lbl = ctk.CTkLabel(homepage_frame, image = logo, text = '')
image_lbl.grid(row=0 , column = 1, sticky="ew")

cea_logo = ctk.CTkImage(light_image= Image.open(resource_path('logocea1.png')), size = (130,99))
cea_image_lbl = ctk.CTkLabel(homepage_frame, image = cea_logo, text = '')
cea_image_lbl.grid(row=0 , column = 2, sticky="ew")

title_lbl = ctk.CTkLabel(homepage_frame, text=" Intern Performance Evaluation System ", font=("Lato" , 27, "bold"))
title_lbl.grid(row=0 , column = 4, sticky="ew")

button_signup = ctk.CTkButton(homepage_frame,height= 40, width = 130, text="Log In",
                              corner_radius=8, fg_color="#C4C9CA",
                            text_color="black" , font=("Lato",15), hover_color="#405460", command=loginAs_user)
button_signup.grid(row=0 , column= 5, padx= 510 )

button_start = ctk.CTkButton(homepage_frame, height= 40,width = 130, text="Get Started",
                             corner_radius=8, fg_color="#8D9094", hover_color="#405460", command= signupAs_user,
                              text_color="#C4D5D7")
button_start.place(x=1390, y= 30 )

button_starter = ctk.CTkButton(main, width = 280, height= 60, text="Let's Get Started",
                                 corner_radius=8, fg_color="#8D9094", bg_color="#60646b", command= signupAs_user,
                              text_color="#EBE8DB", font= ("Lato" , 16, "bold"), hover_color="#405460")
button_starter.place(x= 380, y = 580)


main.grid_rowconfigure(0, weight=0)
main.grid_rowconfigure(1, weight=0)
main.grid_rowconfigure(2, weight=1)
main.grid_columnconfigure(0, weight=1)
main.mainloop()
