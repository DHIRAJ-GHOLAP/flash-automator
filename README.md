# Flash Automator ⚡

**Flash Automator** is a modern, modular Robotic Process Automation (RPA) desktop tool designed for repetitive GUI workflows that require dynamic date variables and iterative execution across time sequences.

Built with **Python 3.12+**, **PySide6**, **pynput**, **PyAutoGUI**, **OpenCV**, and **SQLite**.

---

## 🌟 The Core Architecture: Decoupled Date Engine

Unlike simple macro recorders that rigidly replay static mouse clicks and fixed strings, Flash Automator decouples the **Workflow Recorder** from the **Date Engine**:

```
             RECORDED WORKFLOW
                    │
                    ▼
        "TYPE {{STATEMENT_DATE}}"
                    │
                    │
             DATE ENGINE (Independent)
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   01/10/26     02/10/26     03/10/26
       │            │            │
       ▼            ▼            ▼
    Workflow     Workflow     Workflow
```

This clean architectural separation allows you to:
1. **Record the workflow once** for any single sample date (e.g. typing `01/10/2026`).
2. **Convert the literal date** into a variable token: `{{STATEMENT_DATE}}` with a single click in the UI.
3. **Iterate across dynamic ranges** (e.g., 31 days of October, weekdays only, skip Sundays, or every N days).
4. **Replay the workflow automatically** with the correct date injected at each iteration.

---

## 🎯 Primary Use Case: Monthly Bank Statement Generation

A user needs to download/print daily bank statements for October 2026:
- Day 1: `01/10/2026` → perform workflow → save as `Statement_01-10-2026.pdf`
- Day 2: `02/10/2026` → perform workflow → save as `Statement_02-10-2026.pdf`
- ...
- Day 31: `31/10/2026` → perform workflow → save as `Statement_31-10-2026.pdf`

Flash Automator automates this entire process with safety stops, progress tracking, and audit logging.

---

## 🚀 Key Features

- **Smart Typing Coalescer**: Automatically bundles sequential key presses into clean `TYPE_TEXT` actions rather than generating dozens of raw key down/up events.
- **One-Click Variable Conversion**: In the Workflow Editor timeline, select any recorded text action and click **`✨ Convert to {{STATEMENT_DATE}}`**.
- **Independent Date Engine**:
  - Daily step (`1 day`, `N days`)
  - Configurable formats (`DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY-MM-DD`, `MM/DD/YYYY`, etc.)
  - Calendar rules: *Every Day*, *Weekdays Only*, *Skip Sundays*, *Skip Saturdays*, *Custom Excluded Dates/Holidays*.
  - Full variable suite: `{{STATEMENT_DATE}}`, `{{DAY}}`, `{{MONTH}}`, `{{YEAR}}`, `{{DATE_DD}}`, `{{DATE_MM}}`, `{{DATE_YYYY}}`, `{{COUNTER}}`, `{{ITERATION}}`.
- **Safety First**:
  - Global `F12` Emergency Abort key terminates playback instantly.
  - PyAutoGUI screen corner failsafe.
  - 3-second safety countdown before long batch runs.
  - Non-intrusive floating HUD overlay during recording.
- **Safe Dry Run Mode**: Simulates workflow timing and cursor movements without clicking destructive buttons or overwriting files.
- **Smart Waits & Vision**:
  - `WAIT_FIXED`: Configurable sleep.
  - `WAIT_FOR_IMAGE`: OpenCV template matching with confidence threshold and timeout.
  - `WAIT_FOR_SCREEN_CHANGE`: Monitors pixel variance to detect when reports finish rendering.
  - `WAIT_FOR_WINDOW`: Waits for target application/dialog to become active.
  - Modular optional OCR via `pytesseract`.
- **Human-in-the-Loop Error Recovery**:
  - If a step times out or fails, playback pauses automatically and presents:
    - `RETRY`: Try the current step again.
    - `SKIP THIS DATE`: Skip remainder of this date and proceed to the next iteration.
    - `STOP AUTOMATION`: Abort gracefully.
- **Audit Logging & Persistence**:
  - SQLite database persists workflows, projects, and execution records.
  - One-click CSV export of run history.
  - Portable JSON import/export for sharing workflows across machines.

---

## ⌨️ Global Hotkeys

| Shortcut | Action | Description |
| :--- | :--- | :--- |
| **`F8`** | **Start Recording** | Begins capturing keyboard and mouse interactions |
| **`F9`** | **Stop Recording** | Stops recording and prepares actions for timeline |
| **`F10`** | **Pause Recording** | Temporarily pauses event capturing |
| **`F11`** | **Resume Recording** | Resumes paused recording |
| **`F12`** | **EMERGENCY STOP** | **Immediately terminates any active playback** |

---

## 📦 Project Structure

```
flash_automator/
├── app.py                      # Main application entry point
├── build_exe.py                # Standalone packaging script
├── flash_automator.spec        # PyInstaller specification for Windows
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation
│
├── core/                       # Core RPA & Automation Engine
│   ├── actions.py              # Action model & ActionType enums
│   ├── workflow.py             # Workflow collection & timeline manipulation
│   ├── recorder.py             # Mouse/keyboard capture with smart typing coalescer
│   ├── date_engine.py          # Independent date range generator & rules engine
│   ├── variables.py            # Variable extraction and template substitution engine
│   ├── player.py               # Low-level action execution with PyAutoGUI
│   ├── safety.py               # Failsafe triggers and global emergency listener
│   └── executor.py             # High-level iterative runner with pause/retry/skip
│
├── recognition/                # Vision and smart wait subsystems
│   ├── image_matcher.py        # OpenCV template matching & screen search
│   ├── screen_detector.py      # Screen diff & loading change detector
│   └── ocr.py                  # Modular Tesseract OCR integration
│
├── storage/                    # Persistence layer
│   ├── database.py             # SQLite connection & schema manager
│   ├── models.py               # ORM data models
│   └── project_manager.py      # Project manager, JSON & CSV import/export
│
├── ui/                         # Modern PySide6 Desktop GUI
│   ├── main_window.py          # Root window with navigation sidebar & background worker
│   ├── styles.py               # Dark theme stylesheet
│   ├── overlay.py              # Floating recording HUD overlay
│   ├── views/
│   │   ├── dashboard_view.py   # Overview, status cards, and quick actions
│   │   ├── recorder_view.py    # Recording controls, live table feed
│   │   ├── editor_view.py      # Timeline editor & "Convert to Variable" button
│   │   ├── automation_view.py  # Date engine configuration & sequence preview
│   │   ├── variables_view.py   # Variable inspector & live preview calculator
│   │   ├── history_view.py     # Execution audit logs & CSV export
│   │   └── settings_view.py    # Preferences, hotkeys, and safety toggles
│   └── dialogs/
│       ├── countdown_dialog.py # 3-second safety countdown dialog
│       ├── error_dialog.py     # Human-in-the-loop pause dialog (Retry/Skip/Stop)
│       └── edit_action_dialog.py# Action parameter modification modal
│
└── tests/                      # Comprehensive test suite
    ├── test_actions.py
    ├── test_variables.py
    ├── test_date_engine.py
    ├── test_workflow.py
    ├── test_storage.py
    ├── test_executor.py
    ├── test_ui.py
    └── test_e2e_statement_flow.py # Full 31-day simulation test
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.12+ (tested with Python 3.12 and 3.13)
- Windows 10/11 (or Linux/macOS with X11)

### Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running Flash Automator
```bash
python -m flash_automator.app
# Or directly:
python flash_automator/app.py
```

---

## 🧪 Running Automated Tests

Run the full automated test suite (including date generation, variable substitution, UI navigation, and the complete 31-day end-to-end simulation):

```bash
PYTHONPATH=. pytest -v flash_automator/tests
```

All 27 test cases run headlessly and verify:
- Accurate 31-day date iteration for October 2026.
- Weekday-only, Sunday skipping, and holiday exclusions.
- Replacement of `{{STATEMENT_DATE}}` and multi-token filenames like `Statement_{{DATE_YYYY}}_{{DATE_MM}}_{{DATE_DD}}.pdf`.
- F12 Emergency stop abort mechanism.
- Persistence and CSV audit generation.
- Full UI component initialization and navigation.

---

## 🔨 Packaging as a Standalone Windows Executable (.exe)

To bundle Flash Automator into a standalone Windows `.exe` application using PyInstaller:

```bash
python flash_automator/build_exe.py
```

The output standalone folder will be located in:
```
dist/FlashAutomator/FlashAutomator.exe
```

---

## 📋 Step-by-Step Bank Statement Walkthrough

1. **Open Flash Automator**: Launch the app; navigate to the **Recorder** tab.
2. **Record One Day**:
   - Press **`F8`** (or click *Start Recording*).
   - In your browser or bank application, click the Date filter and type `01/10/2026`.
   - Click *Generate Report*, press `Ctrl+P`, type `Statement_01/10/2026.pdf`, and click *Save*.
   - Press **`F9`** (or click *Stop Recording*).
3. **Transfer to Editor**: Click **Transfer Actions to Workflow Editor**.
4. **Convert Date to Variable**:
   - In the timeline table, select the row where you typed `01/10/2026`.
   - Click the prominent purple button: **`✨ Convert to {{STATEMENT_DATE}}`**.
   - The literal date is instantly replaced by `{{STATEMENT_DATE}}`.
5. **Configure Date Automation**:
   - Go to the **Date Automation** tab.
   - Set **Start Date** = `01/10/2026`, **End Date** = `31/10/2026`.
   - Choose Format = `DD/MM/YYYY`, Step = `1 day`.
   - Select rules (e.g. *Every day* or *Skip Sundays*).
   - Inspect the **Generated Iteration Sequence** preview table (shows 31 iterations).
6. **Execute**:
   - Click **▶ Run Automation** (or **🔍 Dry Run Mode** to preview safely).
   - The 3-second safety countdown begins.
   - Flash Automator automatically loops through all 31 days, substituting each daily date and generating the corresponding statement!
