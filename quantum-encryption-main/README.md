# Quantum Hybrid QKD

A quantum key distribution system using BB84 protocol with QOTP encryption.

## What is this?

This simulates **quantum cryptography** - a method to securely exchange encryption keys using quantum mechanics. It demonstrates:

- **Secure key generation** between two parties (Alice and Bob)
- **Automatic eavesdropping detection** when someone tries to spy
- **Quantum physics** in action (measuring qubits changes their state)

---

## Installation

### Step 1: Install uv (Package Manager)

**Linux & macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (using pip):**
```bash
pip install uv
```

### Step 2: Clone/Download the Project

```bash
cd /path/to/quantum_hybrid_qkd
```

### Step 3: Install Dependencies

**Using uv (Recommended):**
```bash
uv sync
```

This will:
- Create a virtual environment automatically
- Install all required packages (qiskit, qiskit-aer, qunetsim, numpy)

**Alternative (using pip):**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install qiskit qiskit-aer qunetsim numpy
```

---

## Usage

### Run the Simulator

**Using uv:**
```bash
uv run python main.py
```

**Using activated virtual environment:**
```bash
# After activating venv
python main.py
```

### Choose Your Simulation

You'll see a menu:
```
🌟 QUANTUM HYBRID QKD SIMULATOR 🌟

Choose simulation mode:
  1. Basic QKD (Alice & Bob only - secure)
  2. QKD with Eavesdropper (Eve attacks - detectable)
  3. Exit

Enter choice (1/2/3):
```

**Option 1**: Demonstrates successful quantum key exchange  
**Option 2**: Shows how eavesdropping is automatically detected

---

## What You'll See

### Option 1: Secure Communication ✓
```
Alice: Sending qubit 1
Alice: Qubit 1 sent and acknowledged.
...
Bob: Received qubit 1
Bob: Processed qubit 1, measured: 1
...
Bob's sifted key (10 bits): [1, 0, 1, 1, 0, 1, 0, 1, 0, 1]
Bob: Error rate: 0.00% (0/10 errors)
✓ Secure communication established.
```
**Result:** Alice and Bob successfully share a secret key!

### Option 2: Eavesdropping Detected ⚠️
```
Eve: 🔴 Flipped qubit.
...
Bob's sifted key (8 bits): [1, 0, 0, 1, 1, 0, 1, 0]
Bob: Error rate: 37.50% (3/8 errors)
⚠️  Warning: Eavesdropping detected — aborting key!
```
**Result:** Eve's interference is detected, key is rejected for security!

---

## Project Structure

```
quantum_hybrid_qkd/
├── main.py                  # Main simulation script
├── alice_ui.py              # Tkinter UI for Alice (IoMT device)
├── bob_ui.py                # Tkinter UI for Bob (hospital server)
├── README.md               # This file
├── pyproject.toml          # Dependencies & config
├── patient_data.txt        # IoMT data file (created by Alice UI)
├── src/
│   └── quantum_hybrid_qkd/
│       ├── nodes/          # Alice, Bob, Eve implementations
│       │   ├── alice.py    # Sender (prepares & encrypts qubits)
│       │   ├── bob.py      # Receiver (decrypts & measures)
│       │   └── eve.py      # Eavesdropper (attacks channel)
│       ├── crypto/         # QOTP encryption module
│       │   └── qotp.py
│       └── utils/          # Qiskit-QuNetSim converter
│           └── converter.py
├── tests/                  # Unit tests
└── docs/                   # Detailed architecture docs
    └── ARCH.md
```

---

## How it Works (BB84 + QOTP)

1. **Alice** prepares qubits with random bits and bases
2. **QOTP encryption** adds extra security layer
3. Qubits sent over **quantum channel**
4. **Bob** measures qubits in random bases
5. **QOTP decryption** using shared keys
6. **Classical channel** shares bases and keys
7. **Key sifting** keeps only matching measurements
8. **Error checking** detects any eavesdropping

---

## Technology Stack

- **Qiskit** - IBM's quantum computing framework
- **Qiskit Aer** - Quantum circuit simulator
- **QuNetSim** - Quantum network simulator
- **BB84 Protocol** - Proven quantum key distribution
- **QOTP** - Quantum one-time pad encryption

---

## Why Quantum Cryptography?

| Traditional Crypto | Quantum Crypto |
|-------------------|----------------|
| Can be hacked with powerful computers | **Physics prevents hacking** |
| Don't know if someone listened | **Auto-detects eavesdroppers** |
| Based on math problems | **Based on quantum mechanics** |
| Keys can be intercepted | **Measurement destroys the state** |

---

## IoMT (Internet of Medical Things) Integration

This project now includes Tkinter-based UIs for Alice (IoMT Device) and Bob (Hospital Server) to simulate a realistic IoMT environment with real-time updates.

### IoMT Usage

1. **Launch Bob UI (Hospital Server):**
   ```bash
   uv run python bob_ui.py
   ```
   This opens the hospital server dashboard that waits for secure data transmission.

2. **Launch Alice UI (IoMT Device):**
   ```bash
   uv run python alice_ui.py
   ```
   This opens the IoMT sensor interface for entering health data.

3. **Enter Health Data in Alice UI:**
   - Input patient vitals, ECG readings, or other medical data in the text field.
   - Example: "Heart Rate: 72 BPM, ECG: Normal sinus rhythm, Blood Pressure: 120/80"

4. **Send Securely from Alice UI:**
   - Click "Send Securely" to save the data to `patient_data.txt`.
   - The UI will show "Data saved. Run main.py to start transmission."

5. **Run the QKD Simulation:**
   ```bash
   uv run python main.py
   ```
   - Choose option 1 for secure transmission (no eavesdropper).
   - Choose option 2 to test with eavesdropper (Eve attempts to intercept).

6. **Observe Real-Time UI Updates:**
   - **Alice UI:** Shows "Data encrypted and transmitted via quantum channel." when transmission completes.
   - **Bob UI:** Displays either:
     - "Secure data received: [decrypted health data]" (successful transmission)
     - "Eavesdropper detected! Transmission aborted." (if Eve interfered)
   - Quantum security ensures confidentiality, integrity, and privacy.

### IoMT Security Features

- **Confidentiality:** BB84 + QOTP encryption protects data in transit.
- **Integrity:** Protocol detects any tampering or eavesdropping.
- **Authentication:** Quantum key exchange ensures secure identity.
- **Privacy:** Data flows only through the quantum layer.
- **Real-Time Updates:** UIs update automatically based on simulation results using QuNetSim's message passing.

---

## Web Application Usage (Alternative UI)

This project also includes a Flask-based web interface that provides a comprehensive dashboard for running simulations and viewing real-time logs.

### Step 1: Install Web Dependencies

In addition to the core dependencies, you need to install packages for the web server. With your virtual environment activated, run:

```bash
pip install flask flask-socketio pyserial
```

*Note: If you are using `uv`, you should add `flask`, `flask-socketio`, and `pyserial` to your `pyproject.toml` and run `uv sync`.*

### Step 2: Run the Web Application

Launch the web server with:

```bash
python web_app.py
```

### Step 3: Open the Dashboard

Open your web browser and navigate to `http://127.0.0.1:5000`. You will see the main dashboard with controls to start the simulation and view logs. You can also open separate pages for Alice, Bob, and Eve.

---

## Testing

Run unit tests:

```bash
# Using uv
uv run pytest

# With coverage
uv run pytest --cov=quantum_hybrid_qkd --cov-report=html

# Using activated venv
pytest
```

---

## Troubleshooting

### Issue: "uv: command not found"
**Solution:** Make sure uv is in your PATH. Try closing and reopening your terminal, or manually add it to PATH.

### Issue: Import errors
**Solution:** Make sure dependencies are installed:
```bash
uv sync
```

### Issue: `uv sync` fails with "Querying Python... failed"
**Solution:** This means `uv` cannot find a suitable Python interpreter. Run this to let uv install one:
```bash
uv python install
uv sync
```

### Issue: Network errors in simulation
**Solution:** The quantum network simulator needs time to initialize. The code already includes appropriate delays (2 seconds).

---

## Learn More

For detailed architecture and protocol explanation:
- Read [docs/ARCH.md](docs/ARCH.md)

---

## Quick Example Code

```python
from quantum_hybrid_qkd.nodes import alice_protocol, bob_protocol
from qunetsim.components import Host, Network

# Setup quantum network
network = Network.get_instance()
alice = Host('Alice')
bob = Host('Bob')

# Connect and run protocols
alice.add_connection(bob.host_id)
bob.add_connection(alice.host_id)
network.add_host(alice)
network.add_host(bob)
network.start()

# Execute key distribution
alice_protocol(alice, bob.host_id, key_length=20)
bob_protocol(bob, alice.host_id, key_length=20)
```

---

## System Requirements

- **Python**: 3.9 or higher
- **OS**: Linux, macOS, or Windows
- **RAM**: 2GB minimum
- **Storage**: 500MB for dependencies

---

## License

This project is for educational and research purposes.

---

**Built with quantum mechanics. Secured by the laws of physics.** ⚛️
