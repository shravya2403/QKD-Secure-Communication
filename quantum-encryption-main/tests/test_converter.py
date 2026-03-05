"""Tests for Qiskit to QuNetSim converter."""

import pytest
from qiskit import QuantumCircuit
from unittest.mock import Mock

from quantum_hybrid_qkd.utils.converter import apply_qiskit_gates_to_qunetsim_qubit


def test_converter_x_gate():
    """Test conversion of X gate."""
    qc = QuantumCircuit(1)
    qc.x(0)
    
    mock_qubit = Mock()
    apply_qiskit_gates_to_qunetsim_qubit(qc, mock_qubit)
    
    # Verify X was called once
    mock_qubit.X.assert_called_once()


def test_converter_h_gate():
    """Test conversion of H gate."""
    qc = QuantumCircuit(1)
    qc.h(0)
    
    mock_qubit = Mock()
    apply_qiskit_gates_to_qunetsim_qubit(qc, mock_qubit)
    
    # Verify H was called once
    mock_qubit.H.assert_called_once()


def test_converter_z_gate():
    """Test conversion of Z gate."""
    qc = QuantumCircuit(1)
    qc.z(0)
    
    mock_qubit = Mock()
    apply_qiskit_gates_to_qunetsim_qubit(qc, mock_qubit)
    
    # Verify Z was called once
    mock_qubit.Z.assert_called_once()


def test_converter_multiple_gates():
    """Test conversion of multiple gates."""
    qc = QuantumCircuit(1)
    qc.x(0)
    qc.h(0)
    qc.z(0)
    
    mock_qubit = Mock()
    apply_qiskit_gates_to_qunetsim_qubit(qc, mock_qubit)
    
    # Verify all gates were called
    mock_qubit.X.assert_called_once()
    mock_qubit.H.assert_called_once()
    mock_qubit.Z.assert_called_once()


def test_converter_unsupported_gate():
    """Test that unsupported gates raise NotImplementedError."""
    qc = QuantumCircuit(1)
    qc.y(0)  # Y gate is not supported
    
    mock_qubit = Mock()
    
    with pytest.raises(NotImplementedError, match="Gate 'y' not implemented"):
        apply_qiskit_gates_to_qunetsim_qubit(qc, mock_qubit)


def test_converter_empty_circuit():
    """Test conversion of empty circuit."""
    qc = QuantumCircuit(1)
    
    mock_qubit = Mock()
    apply_qiskit_gates_to_qunetsim_qubit(qc, mock_qubit)
    
    # Verify no gates were called
    mock_qubit.X.assert_not_called()
    mock_qubit.H.assert_not_called()
    mock_qubit.Z.assert_not_called()

