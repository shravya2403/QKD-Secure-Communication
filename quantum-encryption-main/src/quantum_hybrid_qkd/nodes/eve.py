"""Eve node implementation - Eavesdropper in QKD protocol."""

import random
import threading
import time

from qunetsim.objects import Qubit


def _classical_forwarding_thread(eve, alice_id, bob_id, stop_event):
    """
    Forward classical traffic in both directions while Eve is active.
    """
    while not stop_event.is_set():
        forwarded = False

        # Forward Alice -> Bob
        alice_messages = eve.get_classical(alice_id, wait=False)
        if alice_messages:
            for msg in alice_messages:
                eve.send_classical(bob_id, msg.content, await_ack=True)
                forwarded = True

        # Forward Bob -> Alice for challenge/response style protocols.
        bob_messages = eve.get_classical(bob_id, wait=False)
        if bob_messages:
            for msg in bob_messages:
                eve.send_classical(alice_id, msg.content, await_ack=True)
                forwarded = True

        if not forwarded:
            time.sleep(0.1)


def eve_protocol(eve, alice_id, bob_id, stop_event):
    """
    Execute Eve's role as an eavesdropper attempting to intercept quantum communication.

    Args:
        eve: QuNetSim Host object representing Eve
        alice_id: Host ID of Alice
        bob_id: Host ID of Bob
        stop_event: A threading.Event to signal when to stop.
    """
    print("Eve: Protocol started.")

    forwarding_thread = threading.Thread(
        target=_classical_forwarding_thread,
        args=(eve, alice_id, bob_id, stop_event),
    )
    forwarding_thread.daemon = True
    forwarding_thread.start()

    while not stop_event.is_set():
        qubit = eve.get_data_qubit(alice_id, wait=False)

        if qubit:
            eve_basis = random.randint(0, 1)
            if eve_basis == 1:
                qubit.H()

            measured_bit = qubit.measure()
            print(f"Eve: Intercepted and measured a qubit, got {measured_bit}")

            new_qubit = Qubit(eve)
            if measured_bit == 1:
                new_qubit.X()
            if eve_basis == 1:
                new_qubit.H()

            eve.send_qubit(bob_id, new_qubit, await_ack=True)
            print("Eve: Sent new qubit to Bob.")
        else:
            time.sleep(0.1)
