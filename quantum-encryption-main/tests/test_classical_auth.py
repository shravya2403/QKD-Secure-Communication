"""Tests for classical authentication helpers."""

from quantum_hybrid_qkd.crypto.classical_auth import (
    build_authenticated_payload,
    derive_auth_key,
    generate_challenge,
    generate_commitment,
    generate_nonce,
    generate_response,
    generate_session_id,
    public_value,
    verify_authenticated_payload,
    verify_proof,
)


def test_schnorr_proof_verifies_for_alice():
    """Alice's generated proof should verify with Alice's public value."""
    session_id = generate_session_id()
    nonce_a = generate_nonce()
    nonce_b = generate_nonce()
    r, commitment = generate_commitment()
    challenge = generate_challenge(session_id, nonce_a, nonce_b, "Alice", "Bob", commitment)
    response = generate_response("Alice", r, challenge)

    assert verify_proof(public_value("Alice"), commitment, challenge, response)


def test_schnorr_proof_rejects_tampered_response():
    """Tampering with the response must invalidate the proof."""
    session_id = generate_session_id()
    nonce_a = generate_nonce()
    nonce_b = generate_nonce()
    r, commitment = generate_commitment()
    challenge = generate_challenge(session_id, nonce_a, nonce_b, "Alice", "Bob", commitment)
    response = generate_response("Alice", r, challenge)

    assert not verify_proof(public_value("Alice"), commitment, challenge, response + 1)


def test_authenticated_payload_verifies():
    """A valid packet should pass sender/session/sequence/MAC checks."""
    session_id = generate_session_id()
    nonce_a = generate_nonce()
    nonce_b = generate_nonce()
    auth_key = derive_auth_key(session_id, nonce_a, nonce_b)
    packet = build_authenticated_payload(auth_key, session_id, "Alice", "bases", 0, [0, 1, 1])

    ok, reason = verify_authenticated_payload(
        packet=packet,
        auth_key=auth_key,
        session_id=session_id,
        expected_sender="Alice",
        expected_seq=0,
    )
    assert ok
    assert reason == "ok"


def test_authenticated_payload_rejects_tampering():
    """Changing payload after signing must fail MAC verification."""
    session_id = generate_session_id()
    nonce_a = generate_nonce()
    nonce_b = generate_nonce()
    auth_key = derive_auth_key(session_id, nonce_a, nonce_b)
    packet = build_authenticated_payload(auth_key, session_id, "Alice", "bits", 1, [1, 0, 1])
    packet["payload"] = [1, 1, 1]

    ok, reason = verify_authenticated_payload(
        packet=packet,
        auth_key=auth_key,
        session_id=session_id,
        expected_sender="Alice",
        expected_seq=1,
    )
    assert not ok
    assert reason == "invalid_mac"
