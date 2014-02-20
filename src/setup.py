"""

Copyright (C) 2008-2014 Wolfgang Rohdewald <wolfgang@rohdewald.de>

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
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.



This is to be executed on windows.
The directory 'share' must already be filled.
That can be done with winprep.py which should run
on linux in the src directory with kajongg fully installed.

Usage: see ../README.windows
"""

# ==== adapt this part =====
FULLAUTHOR = "Wolfgang Rohdewald <wolfgang@rohdewald.de>"
LICENSE = 'GNU General Public License v2'
URL = "http://www.kde.org/applications/games/kajongg/"
VERSION = "4.13.0"
# ==========================

import os, sys, re
from shutil import rmtree

from cx_Freeze import setup, Executable

(AUTHOR, EMAIL) = re.match(r'^(.*?)\s*<(.*)>$', FULLAUTHOR).groups()

# pylint: disable=invalid-name

if os.path.exists('build'):
    rmtree('build')

includes = ["zope.interface", "twisted.internet", "twisted.internet.protocol", "pkg_resources"]
packages = []
namespace_packages = ["zope"]
include_files = ('share',)

excludes = ['tcl', 'tk', 'ttk', 'tkinter', 'Tkconstants', 'Tkinter']
# strangely, excluding modules does not get rid of warnings about missing modules

build_exe_options = {"packages": packages, "excludes": excludes, "includes": includes,
    "include_files": include_files, 'icon':'kajongg.ico',
    "namespace_packages": namespace_packages, "append_script_to_exe":True, 'silent':False}

kajExe = Executable('kajongg.py', icon='kajongg.ico', base='Win32GUI',
    shortcutName='Kajongg', shortcutDir='ProgramMenuFolder')
kajServer = Executable('kajonggserver.py', icon='kajongg.ico')
executables = [kajExe, kajServer]

setup(
    name='kajongg',
    version=VERSION,
    description='The classical game of Mah Jongg',
    long_description="This is the classical Mah Jongg for four players. "
            "If you are looking for the Mah Jongg solitaire please use the "
            "application kmahjongg.",
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    download_url='http://www.kde-apps.org/content/download.php?content=103206&id=1',
    options={"build_exe": build_exe_options},
    executables=executables,
    license=LICENSE)
