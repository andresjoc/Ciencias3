# Tech Stack

## Core

| Layer                | Choice                             | Rationale                                                                                                 |
| -------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Language             | Python 3.11+                       | Clean syntax, native typing, ideal for theoretical CS logic                                               |
| Architecture         | **Model-View-Controller (MVC)**    | Strict separation of automata theory (Model), GUI canvas (View), and event dispatching (Controller)       |
| GUI Framework (View) | **PyQt6**                          | High-performance native desktop canvas (QGraphicsView/QPainter) to render precise tape-and-trace diagrams |
| Distribution         | **Standalone Executable (`.exe`)** | Single-file Windows binary for seamless end-user delivery with zero dependencies                          |

- **Language & Conventions:** All codebase naming conventions (classes, methods, variables), comments, docstrings, and UI user-facing texts must be strictly in **Spanish** (e.g., `Automata`, `alfabeto`, `transiciones`, `evaluar_cadena`).

## Data

- **JSON / Python dataclasses** — In-memory state representation with file-based persistence (`.json`) for saving and loading automata configurations; no external database infrastructure needed.

## Testing

- **pytest** — Fast, Python-native testing suite for formal transitions, alphabet validation, trace correctness, and conversions (`pytest`).

## Tooling

- **PyInstaller** (`pyinstaller --onefile --windowed`) — Packages the entire Python environment, MVC modules, and assets into a portable Windows `.exe`.
- `ruff` / `black` for fast linting and code formatting.
- `venv` for isolated local dependency management.

## What We Are Not Using

- **No Web Frameworks or Browser Wrappers (Electron/Flask/Django)** — Avoids resource overhead; keeps it a native, lightweight desktop app.
- **No Heavy Databases or ORMs** — Graph states and transition matrices live in memory and export to standard JSON files.
- **No Docker or Containerization** — Not needed for local desktop deployment or single-binary exports.
