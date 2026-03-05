"""
Quantum Hybrid QKD - A Quantum Key Distribution system with BB84 and QOTP encryption.

This package provides a complete implementation of quantum key distribution
combining the BB84 protocol with Quantum One-Time Pad encryption.
"""

__version__ = "0.1.0"
__author__ = "Quantum Hybrid QKD Team"

from .nodes.alice import alice_protocol
from .nodes.bob import bob_protocol
from .nodes.eve import eve_protocol
from .crypto.qotp import qotp_encrypt, qotp_decrypt
from .utils.converter import apply_qiskit_gates_to_qunetsim_qubit

__all__ = [
    "alice_protocol",
    "bob_protocol",
    "eve_protocol",
    "qotp_encrypt",
    "qotp_decrypt",
    "apply_qiskit_gates_to_qunetsim_qubit",
]
