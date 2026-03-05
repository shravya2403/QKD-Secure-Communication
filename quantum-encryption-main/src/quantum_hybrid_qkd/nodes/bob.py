"""Bob node implementation - Receiver in QKD protocol."""

import random
import time
import os
import json
from typing import Any

from ..crypto.classical_auth import (
    derive_auth_key,
    generate_challenge,
    generate_commitment,
    generate_nonce,
    generate_response,
    public_value,
    verify_authenticated_payload,
    verify_proof,
)

EAVESDROPPING_THRESHOLD = 0.11
  # Standard QBER threshold for BB84


def _wait_for_tag(bob, peer_id: str, tag: str, timeout_s: float = 20.0) -> dict[str, Any]:
    """Wait until a dictionary classical message with the expected tag arrives."""
    start = time.time()
    while time.time() - start < timeout_s:
        messages = bob.get_classical(peer_id, wait=False)
        for msg in messages:
            content = msg.content
            if isinstance(content, dict) and content.get("tag") == tag:
                return content
        time.sleep(0.1)
    raise TimeoutError(f"Bob: Timed out waiting for '{tag}'")


def bob_protocol(bob, alice_id, sender_id, key_length=20):
    """
    Execute Bob's role in the BB84 QKD protocol with QOTP decryption.
    
    Args:
        bob: QuNetSim Host object representing Bob
        alice_id: Host ID of Alice (for classical messages)
        sender_id: Host ID of the node sending qubits and classical data (Alice or Eve)
        key_length: Number of qubits to receive (default: 20)
    """
    print("Bob: Protocol started.")

    try:
        auth_init = _wait_for_tag(bob, sender_id, "auth_init")
        session_id = auth_init["session_id"]
        nonce_a = auth_init["nonce_a"]
        nonce_b = generate_nonce()
        bob.send_classical(
            sender_id,
            {
                "tag": "auth_ack",
                "session_id": session_id,
                "responder": "Bob",
                "nonce_b": nonce_b,
            },
            await_ack=True,
        )
        print("Bob: Sent authentication acknowledgement.")

        # Verify Alice's identity proof.
        alice_commit_msg = _wait_for_tag(bob, sender_id, "zkp_commit")
        if alice_commit_msg.get("prover") != "Alice":
            raise RuntimeError("Bob: Unexpected prover in Alice commitment")
        alice_commitment = int(alice_commit_msg["commitment"])
        challenge_a = generate_challenge(
            session_id=session_id,
            nonce_a=nonce_a,
            nonce_b=nonce_b,
            prover_id="Alice",
            verifier_id="Bob",
            commitment=alice_commitment,
        )
        bob.send_classical(
            sender_id,
            {
                "tag": "zkp_challenge",
                "session_id": session_id,
                "prover": "Alice",
                "challenge": str(challenge_a),
            },
            await_ack=True,
        )
        alice_response_msg = _wait_for_tag(bob, sender_id, "zkp_response")
        alice_response = int(alice_response_msg["response"])
        if not verify_proof(
            public_y=public_value("Alice"),
            commitment=alice_commitment,
            challenge=challenge_a,
            response=alice_response,
        ):
            raise RuntimeError("Bob: Alice identity proof failed")
        print("Bob: Alice identity proof verified.")

        # Bob proves identity to Alice.
        r_b, t_b = generate_commitment()
        bob.send_classical(
            sender_id,
            {
                "tag": "zkp_commit",
                "session_id": session_id,
                "prover": "Bob",
                "commitment": str(t_b),
            },
            await_ack=True,
        )
        challenge_msg = _wait_for_tag(bob, sender_id, "zkp_challenge")
        challenge_b = int(challenge_msg["challenge"])
        response_b = generate_response("Bob", r_b, challenge_b)
        bob.send_classical(
            sender_id,
            {
                "tag": "zkp_response",
                "session_id": session_id,
                "prover": "Bob",
                "response": str(response_b),
            },
            await_ack=True,
        )
        print("Bob: Completed proof of identity for Alice.")
    except (TimeoutError, RuntimeError, KeyError, ValueError) as auth_err:
        print(f"Bob: Classical authentication failed: {auth_err}")
        bob.send_classical(
            "BobUI",
            {"status": "auth_failed", "reason": str(auth_err)},
            await_ack=False,
        )
        return

    auth_key = derive_auth_key(session_id, nonce_a, nonce_b)
    print("Bob: Derived classical-channel authentication key.")
    
    # Generate random measurement bases
    bob_bases = [random.randint(0, 1) for _ in range(key_length)]

    # Load QOTP keys from previous run or use default
    qotp_keys_file = 'qotp_keys.txt'
    if os.path.exists(qotp_keys_file):
        with open(qotp_keys_file, 'r') as f:
            secret_key = json.load(f)
        # Derive QOTP keys from previous secret key
        qotp_keys = [[secret_key[i % len(secret_key)], secret_key[(i + 1) % len(secret_key)]] for i in range(key_length)]
        print(f"Bob: Loaded QOTP keys from previous run")
    else:
        # For first run, use fixed keys (no encryption)
        qotp_keys = [[0, 0] for _ in range(key_length)]
        print(f"Bob: Using default QOTP keys (no encryption)")

    # Wait for authenticated classical messages (expecting 2: bases, bits).
    try:
        classical_data = {}
        required_tags = {"bases", "bits"}
        while not required_tags.issubset(classical_data.keys()):
            messages = bob.get_classical(sender_id, wait=False)
            for msg in messages:
                content = msg.content
                if not isinstance(content, dict):
                    continue
                if content.get("tag") != "auth_payload":
                    continue

                seq = content.get("seq")
                if not isinstance(seq, int):
                    raise RuntimeError("Invalid classical packet (invalid_sequence)")

                # Validate sender/session/MAC using the packet's own seq so
                # harmless duplicates/out-of-order arrivals don't abort.
                ok, reason = verify_authenticated_payload(
                    packet=content,
                    auth_key=auth_key,
                    session_id=session_id,
                    expected_sender=alice_id,
                    expected_seq=seq,
                )
                if not ok:
                    raise RuntimeError(f"Invalid classical packet ({reason})")

                msg_type = content.get("msg_type")
                if msg_type not in required_tags:
                    continue

                # Keep first valid copy per type; ignore duplicate replays.
                if msg_type not in classical_data:
                    classical_data[msg_type] = content["payload"]

            print(f"Bob: Waiting for classical messages, received {len(classical_data)}/2 so far")
            time.sleep(0.5)
        print("Bob: Received all classical messages.")
    except RuntimeError as packet_err:
        print(f"Bob: Classical authentication failed: {packet_err}")
        bob.send_classical(
            "BobUI",
            {"status": "auth_failed", "reason": str(packet_err)},
            await_ack=False,
        )
        return

    alice_bases = classical_data.get("bases")
    alice_bits = classical_data.get("bits")
    if alice_bases is None or alice_bits is None:
        raise ValueError("Bob did not receive all required classical information.")

    sifted_bits = []

    # Receive and measure qubits
    for i in range(key_length):
        print(f"Bob: Waiting for qubit {i+1}")
        # Get the next qubit from the specified sender.
        qubit = bob.get_data_qubit(sender_id, wait=-1)
        
        if qubit:
            print(f"Bob: Received qubit {i+1}")

            # Simulate realistic channel noise (e.g., 3% chance of an error)
            if random.random() < 0.03:
                if random.random() < 0.5:
                    qubit.X() # bit-flip error
                    print("Bob: (Noise caused a bit-flip)")
                else:
                    qubit.Z() # phase-flip error
                    print("Bob: (Noise caused a phase-flip)")

            # 1. Apply QOTP decryption FIRST (in REVERSE order of encryption: Z then X)
            if qotp_keys[i][1] == 1: # Apply Z key first
                qubit.Z()
            if qotp_keys[i][0] == 1: # Apply X key second
                qubit.X()

            # 2. Apply measurement basis
            if bob_bases[i] == 1: # If Bob chooses X-basis
                qubit.H()

            # Measure the qubit
            measured_bit = qubit.measure()
            sifted_bits.append(measured_bit)
            print(f"Bob: Processed qubit {i+1}, measured: {measured_bit}")
        else:
            print(f"Bob: No qubit received for qubit {i+1}, retrying...")
            continue # Skip this bit if qubit was not received

    # Sift key - keep only bits where bases match
    # On average, this will be ~50% of the original key length.
    secret_key = [bit for bit, a_b, b_b in zip(sifted_bits, alice_bases, bob_bases) if a_b == b_b]
    print(f"Bob's sifted key ({len(secret_key)} bits): {secret_key}")

    # Check for eavesdropping - compare only the sifted bits
    # Bob uses Alice's publicly broadcasted bits ONLY for this error check.
    # The actual 'secret_key' comes from his own private measurements.
    sifted_alice_bits = [a_bit for a_bit, a_b, b_b in zip(alice_bits, alice_bases, bob_bases) if a_b == b_b]
    errors = sum([a != b for a, b in zip(sifted_alice_bits, secret_key)])
    error_rate = errors / len(secret_key) if len(secret_key) > 0 else 0

    print(f"Bob: Error rate: {error_rate:.2%} ({errors}/{len(secret_key)} errors)")
    
    if error_rate > EAVESDROPPING_THRESHOLD:
        print("⚠️  Warning: Eavesdropping detected — aborting key!")
        print("Bob: IoMT data transmission aborted due to eavesdropping.")
        # Notify Bob UI
        bob.send_classical(
            "BobUI",
            {
                "status": "eavesdropped",
                "qber": error_rate * 100,
                "message": "Key generation aborted due to eavesdropping detection",
            },
            await_ack=False,
        )
        print("Bob: Notified Bob UI of eavesdropping.")
    else:
        print("✓ Secure communication established.")
        # Save the sifted key for next run's QOTP keys
        with open(qotp_keys_file, 'w') as f:
            json.dump(secret_key, f)
        print("Bob: Saved sifted key for next run's QOTP encryption.")
        # Decode and display IoMT data if present
        decoded = ''
        if alice_bits:
            for i in range(0, len(alice_bits) - (len(alice_bits) % 8), 8):
                byte = alice_bits[i:i+8]
                char_code = int(''.join(map(str, byte)), 2)
                if 0 <= char_code <= 127 or char_code == 176:
                    decoded += chr(char_code)
            decoded = decoded.rstrip('\x00')  # Remove trailing null bytes
            if decoded:
                print(f"Bob: Received IoMT data: '{decoded}'")
            else:
                print("Bob: No valid IoMT data received.")
        # Notify Bob UI
        bob.send_classical(
            "BobUI",
            {
                "status": "success",
                "qber": error_rate * 100,
                "received_data": decoded if decoded else None,
                "message": "Data received and verified successfully",
            },
            await_ack=False,
        )
        print("Bob: Notified Bob UI of successful transmission.")

    time.sleep(7)
    print("Bob: Protocol finished.")
