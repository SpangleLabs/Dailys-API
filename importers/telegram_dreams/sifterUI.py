from typing import List, TypeVar, Callable, Generic

from PyQt5 import uic, QtWidgets
import sys
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut, QPushButton, QHBoxLayout, QGraphicsView, QGraphicsScene

T = TypeVar("T")


class SiftCategory(Generic[T]):

    def __init__(
            self,
            keyboard_shortcut: str,
            name: str,
            function: Callable[[T], None]
    ):
        self.keyboard_shortcut = keyboard_shortcut
        self.name = name
        self.function = function


Ui_MainWindow, QtBaseClass = uic.loadUiType("sifter.ui")


class SifterUI(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(
            self,
            input_objects: List[T],
            categories: List[SiftCategory[T]],
            display_object: Callable[[T, QGraphicsView], None]
    ):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        h_layout = self.findChild(QHBoxLayout, "horizontalLayout")
        for category in categories:
            qt_button = QPushButton(f"{category.name} ({category.keyboard_shortcut})")
            qt_button.clicked.connect(lambda *, cat=category: self.button_clicked(cat))
            h_layout.addWidget(qt_button)
            shortcut = QShortcut(QKeySequence(category.keyboard_shortcut), self)
            shortcut.activated.connect(lambda *, cat=category: self.button_clicked(cat))

        self.input_messages = input_objects
        self.input_iter = iter(input_objects)
        self.display_object = display_object
        self.update_display(next(self.input_iter))

    def button_clicked(self, category: SiftCategory):
        try:
            next_item = next(self.input_iter)
        except StopIteration:
            self.iterator_done()
            return
        category.function(next_item)
        self.update_display(next_item)

    def iterator_done(self):
        view = self.findChild(QGraphicsView, "graphicsView")
        scene = QGraphicsScene()
        scene.addText("All data processing complete")
        view.setScene(scene)
        h_layout = self.findChild(QHBoxLayout, "horizontalLayout")
        for i in reversed(range(h_layout.count())):
            h_layout.itemAt(i).widget().deleteLater()
        close_button = QPushButton("Close")
        close_button.clicked.connect(lambda: self.close())
        h_layout.addWidget(close_button)

    def update_display(self, message):
        view = self.findChild(QGraphicsView, "graphicsView")
        self.display_object(message, view)


if __name__ == "__main__":
    buttons = [
        SiftCategory(
            "D",
            "Dream",
            lambda x: print(x)
        ),
        SiftCategory(
            "S",
            "Skip",
            lambda x: print("Skip")
        ),
        SiftCategory(
            "A",
            "Additional dream data",
            lambda x: print("Adding that then")
        )
    ]


    def display_text(text: str, view: QGraphicsView):
        scene = QGraphicsScene()
        scene.addText(text)
        view.setScene(scene)


    app = QtWidgets.QApplication(sys.argv)
    window = SifterUI(["aaaa", "bb"], buttons, display_text)
    window.show()
    sys.exit(app.exec_())
