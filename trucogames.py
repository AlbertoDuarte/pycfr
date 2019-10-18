from trucotrees import *
from board_evaluator import trucoBoardEvaluator
from card import Card

def truco_format(player, holecards, board, bet_history):
    cards = holecards[0].RANK_TO_STRING[holecards[0].rank]
    if len(board) > 0:
        cards += board[0].RANK_TO_STRING[board[0].rank]
    return "{0}:{1}:".format(cards, bet_history)

# def truco_eval():
#     pass

def truco_rules():
    players = 4
    deck = [Card(11, 1), Card(11, 2), Card(11, 3), Card(11, 4),
            Card(12, 1), Card(12, 2), Card(12, 3), Card(12, 4),
            Card(13, 1), Card(13, 2), Card(13, 3), Card(13, 4),
            Card(14, 1), Card(14, 2), Card(14, 3), Card(14, 4),
            Card( 2, 1), Card( 2, 2), Card( 2, 3), Card( 2, 4),
            Card( 3, 1), Card( 3, 2), Card( 3, 3), Card( 3, 4),
            Card( 7, 3), Card( 7, 2), Card( 4, 4),
            ]
    ante = 0
    blind = None
    rounds = [RoundInfo(holecards=3,boardcards=0,betsize=1,maxbets=[4,4,4,4]),
              RoundInfo(holecards=0,boardcards=0,betsize=1,maxbets=[4,4,4,4]),
              RoundInfo(holecards=0,boardcards=0,betsize=1,maxbets=[4,4,4,4]) ]

    return GameRules(players, deck, rounds, ante, blind, handeval=trucoBoardEvaluator, infoset_format=truco_format)

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
