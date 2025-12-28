import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
import os
import time
import threading

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")  # Excel-like theme


class ExcelMergerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- WINDOW SETUP (CENTERED) ---
        self.title("Excel Master Tool | Automation")

        # 1. Define the size
        window_width = 700
        window_height = 600

        # 2. Get the screen dimension
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # 3. Calculate the center position
        center_x = int((screen_width / 2) - (window_width / 2))
        center_y = int((screen_height / 2) - (window_height / 2))

        # 4. Set the geometry
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        self.files_to_merge = []

        # --- LAYOUT (Everything else stays the same below) ---
        # HEADER
        self.header_frame = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color="#107C41")
        self.header_frame.pack(fill="x")

        ctk.CTkLabel(self.header_frame, text="EXCEL BATCH MERGER",
                     font=("Segoe UI", 24, "bold"), text_color="white").pack(pady=20)

        # MAIN CARD
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=20)

        # STEP 1: SELECT
        ctk.CTkLabel(self.main_frame, text="1. Select Files to Combine",
                     font=("Segoe UI", 16, "bold"), anchor="w").pack(fill="x", pady=(10, 5))

        self.btn_select = ctk.CTkButton(self.main_frame, text="+ ADD EXCEL FILES",
                                        command=self.select_files,
                                        height=50,
                                        font=("Segoe UI", 14, "bold"),
                                        fg_color="#333333", hover_color="#444444",
                                        border_width=2, border_color="#555555",
                                        corner_radius=10)
        self.btn_select.pack(fill="x", pady=5)

        # FILE LIST DISPLAY
        self.file_list_box = ctk.CTkTextbox(self.main_frame, height=200, corner_radius=10,
                                            font=("Consolas", 13), fg_color="#1e1e1e", border_width=0)
        self.file_list_box.pack(fill="x", pady=10)
        self.file_list_box.insert("0.0", "No files selected.\n")
        self.file_list_box.configure(state="disabled")

        # STEP 2: ACTION
        ctk.CTkLabel(self.main_frame, text="2. Process",
                     font=("Segoe UI", 16, "bold"), anchor="w").pack(fill="x", pady=(20, 5))

        self.btn_merge = ctk.CTkButton(self.main_frame, text="MERGE FILES NOW ➤",
                                       command=self.start_merge_thread,
                                       height=60,
                                       font=("Segoe UI", 16, "bold"),
                                       fg_color="#107C41", hover_color="#0E5C30",
                                       corner_radius=10,
                                       state="disabled")
        self.btn_merge.pack(fill="x", pady=10)

        # PROGRESS BAR
        self.progress = ctk.CTkProgressBar(self.main_frame, height=15, corner_radius=5)
        self.progress.pack(fill="x", pady=10)
        self.progress.set(0)

        # STATUS
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="Waiting for input...", text_color="gray")
        self.lbl_status.pack(pady=5)

    def select_files(self):
        filepaths = filedialog.askopenfilenames(filetypes=[("Excel Files", "*.xlsx")])
        if filepaths:
            self.files_to_merge = list(filepaths)

            # Enable the Merge Button
            self.btn_merge.configure(state="normal")

            # Update Display
            self.file_list_box.configure(state="normal")
            self.file_list_box.delete("0.0", "end")
            for i, path in enumerate(self.files_to_merge, 1):
                filename = os.path.basename(path)
                self.file_list_box.insert("end", f"{i}. {filename}\n")
            self.file_list_box.configure(state="disabled")

            self.lbl_status.configure(text=f"{len(self.files_to_merge)} files ready to merge.")

    def start_merge_thread(self):
        # Run merge in background so window doesn't freeze
        threading.Thread(target=self.merge_files).start()

    def merge_files(self):
        try:
            self.progress.set(0.2)
            self.lbl_status.configure(text="Reading files...", text_color="#3B8ED0")

            all_data = []
            for file in self.files_to_merge:
                df = pd.read_excel(file)
                all_data.append(df)

            self.progress.set(0.6)
            self.lbl_status.configure(text="Combining data...", text_color="#3B8ED0")
            time.sleep(0.5)  # Fake delay just so user sees the progress bar move

            # Combine
            master_df = pd.concat(all_data, ignore_index=True)

            self.progress.set(0.9)

            # Ask where to save (Must be done in main thread usually, but works here in simple apps)
            save_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                     filetypes=[("Excel Files", "*.xlsx")],
                                                     initialfile="Merged_Master.xlsx")

            if save_path:
                master_df.to_excel(save_path, index=False)
                self.progress.set(1.0)
                self.lbl_status.configure(text="DONE! File Saved.", text_color="#107C41")
                messagebox.showinfo("Complete", "Files have been merged successfully!")
                os.startfile(save_path)
            else:
                self.progress.set(0)
                self.lbl_status.configure(text="Save cancelled.", text_color="orange")

        except Exception as e:
            self.lbl_status.configure(text="Error occurred.", text_color="red")
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = ExcelMergerApp()
    app.mainloop()