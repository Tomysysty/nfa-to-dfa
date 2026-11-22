#!/usr/bin/env python3
"""Subset construction: from a nondeterministic finite automaton (NFA) to an
equivalent deterministic finite automaton (DFA).

SI2002 Formal Languages - Assignment 2 - Universidad EAFIT
Students: Sergio Tomas Rincon Jaimes, Sara Arboleda Quintero,
          Jesús Ricardo Gandica Velasco

The algorithm is the subset construction of Kozen (1997), Lecture 6.  For an
NFA N = (Q, Sigma, Delta, S, F) the DFA M = (Q_M, Sigma, delta_M, s_M, F_M) is

    Q_M           = 2^Q          (every subset of Q is a state of M)
    delta_M(A, a) = U { Delta(q, a) : q in A }
    s_M           = S
    F_M           = { A subset of Q : A contains a final state of N }

and M accepts exactly the strings accepted by N.  The program builds the
states of M that are accessible from s_M (option --full adds the rest of 2^Q)
and names them q0, q1, q2, ... in the order in which they are found.

Usage: python subset_construction.py [INPUT_FILE] [--full] [--steps] [--dot DIR]

The input is read from INPUT_FILE, or from the standard input when no file is
given.  See README.md for the input and output formats.
"""

import argparse
import codecs
import itertools
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass

EMPTY_SET = "0"            # the assignment writes the empty set as 0
EMPTY_SET_SIGN = "\u2205"  # the symbol for the empty set, also accepted in the input
MAX_FULL_STATES = 20       # --full builds 2^n states, so it is limited to n <= 20


class InputError(Exception):
    """The input does not follow the format of the assignment."""


# ---------------------------------------------------------------------------
# Automata
# ---------------------------------------------------------------------------

@dataclass
class NFA:
    """N = (Q, Sigma, Delta, S, F), where Q = {1, 2, ..., n}."""

    n: int            # number of states
    alphabet: list    # Sigma: the symbols, in the order of the input
    delta: dict       # delta[q][a] is Delta(q, a), a frozenset of states
    start: frozenset  # S: the start states
    final: frozenset  # F: the final states


@dataclass
class DFA:
    """M = (Q_M, Sigma, delta_M, s_M, F_M), the result of the construction.

    The state q_i of M is the subset states[i] of Q.  The start state is q0.
    """

    alphabet: list    # Sigma (the same alphabet as N)
    states: list      # states[i] is the subset of Q named q_i
    delta: dict       # delta[(i, a)] = j means delta_M(q_i, a) = q_j
    final: set        # the numbers i such that q_i is a final state
    accessible: int   # q0 ... q(accessible - 1) are the states reachable from q0
    start: int = 0    # s_M = q0


# ---------------------------------------------------------------------------
# The subset construction (Kozen 1997, Lecture 6)
# ---------------------------------------------------------------------------

def subset_construction(nfa, full=False):
    """Return the DFA M obtained from nfa by the subset construction.

    The states of M are found with a worklist that starts with s_M = S.  Each
    state is processed once: delta_M(A, a) is computed for every symbol a, in
    the order of the alphabet, and each subset that appears for the first
    time becomes the next state q0, q1, q2, ...  In this way exactly the
    subsets that are accessible from s_M are generated.  The other subsets can
    never be reached while reading a string, so leaving them out does not
    change the accepted language.  If full is True they are added at the end
    anyway, which gives the complete construction with 2^n states.
    """
    states = []   # states[i] is the subset of Q named q_i
    number = {}   # number[A] = i when states[i] == A
    delta = {}    # delta[(i, a)] = j when delta_M(q_i, a) = q_j

    def state_number(subset):
        """Return the number of subset as a state of M, adding it if it is new."""
        if subset not in number:
            number[subset] = len(states)
            states.append(subset)
        return number[subset]

    def process(i):
        """Compute delta_M(q_i, a) for every symbol a of the alphabet."""
        for a in nfa.alphabet:
            target = set()
            for q in states[i]:            # union of Delta(q, a) for q in A
                target |= nfa.delta[q][a]
            delta[(i, a)] = state_number(frozenset(target))

    state_number(nfa.start)                # s_M = S is the state q0
    processed = 0
    while processed < len(states):         # states[processed:] are still pending
        process(processed)
        processed += 1
    accessible = len(states)

    if full:                               # add the inaccessible subsets as well
        for size in range(nfa.n + 1):
            for subset in itertools.combinations(range(1, nfa.n + 1), size):
                state_number(frozenset(subset))
        while processed < len(states):
            process(processed)
            processed += 1

    # F_M: the subsets that contain at least one final state of N
    final = {i for i, subset in enumerate(states) if subset & nfa.final}
    return DFA(nfa.alphabet, states, delta, final, accessible)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def state_name(i):
    """The name of the i-th state of M."""
    return "q%d" % i


def format_set(subset):
    """Write a set of states of N as in the input: {1 5}, or 0 if it is empty."""
    if not subset:
        return EMPTY_SET
    return "{" + " ".join(str(q) for q in sorted(subset)) + "}"


def format_dfa(dfa):
    """Return the lines of the table of M, followed by its start and final states.

    There is one row per state of M: '->' marks the start state and '*' the
    final states; then come the targets of the transitions (one column per
    symbol) and the subset of Q that the state represents.
    """
    table = [[""] + list(dfa.alphabet) + ["subset"]]
    for i, subset in enumerate(dfa.states):
        marker = ("->" if i == dfa.start else "  ") + ("*" if i in dfa.final else " ")
        row = [marker + " " + state_name(i)]
        row += [state_name(dfa.delta[(i, a)]) for a in dfa.alphabet]
        row.append(format_set(subset))
        table.append(row)

    widths = [max(len(row[c]) for row in table) for c in range(len(table[0]))]
    lines = []
    for row in table:
        cells = [cell.ljust(width) for cell, width in zip(row, widths)]
        lines.append("  ".join(cells).rstrip())

    finals = sorted(dfa.final)
    lines.append("Initial state: " + state_name(dfa.start))
    lines.append("Final states: "
                 + (" ".join(state_name(i) for i in finals) if finals else EMPTY_SET))
    return lines


def format_steps(nfa, dfa):
    """Explain, state by state, how each transition of M was computed (--steps)."""
    lines = []
    found = 1                                    # q0 = S is known from the start
    for i, subset in enumerate(dfa.states):
        if i == dfa.accessible:
            lines.append("Subsets of Q that are not accessible from q0 (added by --full):")
        lines.append("%s = %s%s" % (state_name(i), "S = " if i == dfa.start else "",
                                    format_set(subset)))
        members = sorted(subset)
        for a in dfa.alphabet:
            j = dfa.delta[(i, a)]
            if not members:
                how = "union over the empty set = "
            elif len(members) == 1:
                how = "Delta(%d, %s) = " % (members[0], a)
            else:
                how = "%s = %s = " % (
                    " U ".join("Delta(%d, %s)" % (q, a) for q in members),
                    " U ".join(format_set(nfa.delta[q][a]) for q in members))
            new = ""
            if i < dfa.accessible and j == found:  # this subset appears for the first time
                new = " (new)"
                found += 1
            lines.append("  delta(%s, %s) = %s%s = %s%s" % (
                state_name(i), a, how, format_set(dfa.states[j]), state_name(j), new))
    return lines


# ---------------------------------------------------------------------------
# Optional diagrams (Graphviz DOT language)
# ---------------------------------------------------------------------------

def dot_text(text):
    """Quote text for Graphviz; a line break becomes a new line of the label."""
    return '"%s"' % text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def dot_graph(title, nodes, starts, transitions):
    """Return a graph in the DOT language.

    nodes: list of (identifier, label, is_final); starts: identifiers of the
    start states; transitions: list of (source, symbol, target).  Transitions
    with the same source and target are drawn as one edge.
    """
    lines = ["digraph automaton {",
             "  rankdir=LR;",
             "  labelloc=t;",
             "  label=%s;" % dot_text(title),
             "  node [shape=circle];"]
    for identifier, label, is_final in nodes:
        shape = "doublecircle" if is_final else "circle"
        lines.append("  %s [label=%s, shape=%s];" % (dot_text(identifier), dot_text(label), shape))
    for k, identifier in enumerate(starts):
        arrow = dot_text("start%d" % k)
        lines.append("  %s [shape=point];" % arrow)
        lines.append("  %s -> %s;" % (arrow, dot_text(identifier)))
    labels = {}
    for source, symbol, target in transitions:
        labels.setdefault((source, target), []).append(symbol)
    for (source, target), symbols in labels.items():
        lines.append("  %s -> %s [label=%s];" % (dot_text(source), dot_text(target),
                                                 dot_text(", ".join(symbols))))
    lines.append("}")
    return "\n".join(lines) + "\n"


def nfa_dot(nfa, case):
    """Diagram of the NFA N."""
    nodes = [(str(q), str(q), q in nfa.final) for q in range(1, nfa.n + 1)]
    transitions = [(str(q), a, str(p))
                   for q in range(1, nfa.n + 1)
                   for a in nfa.alphabet
                   for p in sorted(nfa.delta[q][a])]
    return dot_graph("Case %d: NFA N" % case, nodes, [str(q) for q in sorted(nfa.start)],
                     transitions)


def dfa_dot(dfa, case):
    """Diagram of the DFA M; each state shows its name and its subset of Q."""
    nodes = [(state_name(i), "%s\n%s" % (state_name(i), format_set(subset)), i in dfa.final)
             for i, subset in enumerate(dfa.states)]
    transitions = [(state_name(i), a, state_name(dfa.delta[(i, a)]))
                   for i in range(len(dfa.states))
                   for a in dfa.alphabet]
    return dot_graph("Case %d: DFA M" % case, nodes, [state_name(dfa.start)], transitions)


def write_diagrams(directory, case, nfa, dfa):
    """Write caseK_nfa.dot and caseK_dfa.dot in directory.

    If Graphviz is installed (the command dot is on the PATH), an SVG image
    is also drawn for each file.
    """
    os.makedirs(directory, exist_ok=True)
    graphviz = shutil.which("dot")
    for kind, text in (("nfa", nfa_dot(nfa, case)), ("dfa", dfa_dot(dfa, case))):
        path = os.path.join(directory, "case%d_%s.dot" % (case, kind))
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        if graphviz:
            image = os.path.splitext(path)[0] + ".svg"
            result = subprocess.run([graphviz, "-Tsvg", path, "-o", image],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                print("warning: Graphviz could not draw %s: %s" % (path, result.stderr.strip()),
                      file=sys.stderr)


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

def decode(data):
    """Turn the bytes of the input into text.

    Besides plain ASCII/UTF-8 this accepts files saved with a byte order mark
    or in UTF-16 (for example, files created by Windows PowerShell 5).
    """
    if data.startswith(codecs.BOM_UTF8):
        return data[len(codecs.BOM_UTF8):].decode("utf-8", errors="replace")
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16", errors="replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def input_lines(path):
    """Return an iterator over the lines of the input (the standard input if path is None)."""
    if path is None or path == "-":
        if sys.stdin.isatty():
            # Typed by hand: read line by line, so that the table of each case
            # is printed as soon as the case is complete.
            return iter(sys.stdin)
        data = sys.stdin.buffer.read()
    else:
        with open(path, "rb") as handle:
            data = handle.read()
    return iter(decode(data).splitlines())


class LineReader:
    """Reads the input line by line, skipping blank lines and counting lines."""

    def __init__(self, lines):
        self.lines = lines
        self.line_number = 0

    def next_line(self, what):
        """Return the next non-blank line, without surrounding blanks."""
        for line in self.lines:
            self.line_number += 1
            line = line.replace("\ufeff", "").strip()
            if line:
                return line
        raise InputError("the input ended while reading %s" % what)

    def error(self, message):
        """An InputError that points to the current line."""
        return InputError("line %d: %s" % (self.line_number, message))


def natural_number(token):
    """The value of token if it is written with decimal digits only, else None."""
    if token and all("0" <= char <= "9" for char in token):
        return int(token)
    return None


def parse_count(reader, line, what, minimum):
    """A line with a single integer that is at least minimum."""
    value = natural_number(line)
    if value is None or value < minimum:
        raise reader.error("expected %s (an integer >= %d), found %r" % (what, minimum, line))
    return value


def parse_state(reader, token, n, what):
    """A state of N: an integer from 1 to n."""
    q = natural_number(token)
    if q is None or not 1 <= q <= n:
        raise reader.error("in %s: %r is not a state (the states are 1 to %d, "
                           "and the empty set is written %s)" % (what, token, n, EMPTY_SET))
    return q


def parse_state_list(reader, line, n, what):
    """A line with states separated by blanks (S or F); 0 is the empty set."""
    text = line
    if (text.startswith("{") and text.endswith("}")
            and text.count("{") == 1 and text.count("}") == 1):
        text = text[1:-1]                     # also accept the set written in braces
    tokens = text.replace(",", " ").split()
    if tokens in ([EMPTY_SET], [EMPTY_SET_SIGN]):
        return frozenset()
    return frozenset(parse_state(reader, token, n, what) for token in tokens)


def parse_alphabet(reader, line, what):
    """The symbols of the alphabet, separated by blanks."""
    symbols = line.replace(",", " ").split()
    for symbol in symbols:
        if "{" in symbol or "}" in symbol:
            raise reader.error("in %s: %r is not a symbol" % (what, symbol))
        if symbols.count(symbol) > 1:
            raise reader.error("in %s: the symbol %r appears more than once" % (what, symbol))
    return symbols


def parse_row(reader, line, n, alphabet, row_number, what):
    """One row of the transition table of N, for example '1 {1 5} 0'.

    The row has the number q of the state followed by Delta(q, a) for every
    symbol a, in the order of the alphabet.  Each entry is a set of states in
    braces or 0 (the empty set).  If the row has only the entries, the state
    is row_number (the rows come in order).  Returns (q, {a: Delta(q, a)}).
    """
    entries = []                  # (kind, value), where kind is "set" or "number"
    text = line.replace(",", " ")
    i = 0
    while i < len(text):
        char = text[i]
        if char.isspace():
            i += 1
        elif char == "{":
            end = text.find("}", i)
            if end < 0:
                raise reader.error("in %s: a '{' is not closed" % what)
            states = frozenset(parse_state(reader, token, n, what)
                               for token in text[i + 1:end].split())
            entries.append(("set", states))
            i = end + 1
        elif char == "}":
            raise reader.error("in %s: unexpected '}'" % what)
        else:
            end = i
            while end < len(text) and not text[end].isspace() and text[end] not in "{}":
                end += 1
            token = text[i:end]
            i = end
            if token in (EMPTY_SET, EMPTY_SET_SIGN):
                entries.append(("set", frozenset()))
            elif natural_number(token.rstrip(":")) is not None:
                entries.append(("number", natural_number(token.rstrip(":"))))
            else:
                raise reader.error("in %s: unexpected %r" % (what, token))

    # A number can only be the state at the beginning of the row; every entry
    # must be a set (in braces, or 0), so a missing entry is always detected.
    if entries and entries[0][0] == "number":
        q, cells = entries[0][1], entries[1:]
    else:
        q, cells = row_number, entries
    m = len(alphabet)
    if len(cells) != m or any(kind != "set" for kind, _ in cells):
        raise reader.error("in %s: expected the state number followed by %d %s "
                           "(one for each symbol: %s), each one a set in braces or %s; "
                           "found %r" % (what, m, "entry" if m == 1 else "entries",
                                         " ".join(alphabet), EMPTY_SET, line))
    if not 1 <= q <= n:
        raise reader.error("in %s: %d is not a state (the states are 1 to %d)" % (what, q, n))
    return q, {a: states for a, (_, states) in zip(alphabet, cells)}


def read_nfa(reader, case):
    """Read one case: n, S, Sigma, F and the n rows of the table of N."""
    n = parse_count(reader, reader.next_line("the number of states of case %d" % case),
                    "the number of states of case %d" % case, 1)
    start = parse_state_list(reader, reader.next_line("the initial states of case %d" % case),
                             n, "the initial states of case %d" % case)
    alphabet = parse_alphabet(reader, reader.next_line("the alphabet of case %d" % case),
                              "the alphabet of case %d" % case)
    final = parse_state_list(reader, reader.next_line("the final states of case %d" % case),
                             n, "the final states of case %d" % case)
    delta = {}
    for row_number in range(1, n + 1):
        what = "row %d of the table of case %d" % (row_number, case)
        q, row = parse_row(reader, reader.next_line(what), n, alphabet, row_number, what)
        if q in delta:
            raise reader.error("in %s: the row of state %d appears twice" % (what, q))
        delta[q] = row
    return NFA(n, alphabet, delta, start, final)


def read_cases(reader):
    """Yield the NFA of every case of the input, one at a time."""
    count = parse_count(reader, reader.next_line("the number of cases"),
                        "the number of cases", 0)
    for case in range(1, count + 1):
        yield read_nfa(reader, case)


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def solve(lines, output, full=False, steps=False, dot_directory=None):
    """Read every case from lines and write the table of its DFA to output."""
    reader = LineReader(lines)
    for case, nfa in enumerate(read_cases(reader), start=1):
        if full and nfa.n > MAX_FULL_STATES:
            raise InputError("case %d has %d states: --full would build 2^%d states "
                             "(it is limited to %d states)"
                             % (case, nfa.n, nfa.n, MAX_FULL_STATES))
        dfa = subset_construction(nfa, full)
        result = format_steps(nfa, dfa) if steps else []
        result += format_dfa(dfa)
        output.write("\n".join(result) + "\n")
        output.flush()
        if dot_directory:
            write_diagrams(dot_directory, case, nfa, dfa)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Subset construction (Kozen 1997, Lecture 6): reads NFAs and "
                    "prints equivalent DFAs.")
    parser.add_argument("input", nargs="?",
                        help="file with the input (default: the standard input)")
    parser.add_argument("--full", action="store_true",
                        help="print all the 2^n subsets of Q, not only the accessible ones")
    parser.add_argument("--steps", action="store_true",
                        help="before each table, show how every transition was computed")
    parser.add_argument("--dot", metavar="DIR",
                        help="write Graphviz diagrams of every NFA and DFA in the folder DIR")
    args = parser.parse_args(argv)

    try:
        solve(input_lines(args.input), sys.stdout, args.full, args.steps, args.dot)
    except (InputError, OSError) as error:
        print("error: %s" % error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")   # never crash on unusual symbols
    sys.exit(main())
