#!/usr/bin/env python3
import sys
import struct

from PySide6 import QtWidgets, QtUiTools, QtCore
from pymodbus.client.tcp import ModbusTcpClient

REG_MOVETYPE = 0
REG_TARGET = 2  # two registers -> float
REG_VELOCITY = 8  # two registers -> float
REG_MOTOR_ON = 14
REG_START_REQ = 15
REG_STOP_REQ = 16
REG_ACTPOS = 18  # two registers -> float

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

    spin_x = window.findChild(QtWidgets.QDoubleSpinBox, "spinX")
    spin_y = window.findChild(QtWidgets.QDoubleSpinBox, "spinY")
    spin_z = window.findChild(QtWidgets.QDoubleSpinBox, "spinZ")
    spin_vel = window.findChild(QtWidgets.QDoubleSpinBox, "spinVelocity")
    move_btn = window.findChild(QtWidgets.QPushButton, "moveButton")
    stop_btn = window.findChild(QtWidgets.QPushButton, "stopButton")

    for spin in (spin_x, spin_y, spin_z, spin_vel):
        if spin is not None:
            spin.setRange(-1e6, 1e6)

    client = ModbusTcpClient("127.0.0.1", port=5020)
    if not client.connect():
        QtWidgets.QMessageBox.critical(
            None, "Connection Error",
            "Could not connect to Modbus emulator at 127.0.0.1:5020"
        )
        return 1

    label = QtWidgets.QLabel("Position: --")
    window.statusbar.addPermanentWidget(label)

    def write_float(address: int, value: float) -> None:
        raw = struct.pack(">f", value)
        hi, lo = struct.unpack(">HH", raw)
        client.write_registers(address, [hi, lo], slave=1)

    def move() -> None:
        target = spin_x.value()
        velocity = spin_vel.value()

        client.write_register(REG_MOVETYPE, 1, slave=1)
        write_float(REG_TARGET, target)
        write_float(REG_VELOCITY, velocity)
        client.write_register(REG_MOTOR_ON, 1, slave=1)
        client.write_register(REG_START_REQ, 1, slave=1)
        client.write_register(REG_START_REQ, 0, slave=1)

    def stop() -> None:
        client.write_register(REG_STOP_REQ, 1, slave=1)
        client.write_register(REG_STOP_REQ, 0, slave=1)

    move_btn.clicked.connect(move)
    stop_btn.clicked.connect(stop)

    def poll() -> None:
        rr = client.read_holding_registers(REG_ACTPOS, count=2, slave=1)
        if not rr.isError():
            raw = struct.pack(">HH", rr.registers[0], rr.registers[1])
            pos = struct.unpack(">f", raw)[0]
            label.setText(f"Position: {pos:.2f}")

    timer = QtCore.QTimer(interval=1000, timeout=poll)
    timer.start()
    poll()

    window.show()
    ret = app.exec()
    client.close()
    return ret

if __name__ == "__main__":
    sys.exit(main())
