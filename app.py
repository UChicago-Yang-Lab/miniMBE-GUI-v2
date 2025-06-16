#!/usr/bin/env python3
import sys
import struct

from PySide6 import QtWidgets, QtUiTools, QtCore
from pymodbus.client.tcp import ModbusTcpClient

REG_ACTPOS = 18  # two registers → one float
REG_POS_BASE = 200
NUM_POSITIONS = 5

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

    table: QtWidgets.QTableWidget = window.findChild(QtWidgets.QTableWidget, "positionTable")
    table.setRowCount(NUM_POSITIONS)
    table.setColumnCount(2)
    table.setHorizontalHeaderLabels(["Position", "Set"])
    table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

    spin_boxes = []
    for i in range(NUM_POSITIONS):
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(-1e6, 1e6)
        table.setCellWidget(i, 0, spin)
        btn = QtWidgets.QPushButton("Set")
        table.setCellWidget(i, 1, btn)
        spin_boxes.append(spin)

        def make_slot(idx: int):
            return lambda: write_position(idx)

        btn.clicked.connect(make_slot(i))

    def write_position(index: int) -> None:
        spin = spin_boxes[index]
        value = spin.value()
        raw = struct.pack(">f", value)
        hi, lo = struct.unpack(">HH", raw)
        client.write_registers(REG_POS_BASE + 2 * index, [hi, lo], slave=1)

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

        rr = client.read_holding_registers(REG_POS_BASE, count=NUM_POSITIONS * 2, slave=1)
        if not rr.isError():
            for i in range(NUM_POSITIONS):
                raw = struct.pack(">HH", rr.registers[2 * i], rr.registers[2 * i + 1])
                pos = struct.unpack(">f", raw)[0]
                spin_boxes[i].setValue(pos)

    timer = QtCore.QTimer(interval=1000, timeout=poll)
    timer.start()

    window.show()
    ret = app.exec()
    client.close()
    return ret

if __name__ == "__main__":
    sys.exit(main())