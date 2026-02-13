# Short Deck CLI (Test MVP)

Simple interactive CLI for 6+ Hold'em input testing.

## What it does

1. Asks for your starting hand and your position.
2. Waits for second input: other player position + action.
3. Resolves a preflop scenario key.
4. Outputs a dummy recommendation for what to do.

This version is intentionally a test application. It now reads a starter scenario schema from JSON and falls back to dummy logic while recommendations are marked `TBD`.

## Starter strategy schema

- File: `src/shortdeck_cli/data/preflop_scenarios.json`
- Includes 24 labeled scenarios from the article categories (Opening / vs Limp / vs All-in)
- Each scenario currently has `default_recommendation: "TBD"`
- `open:UTG_rfi` also includes a hand-level `hand_actions` map, so that spot is already data-driven

`hand_actions` supports either:
- Single action: `"AQo": "all-in"`
- Mixed strategy: `"AQo": {"all-in": 60, "call": 40}` (or decimal weights like `0.6` / `0.4`)

The CLI will print mixed advice as percentages, for example: `Data recommendation: 60% all-in, 40% call`.

When you are ready, replace `TBD` values with real actions and the CLI will return `Data recommendation: ...` for mapped spots.

## Positions (custom)

- UTG
- MP1
- MP2
- HJ
- CO
- BTN

## Supported villain actions

- fold
- limp
- all-in

## Hand format

- Pairs: `AA`, `KK`, `66`
- Non-pairs with suitedness: `AKs`, `QJs`, `T9o`, `A6s`
- Ranks supported for Short Deck input: `A K Q J T 9 8 7 6`

## Run

```bash
python -m shortdeck_cli
```

Or after editable install:

```bash
pip install -e .
shortdeck-cli
```

## Test

```bash
pytest -q
```

## Distributing to a Windows user ✅

Recommended: produce a standalone Windows executable so the recipient doesn't need Python.

Options:
- Quick (no build): share `pip install -e .` / `pipx install .` instructions — requires Python on the target machine.
- Best UX (recommended): provide a single-file EXE built with **PyInstaller** (no Python required).

What I added to this repo:
- GitHub Actions workflow to build a single-file Windows EXE and upload it as an artifact: `.github/workflows/build-windows.yml`.

How the Windows EXE is built (CI):
1. CI runs on `windows-latest`.
2. Installs `pyinstaller` and the package.
3. Runs: `pyinstaller --onefile --name shortdeck-cli src/shortdeck_cli/__main__.py`.
4. Artifact `dist/shortdeck-cli.exe` is uploaded for download.

How a Windows user can run the EXE:
- Download `shortdeck-cli.exe` from the CI artifacts (or your release page).
- Double-click or run from cmd/PowerShell: `shortdeck-cli.exe`.

Developer: build locally on Windows with PyInstaller

1. Install Python 3.11+ for Windows.
2. Create a venv & activate it.
3. pip install -e . pyinstaller
4. pyinstaller --onefile --name shortdeck-cli src/shortdeck_cli/__main__.py

Alternative delivery methods:
- Publish a wheel to PyPI and tell Windows users to `pip install shortdeck-cli`.
- Create an installer (Inno Setup) from the built EXE for an OS-native install experience.

---
