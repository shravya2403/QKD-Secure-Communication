import tkinter as tk
import os
import ast

# Tkinter GUI
root = tk.Tk()
root.title("Bob Hospital Server")

status_label = tk.Label(root, text="Waiting for secure data transmission...")
status_label.pack(pady=20)

def check_status():
    """Check for status updates from file."""
    if os.path.exists('bob_status.txt'):
        with open('bob_status.txt', 'r') as f:
            data_str = f.read().strip()
        try:
            data = ast.literal_eval(data_str)
            if data['status'] == 'success':
                status_label.config(text=f"Secure data received: {data['data']}")
            elif data['status'] == 'eavesdropped':
                status_label.config(text="Key aborted. No data received. Start the process again for secure communication.")
        except:
            pass
    root.after(100, check_status)

check_status()
root.mainloop()
