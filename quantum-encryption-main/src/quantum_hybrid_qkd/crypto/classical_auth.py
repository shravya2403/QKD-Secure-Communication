"""Classical-channel authentication helpers for the QKD demo.

This module provides:
1. A Schnorr-style proof of identity (interactive, zero-knowledge style).
2. HMAC authentication for classical protocol messages.

These primitives are for educational/demo purposes and should be replaced
with vetted protocol libraries for production systems.
"""

import hashlib
import hmac
import json
import secrets
from typing import Any

# Demo finite field parameters (prime modulus group).
SCHNORR_P = (2**127) - 1
SCHNORR_G = 3
SCHNORR_EXP_MOD = SCHNORR_P - 1

# Demo identity secrets shared out-of-band with both endpoints.
IDENTITY_PASSPHRASES = {
    "Alice": "alice-zkp-demo-secret-v1",
    "Bob": "bob-zkp-demo-secret-v1",
}


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    """Serialize JSON in a deterministic way for signing/verification."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def generate_session_id() -> str:
    """Create a random session identifier."""
    return secrets.token_hex(16)


def generate_nonce() -> str:
    """Create a random nonce for handshake freshness."""
    return secrets.token_hex(16)


def _secret_scalar(identity: str) -> int:
    """Derive a secret scalar from an identity passphrase."""
    phrase = IDENTITY_PASSPHRASES.get(identity)
    if not phrase:
        raise ValueError(f"Unknown identity '{identity}' for ZKP")
    digest = hashlib.sha256(phrase.encode("utf-8")).digest()
    return (int.from_bytes(digest, "big") % SCHNORR_EXP_MOD) or 1


def public_value(identity: str) -> int:
    """Get Schnorr-style public value for an identity."""
    return pow(SCHNORR_G, _secret_scalar(identity), SCHNORR_P)


def generate_commitment() -> tuple[int, int]:
    """Create one Schnorr commitment (r, t=g^r mod p)."""
    r = secrets.randbelow(SCHNORR_EXP_MOD - 1) + 1
    t = pow(SCHNORR_G, r, SCHNORR_P)
    return r, t


def generate_challenge(
    session_id: str,
    nonce_a: str,
    nonce_b: str,
    prover_id: str,
    verifier_id: str,
    commitment: int,
) -> int:
    """Generate a context-bound challenge for one proof round."""
    context = "|".join(
        [session_id, nonce_a, nonce_b, prover_id, verifier_id, str(commitment), secrets.token_hex(8)]
    )
    digest = hashlib.sha256(context.encode("utf-8")).digest()
    return (int.from_bytes(digest, "big") % SCHNORR_EXP_MOD) or 1


def generate_response(identity: str, r: int, challenge: int) -> int:
    """Compute Schnorr response s = r + c*x (mod p-1)."""
    x = _secret_scalar(identity)
    return (r + (challenge * x)) % SCHNORR_EXP_MOD


def verify_proof(public_y: int, commitment: int, challenge: int, response: int) -> bool:
    """Verify Schnorr equation g^s == t * y^c (mod p)."""
    left = pow(SCHNORR_G, response, SCHNORR_P)
    right = (commitment * pow(public_y, challenge, SCHNORR_P)) % SCHNORR_P
    return left == right


def derive_auth_key(session_id: str, nonce_a: str, nonce_b: str) -> bytes:
    """Derive a shared classical-channel auth key for this session."""
    seed = "|".join(
        [
            session_id,
            nonce_a,
            nonce_b,
            IDENTITY_PASSPHRASES["Alice"],
            IDENTITY_PASSPHRASES["Bob"],
        ]
    ).encode("utf-8")
    return hashlib.sha256(seed).digest()


def build_authenticated_payload(
    auth_key: bytes,
    session_id: str,
    sender_id: str,
    msg_type: str,
    seq: int,
    payload: Any,
) -> dict[str, Any]:
    """Create an HMAC-authenticated classical payload packet."""
    body = {
        "tag": "auth_payload",
        "session_id": session_id,
        "sender_id": sender_id,
        "msg_type": msg_type,
        "seq": seq,
        "payload": payload,
    }
    body["mac"] = hmac.new(auth_key, _canonical_json_bytes(body), hashlib.sha256).hexdigest()
    return body


def verify_authenticated_payload(
    packet: dict[str, Any],
    auth_key: bytes,
    session_id: str,
    expected_sender: str,
    expected_seq: int,
) -> tuple[bool, str]:
    """Validate packet metadata and HMAC integrity."""
    required_fields = {"tag", "session_id", "sender_id", "msg_type", "seq", "payload", "mac"}
    if not required_fields.issubset(packet.keys()):
        return False, "missing_fields"
    if packet["tag"] != "auth_payload":
        return False, "invalid_tag"
    if packet["session_id"] != session_id:
        return False, "invalid_session"
    if packet["sender_id"] != expected_sender:
        return False, "invalid_sender"
    if packet["seq"] != expected_seq:
        return False, "invalid_sequence"

    supplied_mac = packet["mac"]
    body = {k: v for k, v in packet.items() if k != "mac"}
    expected_mac = hmac.new(auth_key, _canonical_json_bytes(body), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(supplied_mac, expected_mac):
        return False, "invalid_mac"
    return True, "ok"
