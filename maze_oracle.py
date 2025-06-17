# Imports

from qiskit import QuantumCircuit
from qiskit.circuit.library import XGate, ZGate
from PIL import Image as im
import requests
import base64
import matplotlib.pyplot as plt
import numpy as np
import io

# Utility classes

Edge = tuple[int, int]

class MazeOracleGenerator:

    def __init__(self, total_nodes: int, max_path_length: int | None = None, directed_graph: bool = False):
        self.__node_bits_size = int(np.ceil( np.log2(total_nodes) ))
        self.__max_path_length = max_path_length if max_path_length else total_nodes - 1
        self.__directed_graph = directed_graph
        self.__edges = []
        self.__first_node = None
        self.__last_node = None

    def add_edges(self, edges: list[Edge]) -> 'MazeOracleGenerator':
        self.__edges += edges
        return self

    def add_edge(self, edge: Edge) -> 'MazeOracleGenerator':
        self.add_edges([edge])
        return self
    
    def set_first_node(self, node: int) -> 'MazeOracleGenerator':
        self.__first_node = node
        return self
    
    def set_last_node(self, node: int) -> 'MazeOracleGenerator':
        self.__last_node = node
        return self
    
    # maps the x-gates on the correct bits, given the number
    def __node_to_binary(self, number):
        size = self.__node_bits_size
        circ = QuantumCircuit(size)
        exp = 1
        for qubit in range(size):
            if not (number & exp):
                circ.x(qubit)
            exp *= 2
        return circ

    # checks if an edge is valid (input: pair of nodes, output: ancilla)
    def __map_edge(self, from_node: int, to_node: int):
        size = self.__node_bits_size
        target_qubit = (2 * size)
        circ = QuantumCircuit((2 * size) + 1)

        # maps the x-gates on the correct bits, given the number
        def add_x(number, start_qubit):
            exp = 1
            for qubit in range(start_qubit, start_qubit + size):
                if not (number & exp):
                    circ.x(qubit)
                exp *= 2

        add_x(from_node, 0)
        add_x(to_node, size)
        circ.append(XGate().control(size * 2), list(range((2 * size))) + [target_qubit])
        add_x(from_node, 0)
        add_x(to_node, size)

        return circ

    # creates the circuit for all edges check, given a list of edges
    def __generate_edge_check_circuit(self, edges: list, directed_graph: bool):
        size = self.__node_bits_size
        total_size = (2 * size) + 1

        circ = QuantumCircuit(total_size, name='Edge Check')

        for e in edges:
            circ.append(self.__map_edge(e[0], e[1]), range(total_size))
            circ.barrier()

            if not directed_graph:
                circ.append(self.__map_edge(e[1], e[0]), range(total_size))
                circ.barrier()

        return circ
    
    # check if the nodes are equal 
    def __generate_turn_back_check_circuit(self):
        last = self.__last_node
        size = self.__node_bits_size
        circ = QuantumCircuit((2 * size) + 1, name='Turn Back Check')

        # first check: nodes are not equal
        for i in range(size):
            circ.cx(i, i + size)
            circ.x(i + size)
        circ.append(XGate().control(size), range(size, (2 * size) + 1))
        circ.x((2 * size))
        for i in range(size):
            circ.x(i + size)
            circ.cx(i, i + size)

        # second check: first node is equal to the last node
        if last is not None:
            circ.append(self.__node_to_binary(last), range(size))
            circ.append(XGate().control(size), list(range(size)) + [size*2])
            circ.append(self.__node_to_binary(last), range(size))

        return circ

    def generate(self):
        num_qubit_in_path = (self.__max_path_length + 1) * self.__node_bits_size
        num_ancillas = self.__max_path_length * 2 - 1
        # num_ancillas = self.__max_path_length
        total_size = num_qubit_in_path + num_ancillas
        edges = self.__edges

        # generate circuit for edge checking on whole graph
        full_edge_check = QuantumCircuit(total_size, name='Full Edge Check')
        starting_check = 0
        ending_check = self.__max_path_length

        # last node special check
        if self.__last_node is not None:
            edges = edges + [(self.__last_node, self.__last_node)] # add self-cycle to last node (for termination)
            last_edge_check  = self.__generate_edge_check_circuit(filter(lambda e: e[1] == self.__last_node, edges), True) # only check edges containing the last node

            ending_check = self.__max_path_length - 1 # update offset
            start_qubit = ending_check * self.__node_bits_size
            full_edge_check.append(last_edge_check, list(range(start_qubit, start_qubit + 2 * self.__node_bits_size)) + [num_qubit_in_path + ending_check])

        # first node special check
        if self.__first_node is not None:
            first_edge_check = self.__generate_edge_check_circuit(filter(lambda e: e[0] == self.__first_node, edges), True) # only check edges containing the first node
            
            starting_check = 1 # update offset
            full_edge_check.append(first_edge_check, list(range(2 * self.__node_bits_size)) + [num_qubit_in_path])

        # all other nodes check
        edge_check = self.__generate_edge_check_circuit(edges, self.__directed_graph)
        turn_back_check = self.__generate_turn_back_check_circuit()

        for s in range(starting_check, ending_check):
            start_qubit    = s * self.__node_bits_size
            full_edge_check.append(edge_check, list(range(start_qubit, start_qubit + 2 * self.__node_bits_size)) + [num_qubit_in_path + s])  

        for s in range(1, self.__max_path_length):
            start_qubit    = s * self.__node_bits_size
            previous_qubit = (s-1) * self.__node_bits_size
            next_qubit     = (s+1) * self.__node_bits_size
            full_edge_check.append(turn_back_check, list(range(previous_qubit, start_qubit)) + list(range(next_qubit, next_qubit + self.__node_bits_size)) + [self.__max_path_length + num_qubit_in_path + s - 1])
        
        circ = QuantumCircuit(total_size, name='Maze Oracle')
        circ.append(full_edge_check, range(total_size))                                                 # apply graph check
        circ.append(ZGate().control(num_ancillas - 1), range(num_qubit_in_path, total_size))            # flip correct combination
        circ.append(full_edge_check.inverse(), range(total_size))                                       # apply inverse graph check (to reset ancillas)
        return circ
