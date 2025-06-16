# miniMBE GUI

This repository provides a minimal graphical user interface for a miniature molecular beam epitaxy (MBE) system.  The interface is built with PySide6 and loads the `ui/main_window.ui` file at runtime.

## Requirements

* **Python**: tested with Python 3.11 (Python 3.10 or later is recommended)
* **PySide6** and **PySide6-Tools**

## Setup

1. Install Python.
2. Create a virtual environment.
3. Run `pip install -r requirements.txt`.
4. Launch the GUI with `python app.py`.

## SMCD14 Emulator

The repository includes a small Modbus TCP emulator defined in
`smcd14_emulator.py`. It exposes the SMCD14 register map so that you can test
the GUI or other clients without hardware attached.

Run it from a separate terminal:

```bash
python smcd14_emulator.py  # listens on TCP port 5020 by default
```

You can change the port with `--port <number>`. Once the emulator is running,
start the GUI, which connects to `127.0.0.1:5020` by default, or point your own
Modbus client to the same port to verify register reads and writes.
