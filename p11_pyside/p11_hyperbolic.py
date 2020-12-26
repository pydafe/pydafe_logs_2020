from PySide2 import QtCore, QtWidgets, QtGui
import sys
from dataclasses import dataclass
from enum import Enum
import cmath


class HypModel(Enum):
    """
    Модели плоскости Лобачевского. Простой перечислительный тип для удобства.
    """
    BeltramiKlein = 0
    Poincare = 1


@dataclass(frozen=True)
class HypPoint:
    """
    Класс для точек плоскости Лобачевского. Координаты точек заданы в модели Бельтрами-Клейна.

    Parameters
    ----------
    z: complex
      Координаты точки в какой-либо модели плоскости.
    m: HypModel
      Модель, в которой заданы координаты.
    """
    z: complex
    m: HypModel = HypModel.BeltramiKlein

    def isValid(self):
        """
        Лежит ли точка в плоскости Лобачевского?

        Returns
        -------
        bool
          Если лежит, то True.
        """
        return abs(self.z) < 1.0

    def __str__(self):
        bk = self if self.m == HypModel.BeltramiKlein else self.toModel(HypModel.BeltramiKlein)
        return 'x={:.06f}, y={:.06f}'.format(bk.z.real, bk.z.imag)

    def toModel(self, m):
        """
        Приведение координат к какой-либо модели.

        Parameters
        ----------
        m: HypModel
          Модель, к которой приводить координаты.

        Returns
        -------
        HypPoint
          Точка с координатами в новой модели.
        """
        if self.m == m:
            return self
        elif self.m == HypModel.BeltramiKlein and m == HypModel.Poincare:
            return HypPoint(self.z / (1 + (1 - abs(self.z) ** 2) ** 0.5), m)
        elif self.m == HypModel.Poincare and m == HypModel.BeltramiKlein:
            return HypPoint(2 * self.z / (1 + abs(self.z) ** 2), m)
        else:
            raise ValueError('unknown hyperbolic model {}'.format(m))


@dataclass(unsafe_hash=True, init=False)
class HypLine:
    a: float
    b: float
    c: float

    def __init__(self, a, b, c):
        """
        Прямая на плоскости Лобачевского. Задаётся прямой в модели Бельтрами-Клейна:
          a x + b y + c = 0
        При создании каждого объекта коэффициенты приводятся к a**2 + b**2 = 1.

        Parameters
        ----------
        a, b, c
          коэффициенты, задающие прямую в модели Бельтрами-Клейна.
        """
        n = (a ** 2 + b ** 2) ** 0.5
        self.a, self.b, self.c = a / n, b / n, c / n

    def isValid(self):
        """
        Проверка на то, лежит ли вообще прямая с соответствующими коэффициентами в плоскости Лобачевского.

        Returns
        -------
        bool
          True, если прямая лежит в плоскости.
        """
        return abs(self.c) < 1

    def idealPoints(self, m=HypModel.BeltramiKlein):
        """
        Вычисление идеальных точек прямой, т.е. точек абсолюта, к которым подходит прямая.

        Parameters
        ----------
        m
          В какой модели возвращать точки прямой. В обоих моделях координаты точек одинаковые,
          поэтому этот параметр не влияет на расчёт, а только на то, каковы будут соответствующие
          флаги у точек.

        Returns
        -------
        p
          Одна из идеальных точек.
        q
          Вторая из идеальных точек.
        """
        a, b, c = self.a, self.b, self.c
        nc = (1 - c ** 2) ** 0.5
        p = HypPoint(complex(-a * c - b * nc, -b * c + a * nc), m)
        q = HypPoint(complex(-a * c + b * nc, -b * c - a * nc), m)
        return p, q

    def pole(self):
        """
        Полюс прямой. Выделенная точка вне плоскости Лобачевского. С её помощью
        проводятся некоторые построения, в т.ч. построение перпендекуляра.

        Returns
        -------
        HypPoint
          Полюс.
        """
        p, q = self.idealPoints()
        return intersectLines(HypLine(p.z.real, p.z.imag, -1), HypLine(q.z.real, q.z.imag, -1))

    def __str__(self):
        return '{:.06f} x + {:.06f} y + {:.06f} = 0'.format(self.a, self.b, self.c)


def drawLineThroughPoints(p, q):
    """
    Провести прямую через две точки.

    Parameters
    ----------
    p: HypPoint
      Одна из точек.
    q: HypPoint
      Вторая.

    Returns
    -------
    HypLine
      Прямая, проходящая через точки p и q.
    """
    p = p.toModel(HypModel.BeltramiKlein).z
    q = q.toModel(HypModel.BeltramiKlein).z
    return HypLine(p.imag - q.imag, q.real - p.real, p.real * q.imag - p.imag * q.real)


def intersectLines(l1, l2):
    """
    Точка пересечения прямых. Если прямые расходятся, то точка может оказаться не валидной.

    Parameters
    ----------
    l1: HypLine
      Одна из прямых для пересечения.
    l2: HypLine
      Вторая прямая для поиска пересечения.

    Returns
    -------
    HypPoint
      Точка. В модели Бельтрами-Клейна. Может оказаться вне плоскости, если прямые расходятся.
    """
    d = l1.a * l2.b - l1.b * l2.a
    return HypPoint(complex((l1.b * l2.c - l2.b * l1.c) / d, (l2.a * l1.c - l1.a * l2.c) / d))


def drawPerpendicular(line, p):
    """
    Построение перпендикуляра к прямой через точку.

    Parameters
    ----------
    line: HypLine
      Прямая, к которой строить перпендикуляр.
    p: HypPoint
      Точка, через которую проводить перпендикуляр.

    Returns
    -------
    HypLine
      Прямая, перпендикулярная line и проходящая через p.
    """
    q = line.pole()
    return drawLineThroughPoints(p, q)


def drawParallels(line, point):
    """
    Провести две параллельных прямых через точку вне прямой. В геометрии
    Лобачевского это прямые, ограничивающие конус всевозможных прямых,
    проходящих через заданную точку вне прямой и не пересекающихся с данной.

    Parameters
    ----------
    line
      Прямая, параллельные к которой проводить.

    point
      Точка, через которую проводить параллельные.

    Returns
    -------
    tuple
      Пара из двух HypLine.
    """
    p, q = line.idealPoints()
    return drawLineThroughPoints(p, point), drawLineThroughPoints(q, point)


class HypTransform:
    def __init__(self, a, b):
        """
        Преобразование плоскости Лобачевского. Задаётся двумя параметрами как
        дробно-линейное преобразование модели Пуанкаре на диске:
        z -> (a z + b) / (b^* z + a^*)

        Конструктор нормирует параметры к соотношению |a|**2 - |b|**2 = 1.

        Parameters
        ----------
        a
          Параметр преобразования.

        b
          Параметр преобразования.
        """
        n = (a * a.conjugate() - b * b.conjugate()) ** 0.5
        self.a = a / n
        self.b = b / n

    def __mul__(self, other):
        """
        Композиция преобразований.
        """
        return HypTransform(self.a * other.a + self.b * other.b.conjugate(),
                            self.a * other.b + self.b * other.a.conjugate())

    @property
    def inv(self):
        """
        Обратное преобразование.
        """
        return HypTransform(self.a.conjugate(), -self.b)

    @staticmethod
    def identity():
        """
        Тождественное преобразование.
        """
        return HypTransform(1 + 0j, 0j)

    def __call__(self, point):
        """
        Применение преобразования к точке.
        """
        z = point.toModel(HypModel.Poincare).z
        a = self.a
        b = self.b
        w = (a * z + b) / (b.conjugate() * z + a.conjugate())
        return HypPoint(w, HypModel.Poincare)

    @staticmethod
    def pToQ(p, q):
        """
        Преобразование переноса вдоль прямой, переводящее одну точку в другую.

        Parameters
        ----------
        p: HypPoint
          Точка, которую преобразование должно перенести.
        q: HypPoint
          Точка, в которую должна быть перенесена исходная.

        Returns
        -------
        HypTransform
          Преобразование, переносящее точку p в точку q вдоль прямой pq.
        """
        p = p.toModel(HypModel.Poincare).z
        q = q.toModel(HypModel.Poincare).z
        p2 = abs(p) ** 2
        q2 = abs(q) ** 2
        return HypTransform(1 - 2 * p.conjugate() * q + p2 * q2, (1 + p2) * q - (1 + q2) * p)


class HypListItem(QtWidgets.QListWidgetItem):
    """
    Вспомогательный класс для представления объектов плоскости Лобачевского в Qt-виджетах списках.
    """
    def __init__(self, item, parent=None):
        self.raw = item
        super(HypListItem, self).__init__(str(item), parent, QtWidgets.QListWidgetItem.UserType)


class HypListWidget(QtWidgets.QListWidget):
    """
    Виджет для списков объектов.
    """
    def __init__(self, parent=None):
        super(HypListWidget, self).__init__(parent)

    def getRawObjects(self):
        for i in range(self.count()):
            item = self.item(i)
            if isinstance(item, HypListItem):
                yield self.item(i).raw

    def getRawSelection(self):
        for i in range(self.count()):
            item = self.item(i)
            if item.isSelected() and isinstance(item, HypListItem):
                yield item.raw

    def deleteSelected(self):
        selected = set(self.getRawSelection())

        i = 0
        while i < self.count():
            if self.item(i).raw in selected:
                self.takeItem(i)
            else:
                i += 1


class HypArea(QtWidgets.QWidget):
    """
    Виджет "плоскость Лобачевского" для отрисовки всего и вся.
    """
    def __init__(self, parent=None):
        super(HypArea, self).__init__(parent)
        # qt-шные настройки виджета
        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setAutoFillBackground(True)
        # центр диска в координатах виджета
        self.center = QtCore.QPointF(0, 0)
        # радиус диска в них же
        self.radius = 1
        # список объектов для отрисовки
        self.objects = []
        # список объектов для выделения красным
        self.selected = []
        # актуальная отрисованная модель
        self.model = HypModel.BeltramiKlein
        # текущая точка, за которую схватил пользователь для движения плоскостью
        # задаётся в координатах отрисовки
        self.grabPoint = HypPoint(0)
        # актуальное преобразование плоскости для отрисовки
        self.transform = HypTransform.identity()

    def minimumSizeHint(self):
        return QtCore.QSize(300, 300)

    def resizeEvent(self, event):
        self.center = QtCore.QPointF(self.width() / 2, self.height() / 2)
        self.radius = min(self.width(), self.height()) / 2 * 0.98

    def _drawPoint(self, painter, point):
        # отрисовка точки
        z = self.transform(point).toModel(self.model).z
        painter.drawEllipse(QtCore.QPointF(z.real, z.imag), 0.015, 0.015)

    def _drawLine(self, painter, line):
        # отрисовка прямой
        pp, qq = line.idealPoints()
        zp, zq = self.transform(pp).z, self.transform(qq).z

        if self.model == HypModel.BeltramiKlein:
            # в модели БК -- это просто отрезок между двумя идеальными точками
            painter.drawLine(QtCore.QPointF(zp.real, zp.imag), QtCore.QPointF(zq.real, zq.imag))
        elif self.model == HypModel.Poincare:
            # В модели Пуанкаре -- это окружность, местами плавно переходящая в прямую.
            # Поэтому для плавности вырождения окружности больших радиусов отрисовываем
            # с помощью кривых Безье.
            z = (zp + zq) / 2
            if abs(z) > 0.1:
                # центр окружности -- это инверсия от середины отрезка pq
                z = z / abs(z) ** 2

                # радиус окружности
                r = (abs(z) ** 2 - 1) ** 0.5
                # рисовать дугу от p к q или от q к p?
                # здесь следует помнить, что плоскость на отрисовке зазеркалена.
                if cmath.phase((zq - z) / (zp - z)) > 0:
                    zp, zq = zq, zp

                start = cmath.phase(zp - z)
                span = cmath.phase((zq - z) / (zp - z))

                m = 2880 / cmath.pi  # множитель для qt недоградусов
                painter.drawArc(QtCore.QRectF(z.real - r, z.imag - r, 2 * r, 2 * r), -start * m, -span * m)
            else:
                path = QtGui.QPainterPath()
                path.moveTo(zp.real, zp.imag)
                path.quadTo(0, 0, zq.real, zq.imag)
                painter.drawPath(path)
        else:
            raise ValueError('unknown model {}'.format(self.model))

    def paintEvent(self, event):
        # кисти и карандаши для рисования
        redpen = QtGui.QPen(QtCore.Qt.red, 0)
        blackpen = QtGui.QPen(QtCore.Qt.black, 0)
        nopen = QtCore.Qt.NoPen
        redbrush = QtGui.QBrush(QtCore.Qt.red)
        blackbrush = QtGui.QBrush(QtCore.Qt.black)
        nobrush = QtCore.Qt.NoBrush

        # установка координат и отрисовка абсолюта
        painter = QtGui.QPainter(self)
        painter.translate(self.center)
        painter.scale(self.radius, self.radius)
        painter.setPen(blackpen)
        painter.drawEllipse(QtCore.QRectF(-1, -1, 2, 2))

        for obj in self.objects:
            if isinstance(obj, HypPoint):
                painter.setPen(nopen)
                painter.setBrush(blackbrush)
                self._drawPoint(painter, obj)
            elif isinstance(obj, HypLine):
                painter.setPen(blackpen)
                painter.setBrush(nobrush)
                self._drawLine(painter, obj)

        for obj in self.selected:
            if isinstance(obj, HypPoint):
                painter.setPen(nopen)
                painter.setBrush(redbrush)
                self._drawPoint(painter, obj)
            elif isinstance(obj, HypLine):
                painter.setPen(redpen)
                painter.setBrush(nobrush)
                self._drawLine(painter, obj)

        painter.end()

    addPoints = QtCore.Signal(list)

    def _event_coords(self, event):
        x = (event.x() - self.center.x()) / self.radius
        y = (event.y() - self.center.y()) / self.radius
        return x + 1j * y

    def mouseDoubleClickEvent(self, event):
        # двойным кликом -- добавить точку на плоскость.
        # если кликнули по плоскости, конечно.
        z = self._event_coords(event)
        if abs(z) >= 1:
            return

        w = self.transform.inv(HypPoint(z, self.model))

        self.addPoints.emit([w])

    def mousePressEvent(self, event):
        # фиксируем точку, которую ухватил пользователь
        z = self._event_coords(event)
        if abs(z) >= 1:
            return

        self.grabPoint = HypPoint(z, self.model)

    def mouseMoveEvent(self, event):
        # если пользователь тащит плоскость, её надо трансформировать.
        w = self._event_coords(event)
        if abs(w) >= 1 or (not self.grabPoint.isValid()):
            return

        p = self.grabPoint
        q = HypPoint(w, self.model)
        self.transform = HypTransform.pToQ(p, q) * self.transform
        self.grabPoint = q
        self.repaint()

    @QtCore.Slot(list)
    def setObjects(self, objects):
        (self.objects, self.selected) = objects
        self.repaint()

    @QtCore.Slot(str)
    def setModel(self, model):
        d = {'Beltrami-Klein': HypModel.BeltramiKlein,
             'Poincare': HypModel.Poincare}

        if model in d:
            self.model = d[model]
        else:
            raise ValueError('unknown model {}'.format(model))

        self.repaint()


class HypControls(QtWidgets.QWidget):
    """
    Виджеты для управления плоскостью Лобачевского:
      * ведение списков объектов,
      * добавление новых объектов,
      * удаление старых.
    """
    def __init__(self, parent=None):
        super(HypControls, self).__init__(parent)
        expanding = QtWidgets.QSizePolicy.Expanding

        # список отмеченных точек плоскости
        self.points = HypListWidget()
        minimum = QtWidgets.QSizePolicy.Minimum
        self.points.setSizePolicy(minimum, expanding)
        self.points.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        # список отмеченных прямых плоскости
        self.lines = HypListWidget()
        self.lines.setSizePolicy(minimum, expanding)
        self.lines.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        # выпадающее меню с выбором модели плоскости
        self.modelsBox = QtWidgets.QComboBox()
        self.modelsBox.addItems(['Beltrami-Klein', 'Poincare'])

        # различные кнопки с добавлением новых объектов
        buttonsAdd1 = QtWidgets.QHBoxLayout()
        self.linesThroughPointsButton = QtWidgets.QPushButton('Lines through points')
        buttonsAdd1.addWidget(self.linesThroughPointsButton)
        self.intersectionsOfLinesButton = QtWidgets.QPushButton('Intersections')
        buttonsAdd1.addWidget(self.intersectionsOfLinesButton)

        # ещё кнопок с добавление объектов
        buttonsAdd2 = QtWidgets.QHBoxLayout()
        self.perpendicularLinesButton = QtWidgets.QPushButton('Perpendiculars')
        buttonsAdd2.addWidget(self.perpendicularLinesButton)
        self.parallelLinesButton = QtWidgets.QPushButton('Parallels')
        buttonsAdd2.addWidget(self.parallelLinesButton)

        # кнопки с удалением объектов
        buttonsDel = QtWidgets.QHBoxLayout()
        self.deleteObjectsButton = QtWidgets.QPushButton('Delete selection')
        buttonsDel.addWidget(self.deleteObjectsButton)
        self.clearObjectsButton = QtWidgets.QPushButton('Clear')
        buttonsDel.addWidget(self.clearObjectsButton)

        # разложение всего вышеперечисленного в столбик
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Models'))
        layout.addWidget(self.modelsBox)
        layout.addWidget(QtWidgets.QLabel('Add objects'))
        layout.addLayout(buttonsAdd1)
        layout.addLayout(buttonsAdd2)
        layout.addWidget(QtWidgets.QLabel('Remove objects'))
        layout.addLayout(buttonsDel)
        layout.addWidget(QtWidgets.QLabel('Points:'))
        layout.addWidget(self.points)
        layout.addWidget(QtWidgets.QLabel('Lines:'))
        layout.addWidget(self.lines)
        self.setLayout(layout)

        # взаимодействие элементов
        self.points.itemSelectionChanged.connect(self.selectionChanged)
        self.lines.itemSelectionChanged.connect(self.selectionChanged)
        self.modelsBox.currentTextChanged.connect(self.modelChanged)
        self.deleteObjectsButton.clicked.connect(self.deleteObjects)
        self.linesThroughPointsButton.clicked.connect(self.addLinesThroughPoints)
        self.intersectionsOfLinesButton.clicked.connect(self.addIntersectionsOfLines)
        self.clearObjectsButton.clicked.connect(self.clearObjects)
        self.perpendicularLinesButton.clicked.connect(self.addPerpendiculars)
        self.parallelLinesButton.clicked.connect(self.addParallels)

    def _emitObjects(self):
        objs = set(self.points.getRawObjects()).union(self.lines.getRawObjects())
        selected = set(self.points.getRawSelection()).union(self.lines.getRawSelection())
        self.objectsChanged.emit((objs, selected))

    @QtCore.Slot(list)
    def addPoints(self, points):
        for point in points:
            if point.isValid():
                self.points.addItem(HypListItem(point))

        self._emitObjects()

    @QtCore.Slot(list)
    def addLines(self, lines):
        for line in lines:
            if line.isValid():
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
    def clearObjects(self):
        self.lines.clear()
        self.points.clear()
        self._emitObjects()

    @QtCore.Slot()
    def addLinesThroughPoints(self):
        newLines = []
        selectedPoints = list(self.points.getRawSelection())
        for i in range(len(selectedPoints)):
            for j in range(i):
                newLines.append(drawLineThroughPoints(selectedPoints[i], selectedPoints[j]))

        self.addLines(newLines)

    @QtCore.Slot()
    def addIntersectionsOfLines(self):
        newPoints = []
        selectedLines = list(self.lines.getRawSelection())
        for i in range(len(selectedLines)):
            for j in range(i):
                newPoints.append(intersectLines(selectedLines[i], selectedLines[j]))

        self.addPoints(newPoints)

    @QtCore.Slot()
    def addPerpendiculars(self):
        self._addLinesFromPointsAndLines(lambda l, p: [drawPerpendicular(l, p)])

    @QtCore.Slot()
    def addParallels(self):
        self._addLinesFromPointsAndLines(drawParallels)

    def _addLinesFromPointsAndLines(self, maker):
        newLines = []
        selectedLines = list(self.lines.getRawSelection())
        selectedPoints = list(self.points.getRawSelection())
        for li in range(len(selectedLines)):
            for pi in range(len(selectedPoints)):
                newLines.extend(maker(selectedLines[li], selectedPoints[pi]))

        self.addLines(newLines)

    objectsChanged = QtCore.Signal(tuple)
    modelChanged = QtCore.Signal(str)


class HypWindow(QtWidgets.QWidget):
    """
    Сборный виджет для всего приложения.
    """
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
        self.controls.modelChanged.connect(self.drawing.setModel)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    window = HypWindow()
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec_())
