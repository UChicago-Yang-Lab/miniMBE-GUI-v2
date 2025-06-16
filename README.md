# miniMBE GUI

This repository provides a minimal graphical user interface for a miniature molecular beam epitaxy (MBE) system.  The interface is built with PySide6 and loads the `ui/main_window.ui` file at runtime.

## Requirements

* **Python**: tested with Python 3.11 (Python 3.10 or later is recommended)
* **PySide6** and **PySide6-Tools**

## Setup

1. Install Python.
2. Create a virtual environment.
3. Run `pip install -r requirements.txt`.
4. Start the Modbus emulator with `python smcd14_emulator.py`.
5. Launch the GUI with `python app.py`.

The GUI requires OpenGL libraries such as `libEGL.so.1` at runtime. If it fails
to start due to missing system dependencies, install the necessary OpenGL
packages for your platform.
