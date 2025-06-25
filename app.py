#!/usr/bin/env python3
"""Simple PySide6 GUI for controlling an XYZ manipulator.

The application loads `ui/main_window.ui` at runtime and relies on the
`XYZManipulator` helper class to communicate with three SMCD14 stepper
controllers (one per axis). Target positions for X/Y/Z and a common
velocity can be entered in the GUI.
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
        default=os.environ.get("SMCD14_HOST", "169.254.151.255"),
        help="IP address of the SMCD14 controller",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("SMCD14_PORT", "502")),
        help="Modbus TCP port",
    )
    parser.add_argument(
        "--slave-ids",
        default=os.environ.get("SMCD14_SLAVE_IDS", "1,2,3"),
        help="Comma separated slave IDs for X,Y,Z axes",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("SMCD14_TIMEOUT", "10")),
        help="Modbus TCP timeout in seconds",
    )
    parser.add_argument(
        "--backlash",
        type=float,
        default=float(os.environ.get("SMCD14_BACKLASH", "0")),
        help="Backlash compensation in mm",
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

        # load the .ui file
        self.ui = load_ui("ui/main_window.ui")
        self.setCentralWidget(self.ui)

        # find widgets by objectName
        self.spin_x    = self.ui.findChild(QtWidgets.QDoubleSpinBox, "spinX")
        self.spin_y    = self.ui.findChild(QtWidgets.QDoubleSpinBox, "spinY")
        self.spin_z    = self.ui.findChild(QtWidgets.QDoubleSpinBox, "spinZ")
        self.spin_v    = self.ui.findChild(QtWidgets.QDoubleSpinBox, "spinVelocity")
        self.move_btn  = self.ui.findChild(QtWidgets.QPushButton,     "moveButton")
        self.stop_btn  = self.ui.findChild(QtWidgets.QPushButton,     "stopButton")

        # configure ranges
        for spin in (self.spin_x, self.spin_y, self.spin_z, self.spin_v):
            spin.setRange(-1e6, 1e6)

        # status label in statusBar
        self._label = QtWidgets.QLabel("Disconnected")
        self.statusBar().addPermanentWidget(self._label)

        # connect signals
        self.move_btn.clicked.connect(self.start_move)
        self.stop_btn.clicked.connect(self.stop_move)

        # polling timer
        self._timer = QtCore.QTimer(interval=1000, timeout=self.update_position)
        self._timer.start()
        self.update_position()

    def start_move(self) -> None:
        target   = (self.spin_x.value(), self.spin_y.value(), self.spin_z.value())
        velocity = self.spin_v.value()
        try:
            self.manipulator.move_absolute(target, velocity)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Move failed", str(exc))

    def stop_move(self) -> None:
        try:
            self.manipulator.emergency_stop()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Stop failed", str(exc))

    def update_position(self) -> None:
        try:
            x, y, z = self.manipulator.read_positions()
            self._label.setText(f"Pos: {x:.3f}, {y:.3f}, {z:.3f}")
        except Exception as exc:
            self._label.setText("--")
            print("Update failed:", exc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> int:
    args = parse_args()
    slave_ids = tuple(int(s) for s in args.slave_ids.split(","))
    manip = XYZManipulator(
        host      = args.host,
        port      = args.port,
        timeout   = args.timeout,
        slave_ids = slave_ids,
        backlash  = args.backlash,
    )

    # check connection immediately
    if not manip.connect():
        QtWidgets.QMessageBox.critical(
            None,
            "Connection Error",
            f"Could not connect to SMCD14 at {args.host}:{args.port}\n"
            "Please verify IP, port, and network settings."
        )
        return 1

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(manip)
    window.show()
    ret = app.exec()
    manip.disconnect()
    return ret


if __name__ == "__main__":
    sys.exit(main())
