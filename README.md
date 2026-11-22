# Assignment 2: The Subset Construction (NFA → DFA)

SI2002 Formal Languages, Universidad EAFIT. Professor: César Augusto Guerra Villa.

**Students' full names:**

* Sergio Tomas Rincon Jaimes
* Sara Arboleda Quintero
* Jesús Ricardo Gandica Velasco

**Class number:** S2666-0509

The program reads nondeterministic finite automata (NFA) and, for each one, prints the deterministic
finite automaton (DFA) given by the **subset construction** of Kozen (1997), Lecture 6.

---

## 1. Environment and versions

| | |
|---|---|
| Operating system | Windows 11 Home, version 26H2 (OS build 26300.9818), 64-bit |
| Programming language | Python 3.13.14 (CPython, 64-bit) |
| Libraries | Only the Python standard library (`argparse`, `dataclasses`, `itertools`, `codecs`; `unittest` for the tests). Nothing has to be installed. |
| Optional tool | [Graphviz](https://graphviz.org/download/), only to turn the optional diagrams (`--dot`) into images. It is not needed to run the program or the tests. |

The program needs Python 3.7 or newer. It does not depend on the operating system, so it also
runs on Linux and macOS. It was developed and tested on the system above.

## 2. Files

```
subset_construction.py              the program
README.md                           this file
examples/statement_example.txt      the example of the statement of the assignment
examples/more_cases.txt             three more cases in one input
tests/test_subset_construction.py   automatic tests
```

## 3. How to run it

Open a terminal **in the folder that contains `subset_construction.py`**. To check that Python is
installed, run `python --version` (on Linux/macOS: `python3 --version`).

The input can come from the standard input or from a file given as an argument.

**Windows, Command Prompt (cmd):**

```
python subset_construction.py < examples\statement_example.txt
```

**Windows, PowerShell** (PowerShell does not accept `<`; use one of these two forms):

```
python subset_construction.py examples\statement_example.txt
Get-Content examples\statement_example.txt | python subset_construction.py
```

**Linux / macOS:**

```
python3 subset_construction.py < examples/statement_example.txt
```

Other ways to use it:

* **Typing the input by hand.** Run `python subset_construction.py` and type the input. The
  table of each case is printed as soon as the case is complete, and the program ends after the
  last case.
* **Saving the output to a file.** `python subset_construction.py input.txt > output.txt`
* **Help.** `python subset_construction.py --help`

### Options (optional extras)

Without options, the program prints exactly the output described in Section 5 and nothing else.

| Option | What it does |
|---|---|
| `--steps` | Before each table, explains how every transition was computed (see Section 6.5). |
| `--full` | Prints all the 2ⁿ subsets of Q (the complete construction of Kozen), not only the accessible ones (see Section 6.4). Limited to n ≤ 20. |
| `--dot DIR` | Writes diagrams of every NFA and DFA in the folder `DIR` (see Section 7). |

Options can be combined, for example `python subset_construction.py input.txt --steps --dot diagrams`.

### Running the tests

```
python -B -m unittest discover -s tests -v
```

(`-B` stops Python from creating `__pycache__` folders.) The 32 tests take about 20 seconds and
check:

* the exact output for the example of the statement, from the standard input and from a file;
* small cases: several cases in one input, an empty set of initial states, no final states, one
  state, a state that is both initial and final, and the alphabet order;
* 250 random NFAs. For each one, the printed table is read back and checked against the
  definition (q0 = S, δ_M(A, a) = ⋃ Δ(q, a), the final states, every state accessible,
  no repeated subsets). The DFA must also accept exactly the same strings as the NFA, for every
  string of length ≤ 5. Acceptance by the NFA is computed independently, by searching for an
  accepting path;
* `--full` (2ⁿ states, same language), `--steps` and `--dot`;
* input variations (Section 4) and wrong inputs (clear error, exit code 1).

## 4. Input

The input follows the statement of the assignment:

1. A line with the number of cases `c`.
2. For each case:
   - a line with the number of states `n` (the states are `1, 2, ..., n`);
   - a line with the initial states `S`, separated by blanks;
   - a line with the alphabet Σ, with the symbols separated by blanks;
   - a line with the final states `F`, separated by blanks;
   - `n` lines with the rows of the transition table, in order. Each row has the state number
     and then Δ(q, a) for every symbol a, in the order of the alphabet. A set is written in braces
     with its elements separated by blanks, like `{1 5}`, and the empty set is written `0`.

Example (`examples/statement_example.txt`):

```
1
5
3 5
a b
1 4
1 {1 5} 0
2 {1} 0
3 {2 4} 0
4 0 {5}
5 {1 5} {4}
```

To be robust, the program also accepts:

* blank lines and extra spaces or tabs anywhere;
* rows without the state number at the beginning, or with a colon (`1: {1 5} 0`). When the number
  is present, the rows may come in any order;
* commas inside sets (`{1, 5}`), and `{}` or `∅` for the empty set;
* `0` for an empty set of initial or final states, and those sets written in braces (`{3 5}`);
* files with Windows line endings, with a UTF-8 byte order mark, or in UTF-16 (the encoding that
  Windows PowerShell 5 uses for `echo ... > file`).

Wrong inputs are reported on the standard error with the line number, and the exit code is 1.
Examples of wrong inputs are a row with a missing or extra entry, a state outside `1..n`, a
repeated symbol, a repeated row, an unclosed `{`, or an input that ends too early. The tables of
the cases before the error are still printed, and nothing extra is printed on the standard
output. For example:

```
error: line 6: in row 1 of the table of case 1: expected the state number followed by 2 entries (one for each symbol: a b), each one a set in braces or 0; found '1 {2}'
```

## 5. Output

For each case the program prints the table of the DFA M:

```
        a   b   subset
->  q0  q1  q2  {3 5}
  * q1  q3  q4  {1 2 4 5}
  * q2  q5  q6  {4}
  * q3  q3  q2  {1 5}
  * q4  q3  q4  {4 5}
    q5  q5  q5  0
    q6  q3  q2  {5}
Initial state: q0
Final states: q1 q2 q3 q4
```

* The first line has the symbols of the alphabet (in the input order) and `subset`.
* Each other row is one state of M:
  - `->` marks the initial state and `*` marks the final states. A state that is both is marked `->*`;
  - then come the name of the state and the state reached with each symbol;
  - the last column is the set of states of N that the state of M represents, written as in the
    input (`0` is the empty set).
* As the statement allows, the states of M are renamed `q0, q1, q2, ...`. `q0` is always the
  initial state, and the others are numbered in the order in which the construction finds them
  (Section 6.4).
* The last two lines give the initial state and the final states of M. If M has no final states,
  `0` (the empty set) is printed.
* Several cases are printed one after the other. Each table starts with its header line. There
  are no prompts and no blank lines.
* The output uses only ASCII characters, so it displays correctly in any console.

## 6. The algorithm

### 6.1 Definitions (Kozen, Lecture 6)

An NFA is N = (Q, Σ, Δ, S, F), where Q is a finite set of states, Σ is the alphabet,
Δ : Q × Σ → 2^Q is the transition function, S ⊆ Q is the set of **start states** (there may be
several) and F ⊆ Q is the set of final states. Δ is extended to sets of states and strings:

```
Δ̂(A, ε)  = A
Δ̂(A, xa) = ⋃ { Δ(q, a) : q ∈ Δ̂(A, x) }
```

Δ̂(A, x) is the set of all the states N can be in after reading x, starting from any state of A.
N accepts x when Δ̂(S, x) ∩ F ≠ ∅, that is, when some way of reading x ends in a final state.

### 6.2 The subset construction

The DFA M = (Q_M, Σ, δ_M, s_M, F_M) simulates all the possible runs of N at the same time. Its
state after reading x is the set of states where N could be:

```
Q_M          = 2^Q                      (every subset of Q is a state of M)
δ_M(A, a)    = ⋃ { Δ(q, a) : q ∈ A }     (all the states N can reach from A with a)
s_M          = S
F_M          = { A ⊆ Q : A ∩ F ≠ ∅ }    (the subsets with at least one final state of N)
```

δ_M gives exactly one state for every pair (A, a), so M is deterministic. When no state of A
has a transition with a, δ_M(A, a) = ∅. The empty set is then a state of M too. It is a "trap"
state: δ_M(∅, a) = ∅ for every a, and ∅ is not final.

### 6.3 Why M accepts the same language as N

By induction on |x|, δ̂_M(A, x) = Δ̂(A, x) for every A ⊆ Q and every string x (Kozen, Lecture 6):

* For x = ε, both sides are A.
* For a string xa: δ̂_M(A, xa) = δ_M(δ̂_M(A, x), a) = δ_M(Δ̂(A, x), a) = ⋃ { Δ(q, a) : q ∈ Δ̂(A, x) } = Δ̂(A, xa).

Therefore:

x ∈ L(M) ⟺ δ̂_M(s_M, x) ∈ F_M ⟺ Δ̂(S, x) ∩ F ≠ ∅ ⟺ x ∈ L(N).

### 6.4 What the program builds: the accessible subsets

Q_M has 2ⁿ states, but while reading strings M only visits the states δ̂_M(s_M, x), called the
**accessible** states. The other subsets can be removed without changing δ̂_M(s_M, x) for any x,
so the language stays the same. By default the program builds only the accessible states, using
a worklist (a breadth-first search) that starts at s_M = S:

```
states ← [S]                              S is q0
i ← 0
while i < |states|:                       states[i..] are found but not processed yet
    A ← states[i]
    for each symbol a, in the order of the input:
        B ← ⋃ { Δ(q, a) : q ∈ A }
        if B is not in states:
            append B to states            B gets the next name q_k
        δ_M(q_i, a) ← the name of B
    i ← i + 1
F_M ← { q_i : states[i] ∩ F ≠ ∅ }
```

* Every subset added is δ_M of an accessible state, so it is accessible.
* Every accessible state δ̂_M(S, x) is added, which follows by induction on |x|.

So the result is exactly the accessible part of Kozen's M. It also gives a deterministic
naming: `q0` is S, and the other states are numbered in the order in which they are found.

With `--full` the program also adds the inaccessible subsets, after the accessible ones (ordered
by size and then lexicographically), and prints the complete M with 2ⁿ states. The accessible
states keep the same names in both modes.

**Data structures** (in `subset_construction.py`):

* the NFA's Δ is a dictionary `delta[q][a]` whose values are `frozenset`s of states;
* the states of M are a list `states`, where `states[i]` is the subset named `q_i`;
* a dictionary `number` maps each subset to its index. This works because `frozenset`s can be
  dictionary keys, so checking whether a subset is new takes constant expected time;
* δ_M is a dictionary `delta[(i, a)] = j`, and F_M is a set of indices;
* the list `states` together with the index `processed` is the worklist (a FIFO queue).

**Complexity.** Let k be the number of accessible subsets (k ≤ 2ⁿ). Each one is processed once.
For each symbol, the program joins at most n sets of at most n states each, which takes O(n²).
The total time is O(k · |Σ| · n²), and the memory is O(k · (n + |Σ|)). In the worst case
k = 2ⁿ, and this cannot be avoided. For example, the NFA for "the third symbol from the right
is a" (case 2 of `examples/more_cases.txt`) has 4 states, and its DFA needs 2³ = 8 states.

### 6.5 Worked example (the example of the statement)

N has Q = {1, 2, 3, 4, 5}, S = {3, 5}, Σ = {a, b} and F = {1, 4}. The construction starts with
q0 = S = {3, 5}:

| State of M | Subset A | δ_M(A, a) | δ_M(A, b) | Final? (A ∩ {1, 4} ≠ ∅) |
|---|---|---|---|---|
| q0 | {3, 5} | {2,4} ∪ {1,5} = {1,2,4,5} → **q1** (new) | ∅ ∪ {4} = {4} → **q2** (new) | no |
| q1 | {1, 2, 4, 5} | {1,5} ∪ {1} ∪ ∅ ∪ {1,5} = {1,5} → **q3** (new) | ∅ ∪ ∅ ∪ {5} ∪ {4} = {4,5} → **q4** (new) | yes |
| q2 | {4} | ∅ → **q5** (new) | {5} → **q6** (new) | yes |
| q3 | {1, 5} | {1,5} ∪ {1,5} = {1,5} → q3 | ∅ ∪ {4} = {4} → q2 | yes |
| q4 | {4, 5} | ∅ ∪ {1,5} = {1,5} → q3 | {5} ∪ {4} = {4,5} → q4 | yes |
| q5 | ∅ | ∅ → q5 | ∅ → q5 | no |
| q6 | {5} | {1,5} → q3 | {4} → q2 | no |

Only 7 of the 2⁵ = 32 subsets are accessible. The program prints the table of Section 5.
`python subset_construction.py examples\statement_example.txt --steps` prints the same
computation before the table:

```
q0 = S = {3 5}
  delta(q0, a) = Delta(3, a) U Delta(5, a) = {2 4} U {1 5} = {1 2 4 5} = q1 (new)
  delta(q0, b) = Delta(3, b) U Delta(5, b) = 0 U {4} = {4} = q2 (new)
q1 = {1 2 4 5}
  delta(q1, a) = Delta(1, a) U Delta(2, a) U Delta(4, a) U Delta(5, a) = {1 5} U {1} U 0 U {1 5} = {1 5} = q3 (new)
  delta(q1, b) = Delta(1, b) U Delta(2, b) U Delta(4, b) U Delta(5, b) = 0 U 0 U {5} U {4} = {4 5} = q4 (new)
q2 = {4}
  delta(q2, a) = Delta(4, a) = 0 = q5 (new)
  delta(q2, b) = Delta(4, b) = {5} = q6 (new)
...
```

### 6.6 More examples (`examples/more_cases.txt`)

The three cases are:

1. strings over {a, b} that end in `ab`;
2. strings whose third symbol from the right is `a`;
3. an NFA with two start states, one of them final.

Output:

```
        a   b   subset
->  q0  q1  q0  {1}
    q1  q1  q2  {1 2}
  * q2  q1  q0  {1 3}
Initial state: q0
Final states: q2
        a   b   subset
->  q0  q1  q0  {1}
    q1  q2  q3  {1 2}
    q2  q4  q5  {1 2 3}
    q3  q6  q7  {1 3}
  * q4  q4  q5  {1 2 3 4}
  * q5  q6  q7  {1 3 4}
  * q6  q2  q3  {1 2 4}
  * q7  q1  q0  {1 4}
Initial state: q0
Final states: q4 q5 q6 q7
        a   subset
->* q0  q1  {1 2}
  * q1  q2  {2}
    q2  q2  0
Initial state: q0
Final states: q0 q1
```

## 7. Optional feature: diagrams of the automata

```
python subset_construction.py examples\statement_example.txt --dot diagrams
```

This writes `diagrams/case1_nfa.dot` (N) and `diagrams/case1_dfa.dot` (M) in the
[Graphviz](https://graphviz.org/) DOT language. Each case of the input gets its own pair of
files. In the drawings:

* final states are double circles;
* a small arrow points to each initial state;
* the states of M show their name and their subset.

The table printed on the screen does not change.

If Graphviz is installed (the `dot` command is on the PATH), the program also draws an `.svg`
image next to each `.dot` file. Otherwise the images can be drawn later:

```
dot -Tsvg diagrams/case1_dfa.dot -o diagrams/case1_dfa.svg
```

Any online Graphviz viewer can also display the contents of a `.dot` file.

## References

Kozen, Dexter C. (1997). *Automata and Computability*. 1st ed. Berlin, Heidelberg: Springer-Verlag.
ISBN: 0387949070. DOI: [10.1007/978-1-4612-1844-9](https://doi.org/10.1007/978-1-4612-1844-9).
Lecture 6: The Subset Construction.
