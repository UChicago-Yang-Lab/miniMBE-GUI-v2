# miniMBE GUI

This repository provides a minimal graphical user interface for a miniature molecular beam epitaxy (MBE) system.  The interface is built with PySide6 and loads the `ui/main_window.ui` file at runtime.

## Requirements

* **Python**: tested with Python 3.11 (Python 3.10 or later is recommended)
* **PySide6** and **PySide6-Tools**
* **pymodbus** (for communicating with the SMCD14 controller or the emulator)

## Setup

1. Install Python.
2. Create a virtual environment.
3. Run `pip install -r requirements.txt` (or `conda env create -f environment.yml`).
4. Launch the GUI with `python app.py`.

## Emulator

The repository includes a simple Modbus TCP emulator that mimics the SMCD14 controller for offline testing.  Run it in a separate terminal:

```bash
python smcd14_emulator.py --port 5020
```

The GUI connects to `127.0.0.1:5020` by default and displays the current position in its status bar.
