"""Build script for How to Play Interactive Jupyter Notebooks.

Generates:
1. 00_interactive_how_to_play_walkthrough.ipynb
2. 01_interactive_scenarios_lab.ipynb
"""

from hashlib import sha256
from pathlib import Path

import nbformat as nbf

HOW_TO_PLAY_DIR = Path(__file__).resolve().parent


def build_walkthrough_notebook():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "authors": [{"name": "Panepistimion Symbol Game Pedagog Swarm"}],
        "language_info": {"name": "python", "version": "3.12"},
    }

    cells = []

    # Cell 0: Title & Header
    cells.append(
        nbf.v4.new_markdown_cell("""# 00 - Interactive How to Play Walkthrough: The Discrete Host Governor

**AuthorityEffect:** `None` (Academic & educational curriculum walkthrough).
**Lead Governance Council:** `L3_nous_panepistimion` (Academy, Pedagogy, and Research Education).
**Companion Test Suite:** [`test_how_to_play_scenarios.py`](test_how_to_play_scenarios.py).

> **Claim-typing legend**
> - **[Pinned]**: reproduced from local test suite `test_how_to_play_scenarios.py` and exact rational arithmetic.
> - **[Checked locally]**: exercised by the declared triangle teaching runtime, not a native host functional.
> - **[Declared]**: 3-cycle carrier graph $G = (V, E)$ with initial claims $c_e \\in \\mathbb{Q}$.
> - **[Open]**: general polynomial-time chord decoupling on non-planar higher-genus carrier 2-complexes.

---

> This notebook is a finite triangle teaching model. ASSERT records annotations,
> and VERIFY checks only zero triangle circulation. Read [ten ways to play](06_ten_useful_ways_to_play.md)
> for other routes. It is not the native host and does not certify arbitrary claims.

## 1. The Pedagogical Hook: Why Continuous Softmax Needs a Discrete Governor

In standard Large Language Model reasoning, generation proceeds autoregressively via dense matrix multiplication:

$$\\mathbf{h}_{t+1} = \\text{TransformerBlock}(\\mathbf{h}_t), \\quad P(w_{t+1}) = \\text{Softmax}(W_U \\mathbf{h}_{t+1} / \\tau)$$

A generated explanation can contain a false claim. The teaching board demonstrates one independently replayable check; it does not establish a causal explanation or general remedy for model errors.

This exercise illustrates separation of candidate generation and checking; it does not demonstrate a general solution to model hallucination:
1. **The Continuous Proposer (Layer 1/2):** Generates candidate moves, hypotheses, and proof sketches freely.
2. **The Discrete Host Governor (Layer 3):** An independent, deterministic replay oracle that admits or refuses moves based on exact rational topological invariants.

![Dual Space Governor Loop](assets/01_dual_space_governor_loop.svg)

---

## 2. Learning Objectives

In this interactive walkthrough, you will:
1. **[Declared]** Initialize an educational Symbol Game board state with 3 vertices, 3 directed edges, and finite turn fuel.
2. **[Pinned]** Execute and inspect the four legal game moves: `ASSERT`, `CUT`, `VERIFY`, and `RETRACT`.
3. **[Checked locally]** Observe how the **Strict Lyapunov Descent Gate** prevents non-monotonic cheating and triggers atomic rollbacks.
4. **[Pinned]** Experience the **Carrier Firewall (FW-CARRIER)** intercepting smuggled edge claims.
5. **[Pinned]** Perform exact chord repair to reduce circulation $\\Phi_1 \\to 0$ and emit a certified terminal receipt.""")
    )

    # Cell 1: Environment Setup
    cells.append(
        nbf.v4.new_code_cell("""import sys
from pathlib import Path
import unittest

# Ensure current lesson directory is on sys.path
lesson_dir = Path(".").resolve()
if not (lesson_dir / "educational_governor.py").is_file():
    candidates = [lesson_dir / "education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/0_how_to_play_the_symbol_game"]
    lesson_dir = next((p for p in candidates if (p / "educational_governor.py").is_file()), lesson_dir)
if str(lesson_dir) not in sys.path:
    sys.path.insert(0, str(lesson_dir))

# Import educational governor and interactive rendering engine
try:
    from IPython.display import display
except ImportError:
    display = print

from educational_governor import EducationalHostGovernor
from test_how_to_play_scenarios import TestSymbolGameHowToPlay
from interactive_board import (
    render_html_board,
    render_svg_triangle,
    display_board,
    run_scenario_with_feedback,
    create_interactive_game_widget,
)

print(f"Python interpreter: {sys.version.split()[0]}")
print("Educational Host Governor and Interactive Board initialized successfully!")""")
    )

    # Cell 2: Board State Explanation
    cells.append(
        nbf.v4.new_markdown_cell("""## 3. The Canonical Board State

The standard educational board consists of a directed 3-cycle triangle graph:
- **Vertices:** $V = \\{0, 1, 2\\}$
- **Carrier Edges:** $E = \\{0\\to 1, 1\\to 2, 2\\to 0\\}$
- **Initial Claims:** $c(0\\to 1) = 2, \\quad c(1\\to 2) = 1, \\quad c(2\\to 0) = 3$
- **Turn Fuel:** 5 units (each admitted or refused attempt consumes 1 unit of fuel).

The total coboundary circulation defect $\\Phi_1$ is calculated as the signed sum along the directed cycle:

$$\\Phi_1 = |c(0\\to 1) + c(1\\to 2) + c(2\\to 0)| = |2 + 1 + 3| = 6 \\neq 0$$

Because $\\Phi_1 = 6 > 0$, the board has an active holonomy defect. Below, we instantiate the host governor and view the live board state.

![Canonical 3-Cycle Triangle](assets/02_triangle_constraint_cycle.svg)""")
    )

    # Cell 3: Initial Board Display
    cells.append(
        nbf.v4.new_code_cell("""# Instantiate the Educational Host Governor
vertices = [0, 1, 2]
edges = ["0->1", "1->2", "2->0"]
initial_claims = {"0->1": 2, "1->2": 1, "2->0": 3}

board = EducationalHostGovernor(vertices, edges, initial_claims, fuel=5)
initial_defect = board.compute_total_defect()

print(f"Board Initialized: Vertices={vertices}, Edges={edges}")
print(f"Circulation Defect Phi_1 = {initial_defect}")
print(f"Turn Fuel Remaining = {board.fuel} / {board.initial_fuel}")

display_board(board)""")
    )

    # Cell 4: Move 1 - ASSERT
    cells.append(
        nbf.v4.new_markdown_cell("""## 4. Move 1: `ASSERT` — Declaring Invariants

The `ASSERT` move enables a player to register mathematical facts, tree spanning certificates, or algebraic relationships into the host's invariant register.

**Rules for ASSERT:**
- Consumes 1 turn fuel.
- Requires non-empty relation string syntax.
- **Does not mutate edge claims or change defect $\\Phi_1$.**

Let us run Scenario 1: declaring `TREE_SPAN_0_1_2`.""")
    )

    # Cell 5: Execute ASSERT (Scenario 1)
    cells.append(
        nbf.v4.new_code_cell("""# Scenario 1: Propose an ASSERT move
proposal_assert = {
    "move_type": "ASSERT",
    "payload": {"relation": "TREE_SPAN_0_1_2"}
}

res_assert = board.execute_move(proposal_assert)

# Mechanical assertions
assert res_assert["decision"] == "ADMITTED", f"Expected ADMITTED, got {res_assert['decision']}"
assert res_assert["defect_phi1"] == "6", "ASSERT must not mutate defect Phi_1!"
assert "TREE_SPAN_0_1_2" in board.invariants, "Invariant was not added to the register!"
assert board.fuel == 4, f"Expected 4 fuel remaining, got {board.fuel}"

print("Scenario 1 Executed Successfully: Invariant registered, defect preserved at 6.")
display_board(board, res_assert)""")
    )

    # Cell 6: Move 2 - CUT & Lyapunov Monotonicity
    cells.append(
        nbf.v4.new_markdown_cell("""## 5. Move 2: `CUT` — Strict Lyapunov Descent & Rollback Protection

The `CUT` move proposes new rational values for edge claims. This is where the core **Lyapunov Monotonicity Invariant** is enforced:

$$\\Phi_1(S') < \\Phi_1(S)$$

If a proposed move would cause $\\Phi_1(S') \\ge \\Phi_1(S)$ (increasing or preserving the defect), the host executes an **atomic rollback**:
1. The proposed claims are discarded immediately.
2. The previous claims are restored.
3. Turn fuel is still decremented as an anti-spam penalty.

Let us test both failure and success cases:
- **Scenario 3:** Attempt an adversarial non-monotonic CUT ($c(2\\to 0) = 7 \\implies \\Phi_1 = 10$).
- **Scenario 2:** Propose a strictly descending CUT ($c(2\\to 0) = -1 \\implies \\Phi_1 = 2$).

![Strict Lyapunov Descent](assets/04_strict_lyapunov_descent.svg)""")
    )

    # Cell 7: Execute Bad CUT (Scenario 3)
    cells.append(
        nbf.v4.new_code_cell("""# Scenario 3: Propose an adversarial CUT increasing defect to 10
proposal_bad_cut = {
    "move_type": "CUT",
    "payload": {"proposed_claims": {"2->0": 7}}
}

res_bad_cut = board.execute_move(proposal_bad_cut)

print(f"Governor Decision: {res_bad_cut['decision']}")
print(f"Governor Notice: {res_bad_cut['message']}")

# Verification of rollback
assert res_bad_cut["decision"] == "REFUSED_MONOTONICITY_VIOLATION"
assert board.claims["2->0"] == 3, "Rollback failed: original claim 3 was not preserved!"
assert board.fuel == 3, "Fuel was not consumed for refused attempt!"

display_board(board, res_bad_cut)""")
    )

    # Cell 8: Execute Valid Descending CUT (Scenario 2)
    cells.append(
        nbf.v4.new_code_cell("""# Scenario 2: Propose a valid descending CUT
proposal_valid_cut = {
    "move_type": "CUT",
    "payload": {"proposed_claims": {"2->0": -1}}
}

# 2 + 1 + (-1) = 2 < 6 (Strict descent)
res_valid_cut = board.execute_move(proposal_valid_cut)

assert res_valid_cut["decision"] == "ADMITTED"
assert res_valid_cut["defect_phi1"] == "2", f"Expected defect 2, got {res_valid_cut['defect_phi1']}"
assert board.fuel == 2, f"Expected 2 fuel remaining, got {board.fuel}"

print("Scenario 2 Executed Successfully: Defect dropped strictly from 6 -> 2!")
display_board(board, res_valid_cut)""")
    )

    # Cell 9: Carrier Firewall Explanation
    cells.append(
        nbf.v4.new_markdown_cell("""## 6. Move 3: Carrier Domain Smuggling (FW-CARRIER)

A common LLM strategy when trapped in a contradiction is to invent new variables or edges not present in the problem statement. The **Carrier Firewall** makes this impossible:

$$\\text{Domain}(c') \\subseteq E_{\\text{pinned}}$$

Any proposed claim on an edge $e \\notin E$ triggers an immediate `REFUSED_CARRIER_DOMAIN` rejection.

Let us test Scenario 4 by trying to modify non-existent edge `3->4`.""")
    )

    # Cell 10: Execute Carrier Smuggling (Scenario 4)
    cells.append(
        nbf.v4.new_code_cell("""# Scenario 4: Attempt carrier domain smuggling
proposal_smuggle = {
    "move_type": "CUT",
    "payload": {"proposed_claims": {"3->4": 0}}
}

res_smuggle = board.execute_move(proposal_smuggle)

print(f"Governor Decision: {res_smuggle['decision']}")
print(f"Refusal Notice: {res_smuggle['message']}")

assert res_smuggle["decision"] == "REFUSED_CARRIER_DOMAIN"
assert "not in pinned carrier" in res_smuggle["message"]
assert board.fuel == 1, "Fuel was not consumed!"

display_board(board, res_smuggle)""")
    )

    # Cell 11: VERIFY and Terminal Certification
    cells.append(
        nbf.v4.new_markdown_cell("""## 7. Move 4: `VERIFY` & Terminal Receipt Certification

The `VERIFY` move requests formal proof certification from the host:
- If $\\Phi_1 > 0$, the request is refused with `REFUSED_NONZERO_DEFECT` and the board remains unsealed.
- If $\\Phi_1 = 0$, the host issues `ACCEPTED_ZERO_DEFECT`, locks the board (`is_terminal = True`), and emits a scoped teaching receipt.
- Once sealed, **any subsequent mutation is permanently rejected** with `REFUSED_TERMINAL_STATE`.

Let us demonstrate:
1. **Scenario 5:** Calling `VERIFY` prematurely while $\\Phi_1 = 2$.
2. **Scenario 6:** Achieving $\\Phi_1 = 0$ via chord cut $c(2\\to 0) = -3$, then calling `VERIFY`.
3. **Scenario 7:** Attempting post-terminal mutation on the sealed board.""")
    )

    # Cell 12: Execute Scenarios 5, 6, 7
    cells.append(
        nbf.v4.new_code_cell("""# Scenario 5: Early VERIFY while Phi_1 = 2
res_early = board.execute_move({"move_type": "VERIFY", "payload": {}})
assert res_early["decision"] == "REFUSED_NONZERO_DEFECT"
assert not board.is_terminal, "Board must not seal on non-zero defect!"
print(f"Scenario 5 Check: Premature VERIFY correctly refused (defect={res_early['defect_phi1']}).")

# Initialize fresh board to demonstrate the complete winning trajectory
game = EducationalHostGovernor(vertices, edges, initial_claims, fuel=6)

# Execute exact chord cut: 2 + 1 + (-3) = 0
res_chord = game.execute_move({
    "move_type": "CUT",
    "payload": {"proposed_claims": {"2->0": -3}}
})
assert res_chord["decision"] == "ADMITTED"
assert res_chord["defect_phi1"] == "0"

# Scenario 6: Call VERIFY at zero defect
res_cert = game.execute_move({"move_type": "VERIFY", "payload": {}})
assert res_cert["decision"] == "ACCEPTED_ZERO_DEFECT"
assert game.is_terminal is True
assert res_cert["receipt"]["status"] == "CERTIFIED"
print("Scenario 6 Check: Zero defect certified, receipt emitted!")
display_board(game, res_cert)

# Scenario 7: Attempt post-terminal mutation
res_post = game.execute_move({
    "move_type": "CUT",
    "payload": {"proposed_claims": {"2->0": 0}}
})
assert res_post["decision"] == "REFUSED_TERMINAL_STATE"
print(f"Scenario 7 Check: Post-terminal mutation rejected ({res_post['decision']}).")""")
    )

    # Cell 13: Full Automated Test Battery
    cells.append(
        nbf.v4.new_markdown_cell("""## 8. Automated Headless Test Battery Verification

Every pedagogical document in this repository must be mechanically attested by an automated test suite. Below, we load and execute all 7 scenarios from `TestSymbolGameHowToPlay` directly inside the notebook.""")
    )

    # Cell 14: Run Unit Tests
    cells.append(
        nbf.v4.new_code_cell("""# Run the official Symbol Game test suite directly
suite = unittest.TestLoader().loadTestsFromTestCase(TestSymbolGameHowToPlay)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

assert result.wasSuccessful(), "One or more gameplay unit tests failed!"
print(f"\\n100% PASS: All {result.testsRun} gameplay scenario tests passed successfully!")""")
    )

    # Cell 15: Interactive Player Workbench
    cells.append(
        nbf.v4.new_markdown_cell("""## 9. Interactive Player Workbench

Use the reactive control panel below to test custom moves, tweak edge claims with the slider, or trigger fast scenarios with immediate HTML and SVG visual feedback in your browser session.""")
    )

    # Cell 16: Launch Widget
    cells.append(
        nbf.v4.new_code_cell("""# Launch the interactive ipywidgets player workbench
widget_panel = create_interactive_game_widget()
if widget_panel is not None:
    display(widget_panel)
else:
    print("Running in headless / non-widget environment.")""")
    )

    # Cell 17: Exercises
    cells.append(
        nbf.v4.new_markdown_cell("""## 10. Student Exercises

### Exercise 00.1: Monotonicity Proof Obligation
Why does the host governor refuse a move if $\\Phi_1(S') = \\Phi_1(S)$ (defect stays the same) on a `CUT` move, rather than allowing neutral steps?

<details>
<summary><b>Click to reveal solution</b></summary>
Allowing non-decreasing neutral moves ($\\Phi_1(S') = \\Phi_1(S)$) permits infinite wandering loops and cycles without guaranteed termination. Requiring strict descent ($\\Phi_1(S') < \\Phi_1(S)$) makes defect $\\Phi_1$ a strict discrete Lyapunov function, ensuring finite operational closure within the fuel bound.
</details>

---

### Exercise 00.2: The Chord Decoupling Theorem
On a cycle of length $k$, how many edge claims must be modified to reduce an arbitrary circulation defect $\\Phi_1$ to zero?

<details>
<summary><b>Click to reveal solution</b></summary>
Exactly one edge (the chord edge). Holding a spanning tree of $k-1$ edge reports fixed leaves one remaining cycle edge. This repair edits a report; a vertex gauge transformation preserves circulation. Setting $c(e_{\\text{chord}}) = -\\sum_{e \\in \\text{Tree}} c(e)$ immediately sets the cycle sum to 0.
</details>

---

### Exercise 00.3: Three-Layer Sovereignty in Practice
Which layer of the architecture is responsible for ensuring that a post-terminal board cannot be modified?

<details>
<summary><b>Click to reveal solution</b></summary>
Layer 3 (The Discrete Host Governor / Replay Oracle). Neither the LLM weights (Layer 1) nor the logit sampler (Layer 2) can enforce global state immutability; only the independent host runtime can reject post-terminal mutations.
</details>""")
    )

    # Cell 18: Anchors
    cells.append(
        nbf.v4.new_markdown_cell("""## 11. Anchors

- **Research Papers:**
  - Paper 032: §1, §3 (The Wager), §5 (Discrete $L_1$ Projection), §10 (Replay Governance)
  - Paper 003: §III (Epistemic Immune System), §IV (Discrete Host Governor Mechanics)
- **Claim Ledger IDs:** `PO032-C01`, `PO032-C02`, `PO032-C04`
- **Formal Verification Source:** [`education/notebooks/lessons/how_to_play/test_how_to_play_scenarios.py`](test_how_to_play_scenarios.py)
- **Interactive Engine:** [`education/notebooks/lessons/how_to_play/interactive_board.py`](interactive_board.py)
- **Visual Assets:**
  - [`assets/01_dual_space_governor_loop.svg`](file:///c:/Users/a343o/source/repos/the_symbol_game/education/notebooks/lessons/how_to_play/assets/01_dual_space_governor_loop.svg)
  - [`assets/02_triangle_constraint_cycle.svg`](file:///c:/Users/a343o/source/repos/the_symbol_game/education/notebooks/lessons/how_to_play/assets/02_triangle_constraint_cycle.svg)
  - [`assets/03_four_legal_moves.svg`](file:///c:/Users/a343o/source/repos/the_symbol_game/education/notebooks/lessons/how_to_play/assets/03_four_legal_moves.svg)
  - [`assets/04_strict_lyapunov_descent.svg`](file:///c:/Users/a343o/source/repos/the_symbol_game/education/notebooks/lessons/how_to_play/assets/04_strict_lyapunov_descent.svg)""")
    )

    for index, cell in enumerate(cells):
        cell.id = sha256(f"{index}:{cell.source}".encode()).hexdigest()[:16]
    nb.cells = cells

    out_path = HOW_TO_PLAY_DIR / "00_interactive_how_to_play_walkthrough.ipynb"
    with open(out_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Wrote {out_path} ({len(cells)} cells).")


def build_lab_notebook():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "authors": [{"name": "Panepistimion Symbol Game Pedagog Swarm"}],
        "language_info": {"name": "python", "version": "3.12"},
    }

    cells = []

    # Cell 0: Header
    cells.append(
        nbf.v4.new_markdown_cell("""# 01 - Interactive Scenarios Lab: Boundary Probes & Refusal Invariants

**AuthorityEffect:** `None` (Academic & educational curriculum diagnostic lab).
**Lead Governance Council:** `L3_nous_panepistimion` (Academy, Pedagogy, and Research Education).
**Companion Test Suite:** [`test_how_to_play_scenarios.py`](test_how_to_play_scenarios.py).

> **Claim-typing legend**
> - **[Pinned]**: reproduced from local test suite `test_how_to_play_scenarios.py`.
> - **[Checked locally]**: finite state machine refusal boundaries and immutability invariants.
> - **[Declared]**: diagnostic probe configurations across seven canonical edge cases.
> - **[Open]**: automated synthesis of counterexamples for arbitrary simplicial complexes.

---

## 1. Laboratory Overview

This laboratory provides an adversarial testing workbench for studying the refusal boundaries of the **Discrete Host Governor**. Rather than pursuing a happy-path victory, we deliberately probe the governor with malformed proposals, non-monotonic cuts, out-of-domain edges, and premature verification requests.

### The Seven Canonical Scenarios Under Audit:
1. `ASSERT` invariant registration (neutral defect preservation)
2. Valid strictly descending `CUT`
3. Non-monotonic `CUT` with atomic rollback
4. Carrier smuggling injection (`REFUSED_CARRIER_DOMAIN`)
5. Premature `VERIFY` on positive defect (`REFUSED_NONZERO_DEFECT`)
6. Exact chord repair and terminal seal (`ACCEPTED_ZERO_DEFECT`)
7. Post-terminal mutation block (`REFUSED_TERMINAL_STATE`)

![Four Legal Moves](assets/03_four_legal_moves.svg)""")
    )

    # Cell 1: Environment Setup
    cells.append(
        nbf.v4.new_code_cell("""import sys
from pathlib import Path
import unittest

lesson_dir = Path(".").resolve()
if not (lesson_dir / "educational_governor.py").is_file():
    candidates = [lesson_dir / "education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/0_how_to_play_the_symbol_game"]
    lesson_dir = next((p for p in candidates if (p / "educational_governor.py").is_file()), lesson_dir)
if str(lesson_dir) not in sys.path:
    sys.path.insert(0, str(lesson_dir))

from educational_governor import EducationalHostGovernor
from test_how_to_play_scenarios import TestSymbolGameHowToPlay
from interactive_board import display_board, run_scenario_with_feedback

print("Interactive Scenarios Lab initialized.")""")
    )

    # Cell 2: Lab Section 1
    cells.append(
        nbf.v4.new_markdown_cell("""## 2. Lab Station 1: The Monotonicity Trap & Rollback Mechanics

In this station, we inspect how the host governor guarantees data integrity when an agent proposes a move that worsens the defect.

**Experiment:**
1. Record baseline state $(S_0)$.
2. Propose claim $c(2\\to 0) = 7$, which increases circulation from 6 to 10.
3. Assert that the governor refuses the move, preserves $c(2\\to 0) = 3$, and exacts a 1-fuel penalty.""")
    )

    # Cell 3: Code Station 1
    cells.append(
        nbf.v4.new_code_cell("""host = EducationalHostGovernor([0, 1, 2], ["0->1", "1->2", "2->0"], {"0->1": 2, "1->2": 1, "2->0": 3}, fuel=10)

res, commentary = run_scenario_with_feedback(3, host)
print(commentary)
print(f"Receipt Decision: {res['decision']}")
print(f"Preserved Claims: {dict(host.claims)}")
print(f"Fuel Consumption: Remaining={host.fuel}")

assert res["decision"] == "REFUSED_MONOTONICITY_VIOLATION"
assert host.claims["2->0"] == 3
assert host.fuel == 9

display_board(host, res)""")
    )

    # Cell 4: Lab Section 2
    cells.append(
        nbf.v4.new_markdown_cell("""## 3. Lab Station 2: The Carrier Smuggling Probe

In this station, we test whether the governor can be fooled by proposing a modification to an edge outside the carrier graph $E$.

**Experiment:**
Propose $c(3\\to 4) = 0$. The host must immediately reject without altering internal state.""")
    )

    # Cell 5: Code Station 2
    cells.append(
        nbf.v4.new_code_cell("""res, commentary = run_scenario_with_feedback(4, host)
print(commentary)
print(f"Receipt Decision: {res['decision']}")

assert res["decision"] == "REFUSED_CARRIER_DOMAIN"
assert "3->4" not in host.claims
assert host.fuel == 8

display_board(host, res)""")
    )

    # Cell 6: Lab Section 3
    cells.append(
        nbf.v4.new_markdown_cell("""## 4. Lab Station 3: Premature Verification & Terminal Seal Invariants

In this station, we verify that:
1. `VERIFY` cannot be cheated while $\\Phi_1 > 0$.
2. Once $\\Phi_1 = 0$, `VERIFY` emits a permanent seal.
3. Once sealed, no subsequent move can mutate the state.""")
    )

    # Cell 7: Code Station 3
    cells.append(
        nbf.v4.new_code_cell("""# 1. Premature verify
res_premature, comm5 = run_scenario_with_feedback(5, host)
assert res_premature["decision"] == "REFUSED_NONZERO_DEFECT"
assert not host.is_terminal

# 2. Exact chord repair and winning verify
res_win, comm6 = run_scenario_with_feedback(6, host)
assert res_win["decision"] == "ACCEPTED_ZERO_DEFECT"
assert host.is_terminal is True

# 3. Post-terminal mutation probe
res_post, comm7 = run_scenario_with_feedback(7, host)
assert res_post["decision"] == "REFUSED_TERMINAL_STATE"

print("All boundary probes verified: Terminal immutability is strictly enforced!")
display_board(host, res_post)""")
    )

    # Cell 8: Lab Diagnostic Test
    cells.append(
        nbf.v4.new_markdown_cell("""## 5. Automated Diagnostic Self-Grading

Execute the complete scenario verification battery to confirm your laboratory environment is in 100% compliance with canonical Symbol Game specifications.""")
    )

    # Cell 9: Code Run Tests
    cells.append(
        nbf.v4.new_code_cell("""suite = unittest.TestLoader().loadTestsFromTestCase(TestSymbolGameHowToPlay)
runner = unittest.TextTestRunner(verbosity=2)
res = runner.run(suite)

assert res.wasSuccessful(), "Laboratory test battery encountered failures!"
print(f"\\nAll {res.testsRun} automated laboratory scenarios PASSED.")""")
    )

    # Cell 10: Exercises
    cells.append(
        nbf.v4.new_markdown_cell("""## 6. Student Exercises

### Exercise 01.1: Fuel Starvation
What happens if an agent exhausts all turn fuel ($fuel = 0$) while defect $\\Phi_1 > 0$?

<details>
<summary><b>Click to reveal solution</b></summary>
The host returns `REFUSED_FUEL_EXHAUSTED` on any subsequent proposal. The board remains unsealed without certification, recording a failed attempt in the execution trace.
</details>

---

### Exercise 01.2: Atomic Rollback Invariant
Why is an atomic rollback necessary on monotonicity violations rather than accepting the move with a warning?

<details>
<summary><b>Click to reveal solution</b></summary>
If the move were accepted, the system would enter a state of higher defect, degrading the solution quality and opening the door to divergent random walks that violate the discrete Lyapunov stability theorem.
</details>""")
    )

    # Cell 11: Anchors
    cells.append(
        nbf.v4.new_markdown_cell("""## 7. Anchors

- **Paper 032 Sections:** §1, §3, §10
- **Paper 003 Sections:** §IV
- **Claim Ledger IDs:** `PO032-C01`, `PO032-C02`
- **Code:** [`test_how_to_play_scenarios.py`](test_how_to_play_scenarios.py)
- **Interactive Engine:** [`interactive_board.py`](interactive_board.py)""")
    )

    for index, cell in enumerate(cells):
        cell.id = sha256(f"{index}:{cell.source}".encode()).hexdigest()[:16]
    nb.cells = cells

    out_path = HOW_TO_PLAY_DIR / "01_interactive_scenarios_lab.ipynb"
    with open(out_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Wrote {out_path} ({len(cells)} cells).")


if __name__ == "__main__":
    build_walkthrough_notebook()
    build_lab_notebook()
