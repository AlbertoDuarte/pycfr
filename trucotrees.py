from itertools import combinations
from itertools import permutations
from itertools import product
from collections import Counter
from board_evaluator import trucoBoardEvaluator
from copy import deepcopy
from functools import partial

FOLD = 0
PLAY1 = 1
PLAY2 = 2
PLAY3 = 3
RAISE = 4 # RAISE EQUALS ASK TRUCO

def overlap(t1, t2):
    for x in t1:
        if x in t2:
            return True
    return False

def all_unique(hc):
    for i in range(len(hc)-1):
        for j in range(i+1,len(hc)):
            if overlap(hc[i], hc[j]):
                return False
    return True

def default_infoset_format(player, holecards, board, bet_history):
    return "{0}{1}:{2}:".format("".join([str(x) for x in holecards]), "".join([str(x) for x in board]), bet_history)

class GameRules(object):
    def __init__(self, players, deck, rounds, ante, blinds, handeval = trucoBoardEvaluator, infoset_format=default_infoset_format):
        assert(players >= 2)
        assert(ante >= 0)
        assert(rounds != None)
        assert(deck != None)
        assert(len(rounds) > 0)
        assert(len(deck) > 1)
        if blinds != None:
            if type(blinds) is int or type(blinds) is float:
                blinds = [blinds]
        for r in rounds:
            assert(len(r.maxbets) == players)
        self.players = players
        self.deck = deck
        self.roundinfo = rounds
        self.ante = ante
        self.blinds = blinds
        self.handeval = handeval
        self.infoset_format = infoset_format

class RoundInfo(object):
    def __init__(self, holecards, boardcards, betsize, maxbets):
        self.holecards = holecards
        self.boardcards = boardcards # Boardcards has cards which have been played
        self.betsize = betsize
        self.maxbets = maxbets

class GameTree(object):
    def __init__(self, rules):
        self.rules = deepcopy(rules)
        self.information_sets = {}
        self.root = None

    def build(self): # TODO: arrumar next player quando ha truco, verificar possibilidade de pedir truco, debug no valor do round
                     # arrumar node de acao e dar push nas cartas jogadas
        # Assume everyone is in
        players_in = [True] * self.rules.players
        # Collect antes
        committed = [self.rules.ante] * self.rules.players
        bets = [0] * self.rules.players
        # Collect blinds
        next_player = self.collect_blinds(committed, bets, 0)
        holes = [()] * self.rules.players
        board = ()
        last_team_that_raised = -1
        bet_history = ""
        self.root = self.build_rounds(None, players_in, committed, holes, board, self.rules.deck, bet_history, 0, bets, next_player, last_team_that_raised)

    def collect_blinds(self, committed, bets, next_player): # blinds == None in truco
        if self.rules.blinds != None:
            for blind in self.rules.blinds:
                committed[next_player] += blind
                bets[next_player] = int((committed[next_player] - self.rules.ante) / self.rules.roundinfo[0].betsize)
                next_player = (next_player + 1) % self.rules.players
        return next_player

    def deal_holecards(self, deck, holecards, players): # ok?
        a = combinations(deck, holecards)
        return filter(lambda x: all_unique(x), permutations(a, players))

    def build_rounds(self, root, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, bets = None, next_player = 0):
        # Verify if hand must end
        if self.end_hand(board, players_in):
            return self.showdown(root, players_in, committed, holes, board, deck, bet_history, bets)
        bet_history += "/"
        cur_round = self.rules.roundinfo[round_idx]
        while not players_in[next_player]:
            next_player = (next_player + 1) % self.rules.players
        if bets is None:
            bets = [0] * self.rules.players
        min_actions_this_round = players_in.count(True)
        actions_this_round = 0
        if cur_round.holecards:
            return self.build_holecards(root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets)
        if cur_round.boardcards:
            return self.build_boardcards(root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets)
        return self.build_bets(root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets)

    def get_next_player(self, cur_player, players_in):
        next_player = (cur_player + 1) % self.rules.players
        while not players_in[next_player]:
            next_player = (next_player + 1) % self.rules.players
        return next_player

    def end_hand(self, board, players_in):
        round = len(board)/len(players_in)
        score = self.rules.handeval(board)
        score_max = max(score[0], score[1])
        score_min = min(score[0], score[1])
        if round == 2 and ( (score_max == 2 and score_min == 0) or score_max == 3):
            return True
        if round == 3:
            return True

        return False

    def build_holecards(self, root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets):
        cur_round = self.rules.roundinfo[round_idx]
        hnode = HolecardChanceNode(root, committed, holes, board, self.rules.deck, "", cur_round.holecards)
        # Deal holecards
        all_hc = self.deal_holecards(deck, cur_round.holecards, players_in.count(True))
        # Create a child node for every possible distribution
        for cur_holes in all_hc:
            dealt_cards = ()
            cur_holes = list(cur_holes) # TODO: sort holecards
            cur_holes.sort()
            cur_idx = 0
            for i,hc in enumerate(holes):
                # Only deal cards to players who are still in
                if players_in[i]:
                    cur_holes[cur_idx] = hc + cur_holes[cur_idx]
                    cur_idx += 1
            for hc in cur_holes:
                dealt_cards += hc
            cur_deck = filter(lambda x: not (x in dealt_cards), deck)
            if cur_round.boardcards:
                self.build_boardcards(hnode, next_player, players_in, committed, cur_holes, board, cur_deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets)
            else:
                self.build_bets(hnode, next_player, players_in, committed, cur_holes, board, cur_deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets)
        return hnode

    # def build_boardcards(self, root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets):
    #     cur_round = self.rules.roundinfo[round_idx]
    #     bnode = BoardcardChanceNode(root, committed, holes, board, deck, bet_history, cur_round.boardcards)
    #     all_bc = combinations(deck, cur_round.boardcards)
    #     for bc in all_bc:
    #         cur_board = board + bc
    #         cur_deck = filter(lambda x: not (x in bc), deck)
    #         self.build_bets(bnode, next_player, players_in, committed, holes, cur_board, cur_deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets)
    #     return bnode

    def build_bets(self, root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round):
        # if everyone else folded, end the hand
        if players_in.count(True) == 2:
            self.showdown(root, players_in, committed, holes, board, deck, bet_history, bets_this_round)
            return
        # if everyone played a card, end round
        if len(board) == (round_idx+1) * 4:
            self.build_rounds(root, players_in, committed, holes, board, deck, bet_history, round_idx + 1)
            return
        cur_round = self.rules.roundinfo[round_idx]
        anode = ActionNode(root, committed, holes, board, deck, bet_history, next_player, self.rules.infoset_format)
        # add the node to the information set
        if not (anode.player_view in self.information_sets):
            self.information_sets[anode.player_view] = []
        self.information_sets[anode.player_view].append(anode)
        # get the next player to act
        if self.last_play_was_raise(bet_history):
            next_player = (next_player - 2) % 2
            self.add_fold_child(anode, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round)
            self.add_raise_child(anode, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round)

        else:
            next_player = self.get_next_player(next_player, players_in)
            # add a folding option
            self.add_fold_child(anode, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round)
            # add a calling/checking option
            self.add_call_child(anode, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round)
            # add play option
            self.add_play_child(anode, next_player, 0, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round)
            if len(holes[root.player]) >= 2:
                self.add_play_child(anode, next_player, 1, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round)
            if len(holes[root.player]) >= 3:
                self.add_play_child(anode, next_player, 2, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round)

            # add a raising option if bet < max bet and the player and his teammate hasnt raised last
            if cur_round.maxbets[anode.player] > max(bets_this_round) and last_team_that_raised != (next_player-1)%2: # TODO: change if
                self.add_raise_child(anode, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round)
        return anode

    def all_called_last_raisor_or_folded(self, players_in, bets):
        betlevel = max(bets)
        for i,v in enumerate(bets):
            if players_in[i] and bets[i] < betlevel:
                return False
        return True

    def last_play_was_raise(self, bet_history):
        # if bet_history[-1] == '/':
        #     raise ValueError("/ is invalid")
        if bet_history[-1] == 'r':
            return True

        return False

    def add_fold_child(self, root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round):
        players_in[root.player] = False
        players_in[(root.player+2)%2] = False
        bet_history += 'f'
        self.build_bets(root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round + 1, bets_this_round)
        root.fold_action = root.children[-1]
        players_in[root.player] = True
        players_in[(root.player+2)%2] = True

    def add_play_child(self, root, next_player, card_idx, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round):
        # play
        player_commit = committed[root.player]
        player_bets = bets_this_round[root.player]
        committed[root.player] = max(committed)

        bet_history += str(card_idx) # add which card was played

        # update hole and board
        new_holes = holes
        new_board = board
        card = new_holes[root.player][card_idx]
        del new_holes[root.player][card_idx]
        new_board.append(card)

        self.build_bets(root, next_player, players_in, committed, new_holes, new_board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round + 1, bets_this_round)
        root.call_action = root.children[-1]
        committed[root.player] = player_commit
        bets_this_round[root.player] = player_bets

    def add_raise_child(self, root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round, bets_this_round):
        cur_round = self.rules.roundinfo[round_idx]
        prev_betlevel = bets_this_round[root.player]
        prev_commit = committed[root.player]

        if not self.last_play_was_raise(bet_history):
            last_team_that_raised = root.player % 2

        # when a player raises (calls truco), they raise for his teammate too
        bets_this_round[root.player] += 1
        bets_this_round[(root.player+2)%2] = bets_this_round[root.player]

        committed[root.player] += (bets_this_round[root.player] - prev_betlevel) * cur_round.betsize
        bet_history += 'r'
        self.build_bets(root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, last_team_that_raised, min_actions_this_round, actions_this_round + 1, bets_this_round)
        root.raise_action = root.children[-1]
        bets_this_round[root.player] = prev_betlevel
        bets_this_round[(root.player+2) %2] = prev_betlevel
        committed[root.player] = prev_commit

    def showdown(self, root, players_in, committed, holes, board, deck, bet_history, bets): # TODO: WIN CONDITION
        if players_in.count(True) == 2:
            # winners
            payoffs = [1 for i in players_in if i]
            if(sum(payoffs) != 2):
                raise ValueError("Players in game is 2 but sum of winners != 2")
        else:
            scores = self.rules.handeval(board) #handeval(board)
            payoffs = [0 for i in range(len(players_in))]
            if score[0] != score[1]:
                if score[0] > score[1]:
                    for i in range(len(players_in)/2):
                        payoffs[i*2] = 1

                else:
                    for i in range(len(players_in)/2):
                        payoffs[i*2 + 1] = 1

        pay = 1
        if bets != None and min(bets) > 0:
        # min(bets) is used in the case that a team raise and the other fold, so the winner will score based on the bet BEFORE they raise
            min_bet = min(bets)
            if(min_bet >= 1):
                pay = max_bet*3
        payoffs = [x*pay for x in payoffs]

        return TerminalNode(root, committed, holes, board, deck, bet_history, payoffs, players_in)

    def holecard_distributions(self):
        x = Counter(combinations(self.rules.deck, self.holecards))
        d = float(sum(x.values()))
        return zip(x.keys(),[y / d for y in x.values()])

def multi_infoset_format(base_infoset_format, player, holecards, board, bet_history):
    return tuple([base_infoset_format(player, hc, board, bet_history) for hc in holecards])

# class PublicTree(GameTree):
#     def __init__(self, rules):
#         GameTree.__init__(self, GameRules(rules.players, rules.deck, rules.roundinfo, rules.ante, rules.blinds, rules.handeval, partial(multi_infoset_format, rules.infoset_format)))
#
#     def build(self):
#         # Assume everyone is in
#         players_in = [True] * self.rules.players
#         # Collect antes
#         committed = [self.rules.ante] * self.rules.players
#         bets = [0] * self.rules.players
#         # Collect blinds
#         next_player = self.collect_blinds(committed, bets, 0)
#         holes = [[()]] * self.rules.players
#         board = ()
#         bet_history = ""
#         self.root = self.build_rounds(None, players_in, committed, holes, board, self.rules.deck, bet_history, 0, bets, next_player)
#
#
#     def build_holecards(self, root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets):
#         cur_round = self.rules.roundinfo[round_idx]
#         hnode = HolecardChanceNode(root, committed, holes, board, self.rules.deck, "", cur_round.holecards)
#         # Deal holecards
#         all_hc = list(combinations(deck, cur_round.holecards))
#         updated_holes = []
#         for player in range(self.rules.players):
#             if not players_in[player]:
#                 # Only deal to players who are still in the hand
#                 updated_holes.append([old_hc for old_hc in holes[player]])
#             elif len(holes[player]) == 0:
#                 # If this player has no cards, just set their holecards to be the newly dealt ones
#                 updated_holes.append([new_hc for new_hc in all_hc])
#             else:
#                 updated_holes.append([])
#                 # Filter holecards to valid combinations
#                 # TODO: Speed this up by removing duplicate holecard combinations
#                 for new_hc in all_hc:
#                     for old_hc in holes[player]:
#                         if not overlap(old_hc, new_hc):
#                             updated_holes[player].append(old_hc + new_hc)
#         if cur_round.boardcards:
#             self.build_boardcards(hnode, next_player, players_in, committed, updated_holes, board, deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets)
#         else:
#             self.build_bets(hnode, next_player, players_in, committed, updated_holes, board, deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets)
#         return hnode
#
#     # def build_boardcards(self, root, next_player, players_in, committed, holes, board, deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets):
#     #     cur_round = self.rules.roundinfo[round_idx]
#     #     bnode = BoardcardChanceNode(root, committed, holes, board, deck, bet_history, cur_round.boardcards)
#     #     all_bc = combinations(deck, cur_round.boardcards)
#     #     for bc in all_bc:
#     #         cur_board = board + bc
#     #         cur_deck = filter(lambda x: not (x in bc), deck)
#     #         updated_holes = []
#     #         # Filter any holecards that are now impossible
#     #         for player in range(self.rules.players):
#     #             updated_holes.append([])
#     #             for hc in holes[player]:
#     #                 if not overlap(hc, bc):
#     #                     updated_holes[player].append(hc)
#     #         self.build_bets(bnode, next_player, players_in, committed, updated_holes, cur_board, cur_deck, bet_history, round_idx, min_actions_this_round, actions_this_round, bets)
#     #     return bnode
#
#     def showdown(self, root, players_in, committed, holes, board, deck, bet_history):
#         # TODO: Speedup
#         # - Pre-order list of hands
#         pot = sum(committed)
#         showdowns_possible = self.showdown_combinations(holes)
#         if players_in.count(True) == 1:
#             fold_payoffs = [-x for x in committed]
#             fold_payoffs[players_in.index(True)] += pot
#             payoffs = { hands: fold_payoffs for hands in showdowns_possible }
#         else:
#             scores = {}
#             for i in range(self.rules.players):
#                 if players_in[i]:
#                     for hc in holes[i]:
#                         if not (hc in scores):
#                             scores[hc] = self.rules.handeval(hc, board)
#             payoffs = { hands: self.calc_payoffs(hands, scores, players_in, committed, pot) for hands in showdowns_possible }
#         return TerminalNode(root, committed, holes, board, deck, bet_history, payoffs, players_in)
#
#     def showdown_combinations(self, holes):
#         # Get all the possible holecard matchups for a given showdown.
#         # Every card must be unique because two players cannot have the same holecard.
#         return list(filter(lambda x: all_unique(x), product(*holes)))
#
#     def calc_payoffs(self, hands, scores, players_in, committed, pot):
#         winners = []
#         maxscore = -1
#         for i,hand in enumerate(hands):
#             if players_in[i]:
#                 s = scores[hand]
#                 if len(winners) == 0 or s > maxscore:
#                     maxscore = s
#                     winners = [i]
#                 elif s == maxscore:
#                     winners.append(i)
#         payoff = pot / float(len(winners))
#         payoffs = [-x for x in committed]
#         for w in winners:
#             payoffs[w] += payoff
#         return payoffs

class Node(object):
    def __init__(self, parent, committed, holecards, board, deck, bet_history):
        self.committed = deepcopy(committed)
        self.holecards = deepcopy(holecards)
        self.board = deepcopy(board)
        self.deck = deepcopy(deck)
        self.bet_history = deepcopy(bet_history)
        if parent:
            self.parent = parent
            self.parent.add_child(self)

    def add_child(self, child):
        if self.children is None:
            self.children = [child]
        else:
            self.children.append(child)

class TerminalNode(Node):
    def __init__(self, parent, committed, holecards, board, deck, bet_history, payoffs, players_in):
        Node.__init__(self, parent, committed, holecards, board, deck, bet_history)
        self.payoffs = payoffs
        self.players_in = deepcopy(players_in)

class HolecardChanceNode(Node):
    def __init__(self, parent, committed, holecards, board, deck, bet_history, todeal):
        Node.__init__(self, parent, committed, holecards, board, deck, bet_history)
        self.todeal = todeal
        self.children = []

class BoardcardChanceNode(Node):
    def __init__(self, parent, committed, holecards, board, deck, bet_history, todeal):
        Node.__init__(self, parent, committed, holecards, board, deck, bet_history)
        self.todeal = todeal
        self.children = []

class ActionNode(Node):
    def __init__(self, parent, committed, holecards, board, deck, bet_history, player, infoset_format):
        Node.__init__(self, parent, committed, holecards, board, deck, bet_history)
        self.player = player
        self.children = []
        self.raise_action = None
        self.play3_action = None
        self.play2_action = None
        self.play1_action = None
        self.fold_action = None
        self.player_view = infoset_format(player, holecards[player], board, bet_history)

    def valid(self, action):
        if action == FOLD:
            return self.fold_action
        if action == PLAY1:
            return self.play1_action
        if action == PLAY2:
            return self.play2_action
        if action == PLAY3:          # Verificar se há cartas o suficiente para jogar
            return self.play3_action
        if action == RAISE:
            return self.raise_action
        raise Exception("Unknown action {0}. Action must be FOLD, PLAY1, PLAY2, PLAY3, or RAISE".format(action))

    def get_child(self, action):
        return self.valid(action)
