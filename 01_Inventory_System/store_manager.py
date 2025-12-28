import customtkinter as ctk
import sqlite3
from tkinter import messagebox

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. Window Setup
        self.title("Store Inventory Manager (Portfolio Build)")
        self.geometry("900x600")

        # 2. Database Setup
        self.conn = sqlite3.connect("store_data.db")
        self.create_tables()

        # --- LAYOUT FRAMES ---
        # LEFT SIDE: Controls
        self.left_frame = ctk.CTkFrame(self, width=300)
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)

        # RIGHT SIDE: Data View
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)

        # --- TITLE ---
        ctk.CTkLabel(self.left_frame, text="INVENTORY CONTROL", font=("Arial", 20, "bold")).pack(pady=20)

        # --- ADD ITEM SECTION ---
        ctk.CTkLabel(self.left_frame, text="Add New Item", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.entry_name = ctk.CTkEntry(self.left_frame, placeholder_text="Item Name (e.g. Coke)")
        self.entry_name.pack(pady=5)

        self.entry_price = ctk.CTkEntry(self.left_frame, placeholder_text="Price (Php)")
        self.entry_price.pack(pady=5)
        
        self.entry_stock = ctk.CTkEntry(self.left_frame, placeholder_text="Quantity")
        self.entry_stock.pack(pady=5)

        self.btn_add = ctk.CTkButton(self.left_frame, text="ADD STOCK (+)", command=self.add_item, fg_color="#2CC985") # Green
        self.btn_add.pack(pady=10)

        # --- SEPARATOR ---
        ctk.CTkLabel(self.left_frame, text="----------------------").pack(pady=10)

        # --- SELL SECTION ---
        ctk.CTkLabel(self.left_frame, text="Sell Item", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.entry_id = ctk.CTkEntry(self.left_frame, placeholder_text="Enter ID to Sell")
        self.entry_id.pack(pady=5)
        
        self.btn_sell = ctk.CTkButton(self.left_frame, text="SELL ITEM (-1)", command=self.sell_item, fg_color="#D94343") # Red
        self.btn_sell.pack(pady=10)

        # --- REFRESH ---
        self.btn_refresh = ctk.CTkButton(self.left_frame, text="Refresh List", command=self.load_data, fg_color="gray")
        self.btn_refresh.pack(pady=20)

        # --- DISPLAY AREA ---
        self.label_list = ctk.CTkLabel(self.right_frame, text="Current Inventory", font=("Arial", 18, "bold"))
        self.label_list.pack(pady=10)

        self.display_box = ctk.CTkTextbox(self.right_frame, font=("Consolas", 14))
        self.display_box.pack(fill="both", expand=True, padx=10, pady=10)

        # Load initial data
        self.load_data()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        """)
        self.conn.commit()

    def add_item(self):
        name = self.entry_name.get()
        price = self.entry_price.get()
        stock = self.entry_stock.get()

        if name and price and stock:
            try:
                cursor = self.conn.cursor()
                cursor.execute("INSERT INTO inventory (name, price, stock) VALUES (?, ?, ?)", 
                               (name, float(price), int(stock)))
                self.conn.commit()
                messagebox.showinfo("Success", f"Added {name}!")
                # Clear inputs
                self.entry_name.delete(0, 'end')
                self.entry_price.delete(0, 'end')
                self.entry_stock.delete(0, 'end')
                self.load_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Missing Info", "Please fill all fields!")

    def sell_item(self):
        item_id = self.entry_id.get()
        
        if item_id:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT stock, name FROM inventory WHERE id = ?", (item_id,))
                result = cursor.fetchone()
                
                if result:
                    current_stock = result[0]
                    item_name = result[1]
                    
                    if current_stock > 0:
                        new_stock = current_stock - 1
                        cursor.execute("UPDATE inventory SET stock = ? WHERE id = ?", (new_stock, item_id))
                        self.conn.commit()
                        messagebox.showinfo("Sold!", f"Sold 1 {item_name}. Stock is now {new_stock}.")
                        self.load_data()
                    else:
                        messagebox.showerror("Error", f"Out of Stock! Cannot sell {item_name}.")
                else:
                    messagebox.showerror("Error", "Item ID not found.")     
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Missing Info", "Please enter an ID.")

    def load_data(self):
        self.display_box.delete("0.0", "end")
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM inventory")
        rows = cursor.fetchall()
        
        # Table Header
        header = f"{'ID':<5} {'NAME':<25} {'PRICE':<10} {'STOCK':<10}\n"
        header += "-"*60 + "\n"
        self.display_box.insert("end", header)

        for row in rows:
            line = f"{row[0]:<5} {row[1]:<25} ₱{row[2]:<9} {row[3]:<10}\n"
            self.display_box.insert("end", line)

if __name__ == "__main__":
    app = StoreApp()
    app.mainloop()