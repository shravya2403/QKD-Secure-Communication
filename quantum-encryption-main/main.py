"""
Quantum Hybrid QKD - Main Simulation

Run this to see quantum key distribution in action!
"""

import threading
import time
from qunetsim.components import Host, Network

from src.quantum_hybrid_qkd.nodes.alice import alice_protocol
from src.quantum_hybrid_qkd.nodes.bob import bob_protocol
from src.quantum_hybrid_qkd.nodes.eve import eve_protocol
# --- Simulation Configuration ---
KEY_LENGTH = 128  # The number of qubits to be transmitted


def run_basic_qkd():
    """Run basic QKD with just Alice and Bob (no eavesdropper)."""
    print("\n" + "="*70)
    print("  QUANTUM KEY DISTRIBUTION - Secure Communication")
    print("="*70)
    print("\nSetting up quantum network...")

    # Manually reset the singleton instance to ensure a clean network
    Network._instance = None
    network = Network.get_instance()
    alice = Host('Alice')
    bob = Host('Bob')
    alice_ui = Host('AliceUI')
    bob_ui = Host('BobUI')

    alice.add_connection(bob.host_id)
    bob.add_connection(alice.host_id)

    # Add UI connections so nodes can send status updates
    alice.add_connection(alice_ui.host_id)
    alice_ui.add_connection(alice.host_id)
    bob.add_connection(bob_ui.host_id)
    bob_ui.add_connection(bob.host_id)

    network.add_host(alice)
    network.add_host(bob)
    network.add_host(alice_ui)
    network.add_host(bob_ui)
    network.start()

    alice.start()
    bob.start()
    alice_ui.start()
    bob_ui.start()

    # Monitor UI messages and write to files
    stop_monitoring = threading.Event()
    def monitor_ui():
        while not stop_monitoring.is_set():
            try:
                messages = alice_ui.get_classical('Alice', wait=False)
                for msg in messages:
                    with open('alice_status.txt', 'w') as f:
                        f.write(str(msg.content[1]))
                messages = bob_ui.get_classical('Bob', wait=False)
                for msg in messages:
                    with open('bob_status.txt', 'w') as f:
                        if isinstance(msg.content, dict):
                            f.write(str(msg.content))
                        else:
                            f.write(str(msg.content[1]))
            except Exception as e:
                print(f"Error in monitor_ui: {e}")
            finally:
                time.sleep(0.1)

    threading.Thread(target=monitor_ui, daemon=True).start()

    time.sleep(2)

    print("\nStarting quantum key exchange...\n")
    
    # Run protocols
    # In basic QKD, Bob receives everything from Alice
    bob_thread = threading.Thread(target=bob_protocol, args=(bob, alice.host_id, alice.host_id, KEY_LENGTH))
    alice_thread = threading.Thread(target=alice_protocol, args=(alice, bob.host_id, KEY_LENGTH))

    bob_thread.start()
    time.sleep(0.5)
    alice_thread.start()

    alice_thread.join()
    bob_thread.join()

    time.sleep(5)
    stop_monitoring.set()
    network.stop(True)
    
    print("\n" + "="*70)
    print("  Simulation Complete!")
    print("="*70 + "\n")


def run_qkd_with_eve():
    """Run QKD with Eve trying to eavesdrop."""
    print("\n" + "="*70)
    print("  QUANTUM KEY DISTRIBUTION - With Eavesdropper Attack")
    print("="*70)
    print("\nSetting up quantum network...")
    print("Warning: Eve will attempt to intercept communications!\n")

    # Manually reset the singleton instance to ensure a clean network
    Network._instance = None
    network = Network.get_instance()
    alice = Host('Alice')
    bob = Host('Bob')
    eve = Host('Eve')
    alice_ui = Host('AliceUI')
    bob_ui = Host('BobUI')

    # Setup connections
    # Alice <--> Eve <--> Bob
    # This forces all traffic between Alice and Bob to pass through Eve.
    eve.add_connection(alice.host_id)
    alice.add_connection(eve.host_id)
    bob.add_connection(eve.host_id)
    eve.add_connection(bob.host_id)

    # Add UI connections
    alice.add_connection(alice_ui.host_id)
    alice_ui.add_connection(alice.host_id)
    bob.add_connection(bob_ui.host_id)
    bob_ui.add_connection(bob.host_id)

    network.add_host(alice)
    network.add_host(bob)
    network.add_host(eve)
    network.add_host(alice_ui)
    network.add_host(bob_ui)

    network.start()
    alice.start()
    bob.start()
    eve.start()
    alice_ui.start()
    bob_ui.start()

    # Monitor UI messages and write to files
    stop_monitoring = threading.Event()
    def monitor_ui():
        while not stop_monitoring.is_set():
            try:
                messages = alice_ui.get_classical('Alice', wait=False)
                for msg in messages:
                    with open('alice_status.txt', 'w') as f:
                        f.write(str(msg.content[1]))
                messages = bob_ui.get_classical('Bob', wait=False)
                for msg in messages:
                    with open('bob_status.txt', 'w') as f:
                        if isinstance(msg.content, dict):
                            f.write(str(msg.content))
                        else:
                            f.write(str(msg.content[1]))
            except Exception as e:
                print(f"Error in monitor_ui: {e}")
            finally:
                time.sleep(0.1)

    threading.Thread(target=monitor_ui, daemon=True).start()

    time.sleep(2)

    print("Starting quantum key exchange...\n")
    
    # Create a stop event for gracefully shutting down Eve's threads
    stop_event = threading.Event()

    # Run protocols
    # With Eve, Bob receives everything from Eve
    bob_thread = threading.Thread(target=bob_protocol, args=(bob, alice.host_id, eve.host_id, KEY_LENGTH))
    alice_thread = threading.Thread(target=alice_protocol, args=(alice, eve.host_id, KEY_LENGTH)) # Alice sends to Eve
    eve_thread = threading.Thread(target=eve_protocol, args=(eve, alice.host_id, bob.host_id, stop_event))

    bob_thread.start()
    eve_thread.start()
    time.sleep(0.5)
    alice_thread.start()

    alice_thread.join()
    bob_thread.join()

    # Signal Eve's threads to stop and wait for them to finish
    stop_event.set()
    eve_thread.join()

    time.sleep(5)
    stop_monitoring.set()
    network.stop(True)
    
    print("\n" + "="*70)
    print("  Simulation Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\nQUANTUM HYBRID QKD SIMULATOR\n")
    print("Running QKD with Eavesdropper simulation...\n")
    run_qkd_with_eve()