# Grover’s Algorithm to implement a Maze Solver

Federico Bravetti — [federico.bravetti2@studio.unibo.it](mailto:federico.bravetti@studio.unibo.it)

Matteo Bambini — [matteo.bambini@studio.unibo.it](mailto:matteo.bambini4@studio.unibo.it)

Michele Ravaioli — [michele.ravaioli3@studio.unibo.it](mailto:michele.ravaioli3@studio.unibo.it)

Valerio Giannini — [valerio.giannini@studio.unibo.it](mailto:valerio.giannini@studio.unibo.it)

---

## Abstract

This paper presents a quantum maze solver implementation using Grover's algorithm for quadratic speedup over classical approaches. The strategy we adopted was to map maze navigation to a graph search problem. Simulation on 4-node graphs achieve **98,76%** success probability with optimal Grover iterations. The solution highlights quantum computing's potential for pathfinding problems while addressing qubit scalability challenge.

---

## Introduction

Maze solving represents a fundamental class of graph traversal problems with extensive applications across robotics, autonomous navigation, and strategic path planning. In the classical computing paradigm, solving mazes requires traversing through all possible paths sequentially, resulting in computational complexity from $O(N)$ to $O(N^3)$ operations for N potential paths. However, quantum computing offers an intriguing alternative through Grover's algorithm, which achieves a quadratic speedup by requiring only $O(√N)$ operations, marking a significant advancement in search optimization.

Our work consist of:

- Mapping the maze navigation problem into a graph search
- Design the Oracle : $U_f$
- Design the diffuser : $G$
- Implementing a simulation
- Analyze circuit complexity and simulation results

---

## Background

A maze-solving algorithm is an automated method for finding a path from entrance to exit in a maze. The field has developed several approaches with different computational complexities:

1. Random Mouse Algorithm $(O(n³))$: Simulates random walks through the maze until finding the exit. Simple but inefficient for complex mazes.
2. Wall Follower $(O(n²))$: Also known as the "Hand on Wall Rule", it works by keeping one hand on a wall while walking through the maze. Effective for simple mazes but fails in complex structures with isolated walls.
3. Trémaux's Algorithm $(O(n²))$: A depth-first search variant that marks passages when they are visited. More efficient than random walks but requires marking capability.
4. Dead-end Filling $(O(n²))$: Systematically identifies and fills dead-ends until only the solution path remains. Particularly effective for perfect mazes.
5. A* Algorithm $(O(n log n))$: A heuristic search algorithm that evaluates each cell as a node using two key metrics:
- Cost from start to current node
- Estimated cost to destination (Manhattan/Euclidean distance)

In this project we want to create a **Quantum maze-solving algorithm** (Based on Grover’s Algorithm) inspired by A***,** treating the cells as nodes, aiming to achieve better computational complexity than classical approaches. 

---

### Grover’s Algorithm

Grover's algorithm, first described in a 1996 paper, allows finding (with probability > $\frac{1}{2}$) a specific element in a table of $N$ unsorted elements using  $O(\sqrt{N})$  operations. In comparison, a classical computer requires a computational complexity of $O(N)$.

The algorithm's operation is based on an oracle, which enables a general description and geometric interpretation.

---

**Grover's Oracle Implementation**

We search for an element within a space of $N$ elements, indexed from $0$ to $N-1$. We establish that $N = 2^n$ and there exist  $1 \leq M \leq N$  solutions.

The function $f(x)$ is characterized as follows:

$f(x) =
\begin{cases}
1 & \text{if } x \text{ is a solution}, \\
0 & \text{otherwise}.
\end{cases}$

The oracle $U_f$ functions according to:

$\|x\|_q \overset{U_f}{\to} |x|_q \oplus f(x),$

where  $\oplus$  denotes modulo 2 addition. The qubit  $q$  undergoes negation when $f(x) = 1$.

Upon initializing qubit $q$  in state $\frac{|0\rangle - |1\rangle}{\sqrt{2}}$ , the oracle's action transforms to:

$|x\rangle \left|\frac{|0\rangle - |1\rangle}{\sqrt{2}}\right\rangle \overset{U_f}{\longrightarrow} (-1)^{f(x)} |x\rangle \left(\frac{|0\rangle - |1\rangle}{\sqrt{2}}\right).$

The state of $q$  remains constant, facilitating analysis. The oracle designates solutions through phase modification:

$|x\rangle \overset{U_f}{\longrightarrow} (-1)^{f(x)} |x\rangle.$

Given $M$ solutions, the oracle necessitates $O\left(\sqrt{\frac{N}{M}}\right)$  applications.

---

**Grover's Algorithm Circuit Implementation**

- The circuit employs a register of  $n$  qubits, initialized in state $0^{\otimes n}$ .
- The Hadamard transform $H^{\otimes n}$  generates the superposition:

$|\psi\rangle = \frac{1}{\sqrt{N}} \sum_{x=0}^{N-1} |x\rangle.$
- The objective is to determine a solution while minimizing oracle applications $U_f$ .

---

**Grover's Algorithm: Iterations**

The Grover iteration comprises the following steps:

1. Application of the oracle operator $U_f$ .
2. Application of the Hadamard transform $H^{\otimes n}$ .
3. Conditional phase shift:

$|x\rangle \rightarrow -(-1)^{\delta_{x_0}} |x\rangle.$

4. Application of the Hadamard transform $H^{\otimes n}$ .

The overall effect can be expressed as:

$G = (2|\psi\rangle\langle \psi| - I)U_f.$

---

**G: Geometric Interpretation**

$G$ represents a rotation in a two-dimensional vector space, generated by the initial state $|\psi\rangle$ and the superposition of solution states.

The basis states are defined as:

$|\alpha\rangle = \frac{1}{\sqrt{N-M}}\sum_{x}^{''} |x\rangle, \quad |\beta\rangle = \frac{1}{\sqrt{M}}\sum_{x}^{'} |x\rangle,$

where |α⟩ and |β⟩ represent non-solution and solution states respectively. The initial state is:

$|\psi\rangle = \sqrt{\frac{N-M}{N}}|\alpha\rangle + \sqrt{\frac{M}{N}}|\beta\rangle.$

The oracle operator $U_f$ reflects around $|\alpha\rangle$, while the diffusion operator $(2|\psi\rangle\langle \psi| - I)$ reflects around $|\psi\rangle$.

These reflections create a rotation by angle $\theta$:
$\cos \frac{\theta}{2} = \sqrt{\frac{N-M}{N}}.$

After k iterations:
$G^k |\psi\rangle = \cos \left( \frac{2k+1}{2} \theta \right) |\alpha\rangle + \sin \left( \frac{2k+1}{2} \theta \right) |\beta\rangle.$

Each iteration rotates the state closer to $|\beta\rangle$, increasing the probability of finding a solution. The optimal number of iterations is:
$K_{opt} \approx \frac{\pi}{4} \sqrt{\frac{N}{M}}.$
Exceeding this number reduces success probability, though it eventually increases again due to the rotation's periodic nature.

---

## Problem Formulation

Given a directed graph $G=(V,E)$ with:

- $V$ : Set of nodes (maze junctions); Each node represents a **maze cell or junction**
- $*E⊆V×V*$: Valid transitions between nodes
- $s∈V$: Fixed start node (entrance)
- $g∈V$: Fixed goal node (exit)

Identify the unique valid path $P=[s=v0,v1,...,vk=g]$ such that:

1. **Connectivity**: $(vi,vi+1)∈E$ for all $0≤i<k$
2. **Uniqueness**: Only one such path exists in $G$

---

## Implementation

### Quantum Circuit Design

To model maze traversal as a quantum search problem, we represent each potential path as a unique binary string. For a small graph with $N=2nN = 2^nN=2n$ nodes, each path corresponds to a basis state in a quantum system of nnn qubits. Our objective is to amplify the amplitude of the state that encodes the correct path from entrance to exit.

We design a Grover search circuit comprising three main components:

1. **Initialization**: All qubits are placed into a uniform superposition using Hadamard gates.
2. **Oracle**: A quantum subroutine marks the correct path by flipping its phase.
3. **Diffuser (Inversion About the Mean)**: A reflection operation amplifies the marked state's amplitude.

This iterative process leads the system to converge toward the correct path with high probability.

### Oracle

The phase oracle we built for the maze pathfinding problem is based on two main ideas:

- The input is a sequence of nodes representing a path through the maze.
- To mark a state, we check that:
  - The path starts at the starting node and ends at the ending node.
  - Every pair of consecutive nodes forms a valid link in the maze.
  - For any sequence of three nodes, the first and last nodes are either different, or both equal to the ending node.

If all these conditions are satisfied, the oracle marks the corresponding quantum state.

To implement this, we use some ancilla qubits. Given that **N** is the maximum number of nodes in the path and ****n**** is the bit required to represent a node the oracle is built as follow:

- The first **N x n** qubits encode the node sequence of the path.
- The next **N − 1** ancilla qubits are used to check the valid link condition.
- The final **N − 2** ancilla qubits are used to check the three-node condition.

To avoid interference from these ancillas, we uncompute them after the phase flip.

For our 2-qubit example (a 4-node graph), assume that the solution is encoded as `|11⟩`. The oracle can be implemented using a controlled-Z gate with appropriate X-gate preprocessing:

### Diffuser

The diffusion operator amplifies the probability of the marked state by reflecting the quantum state about the equal superposition state $|s\rangle$. This corresponds to inverting each amplitude around the average amplitude of the current state $|\psi\rangle$.

Given the equal superposition state:  
$|s\rangle = \frac{1}{\sqrt{N}} \sum_x |x\rangle$, where $N$ is the total number of basis states.

The diffusion operator is defined as:  
$D = 2 |s\rangle \langle s| - I_N$, where $I_N$ is the identity on $N$ qubits.

Since $|s\rangle = H^{\otimes N} |0\rangle$ and $I_N = H^{\otimes N} I_N H^{\otimes N}$, we can write:  
$D = H^{\otimes N} (2 |0\rangle \langle 0| - I_N) H^{\otimes N}$,
where $2 |0\rangle \langle 0| - I_N = X^{\otimes N} CZ X^{\otimes N}$.

### Simulation

To demonstrate Grover’s algorithm for a 2-qubit maze (4 possible paths), we build the circuit using 1 iteration (optimal for 1 solution among 4 states):

```python

qc = QuantumCircuit(2, 2)
qc.h([0, 1])               # Step 1: Superposition
qc.append(oracle, [0, 1])  # Step 2: Oracle
qc.append(diffuser, [0, 1])# Step 3: Diffuser
qc.measure([0, 1], [0, 1]) # Measurement

# Simulation with Qiskit’s Aer simulator:
backend = Aer.get_backend('qasm_simulator')
job = execute(qc, backend, shots=1000)
counts = job.result().get_counts()
```

```
**Circuit Diagram**:

     ┌───┐┌────────────┐┌────────────┐┌─┐
q_0: ┤ H ├┤            ├┤            ├┤M├───
     ├───┤│   Oracle   ││  Diffuser  │└╥┘
q_1: ┤ H ├┤            ├┤            ├─╫────
     └───┘└────────────┘└────────────┘ ║
                                      ║
c: 2/═════════════════════════════════╩════
                                       0  1
```

This small-scale simulation confirms the quadratic speedup promised by Grover’s algorithm and lays the groundwork for scaling to larger maze graphs using more qubits and iterations.

---

## Results

**`
[0 -> 1 -> 3] : ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■ 9860
[3 -> 1 -> 2] : ■ 4
[2 -> 0 -> 3] : ■ 3
[2 -> 3 -> 1] : ■ 3
[1 -> 2]      : ■ 3
[2]           : ■ 3
Other paths: □ 124 (frequency ≤ 2)
`**

---

## Conclusion

This project represent a proof-of-concept for using quantum Grover’s Algorithm in pathfinding scenarios by modeling the maze as a graph traversal task and encoding potential solutions into quantum states.