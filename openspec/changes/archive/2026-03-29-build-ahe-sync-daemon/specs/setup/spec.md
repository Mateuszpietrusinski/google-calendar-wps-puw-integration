## ADDED Requirements

### Requirement: Setup script creates isolated environment
`scripts/setup.py` SHALL create a `.venv/` virtualenv, install all dependencies from `pyproject.toml`, and copy `.env.example` to `.env` (if `.env` does not already exist). The script SHALL use only Python stdlib modules (`venv`, `subprocess`, `shutil`, `sys`, `pathlib`).

#### Scenario: Fresh clone setup on macOS/Linux
- **WHEN** a student runs `python scripts/setup.py` in a freshly cloned repository with no `.venv/` present
- **THEN** `.venv/` is created, all dependencies are installed into it, and `.env` is copied from `.env.example`

#### Scenario: Fresh clone setup on Windows
- **WHEN** a student runs `python scripts/setup.py` on Windows with Python 3.10+ in PATH
- **THEN** `.venv/` is created using the Windows venv layout and the correct activate script path is printed

#### Scenario: Existing .env is not overwritten
- **WHEN** a student runs `python scripts/setup.py` and a `.env` file already exists
- **THEN** the existing `.env` is not modified and a message is printed: `".env already exists — skipping copy"`

---

### Requirement: Setup script prints OS-specific start command
After successful setup, `scripts/setup.py` SHALL print the exact command the student must run to start the daemon, appropriate for their OS.

#### Scenario: Start command printed on macOS/Linux
- **WHEN** setup completes on macOS or Linux
- **THEN** the script prints: `Run: .venv/bin/python -m ahe_sync`

#### Scenario: Start command printed on Windows
- **WHEN** setup completes on Windows
- **THEN** the script prints: `Run: .venv\Scripts\python -m ahe_sync`

---

### Requirement: Setup script fails clearly on missing Python version
The setup script SHALL check that the Python version is ≥ 3.10 before proceeding and exit with a human-readable message if not.

#### Scenario: Python version too old
- **WHEN** a student runs `python scripts/setup.py` with Python 3.9 or older
- **THEN** the script exits immediately with: `Error: Python 3.10+ required (found X.Y). Please upgrade.`

---

### Requirement: .env.example documents all configuration keys
`.env.example` SHALL include every supported `TOKEN_STORAGE`, `PUW_*`, `WPS_*`, `GOOGLE_*`, and reminder/colour keys, each with an inline comment describing its purpose and valid values.

#### Scenario: Student can derive full config from .env.example alone
- **WHEN** a student opens `.env.example`
- **THEN** every required and optional key is present with a description comment; no key requires consulting additional documentation to understand its purpose
