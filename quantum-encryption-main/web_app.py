from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import threading
import time
import os
import serial
import sys
import ast
from io import StringIO
from contextlib import redirect_stdout
from main import run_basic_qkd, run_qkd_with_eve

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for simulation control
simulation_running = False
simulation_thread = None
logs = []
eve_active = False
global_qber = 0.0
simulation_mode = 'basic'

# Serial connection settings for temperature sensor
# Check Device Manager → Ports to find the correct COM port
ARDUINO_PORT = 'COM5'  # Change this to your Arduino's actual COM port
BAUD_RATE = 9600

latest_temperature = None

def log_message(message):
    """Add message to logs and emit to all clients."""
    timestamp = time.strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    logs.append(log_entry)
    socketio.emit('log_update', {'log': log_entry})

def get_temperature():
    """Read temperature from Arduino serial (same logic as alice_ui.py)."""
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)  # Wait for Arduino to initialize (same as alice_ui.py)
        ser.flushInput()
        line = ser.readline().decode('utf-8').strip()
        ser.close()  # Close immediately after reading (same as alice_ui.py)

        if "Temperature:" in line:
            # Extract temperature value
            temp_str = line.split("Temperature: ")[1].split(" ")[0]
            return temp_str + " °C"
        return None
    except serial.SerialException as e:
        return f"Error: {str(e)}"

def sensor_reading_thread():
    """Background thread using same logic as alice_ui.py."""
    global latest_temperature

    log_message("Sensor: Starting temperature monitoring thread")
    connection_established = False
    consecutive_successes = 0

    while True:
        try:
            # Try Arduino using same method as alice_ui.py
            temp = get_temperature()

            if temp and "Error" not in temp:
                latest_temperature = temp
                consecutive_successes += 1

                # Log success only during initial connection phase
                if not connection_established and consecutive_successes >= 2:
                    log_message("Sensor: Arduino connection established successfully")
                    connection_established = True
                # Don't log routine successful readings once connected

            elif temp and "Error" in temp:
                latest_temperature = None
                consecutive_successes = 0
                connection_established = False
                # Don't log Arduino errors to keep logs clean
            else:
                # No data received
                latest_temperature = None
                consecutive_successes = 0
                connection_established = False
                # Don't log no data messages to keep logs clean

            time.sleep(2)  # Update every 2 seconds (same as alice_ui.py)

        except Exception as e:
            # Don't log unexpected errors to keep logs clean
            latest_temperature = None
            consecutive_successes = 0
            connection_established = False
            time.sleep(2)

# Start sensor thread
threading.Thread(target=sensor_reading_thread, daemon=True).start()

def run_simulation_with_logs(mode):
    """Run simulation and capture logs."""
    global simulation_running, eve_active, global_qber

    simulation_running = True

    try:
        if mode == 'basic':
            log_message("Starting Basic QKD Simulation (Alice & Bob only)")
            log_message("Setting up quantum network...")

            # Capture stdout from the simulation
            f = StringIO()
            with redirect_stdout(f):
                run_basic_qkd()
            output = f.getvalue()
            # Parse and log the output
            for line in output.strip().split('\n'):
                if line.strip():
                    log_message(line.strip())

            log_message("Basic QKD Simulation completed successfully")
        elif mode == 'with_eve':
            log_message("Starting QKD Simulation with Eavesdropper")
            log_message("Setting up quantum network with Eve...")

            # Capture stdout from the simulation
            f = StringIO()
            with redirect_stdout(f):
                run_qkd_with_eve()
            output = f.getvalue()
            # Parse and log the output
            for line in output.strip().split('\n'):
                if line.strip():
                    log_message(line.strip())

            log_message("QKD with Eve Simulation completed")
    except Exception as e:
        log_message(f"Simulation error: {str(e)}")
    finally:
        simulation_running = False
        socketio.emit('simulation_complete')
        # Emit status updates for all clients after simulation
        socketio.emit('refresh_status')

@app.route('/')
def index():
    """Main dashboard."""
    return render_template('index.html')

@app.route('/alice')
def alice():
    """Alice's interface."""
    return render_template('alice.html')

@app.route('/bob')
def bob():
    """Bob's interface."""
    return render_template('bob.html')

@app.route('/eve')
def eve():
    """Eve's interface."""
    return render_template('eve.html')

@app.route('/patient_data.txt')
def serve_patient_data():
    """Serve patient data file."""
    return send_file('patient_data.txt')

@socketio.on('start_simulation')
def handle_start_simulation(data):
    """Handle simulation start request."""
    global simulation_thread, eve_active

    mode = data.get('mode')
    eve_active = data.get('eve_active', False)

    if simulation_running:
        emit('error', {'message': 'Simulation already running'})
        return

    if mode not in ['basic', 'with_eve']:
        emit('error', {'message': 'Invalid simulation mode'})
        return
        
    # Clear previous status files to prevent UI from showing stale data
    if os.path.exists('bob_status.txt'):
        os.remove('bob_status.txt')
    if os.path.exists('alice_status.txt'):
        os.remove('alice_status.txt')
    log_message("System: Cleared previous session data.")

    simulation_thread = threading.Thread(target=run_simulation_with_logs, args=(mode,))
    simulation_thread.start()

    emit('simulation_started', {'mode': mode, 'eve_active': eve_active}, broadcast=True)

@socketio.on('send_transmission')
def handle_send_transmission():
    """Handle Alice sending transmission."""
    temp = latest_temperature
    if temp:
        with open('patient_data.txt', 'w') as f:
            f.write(temp)
        log_message(f"Alice: Temperature data sent - {temp}")
        emit('transmission_sent', {'data': temp})
    else:
        # Write dummy data for testing
        dummy_temp = "25.5 °C"
        with open('patient_data.txt', 'w') as f:
            f.write(dummy_temp)
        log_message(f"Alice: Dummy temperature data sent - {dummy_temp}")
        emit('transmission_sent', {'data': dummy_temp})

@socketio.on('get_temperature')
def handle_get_temperature():
    """Get current temperature reading."""
    emit('temperature_update', {'temperature': latest_temperature})

@socketio.on('get_status')
def handle_get_status(data):
    """Get status for Alice or Bob."""
    node = data.get('node')

    if node == 'alice':
        if os.path.exists('alice_status.txt'):
            with open('alice_status.txt', 'r') as f:
                status = f.read().strip()
            emit('status_update', {'status': status})
        else:
            emit('status_update', {'status': 'No status available'})

    elif node == 'bob':
        if os.path.exists('bob_status.txt'):
            with open('bob_status.txt', 'r') as f:
                content = f.read().strip()
            
            # Try to parse the content if it looks like a dictionary (e.g., "{'status': 'success'}")
            try:
                if content.startswith('{') and content.endswith('}'):
                    data_dict = ast.literal_eval(content)
                    status = data_dict.get('status', content)
                    
                    # If QBER is present in the data, emit it to update the UI meter
                    if 'qber' in data_dict:
                        emit('qber_update', {'qber': float(data_dict['qber'])})
                    emit('status_update', data_dict)
                    return
                else:
                    status = content
            except Exception:
                status = content
                
            emit('status_update', {'status': status})
        else:
            emit('status_update', {'status': 'No status available'})

@socketio.on('toggle_eve')
def handle_toggle_eve(data):
    """Toggle Eve's active status."""
    global eve_active
    eve_active = data.get('active', False)
    status = "activated" if eve_active else "deactivated"
    log_message(f"Eve: Eavesdropper {status}")
    emit('eve_status_changed', {'active': eve_active}, broadcast=True)

@socketio.on('get_eve_status')
def handle_get_eve_status():
    """Get current Eve status."""
    emit('eve_status_response', {'active': eve_active})

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('logs_history', {'logs': logs[-50:]})  # Send last 50 logs
    emit('qber_update', {'qber': global_qber})  # Send current QBER

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
