#!/usr/bin/env python3
import sys
import struct

from PySide6 import QtWidgets, QtUiTools, QtCore
from pymodbus.client.tcp import ModbusTcpClient

REG_ACTPOS = 18  # two registers → one float
REG_POS_BASE = 100  # start address for stored positions
NUM_POS = 10

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

    client = ModbusTcpClient("127.0.0.1", port=5020)
    if not client.connect():
        QtWidgets.QMessageBox.critical(
            None, "Connection Error",
            "Could not connect to Modbus emulator at 127.0.0.1:5020"
        )
        return 1

    label = QtWidgets.QLabel("Position: --")
    window.statusbar.addPermanentWidget(label)

    table: QtWidgets.QTableWidget = window.findChild(QtWidgets.QTableWidget, "positionTable")
    table.setColumnCount(2)
    table.setHorizontalHeaderLabels(["Index", "Value"])
    table.setRowCount(NUM_POS)
    for i in range(NUM_POS):
        item = QtWidgets.QTableWidgetItem(str(i))
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        table.setItem(i, 0, item)
        table.setItem(i, 1, QtWidgets.QTableWidgetItem("0.0"))

    def refresh_positions():
        rr = client.read_holding_registers(REG_POS_BASE, count=NUM_POS * 2, slave=1)
        if rr.isError():
            return
        for i in range(NUM_POS):
            raw = struct.pack(">HH", rr.registers[2 * i], rr.registers[2 * i + 1])
            pos = struct.unpack(">f", raw)[0]
            table.item(i, 1).setText(f"{pos:.3f}")

    def write_positions():
        values = []
        for i in range(NUM_POS):
            try:
                pos = float(table.item(i, 1).text())
            except (TypeError, ValueError):
                pos = 0.0
            raw = struct.pack(">f", pos)
            hi, lo = struct.unpack(">HH", raw)
            values.extend([hi, lo])
        client.write_registers(REG_POS_BASE, values, slave=1)

    refresh_btn = window.findChild(QtWidgets.QPushButton, "refreshButton")
    if refresh_btn:
        refresh_btn.clicked.connect(refresh_positions)
    write_btn = window.findChild(QtWidgets.QPushButton, "writeButton")
    if write_btn:
        write_btn.clicked.connect(write_positions)

    refresh_positions()

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
