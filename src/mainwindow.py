# -*- coding: utf-8 -*-

"""
Copyright (C) 2008-2012 Wolfgang Rohdewald <wolfgang@rohdewald.de>

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
"""

import sys
import os
from util import logError, m18n, m18nc, logDebug
from common import Options, Internal, Preferences, isAlive
import cgitb, tempfile, webbrowser

class MyHook(cgitb.Hook):
    """override the standard cgitb hook: invoke the browser"""
    def __init__(self):
        self.tmpFileName = tempfile.mkstemp(suffix='.html', prefix='bt_', text=True)[1]
        cgitb.Hook.__init__(self, file=open(self.tmpFileName, 'w'))

    def handle(self, info=None):
        """handling the exception: show backtrace in browser"""
        cgitb.Hook.handle(self, info)
        webbrowser.open(self.tmpFileName)

#sys.excepthook = MyHook()

NOTFOUND = []

try:
    from PyQt4.QtCore import Qt, QVariant, \
        QEvent, QMetaObject, PYQT_VERSION_STR, QString
    from PyQt4.QtGui import QWidget
    from PyQt4.QtGui import QGridLayout, QAction
    from PyQt4.QtGui import QSlider, QHBoxLayout, QLabel
    from PyQt4.QtGui import QVBoxLayout, QSpacerItem, QSizePolicy, QCheckBox
except ImportError as importError:
    NOTFOUND.append('Package python-qt4: PyQt4: %s' % importError)

try:
    from zope.interface import implements # pylint: disable=unused-import
except ImportError as importError:
    NOTFOUND.append('Package python-zope-interface missing: %s' % importError)

from kde import KIcon, KAction, KApplication, KToggleFullScreenAction, \
    KXmlGuiWindow, KConfigDialog, KStandardAction

try:
    from board import FittingView
    from playerlist import PlayerList
    from tileset import Tileset
    from background import Background
    from statesaver import StateSaver
    from scoring import scoreGame
    from scoringdialog import ScoreTable, ExplainView
    from humanclient import HumanClient
    from rulesetselector import RulesetSelector
    from tilesetselector import TilesetSelector
    from backgroundselector import BackgroundSelector
    from sound import Sound
    from animation import animate, afterCurrentAnimationDo, Animated
    from chat import ChatWindow
    from scene import PlayingScene, ScoringScene

except ImportError as importError:
    NOTFOUND.append('kajongg is not correctly installed: modules: %s' % importError)

if len(NOTFOUND):
    MSG = "\n".join(" * %s" % s for s in NOTFOUND)
    logError(MSG)
    os.popen("kdialog --sorry '%s'" % MSG)
    sys.exit(3)

class PlayConfigTab( QWidget):
    """Display Config tab"""
    def __init__(self, parent):
        super(PlayConfigTab, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        """layout the window"""
        self.setContentsMargins(0, 0, 0, 0)
        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        sliderLayout = QHBoxLayout()
        self.kcfg_showShadows = QCheckBox(m18n('Show tile shadows'), self)
        self.kcfg_showShadows.setObjectName('kcfg_showShadows')
        self.kcfg_rearrangeMelds = QCheckBox(m18n('Rearrange undisclosed tiles to melds'), self)
        self.kcfg_rearrangeMelds.setObjectName('kcfg_rearrangeMelds')
        self.kcfg_showOnlyPossibleActions = QCheckBox(m18n('Show only possible actions'))
        self.kcfg_showOnlyPossibleActions.setObjectName('kcfg_showOnlyPossibleActions')
        self.kcfg_propose = QCheckBox(m18n('Propose what to do'))
        self.kcfg_propose.setObjectName('kcfg_propose')
        self.kcfg_animationSpeed = QSlider(self)
        self.kcfg_animationSpeed.setObjectName('kcfg_animationSpeed')
        self.kcfg_animationSpeed.setOrientation(Qt.Horizontal)
        self.kcfg_animationSpeed.setSingleStep(1)
        lblSpeed = QLabel(m18n('Animation speed:'))
        lblSpeed.setBuddy(self.kcfg_animationSpeed)
        sliderLayout.addWidget(lblSpeed)
        sliderLayout.addWidget(self.kcfg_animationSpeed)
        self.kcfg_useSounds = QCheckBox(m18n('Use sounds if available'), self)
        self.kcfg_useSounds.setObjectName('kcfg_useSounds')
        self.kcfg_uploadVoice = QCheckBox(m18n('Let others hear my voice'), self)
        self.kcfg_uploadVoice.setObjectName('kcfg_uploadVoice')
        pol = QSizePolicy()
        pol.setHorizontalPolicy(QSizePolicy.Expanding)
        pol.setVerticalPolicy(QSizePolicy.Expanding)
        spacerItem = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vlayout.addWidget(self.kcfg_showShadows)
        vlayout.addWidget(self.kcfg_rearrangeMelds)
        vlayout.addWidget(self.kcfg_showOnlyPossibleActions)
        vlayout.addWidget(self.kcfg_propose)
        vlayout.addWidget(self.kcfg_useSounds)
        vlayout.addWidget(self.kcfg_uploadVoice)
        vlayout.addLayout(sliderLayout)
        vlayout.addItem(spacerItem)
        self.setSizePolicy(pol)
        self.retranslateUi()

    def retranslateUi(self):
        """translate to current language"""
        pass

class ConfigDialog(KConfigDialog):
    """configuration dialog with several pages"""
    def __init__(self, parent, name):
        super(ConfigDialog, self).__init__(parent, QString(name), Preferences)
        self.pages = [
            self.addPage(PlayConfigTab(self),
                m18nc('kajongg','Play'), "arrow-right"),
            self.addPage(TilesetSelector(self),
                m18n("Tiles"), "games-config-tiles"),
            self.addPage(BackgroundSelector(self),
                m18n("Backgrounds"), "games-config-background")]
        StateSaver(self)

    def keyPressEvent(self, event):
        """The four tabs can be selected with CTRL-1 .. CTRL-4"""
        mod = event.modifiers()
        key = chr(event.key()%128)
        if Qt.ControlModifier | mod and key in '123456789'[:len(self.pages)]:
            self.setCurrentPage(self.pages[int(key)-1])
            return
        KConfigDialog.keyPressEvent(self, event)

class MainWindow(KXmlGuiWindow):
    """the main window"""
    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        # see http://lists.kde.org/?l=kde-games-devel&m=120071267328984&w=2
        super(MainWindow, self).__init__()
        Internal.mainWindow = self
        self._scene = None
        self.background = None
        self.playerWindow = None
        self.rulesetWindow = None
        self.confDialog = None
        self.setupUi()
        KStandardAction.preferences(self.showSettings, self.actionCollection())
        self.applySettings()
        self.setupGUI()
        self.retranslateUi()
        for action in self.toolBar().actions():
            if 'onfigure' in action.text():
                action.setPriority(QAction.LowPriority)
        if Options.host:
            self.scene = PlayingScene(self)
            self.scene.applySettings()
            self.scene.playGame()
        self.show()

    @property
    def scene(self):
        """a proxy"""
        return self._scene

    @scene.setter
    def scene(self, value):
        """if changing, updateGUI"""
        if self._scene == value:
            return
        if not value:
            self.actionExplain.setChecked(False)
            self.actionScoreTable.setChecked(False)
            self.actionExplain.setData(QVariant(ExplainView))
            self.actionScoreTable.setData(QVariant(ScoreTable))
            Internal.scene = value # is set by Scene.__init__
        self._scene = value
        self.centralView.setScene(value)
        self.adjustView()
        self.updateGUI()
        self.actionExplain.setEnabled(value is not None)
        self.actionScoreTable.setEnabled(value is not None)

    def sizeHint(self):
        """give the main window a sensible default size"""
        result = KXmlGuiWindow.sizeHint(self)
        result.setWidth(result.height() * 3 // 2) # we want space to the right for the buttons
        # the default is too small. Use at least 2/3 of screen height and 1/2 of screen width:
        available = KApplication.kApplication().desktop().availableGeometry()
        height = max(result.height(), available.height() * 2 // 3)
        width = max(result.width(), available.width() // 2)
        result.setHeight(height)
        result.setWidth(width)
        return result

    def showEvent(self, event):
        """force a resize which calculates the correct background image size"""
        self.centralView.resizeEvent(True)
        KXmlGuiWindow.showEvent(self, event)

    def _kajonggAction(self, name, icon, slot=None, shortcut=None, actionData=None):
        """simplify defining actions"""
        res = KAction(self)
        res.setIcon(KIcon(icon))
        if slot:
            res.triggered.connect(slot)
        self.actionCollection().addAction(name, res)
        if shortcut:
            res.setShortcut( Qt.CTRL + shortcut)
            res.setShortcutContext(Qt.ApplicationShortcut)
        if PYQT_VERSION_STR != '4.5.2' or actionData is not None:
            res.setData(QVariant(actionData))
        return res

    def _kajonggToggleAction(self, name, icon, shortcut=None, actionData=None):
        """a checkable action"""
        res = self._kajonggAction(name, icon, shortcut=shortcut, actionData=actionData)
        res.setCheckable(True)
        res.toggled.connect(self._toggleWidget)
        return res

    def setupUi(self):
        """create all other widgets
        we could make the scene view the central widget but I did
        not figure out how to correctly draw the background with
        QGraphicsView/QGraphicsScene.
        QGraphicsView.drawBackground always wants a pixmap
        for a huge rect like 4000x3000 where my screen only has
        1920x1200"""
        # pylint: disable=too-many-statements
        self.setObjectName("MainWindow")
        centralWidget = QWidget()
        self.centralView = FittingView()
        layout = QGridLayout(centralWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.centralView)
        self.setCentralWidget(centralWidget)
        self.centralView.setFocusPolicy(Qt.StrongFocus)
        self.background = None # just for pylint
        self.windTileset = Tileset(Preferences.windTilesetName)
        self.adjustView()
        self.actionScoreGame = self._kajonggAction("scoreGame", "draw-freehand", self.scoringScene, Qt.Key_C)
        self.actionPlayGame = self._kajonggAction("play", "arrow-right", self.playingScene, Qt.Key_N)
        self.actionAbortGame = self._kajonggAction("abort", "dialog-close", self.abortAction, Qt.Key_W)
        self.actionAbortGame.setEnabled(False)
        self.actionQuit = self._kajonggAction("quit", "application-exit", self.close, Qt.Key_Q)
        self.actionPlayers = self._kajonggAction("players", "im-user", self.slotPlayers)
        self.actionRulesets = self._kajonggAction("rulesets", "games-kajongg-law", self.slotRulesets)
        self.actionChat = self._kajonggToggleAction("chat", "call-start",
            shortcut=Qt.Key_H, actionData=ChatWindow)
        self.actionAngle = self._kajonggAction("angle", "object-rotate-left", self.changeAngle, Qt.Key_G)
        self.actionAngle.setEnabled(False)
        self.actionFullscreen = KToggleFullScreenAction(self.actionCollection())
        self.actionFullscreen.setShortcut(Qt.CTRL + Qt.Key_F)
        self.actionFullscreen.setShortcutContext(Qt.ApplicationShortcut)
        self.actionFullscreen.setWindow(self)
        self.actionCollection().addAction("fullscreen", self.actionFullscreen)
        self.actionFullscreen.toggled.connect(self.fullScreen)
        self.actionScoreTable = self._kajonggToggleAction("scoreTable", "format-list-ordered",
            Qt.Key_T, actionData=ScoreTable)
        self.actionScoreTable.setEnabled(False)
        self.actionExplain = self._kajonggToggleAction("explain", "applications-education",
            Qt.Key_E, actionData=ExplainView)
        self.actionExplain.setEnabled(False)
        self.actionAutoPlay = self._kajonggAction("demoMode", "arrow-right-double", None, Qt.Key_D)
        self.actionAutoPlay.setCheckable(True)
        self.actionAutoPlay.setEnabled(True)
        self.actionAutoPlay.toggled.connect(self._toggleDemoMode)
        self.actionAutoPlay.setChecked(Internal.autoPlay)
        QMetaObject.connectSlotsByName(self)

    def playingScene(self):
        """play a computer game: log into a server and show its tables"""
        self.scene = PlayingScene(self)
        HumanClient()

    def scoringScene(self):
        """start a scoring scene"""
        self.scene = ScoringScene(self)
        game = scoreGame()
        if game:
            self.scene.game = game
            self.scene.adjustView()
            game.throwDices()
            self.updateGUI()

    def fullScreen(self, toggle):
        """toggle between full screen and normal view"""
        self.actionFullscreen.setFullScreen(self, toggle)

    def abortAction(self):
        """abort current game"""
        def doNotQuit(dummy):
            """ignore failure to abort"""
        self.scene.abort().addErrback(doNotQuit)

    def retranslateUi(self):
        """retranslate"""
        self.actionScoreGame.setText(m18nc('@action:inmenu', "&Score Manual Game"))
        self.actionScoreGame.setIconText(m18nc('@action:intoolbar', 'Manual Game'))
        self.actionScoreGame.setHelpText(m18nc('kajongg @info:tooltip', '&Score a manual game.'))

        self.actionPlayGame.setText(m18nc('@action:intoolbar', "&Play"))
        self.actionPlayGame.setPriority(QAction.LowPriority)
        self.actionPlayGame.setHelpText(m18nc('kajongg @info:tooltip', 'Start a new game.'))

        self.actionAbortGame.setText(m18nc('@action:inmenu', "&Abort Game"))
        self.actionAbortGame.setPriority(QAction.LowPriority)
        self.actionAbortGame.setHelpText(m18nc('kajongg @info:tooltip', 'Abort the current game.'))

        self.actionQuit.setText(m18nc('@action:inmenu', "&Quit Kajongg"))
        self.actionQuit.setPriority(QAction.LowPriority)

        self.actionPlayers.setText(m18nc('@action:intoolbar', "&Players"))
        self.actionPlayers.setHelpText(m18nc('kajongg @info:tooltip', 'define your players.'))

        self.actionRulesets.setText(m18nc('@action:intoolbar', "&Rulesets"))
        self.actionRulesets.setHelpText(m18nc('kajongg @info:tooltip', 'customize rulesets.'))

        self.actionAngle.setText(m18nc('@action:inmenu', "&Change Visual Angle"))
        self.actionAngle.setIconText(m18nc('@action:intoolbar', "Angle"))
        self.actionAngle.setHelpText(m18nc('kajongg @info:tooltip', "Change the visual appearance of the tiles."))

        self.actionScoreTable.setText(m18nc('kajongg @action:inmenu', "&Score Table"))
        self.actionScoreTable.setIconText(m18nc('kajongg @action:intoolbar', "&Scores"))
        self.actionScoreTable.setHelpText(m18nc('kajongg @info:tooltip',
                "Show or hide the score table for the current game."))

        self.actionExplain.setText(m18nc('@action:inmenu', "&Explain Scores"))
        self.actionExplain.setIconText(m18nc('@action:intoolbar', "&Explain"))
        self.actionExplain.setHelpText(m18nc('kajongg @info:tooltip',
                'Explain the scoring for all players in the current game.'))

        self.actionAutoPlay.setText(m18nc('@action:inmenu', "&Demo Mode"))
        self.actionAutoPlay.setPriority(QAction.LowPriority)
        self.actionAutoPlay.setHelpText(m18nc('kajongg @info:tooltip',
                'Let the computer take over for you. Start a new local game if needed.'))

        self.actionChat.setText(m18n("C&hat"))
        self.actionChat.setHelpText(m18nc('kajongg @info:tooltip', 'Chat with the other players.'))

    def changeEvent(self, event):
        """when the applicationwide language changes, recreate GUI"""
        if event.type() == QEvent.LanguageChange:
            self.setupGUI()
            self.retranslateUi()

    def slotPlayers(self):
        """show the player list"""
        if not self.playerWindow:
            self.playerWindow = PlayerList(self)
        self.playerWindow.show()

    def slotRulesets(self):
        """show the player list"""
        if not self.rulesetWindow:
            self.rulesetWindow = RulesetSelector()
        self.rulesetWindow.show()

    def adjustView(self):
        """adjust the view such that exactly the wanted things are displayed
        without having to scroll"""
        if not Internal.scaleScene:
            return
        view, scene = self.centralView, self.scene
        if scene:
            scene.adjustView()
            oldRect = view.sceneRect()
            view.setSceneRect(scene.itemsBoundingRect())
            newRect = view.sceneRect()
            if oldRect != newRect:
                view.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    @property
    def backgroundName(self):
        """setting this also actually changes the background"""
        return self.background.desktopFileName if self.background else ''

    @backgroundName.setter
    def backgroundName(self, name):
        """setter for backgroundName"""
        self.background = Background(name)
        self.background.setPalette(self.centralWidget())
        self.centralWidget().setAutoFillBackground(True)

    def applySettings(self):
        """apply preferences"""
        animate() # drain the queue
        afterCurrentAnimationDo(self.__applySettings2)

    def __applySettings2(self, dummyResults):
        """now no animation is running"""
        with Animated(False):
            if self.scene:
                self.scene.applySettings()
        if self.backgroundName != Preferences.backgroundName:
            self.backgroundName = Preferences.backgroundName
        self.adjustView()
        Sound.enabled = Preferences.useSounds
        if self.scene:
            self.scene.focusRect.refresh() # TODO: scene.applySettings

    def showSettings(self):
        """show preferences dialog. If it already is visible, do nothing"""
        if KConfigDialog.showDialog("settings"):
            return
        # if an animation is running, Qt segfaults somewhere deep
        # in the SVG renderer rendering the wind tiles for the tile
        # preview
        afterCurrentAnimationDo(self.__showSettings2)

    def __showSettings2(self, dummyResult):
        """now that no animation is running, show settings dialog"""
        self.confDialog = ConfigDialog(self, "settings")
        self.confDialog.settingsChanged.connect(self.applySettings)
        self.confDialog.show()

    def _toggleWidget(self, checked):
        """user has toggled widget visibility with an action"""
        assert self.scene
        action = self.sender()
        actionData = action.data().toPyObject()
        if checked:
            if isinstance(actionData, type):
                clsName = actionData.__name__
                actionData = actionData(scene=self.scene)
                action.setData(QVariant(actionData))
                setattr(self.scene, clsName[0].lower() + clsName[1:], actionData)
            actionData.show()
            actionData.raise_()
        else:
            assert actionData
            actionData.hide()

    def _toggleDemoMode(self, checked):
        """switch on / off for autoPlay"""
        if self.scene:
            self.scene.toggleDemoMode(checked)
        else:
            Internal.autoPlay = checked
            if checked:
                self.playingScene()

    def updateGUI(self):
        """update some actions, all auxiliary windows and the statusbar"""
        self.setWindowTitle('Kajongg')
        for action in [self.actionScoreGame, self.actionPlayGame]:
            action.setEnabled(not bool(self.scene))
        self.actionAbortGame.setEnabled(bool(self.scene))
        scene = self.scene
        if isAlive(scene):
            scene.updateSceneGUI()

    def changeAngle(self):
        """change the lightSource"""
        if self.scene:
            with Animated(False):
                afterCurrentAnimationDo(self.scene.changeAngle)