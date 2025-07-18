# miniMBE GUI

This repository provides a minimal graphical user interface for a miniature molecular beam epitaxy (MBE) system.  The interface is built with PySide6 and loads the `ui/main_window.ui` file at runtime.

The application now includes a small controller module that communicates with an SMCD14 manipulator over Modbus TCP.  It reads the X, Y and Z axis positions (slave IDs 1, 2 and 3) and displays them in the GUI.

## Requirements

1. Python 3.10 or later (tested with Python 3.11)
2. PySide6 and PySide6-Tools
3. OpenGL libraries such as `libEGL.so.1`
4. Launch the GUI with `python app.py`

The GUI requires OpenGL libraries such as `libEGL.so.1` at runtime. If it fails
to start due to missing system dependencies, install the necessary OpenGL
packages for your platform.

## Hardware Controller

The GUI communicates with up to three SMCD14 stepper controllers.  By default it
connects to ``192.168.0.100:502`` using slave IDs ``1``, ``2`` and ``3``.  These
parameters can be overridden via the command line or the environment variables
``SMCD14_HOST``, ``SMCD14_PORT`` and ``SMCD14_SLAVE_IDS`` (comma separated).

## Setup

1. Install Python.
2. Create a virtual environment.
3. Run `pip install -r requirements.txt` (or `conda env create -f environment.yml`).
4. Launch the GUI with `python app.py`.

## Movement Control

Enter the target coordinates in the **X**, **Y**, and **Z** fields and specify the desired **Velocity**. Click **Start Move** to begin, or press **Stop** to halt the motion.

Use the **Home** button to run the homing sequence on all axes. Homing relies on the controller's configured homing type and establishes the reference zero position required for absolute moves.

### Position Plot

The GUI connects to `127.0.0.1:5020` by default and displays the current X, Y and Z positions in a table.
