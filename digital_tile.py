from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np

class DigTile(QtWidgets.QGraphicsView):
    WEDGE_REQUESTED = QtCore.pyqtSignal(int,int,bool)
    WEDGE_ENTER = QtCore.pyqtSignal(int,int)
    WEDGE_CHOSEN = QtCore.pyqtSignal(bool)

    def __init__(self, parent):
        super(DigTile, self).__init__(parent)

        #Defaults
        self.my_scene = my_scene(self)
        self.setScene(self.my_scene)
        self._is_initialized = False

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor('darkGray')))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

    def initialize_tiles(self,nbs,nba,ac,cursor,click):
        for item in self.my_scene.items():
            self.my_scene.removeItem(item)
        self._mouseIsPressed = False
        self._mouseIsMoved = False
        self.max_zoom_factor = 20
        self._zoom = 0
        self._empty = False
        self.cursor_selection = cursor
        self.click_function = click
        self.wedges = {}
        self.chosen_wedge_indices = set()
        self.edited_wedges_indices = set()
        self._a = 800/2**nbs
        self._tiles_size = 2**nbs*self._a + 200
        self.nbs = nbs
        self.nba = nba
        self.ac = ac
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._background = QtGui.QPixmap(self._tiles_size,self._tiles_size)
        self._background.fill(QtGui.QColor("white"))
        self._photo.setPixmap(self._background)
        self._item_group = QtWidgets.QGraphicsItemGroup()
        self._labelText = QtWidgets.QGraphicsTextItem("")
        self._labelText.setDefaultTextColor(QtGui.QColor("black"))
        self._labelText.setPlainText("Number of scales = {}\nNumber of angles = {}".format(self.nbs, self.nba))
        self._labelText.setPos(40,40)
        self._labelText.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations,True)
        self._labelText.show()
        self._labelIsPresent = True
        self._item_group.addToGroup(self._labelText)
        self.my_scene.addItem(self._item_group)
        self.my_scene.addItem(self._photo)
        self._is_initialized = True
        for i in range(nbs):
            m = 1 if i == 0 else self.nba * 2**(i//2)
            available = False if not self.ac and i == nbs-1 else True
            for j in range(m):
                self.add_wedge(i,j,available)

    def show_selected_cells(self):
        if self._is_initialized:
            for i,j in self.chosen_wedge_indices:
                self.WEDGE_REQUESTED.emit(i,j,False)

    def set_cursor_selection_rule(self,rule):
        self.cursor_selection = rule

    def set_click_function_rule(self,rule):
        self.click_function = rule

    def has_photo(self):
        if self._is_initialized:
            return not self._empty
        else:
            return False

    def set_photo(self, pixmap=None):
        self._zoom = 0
        self._empty = False
        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        self._photo.setPixmap(pixmap)

    def wheelEvent(self, event):
        """This is an overload function"""
        if self.has_photo():
            self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > -self.max_zoom_factor and self._zoom < self.max_zoom_factor:
                self.scale(factor, factor)
                self.end = QtCore.QPointF(self.mapToScene(event.pos()))
            elif self._zoom <=-self.max_zoom_factor:
                self._zoom = -self.max_zoom_factor
            else:
                self._zoom = self.max_zoom_factor

    def zoom_in(self):
        if self.has_photo():
            self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
            factor = 1.25
            self._zoom += 1
            if self._zoom > -self.max_zoom_factor and self._zoom < self.max_zoom_factor:
                self.scale(factor, factor)
            elif self._zoom <=-self.max_zoom_factor:
                self._zoom = -self.max_zoom_factor
            else:
                self._zoom = self.max_zoom_factor

    def zoom_out(self):
        if self.has_photo():
            self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
            factor = 0.8
            self._zoom -= 1
            if self._zoom > -self.max_zoom_factor and self._zoom < self.max_zoom_factor:
                self.scale(factor, factor)
            elif self._zoom <=-self.max_zoom_factor:
                self._zoom = -self.max_zoom_factor
            else:
                self._zoom = self.max_zoom_factor

    def contextMenuEvent(self,event):
        """This is an overload function"""
        if self.has_photo():
            self.menu = QtWidgets.QMenu()
            self.save = QtWidgets.QAction('Save as...')
            self.save.triggered.connect(self.save_scene)
            self.menu.addAction(self.save)
            self.menu.popup(event.globalPos())

    def save_scene(self):
        imageFileName = QtWidgets.QFileDialog.getSaveFileName(None,"choose save file name","./pattern.jpeg",\
                                                                   "Image (*.jpeg)")
        rect = self.my_scene.sceneRect()
        capture = QtGui.QImage(rect.size().toSize(),QtGui.QImage.Format_ARGB32_Premultiplied)
        painter = QtGui.QPainter(capture)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        self.my_scene.render(painter,QtCore.QRectF(capture.rect()),QtCore.QRectF(rect))
        painter.end()
        capture.save(imageFileName[0])

    def add_wedge(self,i,j,available):
        a = self._a
        if i == 0:
            x1, y1, x2, y2, x3, y3, x4, y4 = -a, -a, a, -a, a, a, -a, a
        else:
            m = -self.nba * 2**(i//2)
            x1 = min(2**(i-1)*a, abs(2**(i-1)*a/np.tan(np.pi*2*j/m)))*np.sign(np.cos(np.pi*2*j/m))
            y1 = min(2**(i-1)*a, abs(2**(i-1)*a*np.tan(np.pi*2*j/m)))*np.sign(np.sin(np.pi*2*j/m))
            x2 = min(2**i*a, abs(2**i*a/np.tan(np.pi*2*j/m)))*np.sign(np.cos(np.pi*2*j/m))
            y2 = min(2**i*a, abs(2**i*a*np.tan(np.pi*2*j/m)))*np.sign(np.sin(np.pi*2*j/m))
            x3 = min(2**i*a, abs(2**i*a/np.tan(np.pi*2*(j+1)/m)))*np.sign(np.cos(np.pi*2*(j+1)/m))
            y3 = min(2**i*a, abs(2**i*a*np.tan(np.pi*2*(j+1)/m)))*np.sign(np.sin(np.pi*2*(j+1)/m))
            x4 = min(2**(i-1)*a, abs(2**(i-1)*a/np.tan(np.pi*2*(j+1)/m)))*np.sign(np.cos(np.pi*2*(j+1)/m))
            y4 = min(2**(i-1)*a, abs(2**(i-1)*a*np.tan(np.pi*2*(j+1)/m)))*np.sign(np.sin(np.pi*2*(j+1)/m))
        wedge = QtGui.QPolygonF([QtCore.QPointF(x1 + self._tiles_size/2,y1 + self._tiles_size/2),\
            QtCore.QPointF(x2 + self._tiles_size/2,y2 + self._tiles_size/2),\
            QtCore.QPointF(x3 + self._tiles_size/2,y3 + self._tiles_size/2),\
            QtCore.QPointF(x4 + self._tiles_size/2,y4 + self._tiles_size/2)])
        wedge_object = self.my_scene.addPolygon(i,j,wedge,QtGui.QPen(QtCore.Qt.black,2))
        wedge_object.MOUSE_EVENT.connect(self.wedge_event_manager)
        if not available:
            wedge_object.setStatus('unavailable')
        self.wedges[(i,j)] = wedge_object

    def wedge_event_manager(self,i,j,event):
        if self.cursor_selection == 'cell':
            if event == 'enter':
                self.wedges[(i,j)].setStatus('hover')
                self.WEDGE_ENTER.emit(i,j)
            elif event == 'leave':
                self.wedges[(i,j)].setStatus('leave')
            elif event == 'press':
                if self.click_function == 'show':
                    self.WEDGE_REQUESTED.emit(i,j,True)
                elif self.click_function == 'select':
                    chosen = self.wedges[(i,j)].setStatus('chosen')
                    if chosen:
                        self.chosen_wedge_indices.add((i,j))
                    else:
                        self.chosen_wedge_indices.remove((i,j))
                    self.WEDGE_CHOSEN.emit(True if self.chosen_wedge_indices else False)
        elif self.cursor_selection == 'level':
            m = 1 if i == 0 else self.nba * 2**(i//2)
            if event == 'enter':
                for j in range(m):
                    self.wedges[(i,j)].setStatus('hover')
                self.WEDGE_ENTER.emit(i,j)
            elif event == 'leave':
                for j in range(m):
                    self.wedges[(i,j)].setStatus('leave')
            elif event == 'press':
                if self.click_function == 'show':
                    for j in range(m):
                        self.WEDGE_REQUESTED.emit(i,j,True)
                elif self.click_function == 'select':
                    for j in range(m):
                        chosen = self.wedges[(i,j)].setStatus('chosen')
                        if chosen:
                            self.chosen_wedge_indices.add((i,j))
                        else:
                            self.chosen_wedge_indices.remove((i,j))
                    self.WEDGE_CHOSEN.emit(True if self.chosen_wedge_indices else False)

class my_scene(QtWidgets.QGraphicsScene):
    def __init__(self,parent=None):
        super(my_scene,self).__init__(parent)

    def addPolygon(self, i,j, polygon, pen):
        super(my_scene,self).addPolygon(polygon,pen)
        wedge_object = my_wedge(i,j,polygon)
        self.addItem(wedge_object)
        return wedge_object

class my_wedge(QtWidgets.QGraphicsObject, QtWidgets.QGraphicsPolygonItem):

    MOUSE_EVENT = QtCore.pyqtSignal(int, int, str)

    def __init__(self,i,j,polygon,parent=None):
        super(my_wedge,self).__init__()
        self.item = QtWidgets.QGraphicsPolygonItem(polygon,parent)
        self.i, self.j = i,j
        self.setAcceptHoverEvents(True)
        self._status_chosen = False
        self._status_edited = False
        self._available = True

    def shape(self):
        return self.item.shape()

    def boundingRect(self):
        return self.item.boundingRect()

    def paint(self,painter,option,widget):
        QtWidgets.QGraphicsPolygonItem.paint(self.item,painter,option,widget)

    def hoverEnterEvent(self,event):
        if self._available:
            self.MOUSE_EVENT.emit(self.i, self.j,'enter')

    def hoverLeaveEvent(self,event):
        if self._available:
            self.MOUSE_EVENT.emit(self.i, self.j,'leave')

    def mousePressEvent(self,event):
        if self._available:
            self.MOUSE_EVENT.emit(self.i, self.j,'press')

    def setStatus(self,status):
        if status == 'hover' and not self._status_chosen and not self._status_edited:
            self.item.setBrush(QtGui.QBrush(QtGui.QColor('lightGray'),QtCore.Qt.SolidPattern))
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
        elif status == 'hover' and self._status_chosen and not self._status_edited:
            self.item.setBrush(QtGui.QBrush(QtGui.QColor('darkGreen'),QtCore.Qt.SolidPattern))
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
        elif status == 'hover' and not self._status_chosen and self._status_edited:
            self.item.setBrush(QtGui.QBrush(QtGui.QColor('darkRed'),QtCore.Qt.SolidPattern))
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
        elif status == 'chosen' and self._status_chosen == False:
            self.item.setBrush(QtGui.QBrush(QtGui.QColor('green'),QtCore.Qt.SolidPattern))
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
            self._status_chosen = True
            return self._status_chosen
        elif status == 'chosen' and self._status_chosen == True:
            self.item.setBrush(QtGui.QBrush())
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
            self._status_chosen = False
            return self._status_chosen
        elif status == 'edited':
            self.item.setBrush(QtGui.QBrush(QtGui.QColor('red'),QtCore.Qt.SolidPattern))
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
            self._status_edited = True
        elif status == 'relase':
            self._status_chosen = False
            self.item.setBrush(QtGui.QBrush())
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
        elif status == 'leave' and not self._status_chosen and not self._status_edited:
            self.item.setBrush(QtGui.QBrush())
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
        elif status == 'leave' and self._status_chosen and not self._status_edited:
            self.item.setBrush(QtGui.QBrush(QtGui.QColor('green'),QtCore.Qt.SolidPattern))
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
        elif status == 'leave' and not self._status_chosen and self._status_edited:
            self.item.setBrush(QtGui.QBrush(QtGui.QColor('red'),QtCore.Qt.SolidPattern))
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
        elif status == 'unavailable':
            self.item.setBrush(QtGui.QBrush(QtGui.QColor('lightGray'),QtCore.Qt.BDiagPattern))
            self.item.update(self.item.boundingRect())
            self.update(self.boundingRect())
            self._available = False