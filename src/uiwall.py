# -*- coding: utf-8 -*-

"""
Copyright (C) 2008-2014 Wolfgang Rohdewald <wolfgang@rohdewald.de>

Kajongg is free software you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""

from common import Internal, ZValues
from qt import QRectF, QPointF, QGraphicsSimpleTextItem, QFontMetrics

from board import PlayerWind, YellowText, Board, rotateCenter
from wall import Wall, KongBox
from tile import Tile
from uitile import UITile
from animation import animate, afterCurrentAnimationDo, Animated, \
    ParallelAnimationGroup

class UIWallSide(Board):
    """a Board representing a wall of tiles"""
    def __init__(self, tileset, boardRotation, length):
        Board.__init__(self, length, 1, tileset, boardRotation=boardRotation)
        self.length = length

    @property
    def name(self):
        """name for debug messages"""
        game = Internal.scene.game
        if not game:
            return 'NOGAME'
        for player in game.players:
            if player.front == self:
                return 'wall %s'% player.name

    def center(self):
        """returns the center point of the wall in relation to the faces of the upper level"""
        faceRect = self.tileFaceRect()
        result = faceRect.topLeft() + self.shiftZ(1) + \
            QPointF(self.length // 2 * faceRect.width(), faceRect.height()/2)
        result.setX(result.x() + faceRect.height()/2) # corner tile
        return result

    def hide(self):
        """hide all my parts"""
        self.windTile.hide()
        self.nameLabel.hide()
        Board.hide(self)

class UIKongBox(KongBox):
    """Kong box with UITiles"""
    def __init__(self):
        KongBox.__init__(self)

    def fill(self, tiles):
        """fill the box"""
        for uiTile in self._tiles:
            uiTile.cross = False
        KongBox.fill(self, tiles)
        for uiTile in self._tiles:
            uiTile.cross = True

    def pop(self, count):
        """get count tiles from kong box"""
        result = KongBox.pop(self, count)
        for uiTile in result:
            uiTile.cross = False
        return result

class UIWall(Wall):
    """represents the wall with four sides. self.wall[] indexes them counter clockwise, 0..3. 0 is bottom."""
    tileClass = UITile
    kongBoxClass = UIKongBox

    def __init__(self, game):
        """init and position the wall"""
        # we use only white dragons for building the wall. We could actually
        # use any tile because the face is never shown anyway.
        game.wall = self
        Wall.__init__(self, game)
        self.__square = Board(1, 1, Internal.scene.tileset)
        self.__square.setZValue(ZValues.marker)
        sideLength = len(self.tiles) // 8
        self.__sides = [UIWallSide(Internal.scene.tileset, boardRotation, sideLength) \
            for boardRotation in (0, 270, 180, 90)]
        for side in self.__sides:
            side.setParentItem(self.__square)
            side.lightSource = self.lightSource
            side.windTile = PlayerWind('E', Internal.scene.windTileset, parent=side)
            side.windTile.hide()
            side.nameLabel = QGraphicsSimpleTextItem('', side)
            side.message = YellowText(side)
            side.message.setZValue(ZValues.popup)
            side.message.setVisible(False)
            side.message.setPos(side.center())
        self.__sides[0].setPos(yWidth=sideLength)
        self.__sides[3].setPos(xHeight=1)
        self.__sides[2].setPos(xHeight=1, xWidth=sideLength, yHeight=1)
        self.__sides[1].setPos(xWidth=sideLength, yWidth=sideLength, yHeight=1)
        self.__findOptimalFontHeight()
        Internal.scene.addItem(self.__square)

    @staticmethod
    def name():
        """name for debug messages"""
        return 'wall'

    def __getitem__(self, index):
        """make Wall index-able"""
        return self.__sides[index]

    def __setitem__(self, index, value):
        """only for pylint, currently not used"""
        self.__sides[index] = value

    def __delitem__(self, index):
        """only for pylint, currently not used"""
        del self.__sides[index]

    def __len__(self):
        """only for pylint, currently not used"""
        return len(self.__sides)

    def hide(self):
        """hide all four walls and their decorators"""
        # may be called twice
        self.living = []
        self.kongBox.fill([])
        for side in self.__sides:
            side.hide()
        self.tiles = []
        if self.__square.scene():
            self.__square.scene().removeItem(self.__square)

    def __shuffleTiles(self):
        """shuffle tiles for next hand"""
        discardBoard = Internal.scene.discardBoard
        places = [(x, y) for x in range(-3, discardBoard.width+3) for y in range(-3, discardBoard.height+3)]
        places = self.game.randomGenerator.sample(places, len(self.tiles))
        for idx, uiTile in enumerate(self.tiles):
            uiTile.dark = True
            uiTile.setBoard(discardBoard, *places[idx])

    def build(self, shuffleFirst=False):
        """builds the wall without dividing"""
        # recycle used tiles
        for uiTile in self.tiles:
            uiTile.tile = Tile.unknown
            uiTile.dark = True
#        scene = Internal.scene
#        animateBuild = not scene.game.isScoringGame() and not self.game.isFirstHand()
        animateBuild = False
        with Animated(animateBuild):
            if shuffleFirst:
                self.__shuffleTiles()
            for uiTile in self.tiles:
                uiTile.focusable = False
            return animate().addCallback(self.__placeWallTiles)

    def __placeWallTiles(self, dummyResult=None):
        """place all wall tiles"""
        tileIter = iter(self.tiles)
        tilesPerSide = len(self.tiles) // 4
        for side in (self.__sides[0], self.__sides[3], self.__sides[2], self.__sides[1]):
            upper = True # upper tile is played first
            for position in range(tilesPerSide-1, -1, -1):
                uiTile = tileIter.next()
                uiTile.setBoard(side, position//2, 0, level=int(upper))
                upper = not upper
        self.__setDrawingOrder()
        return animate()

    @property
    def lightSource(self):
        """For possible values see LIGHTSOURCES"""
        return self.__square.lightSource

    @lightSource.setter
    def lightSource(self, lightSource):
        """setting this actually changes the visuals"""
        if self.lightSource != lightSource:
            assert ParallelAnimationGroup.current is None
            self.__square.lightSource = lightSource
            for side in self.__sides:
                side.lightSource = lightSource
            self.__setDrawingOrder()

    @property
    def tileset(self):
        """The tileset of this wall"""
        return self.__square.tileset

    @tileset.setter
    def tileset(self, value):
        """setting this actually changes the visuals."""
        if self.tileset != value:
            assert ParallelAnimationGroup.current is None
            self.__square.tileset = value
            self.__findOptimalFontHeight()
            for side in self.__sides:
                side.tileset = value
            self.__resizeHandBoards()

    def __findOptimalFontHeight(self):
        """for names on walls"""
        tileHeight = Internal.scene.tileset.faceSize.height()
        font = self.__sides[0].nameLabel.font()
        size = 80
        font.setPointSize(size)
        while QFontMetrics(font).ascent() > tileHeight:
            size -= 1
            font.setPointSize(size)
        for side in self.__sides:
            side.nameLabel.setFont(font)

    @property
    def showShadows(self):
        """The current value"""
        return self.__square.showShadows

    @showShadows.setter
    def showShadows(self, showShadows):
        """setting this actually changes the visuals."""
        if self.showShadows != showShadows:
            assert ParallelAnimationGroup.current is None
            self.__square.showShadows = showShadows
            for side in self.__sides:
                side.showShadows = showShadows
            self.__resizeHandBoards()

    def __resizeHandBoards(self, dummyResults=None):
        """we are really calling _setRect() too often. But at least it works"""
        for player in self.game.players:
            player.handBoard.computeRect()
        Internal.mainWindow.adjustView()

    def __setDrawingOrder(self, dummyResults=None):
        """set drawing order of the wall"""
        levels = {'NW': (2, 3, 1, 0), 'NE':(3, 1, 0, 2), 'SE':(1, 0, 2, 3), 'SW':(0, 2, 3, 1)}
        for idx, side in enumerate(self.__sides):
            side.level = (levels[side.lightSource][idx] + 1) * ZValues.boardLevelFactor

    def __moveDividedTile(self, uiTile, offset):
        """moves a uiTile from the divide hole to its new place"""
        board = uiTile.board
        newOffset = uiTile.xoffset + offset
        sideLength = len(self.tiles) // 8
        if newOffset >= sideLength:
            sideIdx = self.__sides.index(uiTile.board)
            board = self.__sides[(sideIdx+1) % 4]
        uiTile.setBoard(board, newOffset % sideLength, 0, level=2)
        uiTile.update()

    def _placeLooseTiles(self):
        """place the last 2 tiles on top of kong box"""
        assert len(self.kongBox) % 2 == 0
        afterCurrentAnimationDo(self.__placeLooseTiles2)

    def __placeLooseTiles2(self, dummyResult):
        """place the last 2 tiles on top of kong box, no animation is active"""
        placeCount = len(self.kongBox) // 2
        if placeCount >= 4:
            first = min(placeCount-1, 5)
            second = max(first-2, 1)
            self.__moveDividedTile(self.kongBox[-1], second)
            self.__moveDividedTile(self.kongBox[-2], first)

    def divide(self):
        """divides a wall, building a living and and a dead end"""
        with Animated(False):
            Wall.divide(self)
            for uiTile in self.tiles:
                # update graphics because tiles having been
                # in kongbox in a previous game
                # might not be there anymore. This gets rid
                # of the cross on them.
                uiTile.update()
            # move last two tiles onto the dead end:
            return animate().addCallback(self.__placeLooseTiles2)

    def decorate(self):
        """show player info on the wall"""
        for player in self.game.players:
            self.decoratePlayer(player)

    def decoratePlayer(self, player):
        """show player info on the wall"""
        side = player.front
        sideCenter = side.center()
        name = side.nameLabel
        name.setText(' - '.join([player.localName, unicode(player.explainHand().total())]))
        name.resetTransform()
        if side.rotation() == 180:
            rotateCenter(name, 180)
        nameRect = QRectF()
        nameRect.setSize(name.mapToParent(name.boundingRect()).boundingRect().size())
        name.setPos(sideCenter - nameRect.center())
        player.colorizeName()
        side.windTile.setWind(player.wind, self.game.roundsFinished)
        side.windTile.resetTransform()
        side.windTile.setPos(sideCenter.x()*1.63, sideCenter.y()-side.windTile.rect().height()/2.5)
        side.nameLabel.show()
        side.windTile.show()
