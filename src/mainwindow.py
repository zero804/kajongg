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

import sys, os

from log import logError, logDebug, m18n, m18nc
from common import Options, Internal, isAlive, Debug
import cgitb, tempfile, webbrowser, logging
from itertools import chain

class MyHook(cgitb.Hook):
    """override the standard cgitb hook: invoke the browser"""
    def __init__(self):
        self.tmpFileName = tempfile.mkstemp(suffix='.html', prefix='bt_', text=True)[1]
        cgitb.Hook.__init__(self, file=open(self.tmpFileName, 'w'))

    def handle(self, info=None):
        """handling the exception: show backtrace in browser"""
        cgitb.Hook.handle(self, info)
        webbrowser.open(self.tmpFileName)

sys.excepthook = MyHook()

NOTFOUND = []

try:
    from qt import Qt, QVariant, variantValue, QEvent, QMetaObject, PYQT_VERSION_STR, QTimer
    from qt import QWidget, QGridLayout, QAction
except ImportError as importError:
    NOTFOUND.append('Please install PyQt4 or PyQt5: %s' % importError)

try:
    from zope.interface import implements # pylint: disable=unused-import
except ImportError as importError:
    NOTFOUND.append('Package python-zope-interface missing: %s' % importError)

from kde import KIcon, KAction, KApplication, KToggleFullScreenAction, \
    KXmlGuiWindow, KStandardAction

try:
    from board import FittingView
    from playerlist import PlayerList
    from tileset import Tileset
    from background import Background
    from scoring import scoreGame
    from scoringdialog import ScoreTable, ExplainView
    from humanclient import HumanClient
    from rulesetselector import RulesetSelector
    from sound import Sound
    from animation import animate, afterCurrentAnimationDo, Animated
    from chat import ChatWindow
    from scene import PlayingScene, ScoringScene
    from configdialog import ConfigDialog
    from statesaver import StateSaver
    from util import checkMemory
    from twisted.internet.error import ReactorNotRunning

except ImportError as importError:
    NOTFOUND.append('Kajongg is not correctly installed: modules: %s' % importError)

if len(NOTFOUND):
    MSG = "\n".join(" * %s" % s for s in NOTFOUND)
    logError(MSG)
    os.popen("kdialog --sorry '%s'" % MSG)
    sys.exit(3)

def cleanExit(*dummyArgs):
    """close sqlite3 files before quitting"""
    if isAlive(Internal.mainWindow):
        if Debug.quit:
            logDebug('cleanExit calling mainWindow.close')
        Internal.mainWindow.close()
    else:
        # this must be very early or very late
        if Debug.quit:
            logDebug('cleanExit calling sys.exit(0)')
        #sys.exit(0)
        MainWindow.aboutToQuit()

from signal import signal, SIGABRT, SIGINT, SIGTERM
signal(SIGABRT, cleanExit)
signal(SIGINT, cleanExit)
signal(SIGTERM, cleanExit)
if os.name != 'nt':
    from signal import SIGHUP, SIGQUIT
    signal(SIGHUP, cleanExit)
    signal(SIGQUIT, cleanExit)

class MainWindow(KXmlGuiWindow):
    """the main window"""
    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        # see http://lists.kde.org/?l=kde-games-devel&m=120071267328984&w=2
        super(MainWindow, self).__init__()
        Internal.app.aboutToQuit.connect(self.aboutToQuit)
        self.exitConfirmed = None
        self.exitReady = None
        self.exitWaitTime = None
        Internal.mainWindow = self
        self._scene = None
        self.background = None
        self.playerWindow = None
        self.rulesetWindow = None
        self.confDialog = None
        if Options.gui:
            self.setupUi()
            KStandardAction.preferences(self.showSettings, self.actionCollection())
            self.applySettings()
            self.setupGUI()
            self.retranslateUi()
            for action in self.toolBar().actions():
                if 'onfigure' in action.text():
                    action.setPriority(QAction.LowPriority)
            if Options.host and not Options.demo:
                self.scene = PlayingScene(self)
                self.scene.applySettings()
                HumanClient()
            StateSaver(self)
            self.show()
        else:
            HumanClient()

    @property
    def scene(self):
        """a proxy"""
        return self._scene

    @scene.setter
    def scene(self, value):
        """if changing, updateGUI"""
        if not isAlive(self):
            return
        if self._scene == value:
            return
        if not value:
            self.actionChat.setChecked(False)
            self.actionExplain.setChecked(False)
            self.actionScoreTable.setChecked(False)
            self.actionExplain.setData(QVariant(ExplainView))
            self.actionScoreTable.setData(QVariant(ScoreTable))
        self._scene = value
        self.centralView.setScene(value)
        self.adjustView()
        self.updateGUI()
        self.actionChat.setEnabled(isinstance(value, PlayingScene))
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

    def kajonggAction(self, name, icon, slot=None, shortcut=None, actionData=None):
        """simplify defining actions"""
        res = KAction(self)
        if icon:
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
        res = self.kajonggAction(name, icon, shortcut=shortcut, actionData=actionData)
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
        self.windTileset = Tileset(Internal.Preferences.windTilesetName)
        self.adjustView()
        self.actionScoreGame = self.kajonggAction("scoreGame", "draw-freehand", self.scoringScene, Qt.Key_C)
        self.actionPlayGame = self.kajonggAction("play", "arrow-right", self.playingScene, Qt.Key_N)
        self.actionAbortGame = self.kajonggAction("abort", "dialog-close", self.abortAction, Qt.Key_W)
        self.actionAbortGame.setEnabled(False)
        self.actionQuit = self.kajonggAction("quit", "application-exit", self.close, Qt.Key_Q)
        self.actionPlayers = self.kajonggAction("players", "im-user", self.slotPlayers)
        self.actionRulesets = self.kajonggAction("rulesets", "games-kajongg-law", self.slotRulesets)
        self.actionChat = self._kajonggToggleAction("chat", "call-start",
            shortcut=Qt.Key_H, actionData=ChatWindow)
        self.actionChat.setEnabled(False)
        self.actionAngle = self.kajonggAction("angle", "object-rotate-left", self.changeAngle, Qt.Key_G)
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
        self.actionAutoPlay = self.kajonggAction("demoMode", "arrow-right-double", None, Qt.Key_D)
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
            self.applySettings()
            game.throwDices()
            self.updateGUI()

    def fullScreen(self, toggle):
        """toggle between full screen and normal view"""
        self.actionFullscreen.setFullScreen(self, toggle)

    def close(self, dummyResult=None):
        """wrap close() because we call it with a QTimer"""
        if isAlive(self):
            return KXmlGuiWindow.close(self)

    def closeEvent(self, event):
        KXmlGuiWindow.closeEvent(self, event)
        if event.isAccepted() and self.exitReady:
            QTimer.singleShot(5000, self.aboutToQuit)

    def queryClose(self):
        """queryClose, queryExit and aboutToQuit are no
        ideal match for the async Deferred approach.

        At app start, self.exitConfirmed and exitReady are None.

        queryClose will show a confirmation prompt if needed, but
        it will not wait for the answer. queryClose always returns True.

        Later, when the user confirms exit, self.exitConfirmed will be set.
        If the user cancels exit, self.exitConfirmed = False, otherwise
        self.close() is called. This time, no prompt will appear because the
        game has already been aborted.

        queryExit will return False if exitConfirmed or exitReady are not True.
        Otherwise, queryExit will set exitReady to False and asynchronously start
        shutdown. After the reactor stops running, exitReady is set to True,
        and self.close() is called. This time it should fall through everywhere,
        having queryClose() and queryExit() return True.

        and it will reset exitConfirmed to None.

        Or in other words: If queryClose or queryExit find something that they
        should do async like asking the user for confirmation or terminating
        the client/server connection, they start async operation and append
        a callback which will call self.close() when the async operation is
        done. This repeats until queryClose() and queryExit() find nothing
        more to do async. At that point queryExit says True
        and we really end the program.
        """

        # pylint: disable=too-many-branches
        def confirmed(result):
            """quit if the active game has been aborted"""
            self.exitConfirmed = bool(result)
            if Debug.quit:
                if self.exitConfirmed:
                    logDebug('mainWindow.queryClose confirmed')
                else:
                    logDebug('mainWindow.queryClose not confirmed')
            # start closing again. This time no question will appear, the game is already aborted
            if self.exitConfirmed:
                assert isAlive(self)
                self.close()
            else:
                self.exitConfirmed = None
        def cancelled(result):
            """just do nothing"""
            if Debug.quit:
                logDebug('mainWindow.queryClose.cancelled: {}'.format(result))
            self.exitConfirmed = None
        if self.exitConfirmed is False:
            # user is currently being asked
            return False
        if self.exitConfirmed is None:
            if self.scene:
                self.exitConfirmed = False
                self.abortAction().addCallbacks(confirmed, cancelled)
            else:
                self.exitConfirmed = True
                if Debug.quit:
                    logDebug('MainWindow.queryClose not asking, exitConfirmed=True')
        return True

    def queryExit(self):
        """see queryClose"""
        if self.exitReady:
            if Debug.quit:
                logDebug('MainWindow.queryExit returns True because exitReady is set')
            return True
        if self.exitConfirmed:
            # now we can get serious
            self.exitReady = False
            for widget in chain((x.tableList for x in HumanClient.humanClients), [self.confDialog,
                    self.rulesetWindow, self.playerWindow]):
                if isAlive(widget):
                    widget.hide()
            if self.exitWaitTime is None:
                self.exitWaitTime = 0
            if Internal.reactor and Internal.reactor.running:
                self.exitWaitTime += 10
                if self.exitWaitTime % 1000 == 0:
                    logDebug('waiting since %d seconds for reactor to stop' % (self.exitWaitTime // 1000))
                try:
                    if Debug.quit:
                        logDebug('now stopping reactor')
                    Internal.reactor.stop()
                    assert isAlive(self)
                    QTimer.singleShot(10, self.close)
                except ReactorNotRunning:
                    self.exitReady = True
                    if Debug.quit:
                        logDebug('MainWindow.queryExit returns True: It got exception ReactorNotRunning')
            else:
                self.exitReady = True
                if Debug.quit:
                    logDebug('MainWindow.queryExit returns True: Reactor is not running')
        return bool(self.exitReady)

    @staticmethod
    def aboutToQuit():
        """now all connections to servers are cleanly closed"""
        mainWindow = Internal.mainWindow
        Internal.mainWindow = None
        if mainWindow:
            if Debug.quit:
                logDebug('aboutToQuit starting')
            if mainWindow.exitWaitTime > 1000.0 or Debug.quit:
                logDebug('reactor stopped after %d ms' % (mainWindow.exitWaitTime ))
        else:
            if Debug.quit:
                logDebug('aboutToQuit: mainWindow is already None')
        StateSaver.saveAll()
        Internal.app.quit()
        try:
            # if we are killed while loading, Internal.db may not yet be defined
            if Internal.db:
                Internal.db.close()
        except NameError:
            pass
        checkMemory()
        logging.shutdown()

    def abortAction(self):
        """abort current game"""
        if Debug.quit:
            logDebug('mainWindow.abortAction invoked')
        return self.scene.abort()

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
        if not Internal.scaleScene or not isAlive(self):
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
        if self.backgroundName != Internal.Preferences.backgroundName:
            self.backgroundName = Internal.Preferences.backgroundName
        self.adjustView()
        Sound.enabled = Internal.Preferences.useSounds

    def showSettings(self):
        """show preferences dialog. If it already is visible, do nothing"""
        if ConfigDialog.showDialog("settings"):
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
        actionData = variantValue(action.data())
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
            if checked and Internal.db:
                self.playingScene()

    def updateGUI(self):
        """update some actions, all auxiliary windows and the statusbar"""
        if not isAlive(self):
            return
        self.setCaption('')
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
