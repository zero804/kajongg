"""
Authors of original libkmahjongg in C++:
    Copyright (C) 1997 Mathias Mueller <in5y158@public.uni-hamburg.de>
    Copyright (C) 2006 Mauricio Piacentini <mauricio@tabuleiro.com>

this python code:
    Copyright (C) 2008-2016 Wolfgang Rohdewald <wolfgang@rohdewald.de>

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

import os

from qt import Qt, QPainter, QBrush, QPalette, QPixmapCache, QPixmap
from qt import QSvgRenderer, QStandardPaths
from kde import KGlobal, KConfig

from log import logWarning, logException, m18n

BACKGROUNDVERSIONFORMAT = 1


class BackgroundException(Exception):

    """will be thrown if the tileset cannot be loaded"""
    pass


def locatebackground(which):
    """locate the file with a background"""
    return QStandardPaths.locate(QStandardPaths.GenericDataLocation, 'kmahjongglib/backgrounds/' + which)


class Background:

    """represents a background"""
    catalogDefined = False

    @staticmethod
    def defineCatalog():
        """whatever this does"""
        if not Background.catalogDefined:
            KGlobal.locale().insertCatalog("libkmahjongglib")
            Background.catalogDefined = True

    @staticmethod
    def __directories():
        """where to look for backgrounds"""
        return QStandardPaths.locateAll(
            QStandardPaths.GenericDataLocation,
            'kmahjongglib/backgrounds',
            QStandardPaths.LocateDirectory)

    @staticmethod
    def backgroundsAvailable():
        """returns all available backgrounds"""
        Background.defineCatalog()
        backgroundDirectories = Background.__directories()
        backgrounds = list()
        for _ in backgroundDirectories:
            backgrounds.extend(x for x in os.listdir(_) if x.endswith('.desktop'))
        # now we have a list of full paths. Use the base name minus .desktop:
        # put the result into a set, avoiding duplicates
        backgrounds = list(set(x.rsplit('/')[-1].split('.')[0]
                               for x in backgrounds))
        # There may be a default desktop file pointing to the same svg as some other desktop file.
        # If so we want to suppress the default entry, or the user visible list would show the default name twice
        nonDefaultSvgNames = list(Background(x).graphicsPath for x in backgrounds if x != 'default')
        if 'default' in backgrounds and Background('default').graphicsPath in nonDefaultSvgNames:
            backgrounds.remove('default')
        return [Background(x) for x in backgrounds]

    def __init__(self, desktopFileName=None):
        if desktopFileName is None:
            desktopFileName = 'default'
        self.__svg = None
        self.__pmap = None
        self.graphicsPath = None
        QPixmapCache.setCacheLimit(20480)  # the chinese landscape needs much
        self.defineCatalog()
        self.desktopFileName = desktopFileName
        self.path = locatebackground(desktopFileName + '.desktop')
        if not self.path:
            self.path = locatebackground('default.desktop')
            if not self.path:
                directories = '\n\n' + '\n'.join(self.__directories())
                logException(BackgroundException(m18n(
                    'cannot find any background in the following directories, is libkmahjongg installed?')
                                                 + directories))
            else:
                logWarning(
                    m18n(
                        'cannot find background %1, using default',
                        desktopFileName))
                self.desktopFileName = 'default'
        config = KConfig(self.path)
        group = config.group("KMahjonggBackground")
        self.name = group.readEntry("Name") or m18n("unknown background")

        # Version control
        backgroundversion = group.readInteger("VersionFormat", default=0)
        # Format is increased when we have incompatible changes, meaning that
        # older clients are not able to use the remaining information safely
        if backgroundversion > BACKGROUNDVERSIONFORMAT:
            logException(BackgroundException('backgroundversion file / program: %d/%d' %
                                             (backgroundversion, BACKGROUNDVERSIONFORMAT)))

        self.tiled = group.readEntry('Tiled') == '1'
        if self.tiled:
            try:
                self.imageWidth = group.readInteger('Width')
                self.imageHeight = group.readInteger('Height')
            except Exception as exc:
                logException(exc) # TODO: simplify if we switch to twisted logger
                raise
        self.isPlain = bool(group.readEntry('Plain'))
        if not self.isPlain:
            graphName = group.readEntry("FileName")
            self.graphicsPath = locatebackground(graphName)
            if not self.graphicsPath:
                logException(BackgroundException(
                    'cannot find kmahjongglib/backgrounds/%s for %s' %
                    (graphName, self.desktopFileName)))

    def pixmap(self, size):
        """returns a background pixmap or None for isPlain"""
        self.__pmap = QBrush()
        if not self.isPlain:
            width = size.width()
            height = size.height()
            if self.tiled:
                width = self.imageWidth
                height = self.imageHeight
            cachekey = '{name}W{width}H{height}'.format(name=self.name, width=width, height=height)
            self.__pmap = QPixmapCache.find(cachekey)
            if not self.__pmap:
                renderer = QSvgRenderer(self.graphicsPath)
                if not renderer.isValid():
                    logException(BackgroundException(
                        m18n('file <filename>%1</filename> contains no valid SVG', self.graphicsPath)))
                self.__pmap = QPixmap(width, height)
                self.__pmap.fill(Qt.transparent)
                painter = QPainter(self.__pmap)
                renderer.render(painter)
                QPixmapCache.insert(cachekey, self.__pmap)
        return self.__pmap

    def brush(self, size):
        """background brush"""
        return QBrush(self.pixmap(size))

    def setPalette(self, onto):
        """sets a background palette for widget onto"""
        palette = QPalette()
        mybrush = self.brush(onto.size())
        palette.setBrush(QPalette.Window, mybrush)
        onto.setPalette(palette)
