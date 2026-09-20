# Roadmap

Phases are intentionally small — each one is a shippable slice, independently reviewable and testable.
Mark with `[ ]` todo / `[x]` done. Your agent finds the first phase with all `[ ]` as "next".

---

## Phase 1 — Project Skeleton & Core Model `[x]`

- [x] Configure virtual environment (`venv`), MVC directory structure (`src/model/`, `src/view/`, `src/controller/`), and `pytest`
- [x] Implement the `Automaton` class in the Model (formal definition of alphabet $\Sigma$, states $Q$, start state $q_0$, accept states $F$, and transition matrix $\delta$)
- [x] Write unit tests in `tests/test_automaton.py` verifying DFA string evaluation with `pytest`

## Phase 2 — Basic MVC & Window Setup `[x]`

- [x] Create the main application window using PyQt6 (`src/view/ventana_principal.py`)
- [x] Connect the Controller to initialize the Model and handle basic UI events
- [x] Build a dedicated input panel to define and validate the custom alphabet ($\Sigma$)

## Phase 3 — Transition Table Editor `[x]`

- [x] Implement a grid view (`QTableWidget`) to display the transition matrix
- [x] Enable two-way editing: modifying table cells updates the Model via the Controller
- [x] Add real-time validation to restrict cell inputs strictly to valid alphabet symbols

## Phase 4 — Tape & Trace Rendering Engine `[x]`

- [x] Build a custom canvas (`QGraphicsView` / `QPainter`) to draw the upper tape (square contiguous cells, top horizontal brace $u$, delimiter $\equiv$, and trailing dots $\dots$)
- [x] Implement lower control unit rendering: discrete state boxes with upward vertical arrows aligned under active tape cells
- [x] Implement step-by-step DFA evaluation with visual acceptance and rejection status

## Phase 5 — NFA Support & Branching Trace `[x]`

- [x] Extend the Model to support non-deterministic transitions and DFA-to-NFA conversion logic
- [x] Render concurrent non-deterministic execution branches (complete accepted/rejected paths and halted branches ending prematurely at empty transitions $\emptyset$)
- [x] Add unit tests verifying branching logic and NFA acceptance resolution

## Phase 6 — Packaging & Standalone Exe `[x]`

- [x] Configure PyInstaller build script (`pyinstaller --onefile --windowed`)
- [x] Generate the standalone Windows `.exe` binary
- [x] Verify clean execution of the executable on a fresh environment without Python dependencies

---

Later phases (not yet planned): export diagram to PNG/SVG, file-based JSON persistence (`save`/`load`).
