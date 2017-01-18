# -*- coding: utf-8 -*-

"""
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

# pylint: disable=unused-import, wrong-import-order, wrong-import-position

import os
import shutil

from common import Internal, Options

from kdestub import *  # pylint: disable=wildcard-import, unused-wildcard-import

from qt import QStandardPaths

def appdataDir():
    """
    The per user directory with kajongg application information like the database.

    @return: The directory path.
    @rtype: C{str}.
    """
    serverDir = os.path.expanduser('~/.kajonggserver/')
    if Internal.isServer:
        # the server might or might not have KDE installed, so to be on
        # the safe side we use our own .kajonggserver directory
        # the following code moves an existing kajonggserver.db to .kajonggserver
        # but only if .kajonggserver does not yet exist
        kdehome = os.environ.get('KDEHOME', '~/.kde')
        oldPath = os.path.expanduser(
            kdehome +
            '/share/apps/kajongg/kajonggserver.db')
        if not os.path.exists(oldPath):
            oldPath = os.path.expanduser(
                '~/.kde' +'4/share/apps/kajongg/kajonggserver.db')
        if os.path.exists(oldPath) and not os.path.exists(serverDir):
            # upgrading an old kajonggserver installation
            os.makedirs(serverDir)
            shutil.move(oldPath, serverDir)
        if not os.path.exists(serverDir):
            try:
                os.makedirs(serverDir)
            except OSError:
                pass
        return serverDir
    else:
        if not os.path.exists(serverDir):
            # the client wants to place the socket in serverDir
            os.makedirs(serverDir)
        result = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        # this may end with kajongg.py or .pyw or whatever, so fix that:
        result = os.path.join(os.path.dirname(result), 'kajongg')
        if not os.path.exists(result):
            os.makedirs(result)
        return result


def cacheDir():
    """the cache directory for this user"""
    result = os.path.join(appdataDir(), '.cache')
    if not os.path.exists(result):
        os.makedirs(result)
    return result


def socketName():
    """client and server process use this socket to talk to each other"""
    serverDir = os.path.expanduser('~/.kajonggserver')
    if not os.path.exists(serverDir):
        appdataDir()
                   # allocate the directory and possibly move old databases
                   # there
    if Options.socket:
        return Options.socket
    else:
        return os.path.normpath('{}/socket{}'.format(serverDir, Internal.defaultPort))
