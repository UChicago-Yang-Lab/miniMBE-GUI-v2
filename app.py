import sys
from PySide6 import QtWidgets, QtUiTools, QtCore
from PySide6.QtCore import Qt

def load_ui(ui_file):
    loader = QtUiTools.QUiLoader()
    ui_file = QtCore.QFile(ui_file)
    ui_file.open(QtCore.QFile.ReadOnly)
    window = loader.load(ui_file)
    ui_file.close()
    return window

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_win = load_ui("ui/main_window.ui")
    main_win.show() 
    sys.exit(app.exec())
