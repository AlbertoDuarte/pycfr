from itertools import combinations
from operator import mul, __or__, __and__, __xor__
from card import Card

def trucoBoardEvaluator(board, players = 4):
    # Only works for 4 players
    def cardEval(card):
        values = {"Js": 1 , "Jh": 1 , "Jd": 1 , "Jc": 1,
                  "Qs": 2 , "Qh": 2 , "Qd": 2 , "Qc": 2,
                  "Ks": 3 , "Kh": 3 , "Kd": 3 , "Kc": 3,
                  "As": 8 , "Ah": 4 , "Ad": 4 , "Ac": 4,
                  "2s": 5 , "2h": 5 , "2d": 5 , "2c": 5,
                  "3s": 6 , "3h": 6 , "3d": 6 , "3c": 6,
                  "7d": 7 , "h7": 9 , "4c": 10
                  }

        return values[repr(card)]

    if len(board) % 4 != 0:
        raise Exception("Error in board size on evaluation! Board has {} cards, which is not divisible by the number of players ".format(len(board)))

    board_size = len(board)
    rounds = int(board_size/players)
    score = [0 for _ in range(players)]
    #print(score)
    for i in range(0, rounds):

        highest_card = -1
        winner = -1
        draw = False
        for player in range(0, 4):

            card = board[i*players + player]
            card_value = cardEval(card)
            if card_value > highest_card:
                highest_card = card_value
                winner = player
                draw = False
            elif card_value == highest_card:
                draw = True

        if not draw:
            score[player] += 1
            score[(player+2) % players] += 1
        else:
            for i in range(len(score)):
                score[i] += 2
        print(score)

    return score
