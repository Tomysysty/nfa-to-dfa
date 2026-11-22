"""Tests for subset_construction.py (only the Python standard library is used).

Run them from the main folder of the assignment with:

    python -B -m unittest discover -s tests -v
"""

import io
import itertools
import os
import random
import subprocess
import sys
import tempfile
import unittest
from functools import lru_cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import subset_construction as sc  # noqa: E402

PROGRAM = os.path.join(ROOT, "subset_construction.py")

STATEMENT_INPUT = """1
5
3 5
a b
1 4
1 {1 5} 0
2 {1} 0
3 {2 4} 0
4 0 {5}
5 {1 5} {4}
"""

# Computed by hand (see README.md, section "Worked example").
STATEMENT_OUTPUT = """\
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
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def solve_text(text, **options):
    """Run the program logic on text and return what it prints."""
    output = io.StringIO()
    sc.solve(iter(text.splitlines()), output, **options)
    return output.getvalue()


def run_program(args=(), stdin=b""):
    """Run the program in a new process. Returns (exit code, stdout, stderr)."""
    if isinstance(stdin, str):
        stdin = stdin.encode("utf-8")
    result = subprocess.run([sys.executable, "-B", PROGRAM] + list(args),
                            input=stdin, capture_output=True)
    stdout = result.stdout.decode("utf-8").replace("\r\n", "\n")
    stderr = result.stderr.decode("utf-8", errors="replace")
    return result.returncode, stdout, stderr


def nfa_to_text(nfa):
    """Write an NFA in the input format of the assignment (without the case count)."""
    lines = [str(nfa.n),
             " ".join(str(q) for q in sorted(nfa.start)) or "0",
             " ".join(nfa.alphabet),
             " ".join(str(q) for q in sorted(nfa.final)) or "0"]
    for q in range(1, nfa.n + 1):
        lines.append(" ".join([str(q)] + [sc.format_set(nfa.delta[q][a]) for a in nfa.alphabet]))
    return "\n".join(lines) + "\n"


def random_nfa(rng, max_states=5):
    """A random NFA with 1..max_states states and 1..3 symbols (in random order)."""
    n = rng.randint(1, max_states)
    alphabet = rng.sample("abc", rng.randint(1, 3))
    density = rng.choice([0.1, 0.25, 0.4, 0.6])
    delta = {q: {a: frozenset(p for p in range(1, n + 1) if rng.random() < density)
                 for a in alphabet}
             for q in range(1, n + 1)}
    start = frozenset(q for q in range(1, n + 1) if rng.random() < 0.4)
    final = frozenset(q for q in range(1, n + 1) if rng.random() < 0.4)
    return sc.NFA(n, alphabet, delta, start, final)


def nfa_accepts(nfa, word):
    """Independent of the subset construction: is there a path labelled word
    from a start state of N to a final state of N?"""

    @lru_cache(maxsize=None)
    def accepts_from(q, i):
        if i == len(word):
            return q in nfa.final
        return any(accepts_from(p, i + 1) for p in nfa.delta[q][word[i]])

    return any(accepts_from(q, 0) for q in nfa.start)


def parse_subset(text):
    if text == "0":
        return frozenset()
    assert text.startswith("{") and text.endswith("}"), text
    return frozenset(int(q) for q in text[1:-1].split())


def parse_printed_table(text, alphabet):
    """Read back the table printed for one case."""
    lines = text.splitlines()
    assert lines[0].split() == list(alphabet) + ["subset"], lines[0]
    assert lines[-2].startswith("Initial state: "), lines[-2]
    assert lines[-1].startswith("Final states: "), lines[-1]
    names, subsets, delta, start_marks, final_marks = [], {}, {}, [], set()
    for line in lines[1:-2]:
        marker, rest = line[:3], line[4:]
        parts = rest.split(None, len(alphabet) + 1)
        name, targets, subset = parts[0], parts[1:-1], parts[-1]
        names.append(name)
        subsets[name] = parse_subset(subset)
        for a, target in zip(alphabet, targets):
            delta[(name, a)] = target
        if marker.startswith("->"):
            start_marks.append(name)
        if marker.endswith("*"):
            final_marks.add(name)
    start = lines[-2][len("Initial state: "):]
    finals_text = lines[-1][len("Final states: "):]
    finals = set() if finals_text == "0" else set(finals_text.split())
    return {"names": names, "subsets": subsets, "delta": delta, "start": start,
            "finals": finals, "start_marks": start_marks, "final_marks": final_marks}


def words(alphabet, max_length):
    for length in range(max_length + 1):
        for word in itertools.product(alphabet, repeat=length):
            yield word


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class StatementExampleTest(unittest.TestCase):
    """The example of the statement of the assignment."""

    def test_output(self):
        self.assertEqual(solve_text(STATEMENT_INPUT), STATEMENT_OUTPUT)

    def test_program_from_stdin_and_from_file(self):
        code, out, err = run_program(stdin=STATEMENT_INPUT)
        self.assertEqual((code, out, err), (0, STATEMENT_OUTPUT, ""))
        path = os.path.join(ROOT, "examples", "statement_example.txt")
        code, out, err = run_program([path])
        self.assertEqual((code, out, err), (0, STATEMENT_OUTPUT, ""))

    def test_steps(self):
        out = solve_text(STATEMENT_INPUT, steps=True)
        self.assertTrue(out.startswith(
            "q0 = S = {3 5}\n"
            "  delta(q0, a) = Delta(3, a) U Delta(5, a) = {2 4} U {1 5} = {1 2 4 5} = q1 (new)\n"
            "  delta(q0, b) = Delta(3, b) U Delta(5, b) = 0 U {4} = {4} = q2 (new)\n"))
        self.assertIn("  delta(q5, a) = union over the empty set = 0 = q5\n", out)
        self.assertTrue(out.endswith(STATEMENT_OUTPUT))   # the table is still printed

    def test_full_construction(self):
        out = solve_text(STATEMENT_INPUT, full=True)
        table = parse_printed_table(out, ["a", "b"])
        self.assertEqual(len(table["names"]), 2 ** 5)
        self.assertEqual(len(set(table["subsets"].values())), 2 ** 5)   # all subsets of Q
        # the accessible states keep the same names and rows as without --full
        reachable = STATEMENT_OUTPUT.splitlines()[1:8]
        self.assertEqual([line.split() for line in out.splitlines()[1:8]],
                         [line.split() for line in reachable])


class SmallCasesTest(unittest.TestCase):

    def test_several_cases(self):
        with open(os.path.join(ROOT, "examples", "more_cases.txt")) as handle:
            text = handle.read()
        out = solve_text(text)
        self.assertEqual(out.count("Initial state: q0"), 3)
        self.assertIn(
            "        a   subset\n"
            "->* q0  q1  {1 2}\n"
            "  * q1  q2  {2}\n"
            "    q2  q2  0\n"
            "Initial state: q0\n"
            "Final states: q0 q1\n", out)
        # "the third symbol from the right is a" needs 2^3 = 8 states
        self.assertIn("Final states: q4 q5 q6 q7\n", out)

    def test_empty_start_set_and_no_final_states(self):
        out = solve_text("1\n2\n0\na\n0\n1 {2}\n2 0\n")
        self.assertEqual(out, "        a   subset\n"
                              "->  q0  q0  0\n"
                              "Initial state: q0\n"
                              "Final states: 0\n")

    def test_one_state(self):
        out = solve_text("1\n1\n1\na b\n1\n1 {1} 0\n")
        self.assertEqual(out, "        a   b   subset\n"
                              "->* q0  q0  q1  {1}\n"
                              "    q1  q1  q1  0\n"
                              "Initial state: q0\n"
                              "Final states: q0\n")

    def test_zero_cases(self):
        self.assertEqual(solve_text("0\n"), "")

    def test_alphabet_order_is_kept(self):
        out = solve_text("1\n2\n1\nb a\n2\n1 {2} {1}\n2 0 0\n")
        self.assertTrue(out.startswith("        b   a   subset\n"))
        self.assertIn("->  q0  q1  q0  {1}\n", out)


class InputVariantsTest(unittest.TestCase):
    """Different ways of writing the example of the statement give the same answer."""

    def check(self, text):
        self.assertEqual(solve_text(text), STATEMENT_OUTPUT)

    def test_rows_without_state_number(self):
        self.check("1\n5\n3 5\na b\n1 4\n{1 5} 0\n{1} 0\n{2 4} 0\n0 {5}\n{1 5} {4}\n")

    def test_commas_and_extra_spaces(self):
        self.check("1\n5\n 3  5 \na   b\n1\t4\n1 {1, 5} 0\n2 { 1 } 0\n"
                   "3 {2,4} 0\n4 0 {5}\n5 {1,5}  {4}  \n")

    def test_rows_in_other_order(self):
        self.check("1\n5\n3 5\na b\n1 4\n5 {1 5} {4}\n3 {2 4} 0\n1 {1 5} 0\n4 0 {5}\n2 {1} 0\n")

    def test_blank_lines(self):
        self.check("\n1\n\n5\n3 5\n\na b\n1 4\n\n1 {1 5} 0\n2 {1} 0\n3 {2 4} 0\n"
                   "4 0 {5}\n5 {1 5} {4}\n\n\n")

    def test_other_notations(self):
        self.check("1\n5\n{3 5}\na b\n1 4\n1: {1 5} ∅\n2: {1} {}\n3: {2 4} 0\n"
                   "4: 0 {5}\n5: {1 5} {4}\n")

    def test_windows_line_endings_and_byte_order_mark(self):
        data = STATEMENT_INPUT.replace("\n", "\r\n").encode("utf-8")
        for stdin in (data, b"\xef\xbb\xbf" + data):
            code, out, err = run_program(stdin=stdin)
            self.assertEqual((code, out, err), (0, STATEMENT_OUTPUT, ""))

    def test_utf16_file(self):
        # Windows PowerShell 5 writes "echo ... > file" in UTF-16 with a BOM
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "input.txt")
            with open(path, "wb") as handle:
                handle.write(STATEMENT_INPUT.replace("\n", "\r\n").encode("utf-16"))
            code, out, err = run_program([path])
            self.assertEqual((code, out, err), (0, STATEMENT_OUTPUT, ""))


class ErrorsTest(unittest.TestCase):
    """Wrong inputs: a clear message on stderr, nothing extra on stdout, exit code 1."""

    def check_error(self, text, *fragments, args=(), stdout=""):
        code, out, err = run_program(list(args), stdin=text)
        self.assertEqual(code, 1)
        self.assertEqual(out, stdout)
        self.assertTrue(err.startswith("error: "), err)
        for fragment in fragments:
            self.assertIn(fragment, err)

    def test_row_with_missing_entry(self):
        self.check_error("1\n2\n1\na b\n2\n1 {2}\n2 0 0\n", "line 6", "2 entries")

    def test_row_with_too_many_entries(self):
        self.check_error("1\n2\n1\na\n2\n1 {2} 0\n2 0\n", "line 6", "1 entry ")

    def test_state_without_braces_is_not_an_entry(self):
        self.check_error("1\n2\n1\na b\n2\n1 2 0\n2 0 0\n", "line 6", "set in braces")

    def test_state_out_of_range(self):
        self.check_error("1\n2\n1\na\n2\n1 {7}\n2 0\n", "line 6", "'7' is not a state")

    def test_input_ends_early(self):
        self.check_error("1\n3\n1\na\n3\n1 {2}\n2 {3}\n", "ended", "row 3")

    def test_bad_number_of_states(self):
        self.check_error("1\nfive\n", "line 2", "number of states")

    def test_repeated_symbol(self):
        self.check_error("1\n1\n1\na a\n1\n1 0 0\n", "line 4", "more than once")

    def test_repeated_row(self):
        self.check_error("1\n2\n1\na\n2\n1 {2}\n1 0\n", "line 7", "appears twice")

    def test_unclosed_brace(self):
        self.check_error("1\n2\n1\na\n2\n1 {2\n2 0\n", "line 6", "not closed")

    def test_alphabet_given_instead_of_initial_states(self):
        self.check_error("1\n2\na\n1\n1 {2}\n2 0\n", "line 3", "initial states")

    def test_missing_file(self):
        self.check_error("", "no_such_file.txt", args=["no_such_file.txt"])

    def test_first_case_is_printed_before_an_error_in_the_second(self):
        text = STATEMENT_INPUT.replace("1\n", "2\n", 1) + "2\n1\na\n"
        self.check_error(text, "ended", stdout=STATEMENT_OUTPUT)

    def test_full_is_limited(self):
        n = sc.MAX_FULL_STATES + 1
        rows = "".join("%d 0\n" % q for q in range(1, n + 1))
        text = "1\n%d\n1\na\n1\n%s" % (n, rows)
        self.check_error(text, "--full", args=["--full"])
        code, out, err = run_program(stdin=text)       # without --full it works
        self.assertEqual(code, 0)


class RandomAutomataTest(unittest.TestCase):
    """For many random NFAs, the printed DFA is checked against the definition
    of the subset construction, and its language is compared with the
    language of the NFA on every string of length <= 5."""

    def test_random_nfas(self):
        rng = random.Random(2026)
        for _ in range(250):
            nfa = random_nfa(rng)
            out = solve_text("1\n" + nfa_to_text(nfa))
            with self.subTest(nfa=nfa_to_text(nfa)):
                self.check_dfa(nfa, parse_printed_table(out, nfa.alphabet))

    def check_dfa(self, nfa, table):
        names, subsets, delta = table["names"], table["subsets"], table["delta"]
        # names q0, q1, ... in order; different states are different subsets
        self.assertEqual(names, ["q%d" % i for i in range(len(names))])
        self.assertEqual(len(set(subsets.values())), len(names))
        # s_M = S, and the markers agree with the last two lines
        self.assertEqual(table["start"], "q0")
        self.assertEqual(subsets["q0"], nfa.start)
        self.assertEqual(table["start_marks"], ["q0"])
        self.assertEqual(table["final_marks"], table["finals"])
        for name in names:
            # F_M = {A : A intersects F}
            self.assertEqual(name in table["finals"], bool(subsets[name] & nfa.final))
            for a in nfa.alphabet:
                # delta_M(A, a) = union of Delta(q, a) for q in A (one target per symbol)
                expected = frozenset().union(*[nfa.delta[q][a] for q in subsets[name]])
                self.assertEqual(subsets[delta[(name, a)]], expected)
        # every printed state is accessible from q0
        seen, pending = {"q0"}, ["q0"]
        while pending:
            name = pending.pop()
            for a in nfa.alphabet:
                if delta[(name, a)] not in seen:
                    seen.add(delta[(name, a)])
                    pending.append(delta[(name, a)])
        self.assertEqual(seen, set(names))
        # same language as the NFA
        for word in words(nfa.alphabet, 5):
            state = "q0"
            for a in word:
                state = delta[(state, a)]
            self.assertEqual(state in table["finals"], nfa_accepts(nfa, word), word)

    def test_full_keeps_the_language(self):
        rng = random.Random(7)
        for _ in range(40):
            nfa = random_nfa(rng, max_states=4)
            dfa = sc.subset_construction(nfa, full=True)
            self.assertEqual(len(dfa.states), 2 ** nfa.n)
            for word in words(nfa.alphabet, 4):
                state = dfa.start
                for a in word:
                    state = dfa.delta[(state, a)]
                self.assertEqual(state in dfa.final, nfa_accepts(nfa, word))


class DiagramsTest(unittest.TestCase):

    def test_dot_files(self):
        with tempfile.TemporaryDirectory() as folder:
            out = solve_text(STATEMENT_INPUT, dot_directory=folder)
            self.assertEqual(out, STATEMENT_OUTPUT)        # the table is not changed
            with open(os.path.join(folder, "case1_dfa.dot"), encoding="utf-8") as handle:
                dfa = handle.read()
            with open(os.path.join(folder, "case1_nfa.dot"), encoding="utf-8") as handle:
                nfa = handle.read()
        self.assertIn('"start0" -> "q0";', dfa)
        self.assertIn('"q1" [label="q1\\n{1 2 4 5}", shape=doublecircle];', dfa)
        self.assertIn('"q5" -> "q5" [label="a, b"];', dfa)
        self.assertIn('"start0" -> "3";', nfa)
        self.assertIn('"start1" -> "5";', nfa)
        self.assertIn('"1" [label="1", shape=doublecircle];', nfa)
        self.assertIn('"5" -> "1" [label="a"];', nfa)


if __name__ == "__main__":
    unittest.main()
