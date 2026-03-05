import tkinter as tk
import os
import serial
import time

# Tkinter GUI
root = tk.Tk()
root.title("Alice IoMT Device - Temperature Sensor")

tk.Label(root, text="Temperature Sensor Data:").pack(pady=10)
temp_label = tk.Label(root, text="Not connected", fg="red")
temp_label.pack(pady=5)

status_label = tk.Label(root, text="")
status_label.pack(pady=10)

# Serial connection settings
ARDUINO_PORT = 'COM5'  # Change this if your Arduino is on a different port
BAUD_RATE = 9600

def get_temperature():
    """Read temperature from Arduino serial."""
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)  # Wait for Arduino to initialize
        ser.flushInput()
        line = ser.readline().decode('utf-8').strip()
        ser.close()
        if "Temperature:" in line:
            # Extract temperature value
            temp_str = line.split("Temperature: ")[1].split(" ")[0]
            return temp_str + " °C"
        return None
    except serial.SerialException as e:
        return f"Error: {str(e)}"

def update_temperature():
    """Update temperature display."""
    temp = get_temperature()
    if temp:
        if "Error" in temp:
            temp_label.config(text=temp, fg="red")
        else:
            temp_label.config(text=temp, fg="green")
    else:
        temp_label.config(text="No data received", fg="orange")
    root.after(2000, update_temperature)  # Update every 2 seconds

def send_securely():
    """Save temperature data to file and prepare for transmission."""
    temp = get_temperature()
    if temp and "Error" not in temp:
        with open('patient_data.txt', 'w') as f:
            f.write(temp)
        status_label.config(text="Temperature data saved. Run main.py to start transmission.")
    else:
        status_label.config(text="Unable to read temperature data.")

tk.Button(root, text="Send Securely", command=send_securely).pack(pady=10)

def check_status():
    """Check for status updates from file."""
    if os.path.exists('alice_status.txt'):
        with open('alice_status.txt', 'r') as f:
            data = f.read().strip()
        if data == "data encrypted and transmitted":
            status_label.config(text="Data encrypted and transmitted via quantum channel.")
    root.after(100, check_status)

check_status()
update_temperature()  # Start temperature monitoring
root.mainloop()
