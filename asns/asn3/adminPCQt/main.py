"""
Smart Parking Admin PC - Qt/PySide6 Version

Entry point for the application.
"""

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from viewmodels import ParkingViewModel


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Smart Parking Admin")
    app.setOrganizationName("CME466")

    # Create the ViewModel
    viewmodel = ParkingViewModel()

    # Set up QML engine
    engine = QQmlApplicationEngine()

    # Load the QML file with viewmodel as initial property
    qml_file = Path(__file__).parent / "Main.qml"
    engine.setInitialProperties({"controller": viewmodel})
    engine.load(qml_file)

    if not engine.rootObjects():
        print("Error: Failed to load QML file")
        sys.exit(-1)

    # Run the application
    exit_code = app.exec()

    # Cleanup - delete engine first to destroy QML objects before viewmodel
    del engine
    viewmodel.cleanup()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
