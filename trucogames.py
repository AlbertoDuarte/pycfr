from trucotrees import *

def truco_format():
    pass

def truco_eval():
    pass

def truco_rules():
    players = 4
    #deck =
    ante = None
    blind = None
    #rounds =
    return GameRules(players, deck, rounds, ante, blind, handeval=truco_eval, infoset_format=truco_format)

def truco_gametree():
    rules = truco_rules()
    tree = GameTree(rules)
    tree.build()
    return tree

def truco_publictree():
    rules = truco_rules()
    tree = PublicTree(rules)
    tree.build()
    return tree
