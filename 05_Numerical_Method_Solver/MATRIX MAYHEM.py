import customtkinter as ctk
from PIL import Image, ImageTk
import pygame
from fractions import Fraction
import mysql.connector
from tkinter import messagebox
from mysql.connector import Error, connect

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
main = ctk.CTk()
main.title("Starting Page")
main.state('zoomed')
main.grid_rowconfigure(0, weight=1)
main.grid_columnconfigure(0, weight=1)
main.resizable(True, True)
pygame.mixer.init()


def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='mickel',
            port='3306',
            database='numerical'
        )
        return connection
    except Error as e:
        messagebox.showerror("Database Error", f"Failed to connect: {e}")
        return None


def save_to_db(method, equations, solution):
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('''INSERT INTO history (method, equations, solution)
                         VALUES (%s, %s, %s)''',
                       (method, equations, solution))
        connection.commit()
    except Error as e:
        print(f"Database error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_history(method=None):
    try:
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        if method:
            cursor.execute("SELECT * FROM history WHERE method = %s ORDER BY timestamp DESC", (method,))
        else:
            cursor.execute("SELECT * FROM history ORDER BY timestamp DESC")
        return cursor.fetchall()
    except Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def clear_history(method=None):
    try:
        connection = create_connection()
        cursor = connection.cursor()
        if method:
            cursor.execute("DELETE FROM history WHERE method = %s", (method,))
        else:
            cursor.execute("DELETE FROM history")
        connection.commit()
    except Error as e:
        print(f"Database error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def start_selection():
    main.withdraw()
    pygame.mixer.music.load("OK.mp3")  # or .wav
    pygame.mixer.music.play()
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTkToplevel()
    root.title("Start Selection")
    root.state('zoomed')  # Start in maximized state
    root.resizable(True, True)
    root.geometry(f"{main.winfo_screenwidth()}x{main.winfo_screenheight()}+0+0")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    selected_method = None

    try:
        bg_img = ctk.CTkImage(light_image=Image.open("Start 1.png"), size=(1920, 1080))
        bg_lbl = ctk.CTkLabel(root, image=bg_img, text="")
        bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
    except FileNotFoundError:
        root.configure(fg_color="#2b2b2b")

    # Labels for ARROWs
    image_label = ctk.CTkLabel(root, text="", bg_color="transparent")
    image_labelB = ctk.CTkLabel(root, text="", bg_color="transparent")
    image_labelC = ctk.CTkLabel(root, text="", bg_color="transparent")

    # Arrow Image Persistent Reference
    arrow_img = Image.open("ARROW.png")
    arrow_tk = ctk.CTkImage(light_image=arrow_img, size=(37, 70))
    image_label.configure(image=arrow_tk)

    def open_cram_method_window():
        root.withdraw()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        choose_method_cram = ctk.CTkToplevel()
        choose_method_cram.title("Cramers Method")
        choose_method_cram.state('zoomed')
        choose_method_cram.grid_rowconfigure(0, weight=1)
        choose_method_cram.grid_columnconfigure(0, weight=1)
        choose_method_cram.resizable(True, True)
        selected_cram_method = None

        try:
            bg_img = ctk.CTkImage(light_image=Image.open("Cram Select.png"), size=(1920, 1080))
            bg_lbl = ctk.CTkLabel(choose_method_cram, image=bg_img, text="")
            bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
        except FileNotFoundError:
            choose_method_cram.configure(fg_color="#2b2b2b")

        def open_cram_method_A():
            choose_method_cram.withdraw()
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            method_cram_A = ctk.CTkToplevel()
            method_cram_A.title("Cramer's Rule Solver METHOD A")
            method_cram_A.state('zoomed')
            method_cram_A.grid_rowconfigure(0, weight=1)
            method_cram_A.grid_columnconfigure(0, weight=1)
            method_cram_A.resizable(True, True)
            pygame.mixer.init()

            # Initialize variables that will be used globally
            entries = []
            variable_labels = []
            input_inner_frame = None
            input_canvas = None
            solution_text = None
            dimension_var = None

            def create_matrix_entries():
                """Create entry widgets based on current dimension"""
                nonlocal entries, variable_labels, input_inner_frame, input_canvas, dimension_var

                n = dimension_var.get()

                # Clear existing widgets from inner frame
                for widget in input_inner_frame.winfo_children():
                    widget.destroy()

                # Clear existing variable labels
                for label in variable_labels:
                    label.destroy()
                variable_labels = []

                # Create a header frame for variable labels
                header_frame = ctk.CTkFrame(input_inner_frame, fg_color="#f0f9ff", corner_radius=0)
                header_frame.grid(row=0, column=0, columnspan=(n * 2) + 1, sticky="ew")

                # Create new variable labels in the header frame
                variables = [f"X{i + 1}" for i in range(n)] + ['  D']
                for i, var in enumerate(variables):
                    label = ctk.CTkLabel(
                        header_frame,
                        text=var,
                        text_color="#ffcf00",
                        fg_color="#f0f9ff",
                        font=("Press Start 2P", 30, "bold"),
                        width=90,
                        anchor="center"
                    )
                    if i < n:
                        label.grid(row=0, column=i * 2, padx=35, pady=(0, 10))
                    else:
                        label.grid(row=0, column=n * 2, padx=35, pady=(0, 10))
                    variable_labels.append(label)

                # Create entry fields in the inner frame below header
                entries = []
                for i in range(n):
                    row = []
                    for j in range(n + 1):  # n coefficients + 1 constant
                        entry = ctk.CTkEntry(
                            input_inner_frame,
                            width=90,
                            height=70,
                            fg_color="#0055a5",
                            border_color="#003366",
                            text_color="white",
                            justify="center",
                            font=("Press Start 2P", 20, "bold")
                        )
                        entry.grid(row=i + 1, column=j * 2, padx=35, pady=15)

                        # Add = sign before constant term
                        if j == n - 1:
                            equals = ctk.CTkLabel(
                                input_inner_frame,
                                text="=",
                                text_color="#000000",
                                font=("Press Start 2P", 35, "bold")
                            )
                            equals.grid(row=i + 1, column=j * 2 + 1, padx=5)

                        row.append(entry)
                    entries.append(row)

                # Update scroll region after adding widgets
                input_inner_frame.update_idletasks()
                input_canvas.configure(scrollregion=input_canvas.bbox("all"), bg="#f0f9ff")

            def update_matrix_size(choice):
                """Update the matrix size when dimension changes"""
                pygame.mixer.init()
                pygame.mixer.music.load("Select.mp3")
                pygame.mixer.music.play()
                create_matrix_entries()
                clear_entries()

            def format_matrix(matrix, name):
                """Format matrix for display in solution text"""
                n = len(matrix)
                lines = [f"{name} = "]
                for row in matrix:
                    line = "|" + " ".join(f"{elem:>8.2f}" for elem in row) + "|"
                    lines.append(line)
                return "\n".join(lines)

            def calculate_determinant_with_steps(matrix, matrix_name):
                """Calculate determinant with detailed multiplication steps"""
                n = len(matrix)
                solution = ""

                if n == 2:
                    # 2x2 case with detailed steps
                    a, b = matrix[0]
                    c, d = matrix[1]

                    solution += f"{matrix_name} = ({a})×({d}) - ({b})×({c})\n"
                    solution += f"{matrix_name} = {a * d} - {b * c}\n"
                    solution += f"{matrix_name} = {a * d - b * c}\n"

                    return a * d - b * c, solution

                elif n == 3:
                    # 3x3 case with detailed steps
                    a, b, c = matrix[0]
                    d, e, f = matrix[1]
                    g, h, i = matrix[2]

                    solution += f"{matrix_name} = {a}({e}×{i} - {f}×{h}) - {b}({d}×{i} - {f}×{g}) + {c}({d}×{h} - {e}×{g})\n"

                    term1 = e * i - f * h
                    term2 = d * i - f * g
                    term3 = d * h - e * g

                    solution += f"{matrix_name} = {a}({term1}) - {b}({term2}) + {c}({term3})\n"

                    term1_val = a * term1
                    term2_val = b * term2
                    term3_val = c * term3

                    solution += f"{matrix_name} = {term1_val} - {term2_val} + {term3_val}\n"

                    det = term1_val - term2_val + term3_val
                    solution += f"{matrix_name} = {det}\n"

                    return det, solution

                else:
                    # For larger matrices (simplified display)
                    det = 0
                    solution += f"Calculating {n}x{n} determinant using cofactor expansion:\n"

                    for col in range(n):
                        minor = [row[:col] + row[col + 1:] for row in matrix[1:]]
                        sign = (-1) ** col
                        minor_det, _ = calculate_determinant_with_steps(minor, f"Minor{col + 1}")
                        cofactor = sign * matrix[0][col] * minor_det
                        det += cofactor

                        solution += f"Cofactor {col + 1}: ({sign})×{matrix[0][col]}×{minor_det} = {cofactor}\n"

                    solution += f"{matrix_name} = Sum of cofactors = {det}\n"
                    return det, solution

            def parse_fraction(value):
                try:
                    # Try to convert directly to float first
                    return float(value)
                except ValueError:
                    # If that fails, try to parse as fraction
                    try:
                        if '/' in value:
                            numerator, denominator = value.split('/')
                            return float(numerator) / float(denominator)
                        else:
                            return float(value)
                    except:
                        raise ValueError("Invalid input - must be a number or fraction (like '1/2')")

            def format_as_fraction(value):
                try:
                    # Try to format as simplified fraction
                    frac = Fraction(value).limit_denominator()
                    if frac.denominator == 1:
                        return str(frac.numerator)
                    return f"{frac.numerator}/{frac.denominator}"
                except:
                    return f"{value:.4f}"

            def solve():
                pygame.mixer.init()
                pygame.mixer.music.load("OK.mp3")
                pygame.mixer.music.play()
                try:
                    n = dimension_var.get()

                    # Get values from entry fields USING parse_fraction
                    coeffs = []
                    for row in entries:
                        row_values = []
                        for entry in row:
                            value = parse_fraction(entry.get())
                            row_values.append(value)
                        coeffs.append(row_values)

                    # Prepare solution text
                    solution = "Input Equations:\n\n"

                    # Display the input equations
                    for i in range(n):
                        equation = ""
                        for j in range(n):
                            coeff = coeffs[i][j]
                            var = f"X{j + 1}"
                            if j == 0:
                                equation += f"{coeff}{var}"
                            else:
                                equation += f" {'+' if coeff >= 0 else '-'} {abs(coeff)}{var}"
                        equation += f" = {coeffs[i][n]}"
                        solution += equation + "\n"
                    solution += "\nSolution Steps:\n\n"

                    # Create main matrix and constants
                    main_matrix = [row[:n] for row in coeffs]
                    constants = [row[n] for row in coeffs]

                    # Display main matrix
                    solution += "1.) Main Matrix (D):\n"
                    solution += format_matrix(main_matrix, "D") + "\n\n"

                    # Calculate main determinant D with steps
                    solution += "2.) Calculate Determinant of (D):\n"
                    D, d_steps = calculate_determinant_with_steps(main_matrix, "D")
                    solution += d_steps + "\n"

                    if abs(D) < 1e-10:
                        solution += "The system has no unique solution (determinant is zero)"
                        solution_text.delete("1.0", "end")
                        solution_text.insert("1.0", solution)
                        return

                    # Calculate determinants for each variable
                    solutions = {}
                    for i in range(n):
                        # Create matrix with replaced column
                        new_matrix = [row[:] for row in main_matrix]
                        for j in range(n):
                            new_matrix[j][i] = constants[j]

                        # Display the modified matrix
                        var_name = f"X{i + 1}"
                        solution += f"3.) {i + 1} Matrix for {var_name} ({var_name}):\n"
                        solution += format_matrix(new_matrix, f"{var_name}") + "\n\n"

                        # Calculate determinant with steps
                        solution += f"Calculate Determinant of {var_name} (D{var_name}):\n"
                        D_var, d_var_steps = calculate_determinant_with_steps(new_matrix, f"D{var_name}")
                        solution += d_var_steps + "\n"

                        # Calculate solution
                        solutions[var_name] = D_var / D

                    # Final solutions
                    solution += "4.) Final Solutions:\n"
                    for var in sorted(solutions.keys()):
                        frac_solution = format_as_fraction(solutions[var])
                        solution += f"   {var} = D{var}/D = {frac_solution} (≈{solutions[var]:.4f})\n"

                    solution_text.delete("1.0", "end")
                    solution_text.insert("1.0", solution)

                    # Save to database
                    equations = []
                    for i in range(n):
                        equation = " + ".join(
                            [f"{entries[i][j].get()}x{j + 1}" for j in range(n)]) + f" = {entries[i][n].get()}"
                        equations.append(equation)
                    solution_text_value = solution_text.get("1.0", "end")
                    save_to_db('cramers_a', '\n'.join(equations), solution_text_value)

                except ValueError:
                    solution_text.delete("1.0", "end")
                    solution_text.insert("1.0", "Please enter valid numbers in all fields")

            def clear_entries():
                pygame.mixer.init()
                pygame.mixer.music.load("Select.mp3")
                pygame.mixer.music.play()

                # Clear all entry fields
                for row in entries:
                    for entry in row:
                        entry.delete(0, "end")
                # Clear solution text
                solution_text.delete("1.0", "end")

            def back_button2():
                pygame.mixer.init()
                pygame.mixer.music.load("Back Sound.mp3")
                pygame.mixer.music.play()
                method_cram_A.withdraw()
                choose_method_cram.deiconify()

            def history_button_cram_A():
                method_cram_A.withdraw()
                pygame.mixer.init()
                pygame.mixer.music.load("Back Sound.mp3")
                pygame.mixer.music.play()

                ctk.set_appearance_mode("dark")
                ctk.set_default_color_theme("blue")
                history_window = ctk.CTkToplevel()
                history_window.title("Cramer's Method A History")
                history_window.state('zoomed')
                history_window.grid_rowconfigure(0, weight=1)
                history_window.grid_columnconfigure(0, weight=1)
                history_window.resizable(True, True)
                pygame.mixer.init()

                def back_to_solver():
                    pygame.mixer.init()
                    pygame.mixer.music.load("Back Sound.mp3")
                    pygame.mixer.music.play()
                    history_window.withdraw()
                    method_cram_A.deiconify()

                def clear_history_entries():
                    pygame.mixer.music.load("Select.mp3")
                    pygame.mixer.music.play()
                    clear_history('cramers_a')
                    history_text.delete("1.0", "end")

                bg_img = ctk.CTkImage(light_image=Image.open("history.png"), size=(1920, 1030))
                bg_lbl = ctk.CTkLabel(history_window, image=bg_img, text="")
                bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

                solu_frame = ctk.CTkFrame(history_window, fg_color=("white", "gray20"))
                solu_frame.place(x=620, y=130)
                solution_frame = ctk.CTkFrame(solu_frame, width=690, height=490)
                solution_frame.pack(pady=10, padx=10)
                history_text = ctk.CTkTextbox(solution_frame, height=490, width=690, font=("Arial", 25, "bold"))
                history_text.pack(pady=10, padx=10)

                history_text.insert("end", "Cramer's Method A History:\n\n")
                history = get_history('cramers_a')

                for entry in history:
                    history_text.insert("end", f"ID: {entry['id']}\n")
                    history_text.insert("end", f"Date: {entry['timestamp']}\n")
                    history_text.insert("end", "Equations:\n")
                    history_text.insert("end", f"{entry['equations']}\n")
                    history_text.insert("end", "\nSolution:\n")
                    history_text.insert("end", f"{entry['solution']}\n")
                    history_text.insert("end", "=" * 50 + "\n")

                back_btn_img = Image.open("Back.png").resize((500, 150))
                back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
                back_button = ctk.CTkButton(history_window, image=back_iconBack, corner_radius=0, text="",
                                            fg_color="#000000",
                                            command=back_to_solver,
                                            hover_color="#ffffff")
                back_button.place(x=50, y=900)

                clear_history_img = Image.open("Clear Button.png").resize((500, 150))
                iconClearHistory = ctk.CTkImage(clear_history_img, size=(180, 70))
                clear_history_btn = ctk.CTkButton(history_window, image=iconClearHistory,
                                                  text="", corner_radius=0, fg_color="#000000",
                                                  hover_color="#ffffff", command=clear_history_entries)
                clear_history_btn.place(x=230, y=900)

                history_window.mainloop()

            bg_img = ctk.CTkImage(light_image=Image.open("ABG.png"), size=(1920, 1080))
            bg_lbl = ctk.CTkLabel(method_cram_A, image=bg_img, text="")
            bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

            # Create main frame
            main_frame = ctk.CTkFrame(method_cram_A, fg_color=("#f0f9ff"), corner_radius=0)
            main_frame.place(x=155, y=205)

            # Create solution frame
            s_frame = ctk.CTkFrame(method_cram_A, fg_color=("white", "gray20"))
            s_frame.place(x=1040, y=90)

            # Dimension selector
            dimension_label = ctk.CTkLabel(
                method_cram_A,
                text="Matrix Dimension:",
                font=("Press Start 2P", 25),
                fg_color="#f0f9ff",
                text_color="#000000"
            )
            dimension_label.place(x=200, y=160)

            dimension_var = ctk.IntVar(value=3)
            dimension_selector = ctk.CTkOptionMenu(
                method_cram_A,
                values=["2", "3", "4", "5", "6"],
                variable=dimension_var,
                font=("Press Start 2P", 20),
                command=update_matrix_size,
                width=170,
                height=50,
                dropdown_font=("Press Start 2P", 20)
            )
            dimension_selector.place(x=650, y=150)

            # Input frame
            input_frame = ctk.CTkFrame(
                main_frame,
                fg_color="#f0f9ff",
                width=900,
                height=320
            )
            input_frame.pack(pady=20)

            # Canvas for scrolling
            input_canvas = ctk.CTkCanvas(input_frame, width=650, height=320)
            input_canvas.pack(side="left", fill="both", expand=True)

            # Scrollbars
            v_scroll = ctk.CTkScrollbar(input_frame, orientation="vertical", command=input_canvas.yview)
            v_scroll.pack(side="right", fill="y")
            h_scroll = ctk.CTkScrollbar(main_frame, orientation="horizontal", command=input_canvas.xview)
            h_scroll.pack(side="bottom", fill="x")

            input_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            input_canvas.bind('<Configure>',
                              lambda e: input_canvas.configure(scrollregion=input_canvas.bbox("all")))

            # Inner frame for entries
            input_inner_frame = ctk.CTkFrame(
                input_canvas,
                fg_color="#f0f9ff"
            )
            input_canvas.create_window((0, 0), window=input_inner_frame, anchor="nw")

            # Initialize entries and labels
            create_matrix_entries()

            solution_frame = ctk.CTkFrame(s_frame, width=700, height=500)
            solution_frame.pack(pady=10, padx=10)

            # Create scrollable text widget for solution
            solution_text = ctk.CTkTextbox(solution_frame, height=500, width=700, font=("Arial", 25, "bold"))
            solution_text.pack(pady=10, padx=10)

            solve_btn = ctk.CTkButton(method_cram_A, text="SOLVE", font=("Press Start 2P", 25, "bold"), command=solve,
                                      height=76, width=154, corner_radius=0, fg_color="#0054a7")
            solve_btn.place(x=690, y=664)

            # Clear button
            clear_btn = ctk.CTkButton(method_cram_A, text="CLEAR", font=("Press Start 2P", 25, "bold"),
                                      command=clear_entries, height=76, width=180, corner_radius=0,
                                      fg_color="#0054a7")
            clear_btn.place(x=480, y=664)

            # History button
            history_img = Image.open("History button.png").resize((500, 150))
            iconHistory = ctk.CTkImage(history_img, size=(180, 70))
            history_btn = ctk.CTkButton(method_cram_A, image=iconHistory,
                                        text="", corner_radius=0, fg_color="#000000",
                                        hover_color="#ffffff", command=history_button_cram_A)
            history_btn.place(x=230, y=900)

            # Back button
            back_btn_img = Image.open("Back.png").resize((500, 150))
            back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
            back_button = ctk.CTkButton(method_cram_A, image=back_iconBack, text="", corner_radius=0,
                                        fg_color="#000000", hover_color="#ffffff",
                                        command=back_button2)
            back_button.place(x=50, y=900)

            method_cram_A.mainloop()

        def open_cram_method_B():
            choose_method_cram.withdraw()
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            method_cram_B = ctk.CTkToplevel()
            method_cram_B.title("Cramer's Rule Solver METHOD B")
            method_cram_B.state('zoomed')
            method_cram_B.grid_rowconfigure(0, weight=1)
            method_cram_B.grid_columnconfigure(0, weight=1)
            method_cram_B.resizable(True, True)
            pygame.mixer.init()

            entries = []
            variable_labels = []
            input_inner_frame = None
            input_canvas = None
            solution_text = None
            dimension_var = None

            def create_matrix_entries():
                """Create entry widgets based on current dimension"""
                nonlocal entries, variable_labels, input_inner_frame, input_canvas, dimension_var

                n = dimension_var.get()
                # Clear existing widgets
                for widget in input_inner_frame.winfo_children():
                    widget.destroy()
                variable_labels.clear()

                # Header frame
                header_frame = ctk.CTkFrame(input_inner_frame, fg_color="#f0f9ff", corner_radius=0)
                header_frame.grid(row=0, column=0, columnspan=(n * 2) + 1, sticky="ew")

                # Variable labels
                variables = [f"X{i + 1}" for i in range(n)] + ['  D']
                for i, var in enumerate(variables):
                    label = ctk.CTkLabel(
                        header_frame,
                        text=var,
                        text_color="#ffcf00",
                        fg_color="#f0f9ff",
                        font=("Press Start 2P", 30, "bold"),
                        width=90,
                        anchor="center"
                    )
                    pos = i * 2 if i < n else n * 2
                    label.grid(row=0, column=pos, padx=35, pady=(0, 10))
                    variable_labels.append(label)

                # Create entry fields
                entries = []
                for i in range(n):
                    row = []
                    for j in range(n + 1):
                        entry = ctk.CTkEntry(
                            input_inner_frame,
                            width=90,
                            height=70,
                            fg_color="#0055a5",
                            border_color="#003366",
                            text_color="white",
                            justify="center",
                            font=("Press Start 2P", 20, "bold")
                        )
                        entry.grid(row=i + 1, column=j * 2, padx=35, pady=15)

                        if j == n - 1:
                            equals = ctk.CTkLabel(
                                input_inner_frame,
                                text="=",
                                text_color="#000000",
                                font=("Press Start 2P", 35, "bold")
                            )
                            equals.grid(row=i + 1, column=j * 2 + 1, padx=5)
                        row.append(entry)
                    entries.append(row)

                input_inner_frame.update_idletasks()
                input_canvas.configure(scrollregion=input_canvas.bbox("all"), bg="#f0f9ff")
                return entries

            def format_matrix(matrix, name=""):
                """Format matrix for display"""
                n = len(matrix)
                lines = [f"{name} = "]
                for row in matrix:
                    line = "|" + " ".join(f"{elem:>6}" for elem in row) + "|"
                    lines.append(line)
                return "\n".join(lines)

            def update_matrix_size(choice):
                """Update the matrix size when dimension changes"""
                pygame.mixer.init()
                pygame.mixer.music.load("Select.mp3")
                pygame.mixer.music.play()
                global entries
                entries = create_matrix_entries()
                clear_entries()

            def format_as_fraction(value):
                try:
                    # Try to format as simplified fraction
                    frac = Fraction(value).limit_denominator()
                    if frac.denominator == 1:
                        return str(frac.numerator)
                    return f"{frac.numerator}/{frac.denominator}"
                except:
                    return f"{value:.4f}"

            def calculate_determinant(matrix, name=""):
                """Calculate determinant with detailed steps for any size matrix"""
                solution_text = []
                solution_text.append(f"\nCalculating determinant {name}:")
                solution_text.append(format_matrix(matrix, name))

                n = len(matrix)

                if n == 1:
                    det = matrix[0][0]
                    solution_text.append(f"\nDeterminant = {det} (1×1 matrix)")
                    return det, solution_text

                elif n == 2:
                    # Detailed 2x2 case
                    a, b = matrix[0]
                    c, d = matrix[1]

                    solution_text.append("\nPositive term:")
                    pos = a * d
                    solution_text.append(f"({a}) × ({d}) = {pos}")

                    solution_text.append("\nNegative term:")
                    neg = b * c
                    solution_text.append(f"({b}) × ({c}) = {neg}")

                    det = pos - neg
                    solution_text.append(f"\nDeterminant = {pos} - {neg} = {det}")
                    return det, solution_text

                elif n == 3:
                    # Detailed 3x3 case with Sarrus rule
                    a11, a12, a13 = matrix[0]
                    a21, a22, a23 = matrix[1]
                    a31, a32, a33 = matrix[2]

                    solution_text.append("\nPositive terms:")
                    pos1 = a11 * a22 * a33
                    solution_text.append(f"({a11}) × ({a22}) × ({a33}) = {pos1}")

                    pos2 = a12 * a23 * a31
                    solution_text.append(f"({a12}) × ({a23}) × ({a31}) = {pos2}")

                    pos3 = a13 * a21 * a32
                    solution_text.append(f"({a13}) × ({a21}) × ({a32}) = {pos3}")

                    solution_text.append("\nNegative terms:")
                    neg1 = a13 * a22 * a31
                    solution_text.append(f"({a13}) × ({a22}) × ({a31}) = {neg1}")

                    neg2 = a11 * a23 * a32
                    solution_text.append(f"({a11}) × ({a23}) × ({a32}) = {neg2}")

                    neg3 = a12 * a21 * a33
                    solution_text.append(f"({a12}) × ({a21}) × ({a33}) = {neg3}")

                    pos_sum = pos1 + pos2 + pos3
                    neg_sum = neg1 + neg2 + neg3
                    det = pos_sum - neg_sum

                    solution_text.append(f"\nPositive sum: {pos1} + {pos2} + {pos3} = {pos_sum}")
                    solution_text.append(f"Negative sum: {neg1} + {neg2} + {neg3} = {neg_sum}")
                    solution_text.append(f"\nDeterminant {name} = {pos_sum} - {neg_sum} = {det}")

                    return det, solution_text
                else:
                    # General case for n > 3 using Laplace expansion
                    solution_text.append(f"\nCalculating {n}×{n} determinant using cofactor expansion:")
                    det = 0
                    total_steps = []

                    # Expand along first row
                    for col in range(n):
                        # Calculate minor
                        minor = [row[:col] + row[col + 1:] for row in matrix[1:]]
                        minor_det, minor_steps = calculate_determinant(minor, f"Minor({1},{col + 1})")

                        # Calculate cofactor
                        sign = (-1) ** (col)
                        cofactor = sign * matrix[0][col] * minor_det
                        det += cofactor

                        # Record steps
                        step = (f"Term {col + 1}: Cofactor for a{1}{col + 1} = "
                                f"({sign}) × {matrix[0][col]} × (det of minor) = "
                                f"{sign} × {matrix[0][col]} × {minor_det} = {cofactor}")
                        total_steps.append(step)
                        total_steps.extend([f"  {s}" for s in minor_steps])

                    solution_text.append(f"\nExpansion along first row:")
                    solution_text.extend(total_steps)
                    solution_text.append(
                        f"\nSum of cofactors: {' + '.join(str(round(c, 4)) for c in [(-1) ** j * matrix[0][j] * calculate_determinant([row[:j] + row[j + 1:] for row in matrix[1:]], '')[0] for j in range(n)])}")
                    solution_text.append(f"\nDeterminant {name} = {det}")

                    return det, solution_text

            def parse_fraction(value):
                try:
                    # Try to convert directly to float first
                    return float(value)
                except ValueError:
                    # If that fails, try to parse as fraction
                    try:
                        if '/' in value:
                            numerator, denominator = value.split('/')
                            return float(numerator) / float(denominator)
                        else:
                            return float(value)
                    except:
                        raise ValueError("Invalid input - must be a number or fraction (like '1/2')")

            def solve():
                pygame.mixer.init()
                pygame.mixer.music.load("OK.mp3")
                pygame.mixer.music.play()
                try:
                    # Clear previous solution
                    solution_text.delete("1.0", "end")
                    solution_steps = []

                    n = dimension_var.get()

                    # Get coefficients and constants
                    coefficients = []
                    constants = []

                    for i in range(n):
                        row_coeffs = []
                        for j in range(n):
                            # Use parse_fraction instead of float directly
                            value = parse_fraction(entries[i][j].get())
                            row_coeffs.append(value)
                        coefficients.append(row_coeffs)
                        # Also parse the constant term as fraction
                        constants.append(parse_fraction(entries[i][n].get()))

                    # Initial system display with proper signs
                    solution_steps.append("System of equations:")
                    for i in range(n):
                        eq_parts = []
                        for j in range(n):
                            coeff = coefficients[i][j]
                            var_name = f"X{j + 1}"  # Changed from chr(120 + j) to X1, X2, etc.
                            if j == 0:
                                eq_parts.append(f"{coeff}{var_name}")
                            else:
                                eq_parts.append(f"{'+ ' if coeff >= 0 else '- '}{abs(coeff)}{var_name}")
                        eq = " ".join(eq_parts) + f" = {constants[i]}"
                        solution_steps.append(eq)

                    # Calculate main determinant D
                    D, d_steps = calculate_determinant(coefficients, "D")
                    solution_steps.extend(d_steps)

                    if abs(D) < 1e-10:
                        solution_steps.append("\nThe system has no unique solution (determinant is zero)")
                        solution_text.insert("1.0", "\n".join(solution_steps))
                        return

                    # Calculate determinants for each variable
                    solutions = {}
                    for i in range(n):
                        var = f"X{i + 1}"  # Changed from chr(120 + i) to X1, X2, etc.
                        # Create matrix for current variable
                        new_matrix = [row[:] for row in coefficients]
                        for j in range(n):
                            new_matrix[j][i] = constants[j]

                        D_var, d_var_steps = calculate_determinant(new_matrix, f"D{var}")
                        solution_steps.extend(d_var_steps)

                        # Calculate and store solution
                        solution = D_var / D
                        solutions[var] = solution
                        solution_steps.append(f"\n{var} = D{var}/D = {D_var}/{D} = {solution:.4f}")

                    # Final solution summary
                    solution_steps.append("\nFinal Solution:")
                    for var in sorted(solutions.keys()):
                        # Use format_as_fraction to display results
                        frac_solution = format_as_fraction(solutions[var])
                        solution_steps.append(f"   {var} = D{var}/D = {frac_solution} (≈{solutions[var]:.4f})")

                    # Display complete solution
                    solution_text.insert("1.0", "\n".join(solution_steps))

                    equations = []
                    for i in range(n):
                        equation = " + ".join(
                            [f"{entries[i][j].get()}X{j + 1}" for j in range(n)]) + f" = {entries[i][n].get()}"
                        equations.append(equation)

                    solution_text_value = solution_text.get("1.0", "end")
                    save_to_db('cramers_b', '\n'.join(equations), solution_text_value)

                except ValueError:
                    solution_text.delete("1.0", "end")
                    solution_text.insert("1.0", "Please enter valid numbers in all fields")

            def clear_entries():
                pygame.mixer.init()
                pygame.mixer.music.load("Select.mp3")  # or .wav
                pygame.mixer.music.play()

                # ung mag bubura sa mga entries
                for row in entries:
                    for entry in row:
                        entry.delete(0, "end")

                solution_text.delete("1.0", "end")

            def back_button3():
                pygame.mixer.init()
                pygame.mixer.music.load("Back Sound.mp3")  # or .wav
                pygame.mixer.music.play()
                method_cram_B.withdraw()
                choose_method_cram.deiconify()

            def history_button_cram_B():
                method_cram_B.withdraw()
                pygame.mixer.init()
                pygame.mixer.music.load("Back Sound.mp3")  # or .wav
                pygame.mixer.music.play()

                ctk.set_appearance_mode("dark")
                ctk.set_default_color_theme("blue")
                history_cramers = ctk.CTkToplevel()
                history_cramers.title("Cramer's Method B History")
                history_cramers.state('zoomed')
                history_cramers.grid_rowconfigure(0, weight=1)
                history_cramers.grid_columnconfigure(0, weight=1)
                history_cramers.resizable(True, True)
                pygame.mixer.init()

                def back_button6():
                    pygame.mixer.init()
                    pygame.mixer.music.load("Back Sound.mp3")  # or .wav
                    pygame.mixer.music.play()
                    history_cramers.withdraw()
                    method_cram_B.deiconify()

                def clear_cramers_B_history():
                    pygame.mixer.music.load("Select.mp3")  # or .wav
                    pygame.mixer.music.play()
                    clear_history('cramers_b')
                    solution_text.delete("1.0", "end")

                bg_img = ctk.CTkImage(light_image=Image.open("history.png"), size=(1920, 1030))
                bg_lbl = ctk.CTkLabel(history_cramers, image=bg_img, text="")
                bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

                solu_frame = ctk.CTkFrame(history_cramers, fg_color=("white", "gray20"))
                solu_frame.place(x=620, y=130)
                solution_frame = ctk.CTkFrame(solu_frame, width=690, height=490)
                solution_frame.pack(pady=10, padx=10)
                solution_text = ctk.CTkTextbox(solution_frame, height=490, width=690, font=("Arial", 25, "bold"))
                solution_text.pack(pady=10, padx=10)

                solution_text.insert("end", "Cramer's Method B History:\n\n")
                history = get_history('cramers_b')

                for entry in history:
                    solution_text.insert("end", f"ID: {entry['id']}\n")
                    solution_text.insert("end", f"Date: {entry['timestamp']}\n")
                    solution_text.insert("end", "Equations:\n")
                    solution_text.insert("end", f"{entry['equations']}\n")
                    solution_text.insert("end", "\nSolution:\n")
                    solution_text.insert("end", f"{entry['solution']}\n")
                    solution_text.insert("end", "=" * 50 + "\n")

                back_btn_img = Image.open("Back.png").resize((500, 150))
                back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
                back_button_6 = ctk.CTkButton(history_cramers, image=back_iconBack, corner_radius=0, text="",
                                              fg_color="#000000",
                                              command=back_button6,
                                              hover_color="#ffffff")
                back_button_6.place(x=50, y=900)

                clear_history_img = Image.open("Clear Button.png").resize((500, 150))
                iconClearHistory = ctk.CTkImage(clear_history_img, size=(180, 70))

                # History Button with image
                clear_history_btn = ctk.CTkButton(history_cramers, image=iconClearHistory,
                                                  text="", corner_radius=0, fg_color="#000000",
                                                  hover_color="#ffffff", command=clear_cramers_B_history)
                clear_history_btn.place(x=230, y=900)

                history_cramers.mainloop()

            bg_img = ctk.CTkImage(light_image=Image.open("BGG.png"), size=(1920, 1080))
            bg_lbl = ctk.CTkLabel(method_cram_B, image=bg_img, text="")
            bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

            main_frame = ctk.CTkFrame(method_cram_B, fg_color=("#f0f9ff"), corner_radius=0)
            main_frame.place(x=155, y=205)

            # Dimension selector
            dimension_label = ctk.CTkLabel(
                method_cram_B,
                text="Matrix Dimension:",
                font=("Press Start 2P", 25),
                fg_color="#f0f9ff",
                text_color="#000000"
            )
            dimension_label.place(x=200, y=160)

            dimension_var = ctk.IntVar(value=3)
            dimension_selector = ctk.CTkOptionMenu(
                method_cram_B,
                values=["2", "3", "4", "5", "6"],
                variable=dimension_var,
                font=("Press Start 2P", 20),
                command=update_matrix_size,
                width=170,
                height=50,
                dropdown_font=("Press Start 2P", 20)
            )
            dimension_selector.place(x=650, y=150)

            # Input frame and canvas setup
            input_frame = ctk.CTkFrame(main_frame, fg_color="#f0f9ff", width=900, height=320)
            input_frame.pack(pady=20)

            input_canvas = ctk.CTkCanvas(input_frame, width=650, height=320)
            input_canvas.pack(side="left", fill="both", expand=True)

            # Scrollbars and inner frame
            v_scroll = ctk.CTkScrollbar(input_frame, orientation="vertical", command=input_canvas.yview)
            v_scroll.pack(side="right", fill="y")
            h_scroll = ctk.CTkScrollbar(main_frame, orientation="horizontal", command=input_canvas.xview)
            h_scroll.pack(side="bottom", fill="x")

            input_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            input_inner_frame = ctk.CTkFrame(input_canvas, fg_color="#f0f9ff")
            input_canvas.create_window((0, 0), window=input_inner_frame, anchor="nw")

            # Initial entries
            variable_labels = []
            entries = create_matrix_entries()

            # Solution frame
            s_frame = ctk.CTkFrame(method_cram_B, fg_color=("white", "gray20"))
            s_frame.place(x=1040, y=90)
            solution_frame = ctk.CTkFrame(s_frame, width=700, height=500)
            solution_frame.pack(pady=10, padx=10)
            solution_text = ctk.CTkTextbox(solution_frame, height=500, width=700, font=("Arial", 25, "bold"))
            solution_text.pack(pady=10, padx=10)

            # Buttons
            solve_btn = ctk.CTkButton(method_cram_B, text="SOLVE", font=("Press Start 2P", 25, "bold"),
                                      command=solve, height=76, width=154, fg_color="#0054a7")
            solve_btn.place(x=690, y=664)

            clear_btn = ctk.CTkButton(method_cram_B, text="CLEAR", font=("Press Start 2P", 25, "bold"),
                                      command=clear_entries, height=76, width=180, fg_color="#0054a7")
            clear_btn.place(x=480, y=664)

            # History button
            history_img = Image.open("History button.png").resize((500, 150))
            iconHistory = ctk.CTkImage(history_img, size=(180, 70))
            history_btn = ctk.CTkButton(method_cram_B, image=iconHistory,
                                        text="", corner_radius=0, fg_color="#000000",
                                        hover_color="#ffffff", command=history_button_cram_B)
            history_btn.place(x=230, y=900)

            # Back button
            back_btn_img = Image.open("Back.png").resize((500, 150))
            back_icon = ctk.CTkImage(back_btn_img, size=(150, 70))
            back_btn = ctk.CTkButton(method_cram_B, image=back_icon, text="",
                                     corner_radius=0, fg_color="#000000",
                                     hover_color="#ffffff", command=back_button3)
            back_btn.place(x=50, y=900)

            method_cram_B.mainloop()

        def open_method_a():
            nonlocal selected_cram_method
            pygame.mixer.music.load("Select.mp3")
            pygame.mixer.music.play()
            arrow_image_labelB.place_forget()

            arrow_img = Image.open("ARROW.png")
            arrow_tk = ctk.CTkImage(light_image=arrow_img, size=(50, 100))
            arrow_image_label.configure(image=arrow_tk)
            arrow_image_label.place(x=630, y=290)
            selected_cram_method = 'method_a'

        def open_method_b():
            nonlocal selected_cram_method
            pygame.mixer.music.load("Select.mp3")
            pygame.mixer.music.play()
            arrow_image_label.place_forget()

            arrow_img = Image.open("ARROW.png")
            arrow_tk = ctk.CTkImage(light_image=arrow_img, size=(50, 100))
            arrow_image_labelB.configure(image=arrow_tk)
            arrow_image_labelB.place(x=630, y=420)
            selected_cram_method = 'method_b'

        def start_solver():
            pygame.mixer.music.load("OK.mp3")
            pygame.mixer.music.play()

            if selected_cram_method == "method_a":
                open_cram_method_A()
            elif selected_cram_method == "method_b":
                open_cram_method_B()
            else:
                pass

        def back_button1():
            pygame.mixer.music.load("Back Sound.mp3")
            pygame.mixer.music.play()
            choose_method_cram.withdraw()
            root.deiconify()

        method_A_img = Image.open("Method A .png").resize((1920, 457))
        method_A_icon = ctk.CTkImage(method_A_img, size=(550, 110))

        arrow_image_label = ctk.CTkLabel(choose_method_cram, text='.', font=("Press Start 2P", .1,), fg_color="#50d5ff",
                                         text_color="#50d5ff")
        arrow_image_label.place(x=630, y=290)

        method_A_btn = ctk.CTkButton(choose_method_cram, text="", image=method_A_icon, corner_radius=0,
                                     fg_color="#50d5ff", hover_color="#ffffff", command=open_method_a)
        method_A_btn.place(x=690, y=280)

        method_B_img = Image.open("Method B.png").resize((1920, 457))
        method_B_icon = ctk.CTkImage(method_B_img, size=(550, 110))

        arrow_image_labelB = ctk.CTkLabel(choose_method_cram, text='.', font=("Press Start 2P", .1,),
                                          fg_color="#50d5ff", text_color="#50d5ff")
        arrow_image_labelB.place(x=630, y=420)

        method_B_btn = ctk.CTkButton(choose_method_cram, text="", image=method_B_icon, corner_radius=0,
                                     fg_color="#50d5ff", hover_color="#ffffff", command=open_method_b)
        method_B_btn.place(x=690, y=410)

        start_btn = ctk.CTkButton(choose_method_cram, text=" START", font=("Retropix", 70, "bold"), width=180,
                                  height=50,
                                  corner_radius=0, fg_color="#e63101", hover_color="#8e1e00", command=start_solver)
        start_btn.place(x=860, y=570)

        back_btn_img = Image.open("Back.png").resize((500, 150))
        back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
        back_button_1 = ctk.CTkButton(choose_method_cram, image=back_iconBack, corner_radius=0, text="",
                                      fg_color="#000000",
                                      command=back_button1,
                                      hover_color="#ffffff")
        back_button_1.place(x=50, y=900)

        choose_method_cram.mainloop()

    def open_gauss_method_window():
        root.withdraw()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        choose_gauss_elimination = ctk.CTkToplevel()
        choose_gauss_elimination.title("Gauss-Jordan Elimination")
        choose_gauss_elimination.state('zoomed')
        choose_gauss_elimination.grid_rowconfigure(0, weight=1)
        choose_gauss_elimination.grid_columnconfigure(0, weight=1)
        choose_gauss_elimination.resizable(True, True)
        pygame.mixer.init()
        selected_gauss_method = None

        def open_gauss_method_elim():
            choose_gauss_elimination.withdraw()
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            gauss_method_elimination = ctk.CTkToplevel()
            gauss_method_elimination.title("Gaussian Elimination Solver")
            gauss_method_elimination.state('zoomed')
            gauss_method_elimination.grid_rowconfigure(0, weight=1)
            gauss_method_elimination.grid_columnconfigure(0, weight=1)
            gauss_method_elimination.resizable(True, True)
            pygame.mixer.init()

            entries = []
            variable_labels = []
            input_inner_frame = None
            input_canvas = None
            solution_text = None
            dimension_var = None

            def create_matrix_entries():
                """Create entry widgets based on current dimension"""
                nonlocal entries, variable_labels, input_inner_frame, input_canvas, dimension_var

                n = dimension_var.get()

                # Clear existing widgets from inner frame
                for widget in input_inner_frame.winfo_children():
                    widget.destroy()

                # Clear existing variable labels
                for label in variable_labels:
                    label.destroy()
                variable_labels = []

                # Create a header frame for variable labels
                header_frame = ctk.CTkFrame(input_inner_frame, fg_color="#f0f9ff", corner_radius=0)
                header_frame.grid(row=0, column=0, columnspan=(n * 2) + 1, sticky="ew")

                # Create new variable labels in the header frame
                variables = [f"X{i + 1}" for i in range(n)] + ['  D']
                for i, var in enumerate(variables):
                    label = ctk.CTkLabel(
                        header_frame,
                        text=var,
                        text_color="#ffcf00",
                        fg_color="#f0f9ff",
                        font=("Press Start 2P", 30, "bold"),
                        width=90,
                        anchor="center"
                    )
                    if i < n:
                        label.grid(row=0, column=i * 2, padx=35, pady=(0, 10))
                    else:
                        label.grid(row=0, column=n * 2, padx=35, pady=(0, 10))
                    variable_labels.append(label)

                # Create entry fields in the inner frame below header
                entries = []
                for i in range(n):
                    row = []
                    for j in range(n + 1):  # n coefficients + 1 constant
                        entry = ctk.CTkEntry(
                            input_inner_frame,
                            width=90,
                            height=70,
                            fg_color="#e63101",
                            border_color="#f64d20",
                            text_color="white",
                            justify="center",
                            font=("Press Start 2P", 20, "bold")
                        )
                        entry.grid(row=i + 1, column=j * 2, padx=35, pady=15)

                        # Add = sign before constant term
                        if j == n - 1:
                            equals = ctk.CTkLabel(
                                input_inner_frame,
                                text="=",
                                text_color="#000000",
                                font=("Press Start 2P", 35, "bold")
                            )
                            equals.grid(row=i + 1, column=j * 2 + 1, padx=5)

                        row.append(entry)
                    entries.append(row)

                # Update scroll region after adding widgets
                input_inner_frame.update_idletasks()
                input_canvas.configure(scrollregion=input_canvas.bbox("all"), bg="#f0f9ff")

            def update_matrix_size(choice):
                """Update the matrix size when dimension changes"""
                pygame.mixer.init()
                pygame.mixer.music.load("Select.mp3")
                pygame.mixer.music.play()
                create_matrix_entries()
                clear_entries()

            def format_matrix(matrix):
                return "\n".join([
                    "| " + " ".join(f"{format_fraction(val):>8}" for val in row[:-1]) +
                    f" | {format_fraction(row[-1]):>8} |"
                    for row in matrix
                ]) + "\n"

            def parse_fraction(value):
                try:
                    # Try to convert directly to float first
                    return float(value)
                except ValueError:
                    # If that fails, try to parse as fraction
                    try:
                        if '/' in value:
                            numerator, denominator = value.split('/')
                            return float(numerator) / float(denominator)
                        else:
                            return float(value)
                    except:
                        raise ValueError("Invalid input - must be a number or fraction (like '1/2')")

            def format_fraction(value):
                try:
                    # Try to format as simplified fraction
                    frac = Fraction(value).limit_denominator()
                    if frac.denominator == 1:
                        return str(frac.numerator)
                    return f"{frac.numerator}/{frac.denominator}"
                except:
                    return f"{value:.4f}"

            def forward_elimination(matrix, steps):
                n = len(matrix)
                for i in range(n):
                    max_row = max(range(i, n), key=lambda r: abs(matrix[r][i]))
                    if max_row != i:
                        steps.append(f"Swap row {i + 1} with row {max_row + 1}")
                        matrix[i], matrix[max_row] = matrix[max_row], matrix[i]
                        steps.append(format_matrix(matrix))

                    pivot = matrix[i][i]
                    if pivot == 0:
                        raise ValueError("Matrix is singular")

                    if pivot != 1:
                        steps.append(f"Row {i + 1} ÷ {format_fraction(pivot)}")
                        matrix[i] = [val / pivot for val in matrix[i]]
                        steps.append(format_matrix(matrix))

                    for r in range(i + 1, n):
                        factor = matrix[r][i]
                        if factor != 0:
                            steps.append(f"Row {r + 1} - ({format_fraction(factor)})×Row {i + 1}")
                            matrix[r] = [val - factor * matrix[i][c] for c, val in enumerate(matrix[r])]
                            steps.append(format_matrix(matrix))
                return matrix

            def back_substitution(matrix):
                n = len(matrix)
                solutions = [0] * n
                steps = []

                for i in reversed(range(n)):
                    sum_terms = matrix[i][-1]
                    equation = f"X{i + 1} = {format_fraction(sum_terms)}"

                    for j in range(i + 1, n):
                        term = matrix[i][j] * solutions[j]
                        sum_terms -= term
                        equation += f" - {format_fraction(matrix[i][j])}×{format_fraction(solutions[j])}"

                    solutions[i] = sum_terms
                    equation += f" = {format_fraction(sum_terms)}"
                    steps.append(f"From row {i + 1}: {equation}")

                return solutions, steps

            def solve():
                pygame.mixer.music.load("OK.mp3")
                pygame.mixer.music.play()
                solution_text.delete("1.0", "end")
                try:
                    steps = []
                    n = dimension_var.get()  # Get current matrix dimension
                    matrix = []
                    for i in range(n):
                        row = []
                        for j in range(n + 1):  # n coefficients + 1 constant
                            entry = entries[i][j]
                            val = entry.get()
                            row.append(parse_fraction(val))
                        matrix.append(row)

                    # Save equations to database
                    equations = []
                    for row in entries:
                        equation = " + ".join(
                            [f"{entry.get()}X{i + 1}" for i, entry in enumerate(row[:-1])]) + f" = {row[-1].get()}"
                        equations.append(equation)

                    # Gaussian Elimination
                    steps.append("=== GAUSSIAN ELIMINATION ===")
                    ge_matrix = [row.copy() for row in matrix]
                    steps.append("\nInitial Matrix:\n" + format_matrix(ge_matrix))
                    forward_elimination(ge_matrix, steps)
                    steps.append("\nUpper Triangular Matrix:\n" + format_matrix(ge_matrix))

                    ge_solution, back_steps = back_substitution(ge_matrix)
                    steps.append("\nBack Substitution Steps:")
                    steps.extend(back_steps)
                    steps.append("\nSolution:")
                    # Dynamically generate solution strings
                    solution_steps = [f"X{i + 1} = {format_fraction(val)}" for i, val in enumerate(ge_solution)]
                    steps.extend(solution_steps)
                    solution_text.insert("1.0", "\n".join(steps))

                    # Save to database
                    solution_text_value = solution_text.get("1.0", "end")
                    save_to_db('gauss_elimination', '\n'.join(equations), solution_text_value)

                except Exception as e:
                    solution_text.insert("1.0", f"Error: {str(e)}")

            def clear_entries():
                pygame.mixer.init()
                pygame.mixer.music.load("Select.mp3")  # or .wav
                pygame.mixer.music.play()

                # Clear all entries
                for row in entries:
                    for entry in row:
                        entry.delete(0, "end")

                solution_text.delete("1.0", "end")

            def back_button4():
                pygame.mixer.init()
                pygame.mixer.music.load("Back Sound.mp3")  # or .wav
                pygame.mixer.music.play()
                gauss_method_elimination.withdraw()
                choose_gauss_elimination.deiconify()

            def history_button_gauss_elim():
                gauss_method_elimination.withdraw()
                pygame.mixer.init()
                pygame.mixer.music.load("Back Sound.mp3")  # or .wav
                pygame.mixer.music.play()

                ctk.set_appearance_mode("dark")
                ctk.set_default_color_theme("blue")
                history_cramers = ctk.CTkToplevel()
                history_cramers.title("Gaussian Elimination History")
                history_cramers.state('zoomed')
                history_cramers.grid_rowconfigure(0, weight=1)
                history_cramers.grid_columnconfigure(0, weight=1)
                history_cramers.resizable(True, True)
                pygame.mixer.init()

                def back_button6():
                    pygame.mixer.init()
                    pygame.mixer.music.load("Back Sound.mp3")  # or .wav
                    pygame.mixer.music.play()
                    history_cramers.withdraw()
                    gauss_method_elimination.deiconify()

                def clear_gauss_elimination_history():
                    pygame.mixer.music.load("Select.mp3")  # or .wav
                    pygame.mixer.music.play()
                    clear_history('gauss_elimination')
                    solution_text.delete("1.0", "end")

                bg_img = ctk.CTkImage(light_image=Image.open("history.png"), size=(1920, 1030))
                bg_lbl = ctk.CTkLabel(history_cramers, image=bg_img, text="")
                bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

                solu_frame = ctk.CTkFrame(history_cramers, fg_color=("white", "gray20"))
                solu_frame.place(x=620, y=130)
                solution_frame = ctk.CTkFrame(solu_frame, width=690, height=490)
                solution_frame.pack(pady=10, padx=10)
                solution_text = ctk.CTkTextbox(solution_frame, height=490, width=690, font=("Arial", 25, "bold"))
                solution_text.pack(pady=10, padx=10)

                solution_text.insert("end", "Gaussian Elimination History:\n\n")
                history = get_history('gauss_elimination')

                for entry in history:
                    solution_text.insert("end", f"ID: {entry['id']}\n")
                    solution_text.insert("end", f"Date: {entry['timestamp']}\n")
                    solution_text.insert("end", "Equations:\n")
                    solution_text.insert("end", f"{entry['equations']}\n")
                    solution_text.insert("end", "\nSolution:\n")
                    solution_text.insert("end", f"{entry['solution']}\n")
                    solution_text.insert("end", "=" * 50 + "\n")

                back_btn_img = Image.open("Back.png").resize((500, 150))
                back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
                back_button_6 = ctk.CTkButton(history_cramers, image=back_iconBack, corner_radius=0, text="",
                                              fg_color="#000000",
                                              command=back_button6,
                                              hover_color="#ffffff")
                back_button_6.place(x=50, y=900)

                clear_history_img = Image.open("Clear Button.png").resize((500, 150))
                iconClearHistory = ctk.CTkImage(clear_history_img, size=(180, 70))

                # History Button with image
                clear_history_btn = ctk.CTkButton(history_cramers, image=iconClearHistory,
                                                  text="", corner_radius=0, fg_color="#000000",
                                                  hover_color="#ffffff", command=clear_gauss_elimination_history)
                clear_history_btn.place(x=230, y=900)

                history_cramers.mainloop()

            bg_img = ctk.CTkImage(light_image=Image.open("gauss elim.png"), size=(1920, 1080))
            bg_lbl = ctk.CTkLabel(gauss_method_elimination, image=bg_img, text="")
            bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

            main_frame = ctk.CTkFrame(gauss_method_elimination, fg_color=("#f0f9ff"), corner_radius=0)
            main_frame.place(x=155, y=205)

            solu_frame = ctk.CTkFrame(gauss_method_elimination, fg_color=("white", "gray20"))
            solu_frame.place(x=1040, y=90)

            dimension_label = ctk.CTkLabel(gauss_method_elimination, text="Matrix Dimension:",
                                           font=("Press Start 2P", 25), fg_color="#f0f9ff", text_color="#000000")
            dimension_label.place(x=200, y=160)

            dimension_var = ctk.IntVar(value=3)
            dimension_selector = ctk.CTkOptionMenu(gauss_method_elimination, values=["2", "3", "4", "5", "6"],
                                                   variable=dimension_var, font=("Press Start 2P", 20),
                                                   command=update_matrix_size, width=170,
                                                   height=50, dropdown_font=("Press Start 2P", 20), fg_color="#e63101",
                                                   dropdown_fg_color="#be2903",
                                                   button_color="#e63101", dropdown_hover_color="#e63101",
                                                   button_hover_color="#be2903")
            dimension_selector.place(x=650, y=150)

            input_frame = ctk.CTkFrame(main_frame, fg_color="#f0f9ff", width=900, height=320)
            input_frame.pack(pady=20)

            input_canvas = ctk.CTkCanvas(input_frame, width=650, height=320)
            input_canvas.pack(side="left", fill="both", expand=True)

            v_scroll = ctk.CTkScrollbar(input_frame, orientation="vertical", command=input_canvas.yview)
            v_scroll.pack(side="right", fill="y")
            h_scroll = ctk.CTkScrollbar(main_frame, orientation="horizontal", command=input_canvas.xview)
            h_scroll.pack(side="bottom", fill="x")

            input_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            input_canvas.bind('<Configure>',
                              lambda e: input_canvas.configure(scrollregion=input_canvas.bbox("all")))

            input_inner_frame = ctk.CTkFrame(input_canvas, fg_color="#f0f9ff")
            input_canvas.create_window((0, 0), window=input_inner_frame, anchor="nw")

            create_matrix_entries()

            solution_frame = ctk.CTkFrame(solu_frame, width=700, height=500)
            solution_frame.pack(pady=10, padx=10)

            solution_text = ctk.CTkTextbox(solution_frame, height=500, width=700, font=("Arial", 25, "bold"))
            solution_text.pack(pady=10, padx=10)

            solve_btn = ctk.CTkButton(gauss_method_elimination, text="SOLVE", font=("Press Start 2P", 25, "bold"),
                                      hover_color="#e63101", command=solve,
                                      height=76, width=154, corner_radius=0, fg_color="#be2903")
            solve_btn.place(x=690, y=664)
            clear_btn = ctk.CTkButton(gauss_method_elimination, text="CLEAR", font=("Press Start 2P", 25, "bold"),
                                      hover_color="#e63101",
                                      command=clear_entries, height=76, width=180, corner_radius=0,
                                      fg_color="#be2903")
            clear_btn.place(x=480, y=664)

            history_img = Image.open("History button.png").resize((500, 150))
            iconHistory = ctk.CTkImage(history_img, size=(180, 70))
            history_btn = ctk.CTkButton(gauss_method_elimination, image=iconHistory,
                                        text="", corner_radius=0, fg_color="#000000",
                                        hover_color="#ffffff", command=history_button_gauss_elim)
            history_btn.place(x=230, y=900)

            back_btn_img = Image.open("Back.png").resize((500, 150))
            back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
            back_button_4 = ctk.CTkButton(gauss_method_elimination, image=back_iconBack, corner_radius=0, text="",
                                          fg_color="#000000",
                                          command=back_button4,
                                          hover_color="#ffffff")
            back_button_4.place(x=50, y=900)

            gauss_method_elimination.mainloop()

        def open_gauss_method_jordan():
            choose_gauss_elimination.withdraw()
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            gauss_method_jordan = ctk.CTkToplevel()
            gauss_method_jordan.title("Gauss-Jordan Elimination Solver")
            gauss_method_jordan.state('zoomed')
            gauss_method_jordan.grid_rowconfigure(0, weight=1)
            gauss_method_jordan.grid_columnconfigure(0, weight=1)
            gauss_method_jordan.resizable(True, True)
            pygame.mixer.init()

            entries = []
            variable_labels = []
            input_inner_frame = None
            input_canvas = None
            solution_text = None
            dimension_var = None

            def create_matrix_entries():
                nonlocal entries, variable_labels, input_inner_frame, input_canvas, dimension_var

                n = dimension_var.get()
                for widget in input_inner_frame.winfo_children():
                    widget.destroy()

                for label in variable_labels:
                    label.destroy()
                variable_labels = []

                header_frame = ctk.CTkFrame(input_inner_frame, fg_color="#f0f9ff", corner_radius=0)
                header_frame.grid(row=0, column=0, columnspan=(n * 2) + 1, sticky="ew")

                variables = [f"X{i + 1}" for i in range(n)] + ['  D']
                for i, var in enumerate(variables):
                    label = ctk.CTkLabel(
                        header_frame,
                        text=var,
                        text_color="#ffcf00",
                        fg_color="#f0f9ff",
                        font=("Press Start 2P", 30, "bold"),
                        width=90,
                        anchor="center"
                    )
                    if i < n:
                        label.grid(row=0, column=i * 2, padx=35, pady=(0, 10))
                    else:
                        label.grid(row=0, column=n * 2, padx=35, pady=(0, 10))
                    variable_labels.append(label)

                entries = []
                for i in range(n):
                    row = []
                    for j in range(n + 1):
                        entry = ctk.CTkEntry(
                            input_inner_frame,
                            width=90,
                            height=70,
                            fg_color="#e63101",
                            border_color="#f64d20",
                            text_color="white",
                            justify="center",
                            font=("Press Start 2P", 20, "bold")
                        )
                        entry.grid(row=i + 1, column=j * 2, padx=35, pady=15)

                        if j == n - 1:
                            equals = ctk.CTkLabel(
                                input_inner_frame,
                                text="=",
                                text_color="#000000",
                                font=("Press Start 2P", 35, "bold")
                            )
                            equals.grid(row=i + 1, column=j * 2 + 1, padx=5)

                        row.append(entry)
                    entries.append(row)

                input_inner_frame.update_idletasks()
                input_canvas.configure(scrollregion=input_canvas.bbox("all"), bg="#f0f9ff")

            def update_matrix_size(choice):
                pygame.mixer.music.load("Select.mp3")
                pygame.mixer.music.play()
                create_matrix_entries()
                clear_entries()

            def parse_fraction(value):
                try:
                    return float(value)
                except ValueError:
                    if '/' in value:
                        numerator, denominator = value.split('/')
                        return float(numerator) / float(denominator)
                    raise ValueError("Invalid input")

            def format_fraction(value):
                try:
                    frac = Fraction(value).limit_denominator()
                    return f"{frac.numerator}/{frac.denominator}" if frac.denominator != 1 else f"{frac.numerator}"
                except:
                    return f"{value:.4f}"

            def format_matrix(matrix):
                return "\n".join([
                    "| " + " ".join(f"{format_fraction(val):>8}" for val in row[:-1]) +
                    f" | {format_fraction(row[-1]):>8} |"
                    for row in matrix
                ]) + "\n"

            def gauss_jordan(matrix, steps):
                n = len(matrix)
                for i in range(n):
                    max_row = max(range(i, n), key=lambda r: abs(matrix[r][i]))
                    if max_row != i:
                        steps.append(f"Swap row {i + 1} with row {max_row + 1}")
                        matrix[i], matrix[max_row] = matrix[max_row], matrix[i]
                        steps.append(format_matrix(matrix))

                    pivot = matrix[i][i]
                    if pivot == 0:
                        raise ValueError("Matrix is singular")

                    if pivot != 1:
                        steps.append(f"Row {i + 1} ÷ {format_fraction(pivot)}")
                        matrix[i] = [val / pivot for val in matrix[i]]
                        steps.append(format_matrix(matrix))

                    for r in range(n):
                        if r != i:
                            factor = matrix[r][i]
                            if factor != 0:
                                steps.append(f"Row {r + 1} - ({format_fraction(factor)})×Row {i + 1}")
                                matrix[r] = [val - factor * matrix[i][c] for c, val in enumerate(matrix[r])]
                                steps.append(format_matrix(matrix))
                return matrix

            def solve():
                pygame.mixer.music.load("OK.mp3")
                pygame.mixer.music.play()
                solution_text.delete("1.0", "end")
                try:
                    steps = []
                    n = dimension_var.get()
                    matrix = []
                    for i in range(n):
                        row = []
                        for j in range(n + 1):
                            entry = entries[i][j]
                            val = parse_fraction(entry.get())
                            row.append(val)
                        matrix.append(row)

                    steps.append("=== GAUSS-JORDAN ELIMINATION ===")
                    gj_matrix = [row.copy() for row in matrix]
                    steps.append("\nInitial Matrix:\n" + format_matrix(gj_matrix))
                    gj_steps = []
                    gauss_jordan(gj_matrix, gj_steps)
                    steps.extend(gj_steps)

                    steps.append("\nReduced Row Echelon Form:\n" + format_matrix(gj_matrix))
                    steps.append("\nDirect Solution:")
                    steps.extend([f"X{i + 1} = {format_fraction(gj_matrix[i][-1])}" for i in range(n)])

                    solution_text.insert("1.0", "\n".join(steps))

                    equations = []
                    for row in entries:
                        equation = " + ".join(
                            [f"{entry.get()}X{i + 1}" for i, entry in enumerate(row[:-1])]) + f" = {row[-1].get()}"
                        equations.append(equation)
                    save_to_db('gauss_jordans', '\n'.join(equations), solution_text.get("1.0", "end"))

                except Exception as e:
                    solution_text.insert("1.0", f"Error: {str(e)}")

            def clear_entries():
                for row in entries:
                    for entry in row:
                        entry.delete(0, "end")
                solution_text.delete("1.0", "end")

            def back_button4():
                pygame.mixer.music.load("Back Sound.mp3")
                pygame.mixer.music.play()
                gauss_method_jordan.withdraw()
                choose_gauss_elimination.deiconify()

            def history_button_gauss_jord():
                gauss_method_jordan.withdraw()
                pygame.mixer.init()
                pygame.mixer.music.load("Back Sound.mp3")  # or .wav
                pygame.mixer.music.play()

                ctk.set_appearance_mode("dark")
                ctk.set_default_color_theme("blue")
                history_cramers = ctk.CTkToplevel()
                history_cramers.title("Gauss Jordan History")
                history_cramers.state('zoomed')
                history_cramers.grid_rowconfigure(0, weight=1)
                history_cramers.grid_columnconfigure(0, weight=1)
                history_cramers.resizable(True, True)
                pygame.mixer.init()

                def back_button6():
                    pygame.mixer.init()
                    pygame.mixer.music.load("Back Sound.mp3")  # or .wav
                    pygame.mixer.music.play()
                    history_cramers.withdraw()
                    gauss_method_jordan.deiconify()

                def clear_gauss_elimination_history():
                    pygame.mixer.music.load("Select.mp3")  # or .wav
                    pygame.mixer.music.play()
                    clear_history('gauss_jordans')
                    solution_text.delete("1.0", "end")

                bg_img = ctk.CTkImage(light_image=Image.open("history.png"), size=(1920, 1030))
                bg_lbl = ctk.CTkLabel(history_cramers, image=bg_img, text="")
                bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

                solu_frame = ctk.CTkFrame(history_cramers, fg_color=("white", "gray20"))
                solu_frame.place(x=620, y=130)
                solution_frame = ctk.CTkFrame(solu_frame, width=690, height=490)
                solution_frame.pack(pady=10, padx=10)
                solution_text = ctk.CTkTextbox(solution_frame, height=490, width=690, font=("Arial", 25, "bold"))
                solution_text.pack(pady=10, padx=10)

                solution_text.insert("end", "GAUSS JORDAN METHOD History:\n\n")
                history = get_history('gauss_jordans')

                for entry in history:
                    solution_text.insert("end", f"ID: {entry['id']}\n")
                    solution_text.insert("end", f"Date: {entry['timestamp']}\n")
                    solution_text.insert("end", "Equations:\n")
                    solution_text.insert("end", f"{entry['equations']}\n")
                    solution_text.insert("end", "\nSolution:\n")
                    solution_text.insert("end", f"{entry['solution']}\n")
                    solution_text.insert("end", "=" * 50 + "\n")

                back_btn_img = Image.open("Back.png").resize((500, 150))
                back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
                back_button_6 = ctk.CTkButton(history_cramers, image=back_iconBack, corner_radius=0, text="",
                                              fg_color="#000000",
                                              command=back_button6,
                                              hover_color="#ffffff")
                back_button_6.place(x=50, y=900)

                clear_history_img = Image.open("Clear Button.png").resize((500, 150))
                iconClearHistory = ctk.CTkImage(clear_history_img, size=(180, 70))

                # History Button with image
                clear_history_btn = ctk.CTkButton(history_cramers, image=iconClearHistory,
                                                  text="", corner_radius=0, fg_color="#000000",
                                                  hover_color="#ffffff", command=clear_gauss_elimination_history)
                clear_history_btn.place(x=230, y=900)

                history_cramers.mainloop()

            bg_img = ctk.CTkImage(light_image=Image.open("gauss elim.png"), size=(1920, 1080))
            bg_lbl = ctk.CTkLabel(gauss_method_jordan, image=bg_img, text="")
            bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

            main_frame = ctk.CTkFrame(gauss_method_jordan, fg_color=("#f0f9ff"), corner_radius=0)
            main_frame.place(x=155, y=205)

            dimension_label = ctk.CTkLabel(gauss_method_jordan, text="Matrix Dimension:",
                                           font=("Press Start 2P", 25), fg_color="#f0f9ff", text_color="#000000")
            dimension_label.place(x=200, y=160)

            dimension_var = ctk.IntVar(value=3)
            dimension_selector = ctk.CTkOptionMenu(gauss_method_jordan, values=["2", "3", "4", "5", "6"],
                                                   variable=dimension_var, font=("Press Start 2P", 20),
                                                   command=update_matrix_size, width=170, height=50,
                                                   dropdown_font=("Press Start 2P", 20), fg_color="#e63101",
                                                   dropdown_fg_color="#be2903", button_color="#e63101",
                                                   dropdown_hover_color="#e63101", button_hover_color="#be2903")
            dimension_selector.place(x=650, y=150)

            input_frame = ctk.CTkFrame(main_frame, fg_color="#f0f9ff", width=900, height=320)
            input_frame.pack(pady=20)

            input_canvas = ctk.CTkCanvas(input_frame, width=650, height=320)
            input_canvas.pack(side="left", fill="both", expand=True)

            v_scroll = ctk.CTkScrollbar(input_frame, orientation="vertical", command=input_canvas.yview)
            v_scroll.pack(side="right", fill="y")
            h_scroll = ctk.CTkScrollbar(main_frame, orientation="horizontal", command=input_canvas.xview)
            h_scroll.pack(side="bottom", fill="x")

            input_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            input_inner_frame = ctk.CTkFrame(input_canvas, fg_color="#f0f9ff")
            input_canvas.create_window((0, 0), window=input_inner_frame, anchor="nw")

            create_matrix_entries()

            solution_frame = ctk.CTkFrame(gauss_method_jordan, fg_color=("white", "gray20"))
            solution_frame.place(x=1040, y=90)
            solution_text = ctk.CTkTextbox(solution_frame, width=700, height=500, font=("Arial", 25, 'bold'))
            solution_text.pack(pady=10, padx=10)

            solve_btn = ctk.CTkButton(gauss_method_jordan, text="SOLVE", font=("Press Start 2P", 25, "bold"),
                                      command=solve, height=76, width=154, fg_color="#be2903", hover_color="#e63101")
            solve_btn.place(x=690, y=664)

            clear_btn = ctk.CTkButton(gauss_method_jordan, text="CLEAR", font=("Press Start 2P", 25, "bold"),
                                      command=clear_entries, height=76, width=180, fg_color="#be2903", hover_color="#e63101")
            clear_btn.place(x=480, y=664)

            history_img = Image.open("History button.png").resize((500, 150))
            iconHistory = ctk.CTkImage(history_img, size=(180, 70))
            history_btn = ctk.CTkButton(gauss_method_jordan, image=iconHistory,
                                        text="", corner_radius=0, fg_color="#000000",
                                        hover_color="#ffffff", command=history_button_gauss_jord)
            history_btn.place(x=230, y=900)

            back_btn_img = Image.open("Back.png").resize((500, 150))
            back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
            back_button_4 = ctk.CTkButton(gauss_method_jordan, image=back_iconBack, corner_radius=0, text="",
                                          fg_color="#000000",
                                          command=back_button4,
                                          hover_color="#ffffff")
            back_button_4.place(x=50, y=900)

            gauss_method_jordan.mainloop()

        def open_method_gauss_elim():
            nonlocal selected_gauss_method
            pygame.mixer.music.load("Select.mp3")
            pygame.mixer.music.play()
            arrow_image_labelB.place_forget()

            arrow_img = Image.open("ARROW.png")
            arrow_tk = ctk.CTkImage(light_image=arrow_img, size=(37, 70))
            arrow_image_label.configure(image=arrow_tk)
            arrow_image_label.place(x=640, y=355)
            selected_gauss_method = 'gauss_eli'

        def open_method_gauss_jord():
            nonlocal selected_gauss_method
            pygame.mixer.music.load("Select.mp3")
            pygame.mixer.music.play()
            arrow_image_label.place_forget()

            arrow_img = Image.open("ARROW.png")
            arrow_tk = ctk.CTkImage(light_image=arrow_img, size=(37, 70))
            arrow_image_labelB.configure(image=arrow_tk)
            arrow_image_labelB.place(x=500, y=450)
            selected_gauss_method = 'gauss_jordan'

        def start_solver():
            pygame.mixer.music.load("OK.mp3")
            pygame.mixer.music.play()

            if selected_gauss_method == 'gauss_eli':
                open_gauss_method_elim()
            elif selected_gauss_method == 'gauss_jordan':
                open_gauss_method_jordan()
            else:
                pass

        def back_button8():
            pygame.mixer.music.load("Back Sound.mp3")
            pygame.mixer.music.play()
            choose_gauss_elimination.withdraw()
            root.deiconify()

        bg_img = ctk.CTkImage(light_image=Image.open("Gauss Selection.png"), size=(1920, 1080))
        bg_lbl = ctk.CTkLabel(choose_gauss_elimination, image=bg_img, text="")
        bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

        method_GE_img = Image.open("Gauss Elimination.png").resize((1920, 457))
        method_GE_icon = ctk.CTkImage(method_GE_img, size=(550, 70))

        arrow_image_label = ctk.CTkLabel(choose_gauss_elimination, text='.', font=("Press Start 2P", .1,),
                                         fg_color="#50d5ff",
                                         text_color="#50d5ff")
        arrow_image_label.place(x=630, y=290)

        method_GE_btn = ctk.CTkButton(choose_gauss_elimination, text="", image=method_GE_icon, corner_radius=0,
                                      fg_color="#50d5ff", hover_color="#ffffff", command=open_method_gauss_elim)
        method_GE_btn.place(x=690, y=350)

        method_GJE_img = Image.open("Gauss.png").resize((1920, 457))
        method_GJE_icon = ctk.CTkImage(method_GJE_img, size=(840, 70))

        arrow_image_labelB = ctk.CTkLabel(choose_gauss_elimination, text='.', font=("Press Start 2P", .1,),
                                          fg_color="#50d5ff", text_color="#50d5ff")
        arrow_image_labelB.place(x=630, y=420)

        method_GJE_btn = ctk.CTkButton(choose_gauss_elimination, text="", image=method_GJE_icon, corner_radius=0,
                                       fg_color="#50d5ff", hover_color="#ffffff", command=open_method_gauss_jord)
        method_GJE_btn.place(x=550, y=440)

        start_btn = ctk.CTkButton(choose_gauss_elimination, text=" START", font=("Retropix", 70, "bold"), width=180,
                                  height=50,
                                  corner_radius=0, fg_color="#e63101", hover_color="#8e1e00", command=start_solver)
        start_btn.place(x=860, y=570)

        back_btn_img = Image.open("Back.png").resize((500, 150))
        back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
        back_button_8 = ctk.CTkButton(choose_gauss_elimination, image=back_iconBack, corner_radius=0, text="",
                                      fg_color="#000000",
                                      command=back_button8,
                                      hover_color="#ffffff")
        back_button_8.place(x=50, y=900)

        choose_gauss_elimination.mainloop()

    def open_lu_method():
        root.withdraw()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        lu_decomposition = ctk.CTkToplevel()
        lu_decomposition.title("LU Decomposition")
        lu_decomposition.state('zoomed')
        lu_decomposition.grid_rowconfigure(0, weight=1)
        lu_decomposition.grid_columnconfigure(0, weight=1)
        lu_decomposition.resizable(True, True)
        pygame.mixer.init()

        entries = []
        variable_labels = []
        input_inner_frame = None
        input_canvas = None
        solution_text = None
        dimension_var = None

        def create_matrix_entries():
            nonlocal entries, variable_labels, input_inner_frame, input_canvas, dimension_var
            n = dimension_var.get()

            # Clear existing widgets
            for widget in input_inner_frame.winfo_children():
                widget.destroy()
            variable_labels.clear()

            # Create header frame
            header_frame = ctk.CTkFrame(input_inner_frame, fg_color="#f0f9ff", corner_radius=0)
            header_frame.grid(row=0, column=0, columnspan=(n * 2) + 1, sticky="ew")

            # Create variable labels
            variables = [f"X{i + 1}" for i in range(n)] + ['  D']
            for i, var in enumerate(variables):
                label = ctk.CTkLabel(
                    header_frame,
                    text=var,
                    text_color="#ffcf00",
                    fg_color="#f0f9ff",
                    font=("Press Start 2P", 30, "bold"),
                    width=90,
                    anchor="center"
                )
                pos = i * 2 if i < n else n * 2
                label.grid(row=0, column=pos, padx=35, pady=(0, 10))
                variable_labels.append(label)

            # Create entry fields
            entries = []
            for i in range(n):
                row = []
                for j in range(n + 1):
                    entry = ctk.CTkEntry(
                        input_inner_frame,
                        width=90,
                        height=70,
                        fg_color="#a84f78",
                        border_color="#e73d72",
                        text_color="white",
                        justify="center",
                        font=("Press Start 2P", 20, "bold")
                    )
                    entry.grid(row=i + 1, column=j * 2, padx=35, pady=15)

                    if j == n - 1:
                        equals = ctk.CTkLabel(
                            input_inner_frame,
                            text="=",
                            text_color="#000000",
                            font=("Press Start 2P", 35, "bold")
                        )
                        equals.grid(row=i + 1, column=j * 2 + 1, padx=5)
                    row.append(entry)
                entries.append(row)

            input_inner_frame.update_idletasks()
            input_canvas.configure(scrollregion=input_canvas.bbox("all"), bg="#f0f9ff")

        def update_matrix_size(choice):
            """Update the matrix size when dimension changes"""
            pygame.mixer.init()
            pygame.mixer.music.load("Select.mp3")
            pygame.mixer.music.play()
            create_matrix_entries()
            clear_entries()

        def parse_fraction(value):
            try:
                # Try to convert directly to float first
                return float(value)
            except ValueError:
                # If that fails, try to parse as fraction
                try:
                    if '/' in value:
                        numerator, denominator = value.split('/')
                        return float(numerator) / float(denominator)
                    else:
                        return float(value)
                except:
                    raise ValueError("Invalid input - must be a number or fraction (like '1/2')")

        def format_fraction(value):
            try:
                # Try to format as simplified fraction
                frac = Fraction(value).limit_denominator()
                if frac.denominator == 1:
                    return str(frac.numerator)
                return f"{frac.numerator}/{frac.denominator}"
            except:
                return f"{value:.4f}"

        def format_fraction_matrix(matrix, is_augmented=False):
            """Improved matrix formatting for any size"""
            if not matrix:
                return ""

            # Convert all elements to Fraction for consistent formatting
            frac_matrix = []
            for row in matrix:
                frac_row = [Fraction(item).limit_denominator() for item in row]
                frac_matrix.append(frac_row)

            # Calculate column widths
            col_widths = []
            for col in range(len(frac_matrix[0])):
                max_len = max(len(str(row[col])) for row in frac_matrix)
                col_widths.append(max(max_len, 6))  # Minimum width 6

            # Build formatted string
            formatted = ""
            for row in frac_matrix:
                if is_augmented:
                    left = " | ".join(f"{str(row[i]):>{col_widths[i]}}" for i in range(len(row) - 1))
                    right = f"{str(row[-1]):>{col_widths[-1]}}"
                    formatted += f"| {left} |   {right} |\n"
                else:
                    elements = " | ".join(f"{str(item):>{col_widths[i]}}" for i, item in enumerate(row))
                    formatted += f"| {elements} |\n"
            return formatted

        def solve():
            pygame.mixer.music.load("OK.mp3")
            pygame.mixer.music.play()
            solution_text.delete("1.0", "end")
            try:
                n = dimension_var.get()  # Get current matrix dimension
                A = []
                b = []

                # Read matrix with dynamic error handling
                for i in range(n):
                    row = []
                    for j in range(n + 1):
                        entry = entries[i][j]
                        val = entry.get()
                        try:
                            parsed = Fraction(val)
                        except:
                            col_name = f"X{j + 1}" if j < n else "D"
                            raise ValueError(f"Row {i + 1}, Column {col_name}: Invalid input")
                        if j < n:
                            row.append(parsed)
                        else:
                            b.append(parsed)
                    A.append(row)

                solution_text.delete("1.0", "end")

                # Show initial augmented matrix
                Ab = [row + [b[i]] for i, row in enumerate(A)]
                solution_text.insert("end", "Given augmented matrix [A | B]:\n")
                solution_text.insert("end", format_fraction_matrix(Ab, is_augmented=True) + "\n")

                # Initialize matrices
                U = [row[:] for row in A]  # Will become upper triangular
                B = b[:]  # Constants vector
                L = [[Fraction(0) for _ in range(n)] for _ in range(n)]  # Lower triangular
                P = [[Fraction(i == j) for j in range(n)] for i in range(n)]  # Permutation matrix

                for i in range(n):
                    L[i][i] = Fraction(1)  # Diagonal of L is 1

                solution_text.insert("end", "Step-by-step Gaussian Elimination with Partial Pivoting:\n")

                # Gaussian Elimination with partial pivoting
                for i in range(n):
                    # Partial pivoting
                    max_row = i
                    for k in range(i + 1, n):
                        if abs(U[k][i]) > abs(U[max_row][i]):
                            max_row = k

                    # Swap rows if needed
                    if max_row != i:
                        U[i], U[max_row] = U[max_row], U[i]
                        B[i], B[max_row] = B[max_row], B[i]
                        P[i], P[max_row] = P[max_row], P[i]
                        # Also swap rows in L for elements above diagonal
                        for k in range(i):
                            L[i][k], L[max_row][k] = L[max_row][k], L[i][k]

                        solution_text.insert("end",
                                             f"Swapped row {i + 1} with row {max_row + 1} for partial pivoting\n")
                        current_augmented = [row[:] + [B[idx]] for idx, row in enumerate(U)]
                        solution_text.insert("end", format_fraction_matrix(current_augmented, True) + "\n")

                    pivot = U[i][i]
                    if pivot == 0:
                        solution_text.insert("end",
                                             f"Zero pivot at row {i + 1}, the system may have no unique solution\n")
                        return

                    for j in range(i + 1, n):
                        multiplier = U[j][i] / pivot
                        L[j][i] = multiplier  # Store multiplier in L
                        solution_text.insert("end",
                                             f"Row{j + 1} = Row{j + 1} - ({format_fraction(multiplier)})×Row{i + 1}\n")

                        for k in range(i, n):
                            U[j][k] -= multiplier * U[i][k]
                        B[j] -= multiplier * B[i]

                        current_augmented = [row[:] + [B[idx]] for idx, row in enumerate(U)]
                        solution_text.insert("end", format_fraction_matrix(current_augmented, True) + "\n")

                solution_text.insert("end", "\nFinal matrices:\n")
                solution_text.insert("end", "Permutation matrix P:\n" + format_fraction_matrix(P) + "\n")
                solution_text.insert("end", "Lower triangular matrix L:\n" + format_fraction_matrix(L) + "\n")
                solution_text.insert("end", "Upper triangular matrix U:\n" + format_fraction_matrix(U) + "\n")

                # Forward substitution (Ly = Pb)
                Pb = [sum(P[i][j] * b[j] for j in range(n)) for i in range(n)]
                solution_text.insert("end", "\nForward substitution (Ly = Pb):\n")
                y = [Fraction(0) for _ in range(n)]
                for i in range(n):
                    sum_terms = sum(L[i][j] * y[j] for j in range(i))
                    y[i] = Pb[i] - sum_terms
                    solution_text.insert("end",
                                         f"y{i + 1} = {Pb[i]} - ({' + '.join(f'{L[i][j]}×{y[j]}' for j in range(i)) or '0'}) = {y[i]}\n")

                # Backward substitution (Ux = y)
                solution_text.insert("end", "\nBackward substitution (Ux = Y):\n")
                x = [Fraction(0) for _ in range(n)]
                for i in reversed(range(n)):
                    sum_terms = sum(U[i][j] * x[j] for j in range(i + 1, n))
                    x[i] = (y[i] - sum_terms) / U[i][i]
                    solution_text.insert("end",
                                         f"x{i + 1} = ({y[i]} - {' + '.join(f'{U[i][j]}×{x[j]}' for j in range(i + 1, n)) or '0'}) / {U[i][i]} = {x[i]}\n")

                # Display final solutions
                solution_text.insert("end", "\nSolutions:\n")
                for i in range(n):
                    solution_text.insert("end", f"X{i + 1} = {format_fraction(x[i])}\n")

                equations = []
                for i in range(n):
                    equation = " + ".join(
                        [f"{entries[i][j].get()}X{j + 1}" for j in range(n)]) + f" = {entries[i][n].get()}"
                    equations.append(equation)

                solution_text_value = solution_text.get("1.0", "end")
                save_to_db('lu_decomposition', '\n'.join(equations), solution_text_value)

            except ValueError as ve:
                solution_text.insert("end", f"Input Error: {str(ve)}\n")
            except Exception as e:
                solution_text.insert("end", f"Calculation Error: {str(e)}\n")

        def clear_entries():
            pygame.mixer.init()
            pygame.mixer.music.load("Select.mp3")  # or .wav
            pygame.mixer.music.play()

            # ung mag bubura sa mga entries
            for row in entries:
                for entry in row:
                    entry.delete(0, "end")

            solution_text.delete("1.0", "end")

        def back_button5():
            pygame.mixer.init()
            pygame.mixer.music.load("Back Sound.mp3")  # or .wav
            pygame.mixer.music.play()
            lu_decomposition.withdraw()
            root.deiconify()

        def history_button_lu():
            lu_decomposition.withdraw()
            pygame.mixer.init()
            pygame.mixer.music.load("Back Sound.mp3")  # or .wav
            pygame.mixer.music.play()

            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            history_cramers = ctk.CTkToplevel()
            history_cramers.title("Lu Decomposition History")
            history_cramers.state('zoomed')
            history_cramers.grid_rowconfigure(0, weight=1)
            history_cramers.grid_columnconfigure(0, weight=1)
            history_cramers.resizable(True, True)
            pygame.mixer.init()

            def back_button6():
                pygame.mixer.init()
                pygame.mixer.music.load("Back Sound.mp3")  # or .wav
                pygame.mixer.music.play()
                history_cramers.withdraw()
                lu_decomposition.deiconify()

            def clear_lu_decomp_history():
                pygame.mixer.music.load("Select.mp3")  # or .wav
                pygame.mixer.music.play()
                clear_history('lu_decomposition')
                solution_text.delete("1.0", "end")

            bg_img = ctk.CTkImage(light_image=Image.open("history.png"), size=(1920, 1030))
            bg_lbl = ctk.CTkLabel(history_cramers, image=bg_img, text="")
            bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

            solu_frame = ctk.CTkFrame(history_cramers, fg_color=("white", "gray20"))
            solu_frame.place(x=620, y=130)
            solution_frame = ctk.CTkFrame(solu_frame, width=690, height=490)
            solution_frame.pack(pady=10, padx=10)
            solution_text = ctk.CTkTextbox(solution_frame, height=490, width=690, font=("Arial", 25, "bold"))
            solution_text.pack(pady=10, padx=10)

            solution_text.insert("end", "LU Decomposition History:\n\n")
            history = get_history('lu_decomposition')

            for entry in history:
                solution_text.insert("end", f"ID: {entry['id']}\n")
                solution_text.insert("end", f"Date: {entry['timestamp']}\n")
                solution_text.insert("end", "Equations:\n")
                solution_text.insert("end", f"{entry['equations']}\n")
                solution_text.insert("end", "\nSolution:\n")
                solution_text.insert("end", f"{entry['solution']}\n")
                solution_text.insert("end", "=" * 50 + "\n")

            back_btn_img = Image.open("Back.png").resize((500, 150))
            back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
            back_button_6 = ctk.CTkButton(history_cramers, image=back_iconBack, corner_radius=0, text="",
                                          fg_color="#000000",
                                          command=back_button6,
                                          hover_color="#ffffff")
            back_button_6.place(x=50, y=900)

            clear_history_img = Image.open("Clear Button.png").resize((500, 150))
            iconClearHistory = ctk.CTkImage(clear_history_img, size=(180, 70))

            # History Button with image
            clear_history_btn = ctk.CTkButton(history_cramers, image=iconClearHistory,
                                              text="", corner_radius=0, fg_color="#000000",
                                              hover_color="#ffffff", command=clear_lu_decomp_history)
            clear_history_btn.place(x=230, y=900)

            history_cramers.mainloop()

        bg_img = ctk.CTkImage(light_image=Image.open("lu decomp.png"), size=(1920, 1080))
        bg_lbl = ctk.CTkLabel(lu_decomposition, image=bg_img, text="")
        bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)

        dimension_label = ctk.CTkLabel(lu_decomposition, text="Matrix Dimension:",
                                       font=("Press Start 2P", 25), fg_color="#f0f9ff", text_color="#000000")
        dimension_label.place(x=200, y=160)

        # Dimension selector
        dimension_var = ctk.IntVar(value=3)
        dimension_selector = ctk.CTkOptionMenu(
            lu_decomposition,
            values=["2", "3", "4", "5", "6"],
            variable=dimension_var,
            font=("Press Start 2P", 20),
            command=update_matrix_size,
            width=170,
            height=50,
            dropdown_font=("Press Start 2P", 20),
            fg_color="#a84f78",
            dropdown_fg_color="#98314f",
            button_color="#a84f78",
            dropdown_hover_color="#a84f78",
            button_hover_color="#98314f"
        )
        dimension_selector.place(x=650, y=150)

        # Input frame and canvas setup
        main_frame = ctk.CTkFrame(lu_decomposition, fg_color=("#f0f9ff"), corner_radius=0)
        main_frame.place(x=155, y=205)

        input_frame = ctk.CTkFrame(main_frame, fg_color="#f0f9ff", width=900, height=320)
        input_frame.pack(pady=20)

        input_canvas = ctk.CTkCanvas(input_frame, width=650, height=320)
        input_canvas.pack(side="left", fill="both", expand=True)

        # Scrollbars and inner frame
        v_scroll = ctk.CTkScrollbar(input_frame, orientation="vertical", command=input_canvas.yview)
        v_scroll.pack(side="right", fill="y")
        h_scroll = ctk.CTkScrollbar(main_frame, orientation="horizontal", command=input_canvas.xview)
        h_scroll.pack(side="bottom", fill="x")

        input_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        input_inner_frame = ctk.CTkFrame(input_canvas, fg_color="#f0f9ff")
        input_canvas.create_window((0, 0), window=input_inner_frame, anchor="nw")

        # Initial entries
        variable_labels = []
        create_matrix_entries()

        # Solution frame
        solu_frame = ctk.CTkFrame(lu_decomposition, fg_color=("white", "gray20"))
        solu_frame.place(x=1040, y=90)
        solution_frame = ctk.CTkFrame(solu_frame, width=700, height=500)
        solution_frame.pack(pady=10, padx=10)
        solution_text = ctk.CTkTextbox(solution_frame, height=500, width=700, font=("Arial", 25, "bold"))
        solution_text.pack(pady=10, padx=10)

        # Buttons
        solve_btn = ctk.CTkButton(lu_decomposition, text="SOLVE", font=("Press Start 2P", 25, "bold"),
                                  command=solve, height=76, width=154, fg_color="#98314f", hover_color="#a84f78",corner_radius=0)
        solve_btn.place(x=690, y=664)

        clear_btn = ctk.CTkButton(lu_decomposition, text="CLEAR", font=("Press Start 2P", 25, "bold"),
                                  command=clear_entries, height=76, width=180, fg_color="#98314f",hover_color="#a84f78")
        clear_btn.place(x=480, y=664)

        # History button
        history_img = Image.open("History button.png").resize((500, 150))
        iconHistory = ctk.CTkImage(history_img, size=(180, 70))
        history_btn = ctk.CTkButton(lu_decomposition, image=iconHistory,
                                    text="", corner_radius=0, fg_color="#000000",
                                    hover_color="#ffffff", command=history_button_lu)
        history_btn.place(x=230, y=900)

        # Back button
        back_btn_img = Image.open("Back.png").resize((500, 150))
        back_icon = ctk.CTkImage(back_btn_img, size=(150, 70))
        back_btn = ctk.CTkButton(lu_decomposition, image=back_icon, text="",
                                 corner_radius=0, fg_color="#000000",
                                 hover_color="#ffffff", command=back_button5)
        back_btn.place(x=50, y=900)

        lu_decomposition.mainloop()

    # Method Buttons
    def open_method_cram():
        nonlocal selected_method
        pygame.mixer.music.load("Select.mp3")
        pygame.mixer.music.play()
        image_labelB.place_forget()
        image_labelC.place_forget()
        image_label.configure(image=arrow_tk)
        image_label.place(x=640, y=290)
        selected_method = "cramers"

    def open_method_gauss():
        nonlocal selected_method
        pygame.mixer.music.load("Select.mp3")
        pygame.mixer.music.play()
        image_label.place_forget()
        image_labelC.place_forget()
        image_labelB.configure(image=arrow_tk)
        image_labelB.place(x=500, y=385)
        selected_method = "gauss"

    def open_method_lu():
        nonlocal selected_method
        pygame.mixer.music.load("Select.mp3")
        pygame.mixer.music.play()
        image_label.place_forget()
        image_labelB.place_forget()
        image_labelC.configure(image=arrow_tk)
        image_labelC.place(x=595, y=475)
        selected_method = "lu"

    # Start Button Action
    def start_app():
        pygame.mixer.music.load("OK.mp3")
        pygame.mixer.music.play()

        if selected_method == 'cramers':
            open_cram_method_window()
        elif selected_method == "gauss":
            open_gauss_method_window()
        elif selected_method == "lu":
            open_lu_method()
        else:
            pass

    def back_button():
        pygame.mixer.music.load("Back Sound.mp3")  # or .wav
        pygame.mixer.music.play()
        root.withdraw()
        main.deiconify()

    # Load button images
    iconA = ctk.CTkImage(Image.open("Cramer.png"), size=(550, 70))
    iconB = ctk.CTkImage(Image.open("Gauss.png"), size=(840, 70))
    iconC = ctk.CTkImage(Image.open("LU Decom.png"), size=(650, 70))

    # Place Buttons
    ctk.CTkButton(root, text="", image=iconA, corner_radius=0, fg_color="#50d5ff",
                  hover_color="#ffffff", command=open_method_cram).place(x=690, y=285)

    ctk.CTkButton(root, text="", image=iconB, corner_radius=0, fg_color="#50d5ff",
                  hover_color="#ffffff", command=open_method_gauss).place(x=550, y=375)

    ctk.CTkButton(root, text="", image=iconC, corner_radius=0, fg_color="#50d5ff",
                  hover_color="#ffffff", command=open_method_lu).place(x=650, y=465)

    ctk.CTkButton(root, text=" START", font=("Retropix", 70, "bold"), width=180,
                  height=50, corner_radius=0, fg_color="#74a050",
                  hover_color="#4f722a", command=start_app).place(x=860, y=620)

    back_btn_img = Image.open("Back.png").resize((500, 150))
    back_iconBack = ctk.CTkImage(back_btn_img, size=(150, 70))
    ctk.CTkButton(root, image=back_iconBack, corner_radius=0, text="", fg_color="#000000",
                  hover_color="#ffffff", command=back_button).place(x=50, y=900)

    root.mainloop()


try:
    start_bg_img = ctk.CTkImage(light_image=Image.open("Start.png"), size=(1920, 1080))
    start_bg_img_lbl = ctk.CTkLabel(main, image=start_bg_img, text="")
    start_bg_img_lbl.place(x=0, y=0, relwidth=1, relheight=1)
except FileNotFoundError:
    # kapag walang picture eto ung lalabas
    main.configure(fg_color="#2b2b2b")

lets_start_btn = ctk.CTkButton(main, text=" START", font=("Retropix", 70, "bold"), width=190,
                               height=60, corner_radius=0, fg_color="#e63101", hover_color="#8e1e00",
                               command=start_selection)
lets_start_btn.place(x=850, y=600)
main.mainloop()
