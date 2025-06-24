#!/usr/bin/env python3
"""Simple PySide6 GUI for controlling an XYZ manipulator.

The application loads ``ui/main_window.ui`` at runtime and relies on the
``XYZManipulator`` helper class to communicate with three SMCD14 stepper
controllers (one per axis).  Target positions for ``X``/``Y``/``Z`` and a
common velocity can be entered in the GUI.
"""

from __future__ import annotations

import argparse
import os
import sys

from PySide6 import QtCore, QtUiTools, QtWidgets

from controllers import XYZManipulator


# ---------------------------------------------------------------------------
# Command line helpers
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="miniMBE manipulator GUI")
    parser.add_argument(
        "--host",
        default=os.environ.get("SMCD14_HOST", "127.0.0.1"),
        help="IP address of the Modbus server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("SMCD14_PORT", "5020")),
        help="TCP port of the Modbus server",
    )
    parser.add_argument(
        "--slave-ids",
        default=os.environ.get("SMCD14_SLAVE_IDS", "1,2,3"),
        help="Comma separated slave IDs for X,Y,Z axes",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# UI loading helper
# ---------------------------------------------------------------------------

def load_ui(path: str) -> QtWidgets.QWidget:
    loader = QtUiTools.QUiLoader()
    f = QtCore.QFile(path)
    if not f.open(QtCore.QFile.ReadOnly):
        raise FileNotFoundError(f"Cannot open UI file: {path}")
    widget = loader.load(f)
    f.close()
    if widget is None:
        raise RuntimeError(f"Failed to load UI file: {path}")
    return widget


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, manipulator: XYZManipulator) -> None:
        super().__init__()
        self.manipulator = manipulator

        self.ui = load_ui("ui/main_window.ui")
        self.setCentralWidget(self.ui)

        self.spin_x = self.ui.findChild(QtWidgets.QDoubleSpinBox, "spinX")
        self.spin_y = self.ui.findChild(QtWidgets.QDoubleSpinBox, "spinY")
        self.spin_z = self.ui.findChild(QtWidgets.QDoubleSpinBox, "spinZ")
        self.spin_v = self.ui.findChild(QtWidgets.QDoubleSpinBox, "spinVelocity")
        self.move_btn = self.ui.findChild(QtWidgets.QPushButton, "moveButton")
        self.stop_btn = self.ui.findChild(QtWidgets.QPushButton, "stopButton")

        for spin in (self.spin_x, self.spin_y, self.spin_z, self.spin_v):
            spin.setRange(-1e6, 1e6)

        self._label = QtWidgets.QLabel("Disconnected")
        self.statusBar().addPermanentWidget(self._label)

        self.move_btn.clicked.connect(self.start_move)
        self.stop_btn.clicked.connect(self.stop_move)

        self._timer = QtCore.QTimer(interval=1000, timeout=self.update_position)
        self._timer.start()
        self.update_position()

    # ------------------------------------------------------------------
    # slots
    # ------------------------------------------------------------------
    def start_move(self) -> None:
        target = (
            self.spin_x.value(),
            self.spin_y.value(),
            self.spin_z.value(),
        )
        velocity = self.spin_v.value()
        try:
            self.manipulator.move_absolute(target, velocity)
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "Move failed", str(exc))

    def stop_move(self) -> None:
        self.manipulator.emergency_stop()

    def update_position(self) -> None:
        try:
            x, y, z = self.manipulator.read_positions()
            self._label.setText(f"Pos: {x:.2f}, {y:.2f}, {z:.2f}")
        except Exception:
            self._label.setText("--")


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    slave_ids = tuple(int(s) for s in args.slave_ids.split(","))
    manip = XYZManipulator(args.host, port=args.port, slave_ids=slave_ids)
    manip.connect()

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(manip)
    window.show()
    ret = app.exec()
    manip.disconnect()
    return ret


if __name__ == "__main__":
    sys.exit(main())
