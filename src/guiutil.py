# -*- coding: utf-8 -*-
"""
    Copyright (C) 2010-2014 Wolfgang Rohdewald <wolfgang@rohdewald.de>

    partially based on C++ code from:
    Copyright (C) 2006 Mauricio Piacentini <mauricio@tabuleiro.com>

    Libkmahjongg is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""

import os

from qt import uic, QVariant, variantValue
from qt import QComboBox, QTableView, QSizePolicy, QAbstractItemView

from kde import KStandardDirs, KIcon

from log import m18n

def loadUi(base):
    """load the ui file for class base, deriving the file name from the class name"""
    name = base.__class__.__name__.lower() + '.ui'
    if os.path.exists(name):
        directory = os.getcwd()
    else:
        directory = os.path.dirname(str(KStandardDirs.locate("appdata", name)))
    uic.loadUi(os.path.join(directory, name), base)

class MJTableView(QTableView):
    """a QTableView with app specific defaults"""
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        pol = QSizePolicy()
        pol.setHorizontalPolicy(QSizePolicy.Expanding)
        pol.setVerticalPolicy(QSizePolicy.Expanding)
        self.setSizePolicy(pol)
        self.verticalHeader().hide()

    def initView(self):
        """set some app specific defaults"""
        self.selectRow(0)
        self.resizeColumnsToContents()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

class ListComboBox(QComboBox):
    """easy to use with a python list. The elements must have an attribute 'name'."""
    def __init__(self, items=None, parent=None):
        QComboBox.__init__(self, parent)
        self.items = items

    @property
    def items(self):
        """combo box items"""
        return [variantValue(self.itemData(idx)) for idx in range(self.count())]

    @items.setter
    def items(self, items):
        """combo box items"""
        self.clear()
        if items:
            for item in items:
                self.addItem(m18n(item.name), QVariant(item))

    def findItem(self, search):
        """returns the index or -1 of not found """
        for idx, item in enumerate(self.items):
            if item == search:
                return idx
        return -1

    def names(self):
        """a list wiith all item names"""
        return list([x.name for x in self.items])

    @property
    def current(self):
        """current item"""
        return variantValue(self.itemData(self.currentIndex()))

    @current.setter
    def current(self, item):
        """current item"""
        newIdx = self.findItem(item)
        if newIdx < 0:
            raise Exception('%s not found in ListComboBox' % item.name)
        self.setCurrentIndex(newIdx)

class Painter(object):
    """a helper class for painting: saves/restores painter"""
    def __init__(self, painter):
        """painter is the painter to be saved/restored"""
        self.painter = painter

    def __enter__(self):
        self.painter.save()
        return self

    def __exit__(self, exc_type, exc_value, trback):
        """now check time passed"""
        self.painter.restore()

def decorateWindow(window, name=None):
    """standard Kajongg window title and icon"""
    if name:
        window.setWindowTitle(u'{} – {}'.format(name, m18n('Kajongg')))
    else:
        window.setWindowTitle(m18n('Kajongg'))
    window.setWindowIcon(KIcon('kajongg'))
