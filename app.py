#!/usr/bin/env python3
import sys
import struct

from PySide6 import QtWidgets, QtUiTools, QtCore
from pymodbus.client.tcp import ModbusTcpClient

# Modbus register holding the current position of the manipulator. Two
# consecutive registers form a single IEEE‑754 float which we decode using the
# ``struct`` module.  The original version of this application referred to a
# number of undefined constants and UI elements.  The simplified implementation
# below focuses solely on displaying this register in the status bar, avoiding
# those undefined names entirely.
REG_ACTPOS = 18  # two registers -> one float

def load_ui(ui_path: str) -> QtWidgets.QWidget:
    loader = QtUiTools.QUiLoader()
    f = QtCore.QFile(ui_path)
    if not f.open(QtCore.QFile.ReadOnly):
        raise FileNotFoundError(f"Cannot open UI file {ui_path!r}")
    widget = loader.load(f)
    f.close()
    if widget is None:
        raise RuntimeError(f"UI loader returned None for {ui_path!r}")
    return widget

def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    window = load_ui("ui/main_window.ui")

    # In the previous iteration this function attempted to populate a table of
    # preset positions using several undefined constants (``NUM_POSITIONS``,
    # ``REG_POS_BASE`` and others).  The corresponding widgets are not present in
    # ``ui/main_window.ui`` which resulted in ``NoneType`` errors when the table
    # could not be found.  The revised version simply loads the UI and focuses on
    # displaying the current position in the status bar.

    client = ModbusTcpClient("127.0.0.1", port=5020)
    if not client.connect():
        QtWidgets.QMessageBox.critical(
            None, "Connection Error",
            "Could not connect to Modbus emulator at 127.0.0.1:5020"
        )
        return 1

    label = QtWidgets.QLabel("Position: --")
    window.statusbar.addPermanentWidget(label)

    def poll():
        rr = client.read_holding_registers(REG_ACTPOS, count=2, slave=1)
        if not rr.isError():
            raw = struct.pack(">HH", rr.registers[0], rr.registers[1])
            pos = struct.unpack(">f", raw)[0]
            label.setText(f"Position: {pos:.2f}")

    timer = QtCore.QTimer(interval=1000, timeout=poll)
    timer.start()

    window.show()
    ret = app.exec()
    client.close()
    return ret

if __name__ == "__main__":
    sys.exit(main())
