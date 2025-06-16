#!/usr/bin/env python3
import sys
import struct

from PySide6 import QtWidgets, QtUiTools, QtCore
from PySide6.QtCore import Qt
from pymodbus.client.tcp import ModbusTcpClient

REG_ACTPOS = 18  # two registers holding the motor position as float

def load_ui(ui_file: str) -> QtWidgets.QWidget:
    loader = QtUiTools.QUiLoader()
    ui_file = QtCore.QFile(ui_file)
    ui_file.open(QtCore.QFile.ReadOnly)
    window = loader.load(ui_file)
    ui_file.close()
    return window

def main() -> int:
    app = QtWidgets.QApplication(sys.argv)

    main_win = load_ui("ui/main_window.ui")

    client = ModbusTcpClient("127.0.0.1", port=5020)
    client.connect()

    position_label = QtWidgets.QLabel("Position: --")
    main_win.statusbar.addPermanentWidget(position_label)

    def poll() -> None:
        rr = client.read_holding_registers(REG_ACTPOS, count=2, slave=1)
        if rr.isError():
            return
        raw = struct.pack(">HH", rr.registers[0], rr.registers[1])
        pos = struct.unpack(">f", raw)[0]
        position_label.setText(f"Position: {pos:.2f}")

    timer = QtCore.QTimer()
    timer.timeout.connect(poll)
    timer.start(1000)

    main_win.show()
    ret = app.exec()
    client.close()
    return ret

if __name__ == "__main__":
    sys.exit(main())
