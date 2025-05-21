import pyodbc
import customtkinter as ctk
from PIL import Image, ImageTk
import subprocess
import tkinter.messagebox as messagebox

# Database connection function
def connect_to_database():
    try:
        connection = pyodbc.connect(
            'DRIVER={SQL Server};'
            'Server=MSI\\SQLEXPRESS;'  # Update this if your instance name is different
            'Database=University_Billing_System;'
            'Trusted_Connection=True'
        )
        print('Connected to database')
        return connection
    except pyodbc.Error as ex:
        print('Connection failed:', ex)
        return None

# Function to verify student ID
def verify_student_id():
    student_id = entry.get().strip()

    if not student_id:
        messagebox.showwarning("Input Error", "Please enter your Student ID.")
        return
    
    if not student_id.isdigit():
        messagebox.showerror("Input Error", "Student ID must be a number.")
        return

    conn = connect_to_database()
    if conn is None:
        messagebox.showerror("Database Error", "Failed to connect to the database.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (int(student_id),))
        result = cursor.fetchone()

        if result:
            app.destroy()  # Close login window
            subprocess.Popen(["python", "main.py", student_id])
  # Open main page
        else:
            messagebox.showerror("Login Failed", "Invalid Student ID.")
    except Exception as e:
        messagebox.showerror("Database Error", f"Something went wrong:\n{str(e)}")
    finally:
        cursor.close()
        conn.close()

# Initialize the app
app = ctk.CTk()
app.title("USTP Login")
app.geometry("900x500")
app.resizable(False, False)

# Grid configuration
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

# Left Frame (Login Form)
left_frame = ctk.CTkFrame(app, fg_color="#0E1B2B", width=450)
left_frame.grid(row=0, column=0, sticky="nsew")

# Right Frame (Logo Display)
right_frame = ctk.CTkFrame(app, fg_color="white", width=450)
right_frame.grid(row=0, column=1, sticky="nsew")

# Left Frame Content
label = ctk.CTkLabel(left_frame, text="Enter your Student ID", text_color="white", font=("Arial", 20))
label.pack(pady=(100, 10))

entry = ctk.CTkEntry(left_frame, width=250, height=40, font=("Arial", 16))
entry.pack(pady=10)

submit_button = ctk.CTkButton(
    left_frame, text="SUBMIT", width=120, height=40,
    font=("Arial", 16, "bold"), command=verify_student_id
)
submit_button.pack(pady=20)

# Right Frame Content (Logo)
try:
    img_logo = Image.open("assets/ustpcdologo.jpg")
    img_logo = img_logo.resize((400, 400))
    logo_image = ImageTk.PhotoImage(img_logo)

    logo_label = ctk.CTkLabel(right_frame, image=logo_image, text="")
    logo_label.image = logo_image  # Prevent garbage collection
    logo_label.pack(expand=True)
except Exception as e:
    print("Failed to load image:", e)

# Run the app
app.mainloop()
