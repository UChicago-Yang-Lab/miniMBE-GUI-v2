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
import pyqtgraph as pg

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
        self.stop_btn      = self.ui.findChild(QtWidgets.QPushButton, "stopButton")
        self.home_btn      = self.ui.findChild(QtWidgets.QPushButton, "homeButton")
        self.zoom_in_btn   = self.ui.findChild(QtWidgets.QPushButton, "zoomInButton")
        self.zoom_out_btn  = self.ui.findChild(QtWidgets.QPushButton, "zoomOutButton")

        # setup plotting widget for X/Y position history
        container = self.ui.findChild(QtWidgets.QWidget, "plotContainer")
        self.plot = pg.PlotWidget(title="Manipulator position")
        self.plot.setLabel("left", "Y (mm)")
        self.plot.setLabel("bottom", "X (mm)")
        self.plot.setAspectLocked(True)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.addLine(x=0, pen=pg.mkPen((150, 150, 150)))
        self.plot.addLine(y=0, pen=pg.mkPen((150, 150, 150)))
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.plot_line = self.plot.plot([], [], pen=pg.mkPen("y"))
        self.current_point = self.plot.plot([], [], pen=None, symbol="o", symbolBrush="w")
        self.data_x: list[float] = []
        self.data_y: list[float] = []
        self._zoom = 1.0
        self._base_range = 5.0
        self.update_zoom()

        # configure ranges
        for spin in (self.spin_x, self.spin_y, self.spin_z, self.spin_v):
            spin.setRange(-1e6, 1e6)

        # status label in statusBar
        self._label = QtWidgets.QLabel("Disconnected")
        self.statusBar().addPermanentWidget(self._label)

        # connect signals
        self.move_btn.clicked.connect(self.start_move)
        self.stop_btn.clicked.connect(self.stop_move)
        if self.home_btn:
            self.home_btn.clicked.connect(self.start_home)
        if self.zoom_in_btn:
            self.zoom_in_btn.clicked.connect(self.zoom_in)
        if self.zoom_out_btn:
            self.zoom_out_btn.clicked.connect(self.zoom_out)

        # polling timer
        self._timer = QtCore.QTimer(interval=200, timeout=self.update_position)
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

    def start_home(self) -> None:
        try:
            self.manipulator.home()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Home failed", str(exc))

    def update_position(self) -> None:
        try:
            x, y, z = self.manipulator.read_positions()
            self._label.setText(f"Pos: {x:.3f}, {y:.3f}, {z:.3f}")
            self.data_x.append(x)
            self.data_y.append(y)
            if len(self.data_x) > 1000:
                self.data_x.pop(0)
                self.data_y.pop(0)
            self.plot_line.setData(self.data_x, self.data_y)
            self.current_point.setData([x], [y])
        except Exception as exc:
            self._label.setText("--")
            print("Update failed:", exc)

    # -- zoom helpers ----------------------------------------------------
    def update_zoom(self) -> None:
        half = self._base_range / self._zoom
        self.plot.setXRange(-half, half, padding=0)
        self.plot.setYRange(-half, half, padding=0)

    def zoom_in(self) -> None:
        self._zoom *= 1.2
        self.update_zoom()

    def zoom_out(self) -> None:
        self._zoom /= 1.2
        self.update_zoom()


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
