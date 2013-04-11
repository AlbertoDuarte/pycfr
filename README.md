pyCFR
=====

A python implementation of Counterfactual Regret Minimization for flop-style poker games like Texas Hold'em, Leduc, and Kuhn poker.

Note that this library is intended for *very* simple games. It is written in pure python and is not optimized for speed nor memory usage. Full-scale Texas Hold'em will likely be too slow and too big to handle.

Creating a game tree
--------------------
To generate a tree for a game, simply specify the rules of the game:

```python
from pokertrees import *
from pokergames import *
players = 2
deck = [Card(14,1),Card(13,2),Card(13,1),Card(12,1)]
rounds = [RoundInfo(holecards=1,boardcards=0,betsize=2,maxbets=[2,2]),RoundInfo(holecards=0,boardcards=1,betsize=4,maxbets=[2,2])]
ante = 1
blinds = [1,2]
gamerules = GameRules(players, deck, rounds, ante, blinds, handeval=leduc_eval)
gametree = GameTree(gamerules)
gametree.build()
```

Or use one of the pre-built games:

```python
from pokergames import *
gametree = leduc_gametree()
```

Evaluating a strategy profile
-----------------------------
You can calculate the expected value of a set of strategies for a game:

```python
from pokertrees import *
from pokergames import *
from pokerstrategy import *
rules = leduc_rules()

# load first player strategy
s0 = Strategy(0)
s0.load_from_file('strategies/leduc/0.strat')

# load second player strategy
s1 = Strategy(1)
s1.load_from_file('strategies/leduc/1.strat')

# Create a strategy profile for this game
profile = StrategyProfile(rules, [s0,s1])

ev = profile.expected_value()
```

Getting the best response strategy
----------------------------------
Given a strategy profile, you can calculate the best response strategy for each agent:

```python
from pokertrees import *
from pokergames import *
from pokerstrategy import *
rules = leduc_rules()

# load first player strategy
s0 = Strategy(0)
s0.load_from_file('strategies/leduc/0.strat')

# load second player strategy
s1 = Strategy(1)
s1.load_from_file('strategies/leduc/1.strat')

# Create a strategy profile for this game
profile = StrategyProfile(rules, [s0,s1])

# Calculates the best response for every agent and the value of that response
brev = profile.best_response()

# The first element is a StrategyProfile of all the best responses
best_response = brev[0]

# The second element is a list of expected values of the responses vs. the original strategy profile
expected_values = brev[1]
```

The underlying implementation of the best response calculation uses a generalized version of the public tree algorithm presented in [1].

Finding a Nash equilibrium
--------------------------
Given the rules for a game, you can run the Counterfactual Regret (CFR) Minimization algorithm:

```python
# Get the rules of the game
hskuhn = half_street_kuhn_rules()

# Create the CFR minimizer
cfr = CounterfactualRegretMinimizer(hskuhn)

# Run a number of iterations, determining the exploitability of the agents periodically
iterations_per_block = 1000
blocks = 50
for block in range(blocks):
    print 'Iterations: {0}'.format(block * iterations_per_block)
    cfr.run(iterations_per_block)
    result = cfr.profile.best_response()
    print 'Best response EV: {0}'.format(result[1])

# The final result is a strategy profile of epsilon-optimal agents
nash_strategies = cfr.profile
```

Tests
-----
Tests for the game tree code are implemented in the `tests` directory.

- test_gametree.py - Tests the game tree functionality against a leduc-like game and verifies some branches are built as expected.

- test_strategy.py - Tests the strategy functionality by loading some pre-computed near-optimal strategies for Leduc poker and a default equal-probability policy.

- test_cfr.py - Tests the CFR minimizer functionality by running it on half-street Kuhn poker and Leduc poker. WARNING: Leduc poker is slow due to the size of the game.

Note the tests are intended to be run from the main directory, e.g. `python test/test_gametree.py`. They make some assumptions about relative paths when importing modules and loading and saving files.

TODO
----
The following is a list of items that still need to be implemented:

- MC-CFR (CS, PCS, AS)
- Pretty print game tree
- Simulator from game tree
- Handle edge cases where holecards come after the first round when there may be a variable number of players


Contributors
------------

Wesley Tansey

Hand evaluator code courtesy of [Alvin Liang's library](https://github.com/aliang/pokerhand-eval).




References
----------
[1] Johanson, Michael, Kevin Waugh, Michael Bowling, and Martin Zinkevich. "Accelerating best response calculation in large extensive games." In Proceedings of the Twenty-Second international joint conference on Artificial Intelligence-Volume Volume One, pp. 258-265. AAAI Press, 2011.