import customtkinter as ctk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from tkinter import messagebox
import os
from datetime import datetime

# --- CONFIG ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class InvoiceApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Quick Invoice Generator")
        self.geometry("500x650")

        # --- HEADER ---
        self.header_frame = ctk.CTkFrame(self, height=80, fg_color="#3B8ED0", corner_radius=0)
        self.header_frame.pack(fill="x")

        ctk.CTkLabel(self.header_frame, text="INVOICE MAKER",
                     font=("Arial", 24, "bold"), text_color="white").pack(pady=20)

        # --- FORM INPUTS ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=40, pady=20)

        # 1. Company / Your Name
        ctk.CTkLabel(self.main_frame, text="Your Company Name:", anchor="w").pack(fill="x")
        self.entry_company = ctk.CTkEntry(self.main_frame, placeholder_text="e.g. Falcon Tech Solutions")
        self.entry_company.pack(fill="x", pady=(5, 15))

        # 2. Client Name
        ctk.CTkLabel(self.main_frame, text="Client Name:", anchor="w").pack(fill="x")
        self.entry_client = ctk.CTkEntry(self.main_frame, placeholder_text="e.g. John Doe")
        self.entry_client.pack(fill="x", pady=(5, 15))

        # 3. Service Description
        ctk.CTkLabel(self.main_frame, text="Service / Item:", anchor="w").pack(fill="x")
        self.entry_service = ctk.CTkEntry(self.main_frame, placeholder_text="e.g. Website Development")
        self.entry_service.pack(fill="x", pady=(5, 15))

        # 4. Amount
        ctk.CTkLabel(self.main_frame, text="Amount (Php):", anchor="w").pack(fill="x")
        self.entry_amount = ctk.CTkEntry(self.main_frame, placeholder_text="0.00")
        self.entry_amount.pack(fill="x", pady=(5, 15))

        # --- GENERATE BUTTON ---
        self.btn_generate = ctk.CTkButton(self.main_frame, text="GENERATE PDF",
                                          command=self.generate_pdf,
                                          height=50,
                                          font=("Arial", 16, "bold"),
                                          fg_color="#2CC985", hover_color="#229A65")
        self.btn_generate.pack(fill="x", pady=30)

        self.lbl_status = ctk.CTkLabel(self.main_frame, text="", text_color="gray")
        self.lbl_status.pack()

    def generate_pdf(self):
        company = self.entry_company.get()
        client = self.entry_client.get()
        service = self.entry_service.get()
        amount = self.entry_amount.get()

        if not company or not client or not service or not amount:
            messagebox.showwarning("Missing Info", "Please fill in all fields!")
            return

        # PDF Generation Logic
        try:
            filename = f"Invoice_{client.replace(' ', '_')}.pdf"
            c = canvas.Canvas(filename, pagesize=letter)
            width, height = letter

            # 1. Header Area
            c.setFillColorRGB(0.2, 0.2, 0.2)  # Dark Gray
            c.rect(0, height - 100, width, 100, fill=1, stroke=0)  # Top Bar

            c.setFillColorRGB(1, 1, 1)  # White Text
            c.setFont("Helvetica-Bold", 24)
            c.drawString(50, height - 60, "INVOICE")

            c.setFont("Helvetica", 14)
            c.drawString(50, height - 85, company)

            # 2. Date
            c.setFillColorRGB(0, 0, 0)  # Black Text
            c.setFont("Helvetica", 12)
            today = datetime.now().strftime("%Y-%m-%d")
            c.drawString(400, height - 130, f"Date: {today}")

            # 3. Bill To
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height - 150, "Bill To:")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 170, client)

            # 4. Table Header
            c.setLineWidth(1)
            c.line(50, height - 210, 550, height - 210)  # Top Line
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, height - 230, "Description")
            c.drawString(450, height - 230, "Amount")
            c.line(50, height - 240, 550, height - 240)  # Bottom Line

            # 5. Table Content
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 270, service)
            c.drawString(450, height - 270, f"P {amount}")

            # 6. Total
            c.setFont("Helvetica-Bold", 14)
            c.drawString(350, height - 350, f"TOTAL: P {amount}")

            # 7. Footer
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(50, 50, "Thank you for your business!")

            c.save()

            self.lbl_status.configure(text=f"Saved: {filename}", text_color="#2CC985")
            os.startfile(filename)  # Open the PDF automatically

        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = InvoiceApp()
    app.mainloop()