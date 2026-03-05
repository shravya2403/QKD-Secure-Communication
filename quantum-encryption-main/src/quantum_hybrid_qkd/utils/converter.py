"""Converter for translating Qiskit circuits to QuNetSim qubits."""


def apply_qiskit_gates_to_qunetsim_qubit(qc, qunetsim_qubit):
    """
    Apply gates from a Qiskit QuantumCircuit to a QuNetSim Qubit.
    
    This function bridges Qiskit's circuit model with QuNetSim's network simulation
    by translating gate operations.
    
    Args:
        qc: Qiskit QuantumCircuit containing gates to apply
        qunetsim_qubit: QuNetSim Qubit object to apply gates to
        
    Raises:
        NotImplementedError: If an unsupported gate is encountered
        
    Supported Gates:
        - X (NOT/Pauli-X)
        - H (Hadamard)
        - Z (Pauli-Z)
    """
    for instruction, qargs, cargs in qc.data:
        gate_name = instruction.name
        
        if gate_name == 'x':
            qunetsim_qubit.X()
        elif gate_name == 'h':
            qunetsim_qubit.H()
        elif gate_name == 'z':
            qunetsim_qubit.Z()
        else:
            raise NotImplementedError(f"Gate '{gate_name}' not implemented in converter.")

