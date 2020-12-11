from PySide2 import QtCore, QtWidgets, QtGui
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class HypPoint:
    x: float
    y: float

    def isValid(self):
        return self.y ** 2 + self.x ** 2 < 1.0

    def __str__(self):
        return 'x={:.06f}, y={:.06f}'.format(self.x, self.y)


class HypListItem(QtWidgets.QListWidgetItem):
    def __init__(self, item):
        self.raw = item
        super(HypListItem, self).__init__(str(item))


class HypArea(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HypArea, self).__init__(parent)
        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setAutoFillBackground(True)
        self.center = QtCore.QPointF(0, 0)
        self.radius = 1
        self.objects = []

    def minimumSizeHint(self):
        return QtCore.QSize(300, 300)

    def resizeEvent(self, event):
        self.center = QtCore.QPointF(self.width() / 2, self.height() / 2)
        self.radius = min(self.width(), self.height()) / 2 * 0.98

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.translate(self.center)
        painter.scale(self.radius, self.radius)
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 0))
        painter.drawEllipse(QtCore.QRectF(-1, -1, 2, 2))

        painter.setBrush(QtCore.Qt.black)
        for obj in self.objects:
            if isinstance(obj, HypPoint):
                painter.setPen(QtCore.Qt.NoPen)
                painter.drawEllipse(QtCore.QPointF(obj.x, obj.y), 0.015, 0.015)

        painter.end()

    addPoints = QtCore.Signal(list)

    def mouseDoubleClickEvent(self, event):
        x = (event.x() - self.center.x()) / self.radius
        y = (event.y() - self.center.y()) / self.radius

        if x ** 2 + y ** 2 < 1:
            self.addPoints.emit([HypPoint(x, y)])

    @QtCore.Slot(list)
    def setObjects(self, objects):
        self.objects = objects
        self.repaint()


class HypControls(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HypControls, self).__init__(parent)
        expanding = QtWidgets.QSizePolicy.Expanding

        self.points = QtWidgets.QListWidget()
        minimum = QtWidgets.QSizePolicy.Minimum
        self.points.setSizePolicy(minimum, expanding)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.points)
        self.setLayout(layout)

    def _emitObjects(self):
        objs = set()
        for i in range(self.points.count()):
            objs.add(self.points.item(i).raw)

        self.objectsChanged.emit(objs)

    @QtCore.Slot(list)
    def addPoints(self, points):
        for point in points:
            self.points.addItem(HypListItem(point))

        self._emitObjects()

    objectsChanged = QtCore.Signal(tuple)


class HypWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HypWindow, self).__init__(parent)

        self.drawing = HypArea(self)
        expanding = QtWidgets.QSizePolicy.Expanding
        policy = QtWidgets.QSizePolicy(expanding, expanding)
        self.drawing.setSizePolicy(policy)

        self.controls = HypControls(self)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.drawing)
        layout.addWidget(self.controls)
        self.setLayout(layout)

        self.drawing.addPoints.connect(self.controls.addPoints)
        self.controls.objectsChanged.connect(self.drawing.setObjects)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    window = HypWindow()
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec_())
