from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QPen
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication
# Contains a pixmap which can be drawn to, is for images or text.
# Can't use pixmap directly because it's off-screen.
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QWidget

from nes import NES


class MainWindow(QMainWindow):

    def __init__(self, filepath: Path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.window = QLabel()
        self.pixel_buffer = QPixmap(256, 240)
        self.window.setPixmap(self.pixel_buffer)
        self.setCentralWidget(self.window)
        self.nes = NES(filepath)
        # Skip drawing frames to disk.
        self.nes.ppu.renderer.renderer_type = 'memory'

        # https://doc.qt.io/qt-5/qapplication.html#exec
        # "To make your application perform idle processing, i.e., executing
        # a special function whenever there are no pending events, use a
        # QTimer with 0 timeout. More advanced idle processing schemes can
        # be achieved using processEvents()."
        self.timer = QTimer()
        # Run the update on a timer while QT isn't processing UI.
        # The downside of this is we may block the main GUI thread, which
        # is why we should probably use multithreading.
        # https://github.com/pyqt/examples/tree/_/src/11%20PyQt%20Thread%20example
        self.timer.timeout.connect(self.update)
        self.timer.start(0)
        # FIXME
        # Remove this when we can properly load a buffer of pixels.
        self.pen = QPen()
        self.pen.setWidth(1)
        self.last_frame = 0

        # A way to force a jump to the demo at a certain
        # CPU instruction.
        self._skip_to_demo = False

    def keyPressEvent(self, e) -> bool:
        print(hex(e.key()))
        # https://doc.qt.io/qt-5/qt.html#Key-enum
        if e.key() == 0x5a:
            self._skip_to_demo = not self._skip_to_demo
            print('Toggled skipping to demo', self._skip_to_demo)

    # def event(self, e) -> bool:
    #     # Gets all events.
    #     print(e)
    #     return True

    def update(self) -> None:
        if self.nes.cpu.pc == 0xc953 and self._skip_to_demo:
            print("Skipping to demo")
            self.nes.cpu.pc = 0xc955
            self.nes.cpu._set_zero(True)
        self.nes.run()

        if self.nes.ppu._frames == self.last_frame:
            return
        # We have enough for a frame now draw it.
        self.last_frame = self.nes.ppu._frames

        # Paint the next pixel.
        # FIXME
        # This really should just copy the entire frame in one go.
        # qba = QByteArray(self.nes.ppu._pixels)
        # self.pixel_buffer.loadFromData(qba)
        painter = QPainter(self.window.pixmap())
        for y in range(240):
            # Go row by row.
            for x in range(256):
                # Each column in the row.
                idx = x + y * 256
                pixel_lookup = self.nes.ppu._pixels[idx]
                from palettes import LUT
                r, g, b = LUT[pixel_lookup]
                colour = QColor(r, g, b)
                self.pen.setColor(colour)
                painter.setPen(self.pen)
                painter.drawPoint(x, y)
        painter.end()

        # Update the widget. Forces a repaint. If we don't do this
        # we need to wait for some other event like the widget being
        # covered/uncovered, etc.
        self.window.update()

    def closeEvent(self, e):
        print(e)
        # e.ignore() to ignore window closing event.
        # if not text.document().isModified():
        #     return
        # answer = QMessageBox.question(
        #     window, None,
        #     "You have unsaved changes. Save before closing?",
        #     QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        # )
        # if answer & QMessageBox.Save:
        #     save()
        # elif answer & QMessageBox.Cancel:
        #     e.ignore()


def main(filepath):
    # All QT applications need a QT(Gui)Application by default.
    app = QApplication([])
    window = MainWindow(filepath)
    window.show()
    app.exec_()


if __name__ == "__main__":
    path = Path(__file__).parent / '../roms/donkey_kong/donkey_kong.nes'
    main(path)
