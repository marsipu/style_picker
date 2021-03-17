import os

from PyQt5.QtCore import QCoreApplication, QTimer, Qt
from PyQt5.QtWidgets import QApplication
import sys

from style_picker import DarkSheetPicker

ismac = sys.platform.startswith("darwin")
iswin = sys.platform.startswith("win32")
islin = not ismac and not iswin

def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName('mne_dark_picker')

    # Make Style-Sheet inheritable
    app.setAttribute(Qt.AA_UseStyleSheetPropagationInWidgetStyles, True)

    if ismac:
        app.setAttribute(Qt.AA_DontShowIconsInMenus, True)
        # Workaround for MAC menu-bar-focusing issue
        app.setAttribute(Qt.AA_DontUseNativeMenuBar, True)
        # Workaround for not showing with PyQt < 5.15.2
        os.environ['QT_MAC_WANTS_LAYER'] = '1'

    sp = DarkSheetPicker()
    sp.show()

    # Command-Line interrupt with Ctrl+C possible
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(500)

    # For Spyder to make console accessible again
    app.lastWindowClosed.connect(app.quit)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
