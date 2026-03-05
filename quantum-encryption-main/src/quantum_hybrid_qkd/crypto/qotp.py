"""Quantum One-Time Pad (QOTP) encryption and decryption."""

from qiskit import QuantumCircuit


def qotp_encrypt(qc: QuantumCircuit, qubit_idx: int, key: list) -> None:
    """
    Encrypt a qubit with QOTP using Pauli gates.
    
    QOTP applies X and Z gates based on a 2-bit key to encrypt quantum information.
    
    Args:
        qc: Qiskit QuantumCircuit
        qubit_idx: Index of the qubit to encrypt
        key: 2-element list [X_key, Z_key] where each element is 0 or 1
    """
    if key[0] == 1:
        qc.x(qubit_idx)
    if key[1] == 1:
        qc.z(qubit_idx)


def qotp_decrypt(qc: QuantumCircuit, qubit_idx: int, key: list) -> None:
    """
    Decrypt a qubit with QOTP using the same key.
    
    QOTP decryption is identical to encryption since X² = I and Z² = I.
    
    Args:
        qc: Qiskit QuantumCircuit
        qubit_idx: Index of the qubit to decrypt
        key: 2-element list [X_key, Z_key] where each element is 0 or 1
    """
    qotp_encrypt(qc, qubit_idx, key)

