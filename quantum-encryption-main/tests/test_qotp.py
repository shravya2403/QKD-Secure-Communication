"""Tests for QOTP encryption and decryption."""

import pytest
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer

from quantum_hybrid_qkd.crypto.qotp import qotp_encrypt, qotp_decrypt


def test_qotp_encrypt_key_00():
    """Test QOTP encryption with key [0, 0] (no operation)."""
    qc = QuantumCircuit(1)
    qotp_encrypt(qc, 0, [0, 0])
    
    # Circuit should be empty (no gates applied)
    assert len(qc.data) == 0


def test_qotp_encrypt_key_10():
    """Test QOTP encryption with key [1, 0] (X gate)."""
    qc = QuantumCircuit(1)
    qotp_encrypt(qc, 0, [1, 0])
    
    # Should have one X gate
    assert len(qc.data) == 1
    assert qc.data[0][0].name == 'x'


def test_qotp_encrypt_key_01():
    """Test QOTP encryption with key [0, 1] (Z gate)."""
    qc = QuantumCircuit(1)
    qotp_encrypt(qc, 0, [0, 1])
    
    # Should have one Z gate
    assert len(qc.data) == 1
    assert qc.data[0][0].name == 'z'


def test_qotp_encrypt_key_11():
    """Test QOTP encryption with key [1, 1] (X and Z gates)."""
    qc = QuantumCircuit(1)
    qotp_encrypt(qc, 0, [1, 1])
    
    # Should have two gates
    assert len(qc.data) == 2
    gate_names = [qc.data[i][0].name for i in range(2)]
    assert 'x' in gate_names
    assert 'z' in gate_names


def test_qotp_encrypt_decrypt_identity():
    """Test that QOTP encrypt followed by decrypt is identity."""
    for key in [[0, 0], [0, 1], [1, 0], [1, 1]]:
        qc = QuantumCircuit(1, 1)
        
        # Start in |1⟩ state
        qc.x(0)
        
        # Encrypt and decrypt
        qotp_encrypt(qc, 0, key)
        qotp_decrypt(qc, 0, key)
        
        # Measure
        qc.measure(0, 0)
        
        # Execute
        backend = Aer.get_backend('qasm_simulator')
        transpiled_qc = transpile(qc, backend)
        result = backend.run(transpiled_qc, shots=100).result()
        counts = result.get_counts()
        
        # Should measure |1⟩ with high probability
        assert counts.get('1', 0) > 90


def test_qotp_decrypt_is_encrypt():
    """Test that decrypt function is identical to encrypt (involutory)."""
    qc1 = QuantumCircuit(1)
    qc2 = QuantumCircuit(1)
    
    key = [1, 1]
    qotp_encrypt(qc1, 0, key)
    qotp_decrypt(qc2, 0, key)
    
    # Both circuits should be identical
    assert len(qc1.data) == len(qc2.data)
    for i in range(len(qc1.data)):
        assert qc1.data[i][0].name == qc2.data[i][0].name

