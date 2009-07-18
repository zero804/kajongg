#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Copyright (C) 2009 Wolfgang Rohdewald <wolfgang@rohdewald.de>

kmj is free software you can redistribute it and/or modify
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

# See the user manual for a description of how to define rulesets.
# Names and descriptions must be english and may only contain ascii chars.
# Because kdecore.i18n() only accepts 8bit characters, no unicode.
# The KDE translation teams will "automatically" translate name and
# description into many languages.

from inspect import isclass
from scoring import PredefinedRuleset, Rule
from util import m18nE, m18n


class ClassicalChinese(PredefinedRuleset):
    def addPenaltyRules(self):
        self.penaltyRules.append(Rule('False Naming of Discard, Claimed for Chow', r'.*\bm', points = -50))
        self.penaltyRules.append(Rule('False Naming of Discard, Claimed for Pung/Kong', r'.*\bm', points = -100))
        self.penaltyRules.append(Rule('False Naming of Discard, Claimed for Mah Jongg', r'.*\bm||Aabsolute payees=3', points = -300))
        self.penaltyRules.append(Rule('False Naming of Discard, Claimed for Mah Jongg and False Declaration of Mah Jongg', r'.*\bm||Aabsolute payers=2 payees=2', points = -300))
        self.penaltyRules.append(Rule('False Declaration of Mah Jongg by One Player', r'.*\bm||Aabsolute payees=3', points = -300))
        self.penaltyRules.append(Rule('False Declaration of Mah Jongg by Two Players', r'.*\bm||Aabsolute payers=2 payees=2', points = -300))
        self.penaltyRules.append(Rule('False Declaration of Mah Jongg by Three Players', r'.*\bm||Aabsolute payers=3', points = -300))
        self.manualRules.append(Rule('Dangerous Game', r'.*\bm||Apayforall'))

class ClassicalChinesePattern(ClassicalChinese):
    """classical chinese rules expressed by patterns, not complete"""

    name = m18nE('Classical Chinese with Patterns')

    def __init__(self):
        PredefinedRuleset.__init__(self, ClassicalChinesePattern.name)

    def initRuleset(self):
        self.description = m18n('Classical Chinese as defined by the Deutsche Mahj Jongg Liga (DMJL) e.V.' \
            ' This ruleset uses mostly patterns for the rule definitions.')

    def rules(self):
        """define the rules"""
        self.addPenaltyRules()
        self.intRules.append(Rule('minMJPoints', 0))
        self.intRules.append(Rule('limit', 500))
        self.mjRules.append(Rule('Mah Jongg', 'PMahJongg()', points=20))
        self.mjRules.append(Rule('Last Tile Completes Simple Pair', 'PLastTileCompletes(Simple(Pair))', points=2))
        self.mjRules.append(Rule('Last Tile Completes Pair of Terminals or Honours',
            'PLastTileCompletes(NoSimple(Pair))', points=4))
        self.mjRules.append(Rule('Last Tile is Only Possible Tile', 'PLastTileOnlyPossible()',  points=4))
        self.mjRules.append(Rule('Won with Last Tile Taken from Wall', 'PLastTileCompletes(Concealed)', points=2))

        self.handRules.append(Rule('Own Flower and Own Season',
                r'I.* f(.).* y\1 .*m\1', doubles=1))
        self.handRules.append(Rule('All Flowers', r'I.*(\bf[eswn]\s){4,4}',
                                                doubles=1))
        self.handRules.append(Rule('All Seasons', r'I.*(\by[eswn]\s){4,4}',
                                                doubles=1))
        self.handRules.append(Rule('Three Concealed Pongs',  'PConcealed(PungKong)*3  +  Rest', doubles=1))
        self.handRules.append(Rule('Little Three Dragons', 'PDragons(PungKong)*2 +  Dragons(Pair) +   Rest', doubles=1))
        self.handRules.append(Rule('Big Three Dragons', 'PDragons(PungKong)*3  +  Rest', doubles=2))
        self.handRules.append(Rule('Little Four Joys', 'PWinds(PungKong)*3 + Winds(Pair) +   Rest', doubles=1))
        self.handRules.append(Rule('Big Four Joys', 'PWinds(PungKong)*4  +  Rest', doubles=2))

        self.mjRules.append(Rule('Zero Point Hand', r'I.*/([dwsbc].00)* M', doubles=1))
        self.mjRules.append(Rule('No Chow', 'PNoChow(MahJongg)', doubles=1))
        self.mjRules.append(Rule('Only Concealed Melds', 'PConcealed(MahJongg)', doubles=1))
        self.mjRules.append(Rule('False Color Game',
                                        'PHonours() + Character + NoBamboo(NoStone)*3 ||'
                                        'PHonours() + Stone + NoBamboo(NoCharacter)*3 ||'
                                        'PHonours() + Bamboo + NoStone(NoCharacter)*3', doubles=1 ))
        self.mjRules.append(Rule('True Color Game', 'POneColor(NoHonours(MahJongg))', doubles=3))
        self.mjRules.append(Rule('Only Terminals and Honours', 'PNoSimple(MahJongg)', doubles=1))
        self.mjRules.append(Rule('Only Honours',  'PHonours(MahJongg)', doubles=2))
        self.manualRules.append(Rule('Last Tile Taken from Dead Wall', 'PMahJongg()',  doubles=1))
        self.manualRules.append(Rule('Last Tile is Last Tile of Wall', 'PMahJongg()', doubles=1))
        self.manualRules.append(Rule('Last Tile is Last Tile of Wall Discarded', 'PMahJongg()', doubles=1))
        self.manualRules.append(Rule('Robbing the Kong', 'PMahJongg()', doubles=1))
        self.manualRules.append(Rule('Mah Jongg with Call at Beginning', 'PMahJongg()', doubles=1))
        self.handRules.append(Rule('Long Hand', r'PLongHand()||Aabsolute'))
        # limit hands:
        self.manualRules.append(Rule('Blessing of Heaven', r'[dwsbcDWSBC].*Me', limits=1))
        self.manualRules.append(Rule('Blessing of Earth', r'[dwsbcDWSBC].*M[swn]', limits=1))
        self.mjRules.append(Rule('Concealed True Color Game',
                'PConcealed(ClaimedKongAsConcealed(OneColor(NoHonours(MahJongg))))', limits=1))
        self.mjRules.append(Rule('Hidden Treasure',
                'PConcealed(ClaimedKongAsConcealed(PungKong())*4+Pair())', limits=1))
        self.mjRules.append(Rule('All Honours', 'PHonours(MahJongg)', limits=1))
        self.mjRules.append(Rule('All Terminals', 'PTerminals(MahJongg)', limits=1))
        self.mjRules.append(Rule('Winding Snake',
                'POneColor(PungKong(1)+Chow(2)+Chow(5)+PungKong(9)+Pair(8)) ||'
                'POneColor(PungKong(1)+Chow(3)+Chow(6)+PungKong(9)+Pair(2)) ||'
                'POneColor(PungKong(1)+Chow(2)+Chow(6)+PungKong(9)+Pair(5))', limits=1))
        self.mjRules.append(Rule('Fourfold Plenty', 'PKong()*4 + Pair()', limits=1))
        self.mjRules.append(Rule('Three Great Scholars', 'PDragons(PungKong)*3 + Rest', limits=1))
        self.mjRules.append(Rule('Four Blessings Hovering Over the Door', 'PWinds(PungKong)*4 + Rest', limits=1))
        self.mjRules.append(Rule('All Greens', 'PAllGreen(MahJongg)', limits=1))
        self.mjRules.append(Rule('Nine Gates',
                'POneColor(Concealed(Pung(1)+Chow(2)+Chow(5)+Single(8)+Pung(9))+Exposed(Single))', limits=1))
        self.mjRules.append(Rule('Thirteen Orphans', "PBamboo(Single(1)+Single(9))+Character(Single(1)+Single(9))"
            "+Stone(Single(1)+Single(9))+Single('b')+Single('g')+Single('r')"
            "+Single('e')+Single('s')+Single('w')+Single('n')+Single(NoSimple)", limits=1))

        self.handRules.append(Rule('Flower 1', r'I.*\bfe ', points=4))
        self.handRules.append(Rule('Flower 2', r'I.*\bfs ', points=4))
        self.handRules.append(Rule('Flower 3', r'I.*\bfw ', points=4))
        self.handRules.append(Rule('Flower 4', r'I.*\bfn ', points=4))
        self.handRules.append(Rule('Season 1', r'I.*\bye ', points=4))
        self.handRules.append(Rule('Season 2', r'I.*\bys ', points=4))
        self.handRules.append(Rule('Season 3', r'I.*\byw ', points=4))
        self.handRules.append(Rule('Season 4', r'I.*\byn ', points=4))

        # doubling melds:
        self.meldRules.append(Rule('Pung/Kong of Dragons', 'PDragons(PungKong)', doubles=1))
        self.meldRules.append(Rule('Pung/Kong of Own Wind', 'POwnWind(PungKong)', doubles=1))
        self.meldRules.append(Rule('Pung/Kong of Round Wind', 'PRoundWind(PungKong)', doubles=1))

        # exposed melds:
        self.meldRules.append(Rule('Exposed Kong', 'PSimple(Exposed(Kong))', points=8))
        self.meldRules.append(Rule('Exposed Kong of Terminals', 'PTerminals(Exposed(Kong))', points=16))
        self.meldRules.append(Rule('Exposed Kong of Honours', 'PHonours(Exposed(Kong))', points=16))

        self.meldRules.append(Rule('Exposed Pung', 'PSimple(Exposed(Pung))', points=2))
        self.meldRules.append(Rule('Exposed Pung of Terminals', 'PTerminals(Exposed(Pung))', points=4))
        self.meldRules.append(Rule('Exposed Pung of Honours', 'PHonours(Exposed(Pung))', points=4))

        # concealed melds:
        self.meldRules.append(Rule('Concealed Kong', 'PSimple(Concealed(Kong))', points=16))
        self.meldRules.append(Rule('Concealed Kong of Terminals', 'PTerminals(Concealed(Kong))', points=32))
        self.meldRules.append(Rule('Concealed Kong of Honours', 'PHonours(Concealed(Kong))', points=32))

        self.meldRules.append(Rule('Concealed Pung', 'PSimple(Concealed(Pung))', points=4))
        self.meldRules.append(Rule('Concealed Pung of Terminals', 'PTerminals(Concealed(Pung))', points=8))
        self.meldRules.append(Rule('Concealed Pung of Honours', 'PHonours(Concealed(Pung))', points=8))

        self.meldRules.append(Rule('Pair of Own Wind', 'POwnWind(Pair)', points=2))
        self.meldRules.append(Rule('Pair of Round Wind', 'PRoundWind(Pair)', points=2))
        self.meldRules.append(Rule('Pair of Dragons', 'PDragons(Pair)', points=2))

class ClassicalChineseRegex(ClassicalChinese):
    """classical chinese rules expressed by regular expressions, not complete"""

    name = m18nE('Classical Chinese with Regular Expressions')

    def __init__(self):
        PredefinedRuleset.__init__(self,  ClassicalChineseRegex.name)

    def initRuleset(self):
        self.description = m18n('Classical Chinese as defined by the Deutsche Mahj Jongg Liga (DMJL) e.V.' \
            ' This ruleset uses mostly regular expressions for the rule definitions.')

    def rules(self):
        """define the rules"""
        self.addPenaltyRules()
        self.intRules.append(Rule('minMJPoints', 0))
        self.intRules.append(Rule('limit', 500))
        self.mjRules.append(Rule('Mah Jongg',   r'.*M', points=20))
        self.mjRules.append(Rule('Last Tile Completes Pair of 2..8', r'.*\bL(.[2-8])\1\1\b', points=2))
        self.mjRules.append(Rule('Last Tile Completes Pair of Terminals or Honours',
                r'.*\bL((.[19])|([dwDW].))\1\1\b', points=4))
        self.mjRules.append(Rule('Last Tile is Only Possible Tile', 'PLastTileOnlyPossible()',  points=4))
        self.mjRules.append(Rule('Won with Last Tile Taken from Wall', r'.*M.*\bL[A-Z]', points=2))

        self.handRules.append(Rule('Own Flower and Own Season',
                r'I.* f(.).* y\1 .*m\1', doubles=1))
        self.handRules.append(Rule('All Flowers', r'I.*(\bf[eswn]\s){4,4}',
                                                doubles=1))
        self.handRules.append(Rule('All Seasons', r'I.*(\by[eswn]\s){4,4}',
                                                doubles=1))
        self.handRules.append(Rule('Three Concealed Pongs', r'.*/.*(([DWSBC][34]..).*?){3,} [mM]',
                                                doubles=1))
        self.handRules.append(Rule('Little Three Dragons', r'I.*/d2..d[34]..d[34]..',
                                                doubles=1))
        self.handRules.append(Rule('Big Three Dragons', r'I.*/d[34]..d[34]..d[34]..',
                                                doubles=2))
        self.handRules.append(Rule('Little Four Joys', r'I.*/.*w2..(w[34]..){3,3}',
                                                 doubles=1))
        self.handRules.append(Rule('Big Four Joys', r'I.*/.*(w[34]..){4,4}',
                                                doubles=2))

        self.mjRules.append(Rule('Zero Point Hand', r'I.*/([dwsbc].00)* M',
                                                doubles=1))
        self.mjRules.append(Rule('No Chow', r'I.*/([dwsbc][^0]..)* M',
                                                doubles=1))
        self.mjRules.append(Rule('Only Concealed Melds', r'.*/([DWSBC]...)* M', doubles=1))
        self.mjRules.append(Rule('False Color Game', r'I.*/([dw]...){1,}(([sbc])...)(\3...)* M',
                                                doubles=1))
        self.mjRules.append(Rule('True Color Game',   r'I.*/(([sbc])...)(\2...)* M',
                                                doubles=3))
        self.mjRules.append(Rule('Only Terminals and Honours', r'I((([dw].)|(.[19])){1,4} )*[fy/].*M',
                                                doubles=1 ))
        self.mjRules.append(Rule('Only Honours', r'I.*/([dw]...)* M',
                                                doubles=2 ))
        self.manualRules.append(Rule('Last Tile Taken from Dead Wall', r'[dwsbcDWSBC].*M.*\bL[A-Z]', doubles=1))
        self.manualRules.append(Rule('Last Tile is Last Tile of Wall', r'[dwsbcDWSBC].*M.*\bL[A-Z]', doubles=1))
        self.manualRules.append(Rule('Last Tile is Last Tile of Wall Discarded', r'[dwsbcDWSBC].*M.*\bL[a-z]', doubles=1))
        self.manualRules.append(Rule('Robbing the Kong', r'[dwsbcDWSBC].*M.*\bL[A-Z]', doubles=1))
        self.manualRules.append(Rule('Mah Jongg with Call at Beginning', r'[dwsbcDWSBC].*M', doubles=1))

        self.handRules.append(Rule('Long Hand', r'PLongHand()||Aabsolute'))

        # limit hands:
        self.manualRules.append(Rule('Blessing of Heaven', r'[dwsbcDWSBC].*Me', limits=1))
        self.manualRules.append(Rule('Blessing of Earth', r'[dwsbcDWSBC].*M[swn]', limits=1))
        # concealed true color game ist falsch, da es nicht auf korrekte Aufteilung in Gruppen achtet
        self.mjRules.append(Rule('Concealed True Color Game',   r'(([sbc][1-9])*([SBC].){1,3} )*[fy/]', limits=1))
        self.mjRules.append(Rule('Hidden Treasure', 'PMJHiddenTreasure()', limits=1))
        self.mjRules.append(Rule('All Honours', r'.*/([DWdw]...)* M', limits=1))
        self.mjRules.append(Rule('All Terminals', r'((.[19]){1,4} )*[fy/]', limits=1))
        self.mjRules.append(Rule('Winding Snake',
                                           'POneColor(PungKong(1)+Chow(2)+Chow(5)+PungKong(9)+Pair(8)) ||'
                                           'POneColor(PungKong(1)+Chow(3)+Chow(6)+PungKong(9)+Pair(2)) ||'
                                           'POneColor(PungKong(1)+Chow(2)+Chow(6)+PungKong(9)+Pair(5))', limits=1))
        self.mjRules.append(Rule('Fourfold Plenty', r'.*/((....)*(.4..)(....)?){4,4}', limits=1))
        self.mjRules.append(Rule('Three Great Scholars', r'.*/[Dd][34]..[Dd][34]..[Dd][34]', limits=1))
        self.mjRules.append(Rule('Four Blessings Hovering Over the Door', r'.*/.*([Ww][34]..){4,4}', limits=1))
        self.mjRules.append(Rule('all Greens', r'( |[bB][23468]|[dD]g)*[fy/]', limits=1))
        self.mjRules.append(Rule('Nine Gates', r'(S1S1S1 S2S3S4 S5S6S7 S8 S9S9S9 s.|'
                'B1B1B1 B2B3B4 B5B6B7 B8 B9B9B9 b.|C1C1C1 C2C3C4 C5C6C7 C8 C9C9C9 c.)', limits=1))
        self.mjRules.append(Rule('Thirteen Orphans', \
            r'I(db ){1,2}(dg ){1,2}(dr ){1,2}(we ){1,2}(wn ){1,2}(ws ){1,2}(ww ){1,2}'
            '(s1 ){1,2}(s9 ){1,2}(b1 ){1,2}(b9 ){1,2}(c1 ){1,2}(c9 ){1,2}[fy/].*M', limits=1))

        self.handRules.append(Rule('Flower 1', r'I.*\bfe ', points=4))
        self.handRules.append(Rule('Flower 2', r'I.*\bfs ', points=4))
        self.handRules.append(Rule('Flower 3', r'I.*\bfw ', points=4))
        self.handRules.append(Rule('Flower 4', r'I.*\bfn ', points=4))
        self.handRules.append(Rule('Season 1', r'I.*\bye ', points=4))
        self.handRules.append(Rule('Season 2', r'I.*\bys ', points=4))
        self.handRules.append(Rule('Season 3', r'I.*\byw ', points=4))
        self.handRules.append(Rule('Season 4', r'I.*\byn ', points=4))

        # doubling melds:
        self.meldRules.append(Rule('Pung/Kong of Dragons', r'([dD][brg])\1\1', doubles=1))
        self.meldRules.append(Rule('Pung/Kong of Own Wind', r'(([wW])([eswn])){3,4}.*[mM]\3', doubles=1))
        self.meldRules.append(Rule('Pung/Kong of Round Wind', r'(([wW])([eswn])){3,4}.*[mM].\3', doubles=1))

        # exposed melds:
        self.meldRules.append(Rule('Exposed Kong', r'([sbc])([2-8])(\1\2\1\2.\2)\b', points=8))
        self.meldRules.append(Rule('Exposed Kong of Terminals', r'([sbc])([19])(\1\2\1\2.\2)\b', points=16))
        self.meldRules.append(Rule('Exposed Kong of Honours', r'([dw])([brgeswn])(\1\2\1\2.\2)\b', points=16))

        self.meldRules.append(Rule('Exposed Pung', r'([sbc][2-8])(\1\1)\b', points=2))
        self.meldRules.append(Rule('Exposed Pung of Terminals', r'([sbc][19])(\1\1)\b', points=4))
        self.meldRules.append(Rule('Exposed Pung of Honours', r'(d[brg]|w[eswn])(\1\1)\b', points=4))

        # concealed melds:
        self.meldRules.append(Rule('Concealed Kong', r'([sbc][2-8])([SBC][2-8])(\2)(\1)\b', points=16))
        self.meldRules.append(Rule('Concealed Kong of Terminals', r'([sbc][19])([SBC][19])(\2)(\1)\b', points=32))
        self.meldRules.append(Rule('Concealed Kong of Honours', r'(d[brg]|w[eswn])(D[brg]|W[eswn])(\2)(\1)\b',
                                                    points=32))

        self.meldRules.append(Rule('Concealed Pung', r'([SBC][2-8])(\1\1)\b', points=4))
        self.meldRules.append(Rule('Concealed Pung of Terminals', r'([SBC][19])(\1\1)\b', points=8))
        self.meldRules.append(Rule('Concealed Pung of Honours', r'(D[brg]|W[eswn])(\1\1)\b', points=8))

        self.meldRules.append(Rule('Pair of Own Wind', r'([wW])([eswn])(\1\2) [mM]\2', points=2))
        self.meldRules.append(Rule('Pair of Round Wind', r'([wW])([eswn])(\1\2) [mM].\2', points=2))
        self.meldRules.append(Rule('Pair of Dragons', r'([dD][brg])(\1)\b', points=2))

__predefClasses = []
__predefRulesets = []

def predefinedRulesetClasses():
    """returns all rulesets defined in this module"""
    global __predefClasses
    if not __predefClasses:
        thisModule = __import__(__name__)
        __predefClasses = []
        for attrName in globals():
            obj = getattr(thisModule, attrName)
            if isclass(obj) and PredefinedRuleset in obj.__mro__ and obj.name:
                cName = obj.__name__
                if cName not in ('PredefinedRuleset'):
                    __predefClasses.append(obj)
    return __predefClasses

def predefinedRulesets():
    """returns a list with all predefined rulesets"""
    global __predefRulesets
    if not __predefRulesets:
        __predefRulesets = list(x() for x in predefinedRulesetClasses())
    return __predefRulesets
