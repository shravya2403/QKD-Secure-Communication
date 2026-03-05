"""Alice node implementation - Sender in QKD protocol."""

import random
import time
import os
import json
from typing import Any
from qiskit import QuantumCircuit
from qunetsim.objects import Qubit

from ..crypto.classical_auth import (
    build_authenticated_payload,
    derive_auth_key,
    generate_challenge,
    generate_commitment,
    generate_nonce,
    generate_response,
    generate_session_id,
    public_value,
    verify_proof,
)
from ..crypto.qotp import qotp_encrypt
from ..utils.converter import apply_qiskit_gates_to_qunetsim_qubit


def _wait_for_tag(alice, peer_id: str, tag: str, timeout_s: float = 15.0) -> dict[str, Any]:
    """Wait until a dictionary classical message with the expected tag arrives."""
    start = time.time()
    while time.time() - start < timeout_s:
        messages = alice.get_classical(peer_id, wait=False)
        for msg in messages:
            content = msg.content
            if isinstance(content, dict) and content.get("tag") == tag:
                return content
        time.sleep(0.1)
    raise TimeoutError(f"Alice: Timed out waiting for '{tag}'")


def alice_protocol(alice, bob_id, key_length=20):
    """
    Execute Alice's role in the BB84 QKD protocol with QOTP encryption.

    Args:
        alice: QuNetSim Host object representing Alice
        bob_id: Host ID of Bob
        key_length: Number of qubits to transmit (default: 20)
    """
    session_id = generate_session_id()
    nonce_a = generate_nonce()
    alice.send_classical(
        bob_id,
        {
            "tag": "auth_init",
            "session_id": session_id,
            "initiator": "Alice",
            "nonce_a": nonce_a,
        },
        await_ack=True,
    )
    print("Alice: Sent authentication init.")

    # Track sequence numbers for authenticated packets
    seq_counter = 0
    auth_ack = _wait_for_tag(alice, bob_id, "auth_ack")
    if auth_ack.get("session_id") != session_id:
        raise RuntimeError("Alice: Session mismatch in auth_ack")
    nonce_b = auth_ack["nonce_b"]
    print("Alice: Received auth acknowledgement.")

    # Alice proves identity to Bob.
    r_a, t_a = generate_commitment()
    alice.send_classical(
        bob_id,
        {
            "tag": "zkp_commit",
            "session_id": session_id,
            "prover": "Alice",
            "commitment": str(t_a),
        },
        await_ack=True,
    )
    challenge_msg = _wait_for_tag(alice, bob_id, "zkp_challenge")
    challenge_a = int(challenge_msg["challenge"])
    response_a = generate_response("Alice", r_a, challenge_a)
    alice.send_classical(
        bob_id,
        {
            "tag": "zkp_response",
            "session_id": session_id,
            "prover": "Alice",
            "response": str(response_a),
        },
        await_ack=True,
    )
    print("Alice: Completed proof of identity for Bob.")

    # Bob proves identity to Alice.
    bob_commit_msg = _wait_for_tag(alice, bob_id, "zkp_commit")
    if bob_commit_msg.get("prover") != "Bob":
        raise RuntimeError("Alice: Unexpected prover in Bob commitment")
    bob_commitment = int(bob_commit_msg["commitment"])
    challenge_b = generate_challenge(
        session_id=session_id,
        nonce_a=nonce_a,
        nonce_b=nonce_b,
        prover_id="Bob",
        verifier_id="Alice",
        commitment=bob_commitment,
    )
    alice.send_classical(
        bob_id,
        {
            "tag": "zkp_challenge",
            "session_id": session_id,
            "prover": "Bob",
            "challenge": str(challenge_b),
        },
        await_ack=True,
    )
    bob_response_msg = _wait_for_tag(alice, bob_id, "zkp_response")
    bob_response = int(bob_response_msg["response"])
    if not verify_proof(
        public_y=public_value("Bob"),
        commitment=bob_commitment,
        challenge=challenge_b,
        response=bob_response,
    ):
        raise RuntimeError("Alice: Bob identity proof failed")
    print("Alice: Bob identity proof verified.")

    auth_key = derive_auth_key(session_id, nonce_a, nonce_b)
    print("Alice: Derived classical-channel authentication key.")

    # Check for IoMT data file
    if os.path.exists('patient_data.txt'):
        with open('patient_data.txt', 'r') as f:
            data = f.read().strip()
        # Convert text to bits
        bits = []
        for char in data:
            bin_str = format(ord(char), '08b')
            bits.extend([int(b) for b in bin_str])
        # Adjust to key_length: truncate if longer, pad with 0s if shorter
        if len(bits) > key_length:
            bits = bits[:key_length]
        else:
            bits.extend([0] * (key_length - len(bits)))
        print(f"Alice: Loaded IoMT data bits: {bits}")
    else:
        # Generate random bits for standard QKD
        bits = [random.randint(0, 1) for _ in range(key_length)]
        print(f"Alice: Generated original bits: {bits}")

    bases = [random.randint(0, 1) for _ in range(key_length)]  # 0=Z, 1=X

    # Load QOTP keys from previous run or use default
    qotp_keys_file = 'qotp_keys.txt'
    if os.path.exists(qotp_keys_file):
        with open(qotp_keys_file, 'r') as f:
            secret_key = json.load(f)
        # Derive QOTP keys from previous secret key
        qotp_keys = [[secret_key[i % len(secret_key)], secret_key[(i + 1) % len(secret_key)]] for i in range(key_length)]
        print(f"Alice: Loaded QOTP keys from previous run")
    else:
        # For first run, use fixed keys (no encryption)
        qotp_keys = [[0, 0] for _ in range(key_length)]
        print(f"Alice: Using default QOTP keys (no encryption)")

    # Prepare and send qubits
    for i in range(key_length):
        # Create quantum circuit
        qc = QuantumCircuit(1)
        
        # Encode bit
        if bits[i] == 1:
            qc.x(0)
        
        # Apply basis
        if bases[i] == 1:
            qc.h(0)
        
        # Apply QOTP encryption
        qotp_encrypt(qc, 0, qotp_keys[i])

        # Convert to QuNetSim qubit
        qubit = Qubit(alice)
        apply_qiskit_gates_to_qunetsim_qubit(qc, qubit)

        print(f"Alice: Sending qubit {i+1}")
        alice.send_qubit(bob_id, qubit, await_ack=True)
        print(f"Alice: Qubit {i+1} sent and acknowledged.")

    # Send authenticated classical information.
    bases_packet = build_authenticated_payload(
        auth_key=auth_key,
        session_id=session_id,
        sender_id="Alice",
        msg_type="bases",
        seq=seq_counter,
        payload=bases,
    )
    alice.send_classical(bob_id, bases_packet, await_ack=True)
    print("Alice: Authenticated bases sent.")
    time.sleep(0.5)
    seq_counter += 1

    bits_packet = build_authenticated_payload(
        auth_key=auth_key,
        session_id=session_id,
        sender_id="Alice",
        msg_type="bits",
        seq=seq_counter,
        payload=bits,
    )
    alice.send_classical(bob_id, bits_packet, await_ack=True)
    print("Alice: Authenticated bits sent.")
    time.sleep(0.5)
    seq_counter += 1
    # Notify Alice UI
    alice.send_classical('AliceUI', ("status", "data encrypted and transmitted"), await_ack=False)
    print("Alice: Notified Alice UI.")
