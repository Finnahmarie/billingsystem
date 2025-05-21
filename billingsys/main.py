import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pyodbc
import sys


# Database connection
connection_string = "DRIVER={SQL Server};SERVER=MSI\\SQLEXPRESS;DATABASE=University_Billing_System;Trusted_Connection=yes;"
conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# Fetch student info (example: one student for now)
# Get student_id from command-line argument
student_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
cursor.execute("SELECT student_id, stud_name FROM students WHERE student_id = ?", (student_id,))
student_row = cursor.fetchone()
student_info = {
    "id": student_row.student_id,
    "name": student_row.stud_name
}

# Fetch fees
cursor.execute("SELECT fee_id, fee_name, cost FROM fees")
fees = [{"fee_id": row.fee_id, "fee_name": row.fee_name, "cost": float(row.cost)} for row in cursor.fetchall()]

# Fetch scholarships
cursor.execute("SELECT scholarship_id, scholarship_name, amount FROM scholarships")
scholarship_list = cursor.fetchall()
scholarships = {row.scholarship_name: float(row.amount) for row in scholarship_list}

# GUI Setup
root = tk.Tk()
root.title("Student Billing Dashboard")
root.geometry("1000x600")
root.configure(bg="#f0f0f0")

tk.Label(root, text="Student Billing Dashboard", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)
tk.Label(root, text=f"Name: {student_info['name']} | ID: {student_info['id']}", bg="#f0f0f0").pack()

main_frame = tk.Frame(root, bg="#f0f0f0")
main_frame.pack(pady=10, padx=20, fill="both", expand=True)

# Left Treeview: Available Fees
left_frame = tk.Frame(main_frame, bg="#f0f0f0")
tk.Label(left_frame, text="Available Fees", font=("Arial", 12, "bold")).pack()
left_tree = ttk.Treeview(left_frame, columns=("Fee", "Cost"), show="headings", height=10, selectmode="extended")
left_tree.heading("Fee", text="Fee Name")
left_tree.heading("Cost", text="Cost")

for fee in fees:
    left_tree.insert("", "end", iid=fee["fee_id"], values=(fee["fee_name"], f"${fee['cost']:.2f}"))

left_tree.pack()
left_frame.grid(row=0, column=0, padx=10)

# Buttons
btn_frame = tk.Frame(main_frame, bg="#f0f0f0")
tk.Button(btn_frame, text="→ Add to Pay", command=lambda: move_fees(left_tree, right_tree), width=15).pack(pady=5)
tk.Button(btn_frame, text="← Remove", command=lambda: move_fees(right_tree, left_tree), width=15).pack()
btn_frame.grid(row=0, column=1)

# Right Treeview: Selected Fees
right_frame = tk.Frame(main_frame, bg="#f0f0f0")
tk.Label(right_frame, text="Selected Fees to Pay", font=("Arial", 12, "bold")).pack()
right_tree = ttk.Treeview(right_frame, columns=("Fee", "Cost"), show="headings", height=10, selectmode="extended")
right_tree.heading("Fee", text="Fee Name")
right_tree.heading("Cost", text="Cost")
right_tree.pack()
right_frame.grid(row=0, column=2, padx=10)

# Scholarship Selector
scholarship_frame = tk.Frame(root, bg="#f0f0f0")
tk.Label(scholarship_frame, text="Select Scholarship:", font=("Arial", 12)).pack(side="left", padx=10)

scholarship_var = tk.StringVar()
scholarship_combo = ttk.Combobox(scholarship_frame, textvariable=scholarship_var, state="readonly", width=30)
scholarship_combo['values'] = ["No Scholarship"] + list(scholarships.keys())
scholarship_combo.current(0)
scholarship_combo.pack(side="left")
scholarship_frame.pack(pady=10)

# Move fee function
def move_fees(source_tree, target_tree):
    selected = source_tree.selection()
    for item_id in selected:
        values = source_tree.item(item_id, "values")
        target_tree.insert("", "end", iid=item_id, values=values)
        source_tree.delete(item_id)

# Billing Statement
def pay_now():
    selected = right_tree.get_children()
    if not selected:
        messagebox.showwarning("No Fees", "Please select fees to pay.")
        return

    confirm = messagebox.askyesno("Confirm", "Is this all the fees you will ever pay?")
    if not confirm:
        return

    selected_scholarship = scholarship_var.get()
    discount_amount = scholarships.get(selected_scholarship, 0.0)

    # Get scholarship ID
    # Get scholarship ID, handle 'No Scholarship'
    if selected_scholarship == "No Scholarship":
        scholarship_id = None
        discount_amount = 0.0
    else:
        for row in scholarship_list:
            if row.scholarship_name == selected_scholarship:
                scholarship_id = row.scholarship_id
                break


    selected_items = []
    total_cost = 0
    today = datetime.today().strftime('%Y-%m-%d')

    for item_id in selected:
        values = right_tree.item(item_id)["values"]
        fee_name = values[0]
        cost = float(values[1].replace("$", ""))
        total_cost += cost

        # Get fee_id based on fee_name
        fee_id = None
        for fee in fees:
            if fee["fee_name"] == fee_name:
                fee_id = fee["fee_id"]
                break

        # Insert into billing table
        cursor.execute("""
            INSERT INTO billing (billing_id, student_id, fee_id, scholarship_id, date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            int(f"{student_info['id']}{fee_id}"),  # Simple way to generate unique billing_id
            student_info['id'],
            fee_id,
            scholarship_id,
            today
        ))
        conn.commit()

        selected_items.append({"fee_name": fee_name, "cost": cost})

    final_cost = max(total_cost - discount_amount, 0)
    show_billing_statement(selected_items, total_cost, discount_amount, final_cost, selected_scholarship)


def show_billing_statement(selected_items, total_cost, discount_amount, final_cost, scholarship_name):
    window = tk.Toplevel(root)
    window.title("Billing Statement")
    window.geometry("400x400")

    tk.Label(window, text="BILLING STATEMENT", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(window, text=f"Name: {student_info['name']}").pack()
    tk.Label(window, text=f"Student ID: {student_info['id']}").pack()
    tk.Label(window, text=f"Date: {datetime.today().strftime('%Y-%m-%d')}").pack()
    tk.Label(window, text="").pack()

    tk.Label(window, text="Fees Selected:", font=("Arial", 12, "bold")).pack()
    for item in selected_items:
        tk.Label(window, text=f"- {item['fee_name']}: ${item['cost']:.2f}").pack()

    tk.Label(window, text=f"\nTotal: ${total_cost:.2f}", font=("Arial", 11)).pack()
    if discount_amount > 0:
        tk.Label(window, text=f"Scholarship Applied: {scholarship_name}").pack()
        tk.Label(window, text=f"Discount: -${discount_amount:.2f}").pack()
    else:
        tk.Label(window, text="No Scholarship Applied").pack()

    tk.Label(window, text=f"Final Amount Due: ${final_cost:.2f}", font=("Arial", 12, "bold"), fg="green").pack(pady=10)

# Pay button
tk.Button(root, text="Proceed to Pay", command=pay_now, bg="green", fg="white", font=("Arial", 12), width=20).pack(pady=10)

root.mainloop()
