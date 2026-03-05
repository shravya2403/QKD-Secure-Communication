"""
IoMT Interface - Tkinter GUI for Secure Health Data Transmission

This GUI allows users to input health data (e.g., ECG readings) and securely transmit
it through the Quantum Hybrid QKD system using BB84 + QOTP protocols.
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import os
import threading

def run_simulation():
    """Run the QKD simulation and display output."""
    data = data_entry.get("1.0", tk.END).strip()
    if not data:
        messagebox.showerror("Error", "Please enter some health data.")
        return

    mode = mode_var.get()
    if not mode:
        messagebox.showerror("Error", "Please select a simulation mode.")
        return

    # Save data to file
    with open('patient_data.txt', 'w') as f:
        f.write(data)

    # Disable button
    send_button.config(state=tk.DISABLED)
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, "Running simulation...\n")

    # Run simulation in thread to avoid freezing GUI
    def simulate():
        try:
            # Run the simulation
            proc = subprocess.Popen(['uv', 'run', 'python', 'main.py'],
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  text=True)
            # Send the mode choice
            proc.stdin.write(f"{mode}\n")
            proc.stdin.flush()
            # Read output
            output, _ = proc.communicate()
            # Update GUI
            root.after(0, lambda: output_text.delete(1.0, tk.END))
            root.after(0, lambda: output_text.insert(tk.END, output))
        except Exception as e:
            root.after(0, lambda: output_text.insert(tk.END, f"Error: {e}"))
        finally:
            root.after(0, lambda: send_button.config(state=tk.NORMAL))

    threading.Thread(target=simulate, daemon=True).start()

# Create main window
root = tk.Tk()
root.title("IoMT Secure Data Transmission")
root.geometry("600x600")

# Instructions
instructions = tk.Label(root, text="Enter IoMT Health Data (e.g., ECG readings, patient vitals):",
                       font=("Arial", 12), wraplength=580, justify="left")
instructions.pack(pady=10)

# Text entry for data
data_entry = tk.Text(root, height=6, width=60, font=("Arial", 10))
data_entry.pack(pady=10)
data_entry.insert(tk.END, "Example: Heart Rate: 72 BPM, ECG: Normal sinus rhythm")

# Mode selection
mode_frame = tk.Frame(root)
mode_frame.pack(pady=10)
tk.Label(mode_frame, text="Simulation Mode:", font=("Arial", 12)).pack(side=tk.LEFT)
mode_var = tk.StringVar()
tk.Radiobutton(mode_frame, text="Secure (Alice & Bob only)", variable=mode_var, value="1").pack(side=tk.LEFT)
tk.Radiobutton(mode_frame, text="With Eavesdropper (Eve)", variable=mode_var, value="2").pack(side=tk.LEFT)

# Send button
send_button = tk.Button(root, text="Send Securely", command=run_simulation,
                       font=("Arial", 14), bg="green", fg="white")
send_button.pack(pady=10)

# Output display
output_label = tk.Label(root, text="Simulation Output:", font=("Arial", 12))
output_label.pack(pady=5)
output_text = scrolledtext.ScrolledText(root, height=15, width=70, font=("Courier", 10))
output_text.pack(pady=10)

# Run the GUI
root.mainloop()
