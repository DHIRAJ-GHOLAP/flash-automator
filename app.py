import argparse
import sys
import types

# Ensure pyautogui does not require tkinter via optional mouseinfo module
if "mouseinfo" not in sys.modules:
    sys.modules["mouseinfo"] = types.ModuleType("mouseinfo")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from flash_automator.ui.main_window import MainWindow
from flash_automator.utils.logger import setup_logger

logger = setup_logger("flash_automator")


def main() -> int:
    parser = argparse.ArgumentParser(description="Flash Automator - Desktop RPA & Date Macro Engine")
    parser.add_argument("--version", action="version", version="Flash Automator 1.0.0")
    parser.add_argument("--test-init", action="store_true", help="Initialize and exit immediately to verify startup")
    args = parser.parse_args()

    # Enable High-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Flash Automator")
    app.setOrganizationName("Flash Automator Team")

    logger.info("Initializing Flash Automator UI...")
    window = MainWindow()

    if args.test_init:
        logger.info("Test init successful, exiting cleanly.")
        return 0

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
