# -*- coding: utf-8 -*-

"""
 (C) 2008,2009,2010 Wolfgang Rohdewald <wolfgang@rohdewald.de>

kajongg is free software you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

from PyQt4.QtCore import Qt, QString, QRectF, QPointF
from PyQt4.QtGui import QGraphicsRectItem, QGraphicsItem, QPixmap, QPainter
from PyQt4.QtGui import QColor, QPen, QBrush, QStyleOptionGraphicsItem
from PyQt4.QtSvg import QGraphicsSvgItem
from util import logException
from common import LIGHTSOURCES

def chiNext(element, offset):
    """the element name of the following value"""
    color, baseValue = element
    baseValue = int(baseValue)
    return '%s%d' % (color, baseValue+offset)

def offsetTiles(tileName, offsets):
    """returns two adjacent tiles placed at offsets"""
    chow2 = chiNext(tileName, offsets[0])
    chow3 = chiNext(tileName, offsets[1])
    return [chow2, chow3]

class Tile(QGraphicsSvgItem):
    """a single tile on the board.
    the unit of xoffset is the width of the tile,
    the unit of yoffset is the height of the tile.
    """
    # pylint: disable=R0902
    # pylint - we need more than 10 attributes
    def __init__(self, element, xoffset = 0, yoffset = 0, level=0):
        QGraphicsSvgItem.__init__(self)
        if isinstance(element, Tile):
            xoffset, yoffset, level = element.xoffset, element.yoffset, element.level
            element = element.element
        self.focusable = True
        self.__board = None
        self.element = element
        self.__selected = False
        self.level = level
        self.xoffset = xoffset
        self.yoffset = yoffset
        self.face = None
        self.__pixmap = None
        self.darkener = None

    def keyPressEvent(self, event):
        """redirect to the board"""
        assert self == self.board.focusTile
        return self.board.keyPressEvent(event)

    def boundingRect(self):
        """define the part of the tile we want to see"""
        if not self.showShadows and self.tileset:
            return QRectF(QPointF(), self.tileset.faceSize)
        return QGraphicsSvgItem.boundingRect(self)

    def paintAll(self, painter):
        """paint full tile with shadows"""
        option = QStyleOptionGraphicsItem()
        self.paint(painter, option)
        for item in [self.darkener, self.face]:
            if item and item.isVisibleTo(self):
                painter.save()
                painter.translate(item.pos())
                item.paint(painter, option)
                painter.restore()

    def setFocus(self, reason=Qt.OtherFocusReason):
        """any tile that gets focus should also be focusItem for the scene"""
        assert self.board
        # TODO: why is this always called twice?
        QGraphicsSvgItem.setFocus(self, reason)
        self.scene().setFocusItem(self)

    @apply
    def focusable(): # pylint: disable=E0202
        """hide code"""
        def fget(self):
            return bool(self.flags() & QGraphicsItem.ItemIsFocusable)
        def fset(self, focusable):
            self.setFlag(QGraphicsItem.ItemIsFocusable, focusable)
        return property(**locals())

    @apply
    def board(): # pylint: disable=E0202
        """get/assign the tile to a board and define it according to the board parameters.
        This always recomputes the tile position in the board even if we assign to the
        same board - class Board depends on this"""
        def fget(self):
            # pylint: disable=W0212
            return self.__board
        return property(**locals())

    def facePos(self):
        """returns the face position relative to the tile"""
        return self.board.tileFacePos()

    def recompute(self):
        """recomputes position and visuals of the tile"""
        if self.__board is None:
            return
        if self.tileset:
            self.setSharedRenderer(self.tileset.renderer())
        if self.dark: # we need to regenerate the darkener
            self.dark = False
            self.dark = True
        self.setTileId()
        self.__board.placeTile(self)

        if self.element and self.element != 'Xy':
            if not self.face:
                self.face = QGraphicsSvgItem()
                self.face.setParentItem(self)
                self.face.setElementId(self.tileset.svgName[self.element.lower()])
                self.face.setZValue(1) # above the darkener
            # if we have a left or a top shadow, move face
            # by shadow width
            facePos = self.facePos()
            self.face.setPos(facePos.x(), facePos.y())
            self.face.setSharedRenderer(self.tileset.renderer())
        elif self.face:
            self.face.setParentItem(None)
            self.face = None

    @apply
    def dark(): # pylint: disable=E0202
        """darken the tile. Used for concealed tiles and dead wall"""
        def fget(self):
            return self.darkener is not None
        def fset(self, dark):
            if dark:
                if self.darkener is None:
                    self.darkener = QGraphicsRectItem()
                    self.darkener.setParentItem(self)
                    self.darkener.setRect(QRectF(self.facePos(), self.tileset.faceSize))
                    self.darkener.setPen(QPen(Qt.NoPen))
                    color = QColor('black')
                    color.setAlpha(self.tileset.darkenerAlpha)
                    self.darkener.setBrush(QBrush(color))
            else:
                if self.darkener is not None:
                    self.darkener.hide()
                    self.darkener = None
        return property(**locals())

    def setBoard(self, board, xoffset=None, yoffset=None, level=None):
        """change Position of tile in board"""
        if xoffset is None:
            xoffset = self.xoffset
        if yoffset is None:
            yoffset = self.yoffset
        if level is None:
            level = self.level
        if (self.__board, self.level, self.xoffset, self.yoffset) != (board, level, xoffset, yoffset):
            if self.__board:
                self.__board.tiles.remove(self)
            self.__board = board
            board.tiles.append(self)
            self.level = level
            self.xoffset = xoffset
            self.yoffset = yoffset
            self.recompute()
            if self.board:
                self.board.setDrawingOrder()

    def setTileId(self):
        """sets the SVG element id of the tile"""
        if not self.showShadows:
            tileName = QString("TILE_2")
        else:
            lightSourceIndex = LIGHTSOURCES.index(self.board.rotatedLightSource())
            tileName = QString("TILE_%1").arg(lightSourceIndex%4+1)
        if self.selected:
            tileName += '_SEL'
        self.setElementId(tileName)

    @property
    def tileset(self):
        """the active tileset"""
        return self.board.tileset if self.board else None

    @property
    def showShadows(self):
        """do we need to show shadows?"""
        return self.board.showShadows if self.board else False

    def sizeStr(self):
        """printable string with tile size"""
        size = self.sceneBoundingRect()
        if size:
            return '%d.%d %dx%d' % (size.left(), size.top(), size.width(), size.height())
        else:
            return 'No Size'

    def lower(self):
        """return element.lower"""
        return self.element.lower()

    def upper(self):
        """return hidden element name"""
        if self.isBonus():
            return self.element
        return self.element.capitalize()

    def __str__(self):
        """printable string with tile"""
        level = ' level=%d' % self.level if self.level else ''
        scale = ' scale=%.2f' % self.scale()if self.scale() != 1 else ''
        return '%s(%s) %d: x/y=%.1f(%.1f)/%.1f(%.1f) rot%d %s %s' % (self.element,
            self.board.name() if self.board else 'None', id(self) % 10000, self.xoffset, self.x(), self.yoffset,
            self.y(), self.rotation(), scale, level)

    @apply
    def selected():
        """selected tiles are drawn differently"""
        def fget(self):
            # pylint: disable=W0212
            return self.__selected
        def fset(self, selected):
            # pylint: disable=W0212
            if self.__selected != selected:
                self.__selected = selected
                self.setTileId()
        return property(**locals())

    def hide(self):
        """hide the tile and its focus rect"""
        if self.board and self == self.board.focusTile:
            # pylint: disable=W0612
            # pylint - I have no idea why it warns here
            self.board.focusTile = None
        QGraphicsSvgItem.hide(self)

    def clickableRect(self):
        """returns a rect for the range where a click is allowed (excludes border and shadow).
        Value in item coordinates"""
        return QRectF(self.facePos(), self.tileset.faceSize)

    def isFlower(self):
        """is this a flower tile?"""
        return self.element[0] == 'f'

    def isSeason(self):
        """is this a season tile?"""
        return self.element[0] == 'y'

    def isBonus(self):
        """is this a bonus tile? (flower,season)"""
        return self.isFlower() or self.isSeason()

    def isHonor(self):
        """is this a wind or dragon?"""
        return self.element[0] in 'wWdD'

    def pixmap(self, pmapSize=None, withBorders=False):
        """returns a pixmap with default size as given in SVG and optional borders/shadows"""
        if withBorders:
            wantSize = self.tileset.tileSize
        else:
            wantSize = self.tileset.faceSize
        if not pmapSize:
            pmapSize = wantSize
        if self.__pixmap is None or self.__pixmap.size() != pmapSize:
            self.__pixmap = QPixmap(pmapSize)
            self.__pixmap.fill(Qt.transparent)
            painter = QPainter(self.__pixmap)
            if not painter.isActive():
                logException('painter is not active')
            try:
                xScale = pmapSize.width() / wantSize.width()
                yScale = pmapSize.height() / wantSize.height()
            except ZeroDivisionError:
                xScale = 1
                yScale = 1
            painter.scale(xScale, yScale)
            if not withBorders:
                painter.translate(-self.facePos())
            QGraphicsSvgItem.paint(self, painter, QStyleOptionGraphicsItem())
            for child in self.childItems():
                if isinstance(child, QGraphicsSvgItem):
                    painter.save()
                    painter.translate(child.mapToParent(0.0, 0.0))
                    QGraphicsSvgItem.paint(child, painter, QStyleOptionGraphicsItem())
                    painter.restore()
        return self.__pixmap
