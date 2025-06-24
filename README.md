# miniMBE GUI

This repository provides a minimal graphical user interface for a miniature molecular beam epitaxy (MBE) system.  The interface is built with PySide6 and loads the `ui/main_window.ui` file at runtime.

## Requirements

1. Python 3.10 or later (tested with Python 3.11)
2. PySide6 and PySide6-Tools
3. OpenGL libraries such as `libEGL.so.1`
4. For offline testing, start the Modbus emulator with
   `python smcd14_emulator.py`
5. Launch the GUI with `python app.py`

The GUI requires OpenGL libraries such as `libEGL.so.1` at runtime. If it fails
to start due to missing system dependencies, install the necessary OpenGL
packages for your platform.

## Hardware Controller

When connected to a real SMCD14 controller, use the helper module
`controllers/smcd14_controller.py` to open a Modbus TCP connection and issue
motion commands.  See the source for available methods.

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
The emulator now supports registers 0-10 so the GUI can be tested without hardware.

## Movement Control

Enter the target coordinates in the **X**, **Y**, and **Z** fields and specify the desired **Velocity**. Click **Start Move** to begin, or press **Stop** to halt the motion.
