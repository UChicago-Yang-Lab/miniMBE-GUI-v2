#!/usr/bin/env python3
import sys

from PySide6 import QtWidgets, QtUiTools, QtCore

from controller import ManipulatorController


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
    table.setRowCount(3)
    table.setColumnCount(2)
    table.setHorizontalHeaderLabels(["Axis", "Position"])
    table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

    axis_names = ["X", "Y", "Z"]
    for row, name in enumerate(axis_names):
        item = QtWidgets.QTableWidgetItem(name)
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        table.setItem(row, 0, item)
        table.setItem(row, 1, QtWidgets.QTableWidgetItem("--"))

    status_label = QtWidgets.QLabel("Connecting...")
    window.statusbar.addPermanentWidget(status_label)

    controller = ManipulatorController()

    def update_positions():
        try:
            x, y, z = controller.read_all_axes()
        except Exception as exc:  # pragma: no cover - GUI feedback
            status_label.setText(f"Error: {exc}")
            return
        for row, val in enumerate([x, y, z]):
            table.item(row, 1).setText(f"{val:.3f}")
        status_label.setText("Connected")

    timer = QtCore.QTimer(interval=1000, timeout=update_positions)
    timer.start()

    window.show()
    ret = app.exec()
    controller.close()
    return ret


if __name__ == "__main__":
    sys.exit(main())
