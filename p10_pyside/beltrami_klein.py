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


@dataclass(frozen=True)
class HypLine:
    a: float
    b: float
    c: float

    def normalize(self):
        n = (self.a ** 2 + self.b ** 2) ** 0.5
        return HypLine(self.a / n, self.b / n, self.c / n)

    def isValid(self):
        return self.c ** 2  < self.a ** 2 + self.b ** 2

    def circlePoints(self):
        normed = self.normalize()
        nc = (1 - normed.c ** 2) ** 0.5
        a, b, c = normed.a, normed.b, normed.c
        p = HypPoint(-a * c - b * nc, -b * c + a * nc)
        q = HypPoint(-a * c + b * nc, -b * c - a * nc)
        return p, q

    def __str__(self):
        return '{:.06f} x + {:.06f} y + {:.06f} = 0'.format(self.a, self.b, self.c)


def drawLineOverPoints(p, q):
    return HypLine(p.y - q.y, q.x - p.x, p.x * q.y - p.y * q.x)


def intersectLines(l1, l2):
    d = l1.a * l2.b - l1.b * l2.a
    return HypPoint((l1.b * l2.c - l2.b * l1.c) / d, (l2.a * l1.c - l1.a * l2.c) / d)


class HypListItem(QtWidgets.QListWidgetItem):
    def __init__(self, item):
        self.raw = item
        super(HypListItem, self).__init__(str(item))


class HypListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super(HypListWidget, self).__init__(parent)

    def deleteSelected(self):
        selected = set(item.raw for item in self.selectedItems())

        i = 0
        while i < self.count():
            if self.item(i).raw in selected:
                self.takeItem(i)
            else:
                i += 1


class HypArea(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HypArea, self).__init__(parent)
        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setAutoFillBackground(True)
        self.center = QtCore.QPointF(0, 0)
        self.radius = 1
        self.objects = []
        self.selected = []

    def minimumSizeHint(self):
        return QtCore.QSize(300, 300)

    def resizeEvent(self, event):
        self.center = QtCore.QPointF(self.width() / 2, self.height() / 2)
        self.radius = min(self.width(), self.height()) / 2 * 0.98

    def _circle_painter(self):
        painter = QtGui.QPainter(self)
        painter.translate(self.center)
        painter.scale(self.radius, self.radius)

        return painter

    def paintEvent(self, event):
        redpen = QtGui.QPen(QtCore.Qt.red, 0)
        blackpen = QtGui.QPen(QtCore.Qt.black, 0)
        nopen = QtCore.Qt.NoPen

        painter = self._circle_painter()
        painter.setPen(blackpen)
        painter.drawEllipse(QtCore.QRectF(-1, -1, 2, 2))

        painter.setBrush(QtCore.Qt.black)
        for obj in self.objects:
            if isinstance(obj, HypPoint):
                painter.setPen(nopen)
                painter.drawEllipse(QtCore.QPointF(obj.x, obj.y), 0.015, 0.015)
            elif isinstance(obj, HypLine):
                painter.setPen(blackpen)
                p, q = obj.circlePoints()
                painter.drawLine(QtCore.QPointF(p.x, p.y), QtCore.QPointF(q.x, q.y))

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.red)
        for obj in self.selected:
            if isinstance(obj, HypPoint):
                painter.drawEllipse(QtCore.QPointF(obj.x, obj.y), 0.015, 0.015)
            elif isinstance(obj, HypLine):
                painter.setPen(redpen)
                p, q = obj.circlePoints()
                painter.drawLine(QtCore.QPointF(p.x, p.y), QtCore.QPointF(q.x, q.y))

        painter.end()

    addPoints = QtCore.Signal(list)

    def mouseDoubleClickEvent(self, event):
        x = (event.x() - self.center.x()) / self.radius
        y = (event.y() - self.center.y()) / self.radius

        if x ** 2 + y ** 2 < 1:
            self.addPoints.emit([HypPoint(x, y)])

    @QtCore.Slot(list)
    def setObjects(self, objects):
        (self.objects, self.selected) = objects
        self.repaint()


class HypControls(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HypControls, self).__init__(parent)
        expanding = QtWidgets.QSizePolicy.Expanding

        self.points = HypListWidget()
        minimum = QtWidgets.QSizePolicy.Minimum
        self.points.setSizePolicy(minimum, expanding)
        self.points.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        self.lines = HypListWidget()
        self.lines.setSizePolicy(minimum, expanding)
        self.lines.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        buttons = QtWidgets.QHBoxLayout()
        self.drawLinesButton = QtWidgets.QPushButton('Draw lines')
        buttons.addWidget(self.drawLinesButton)
        self.pointIntersectionsButton = QtWidgets.QPushButton('Point intersections')
        buttons.addWidget(self.pointIntersectionsButton)
        self.deleteObjectsButton = QtWidgets.QPushButton('Delete objects')
        buttons.addWidget(self.deleteObjectsButton)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.points)
        layout.addLayout(buttons)
        layout.addWidget(self.lines)
        self.setLayout(layout)

        self.points.itemSelectionChanged.connect(self.selectionChanged)
        self.lines.itemSelectionChanged.connect(self.selectionChanged)
        self.deleteObjectsButton.clicked.connect(self.deleteObjects)
        self.drawLinesButton.clicked.connect(self.drawLines)
        self.pointIntersectionsButton.clicked.connect(self.pointIntersections)

    def _emitObjects(self):
        objs = set()
        for i in range(self.points.count()):
            objs.add(self.points.item(i).raw)

        for i in range(self.lines.count()):
            objs.add(self.lines.item(i).raw)

        selected = {i.raw for i in self.points.selectedItems()}.union(i.raw for i in self.lines.selectedItems())

        self.objectsChanged.emit((objs, selected))

    @QtCore.Slot(list)
    def addPoints(self, points):
        for point in points:
            self.points.addItem(HypListItem(point))

        self._emitObjects()

    @QtCore.Slot(list)
    def addLines(self, lines):
        for line in lines:
            self.lines.addItem(HypListItem(line))

        self._emitObjects()

    @QtCore.Slot()
    def selectionChanged(self):
        self._emitObjects()

    @QtCore.Slot()
    def deleteObjects(self):
        self.lines.deleteSelected()
        self.points.deleteSelected()
        self._emitObjects()

    @QtCore.Slot()
    def drawLines(self):
        lines = []
        selected = [item.raw for item in self.points.selectedItems()]
        for i in range(len(selected)):
            for j in range(i):
                line = drawLineOverPoints(selected[i], selected[j])
                if line.isValid():
                    lines.append(line)

        self.addLines(lines)

    @QtCore.Slot()
    def pointIntersections(self):
        points = []
        selected = [item.raw for item in self.lines.selectedItems()]
        for i in range(len(selected)):
            for j in range(i):
                point = intersectLines(selected[i], selected[j])
                if point.isValid():
                    points.append(point)

        self.addPoints(points)

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
