"""Finish all TODO items in this file to complete the isolation project, then
test your agent's strength against a set of known agents using tournament.py
and include the results in your report.
"""
import random
import math

class SearchTimeout(Exception):
    """Subclass base exception for code clarity. """
    pass

# game board diagonal

ADD_DEPTH = 2 ** 32

def is_at_corner(w, h, x, y):
    cx = x == 0 or x == w - 1
    cy = y == 0 or y == h - 1
    return cx and cy

def custom_score(game, player):
    """Calculate the heuristic value of a game state from the point of view
    of the given player.

    This should be the best heuristic function for your project submission.

    Note: this function should be called from within a Player instance as
    `self.score()` -- you should not need to call this function directly.

    Parameters
    ----------
    game : `isolation.Board`
        An instance of `isolation.Board` encoding the current state of the
        game (e.g., player locations and blocked cells).

    player : object
        A player instance in the current game (i.e., an object corresponding to
        one of the player objects `game.__player_1__` or `game.__player_2__`.)

    Returns
    -------
    float
        The heuristic value of the current game state to the specified player.
    <=> based on improved_score. randonly reduce score a bit if the location is 
        close to edge,  
    """
    if game.is_loser(player):
        return float("-inf")

    if game.is_winner(player):
        return float("inf")

    w, h = game.width, game.height
    y, x = game.get_player_location(player)
    random_interval = 0.6
    rx = random.uniform(0, random_interval) if x == 0 or x == w - 1 else 0
    ry = random.uniform(0, random_interval) if y == 0 or y == h - 1 else 0
    own_moves = len(game.get_legal_moves(player))
    opp_moves = len(game.get_legal_moves(game.get_opponent(player)))
    score = float(own_moves - opp_moves)
    return score * (1 - rx - ry)

def custom_score_2(game, player):
    """Calculate the heuristic value of a game state from the point of view
    of the given player.

    Note: this function should be called from within a Player instance as
    `self.score()` -- you should not need to call this function directly.

    Parameters
    ----------
    game : `isolation.Board`
        An instance of `isolation.Board` encoding the current state of the
        game (e.g., player locations and blocked cells).

    player : object
        A player instance in the current game (i.e., an object corresponding to
        one of the player objects `game.__player_1__` or `game.__player_2__`.)

    Returns
    -------
    float
        The heuristic value of the current game state to the specified player.
    <=> based on improved_score, randomly add or reduce score a bit 
    """
    if game.is_loser(player):
        return float("-inf")

    if game.is_winner(player):
        return float("inf")

    own_moves = len(game.get_legal_moves(player))
    opp_moves = len(game.get_legal_moves(game.get_opponent(player)))
    score = own_moves - opp_moves
    w, h = game.width / 2., game.height / 2.
    y, x = game.get_player_location(player)
    ratio = (abs(h - y) + abs(w - x))/(w+h)     # how close to center
    return score * (2 + ratio)                  # weight score more than the closeness

def custom_score_3(game, player):
    """Calculate the heuristic value of a game state from the point of view
    of the given player.

    Note: this function should be called from within a Player instance as
    `self.score()` -- you should not need to call this function directly.

    Parameters
    ----------
    game : `isolation.Board`
        An instance of `isolation.Board` encoding the current state of the
        game (e.g., player locations and blocked cells).

    player : object
        A player instance in the current game (i.e., an object corresponding to
        one of the player objects `game.__player_1__` or `game.__player_2__`.)

    Returns
    -------
    float
        The heuristic value of the current game state to the specified player.
        within improved score prefer the move closer to opponent's location
    """
    if game.is_loser(player):
        return float("-inf")

    if game.is_winner(player):
        return float("inf")

    own_moves = len(game.get_legal_moves(player))
    opp_moves = len(game.get_legal_moves(game.get_opponent(player)))
    score = float(own_moves - opp_moves)
    y1, x1 = game.get_player_location(player)
    w, h = game.width, game.height
    if is_at_corner(w, h, x1, y1):
       return score
    y2, x2 = game.get_player_location(game.get_opponent(player))
    distance = (y1 - y2)**2 + (x1 - x2)**2
    max_distance = game.width **2 + game.height**2
    rev_distance_ratio = (1.0 - (distance / max_distance))
    return score * (1.0 + rev_distance_ratio)

class IsolationPlayer:
    """Base class for minimax and alphabeta agents -- this class is never
    constructed or tested directly.

    ********************  DO NOT MODIFY THIS CLASS  ********************

    Parameters
    ----------
    search_depth : int (optional)
        A strictly positive integer (i.e., 1, 2, 3,...) for the number of
        layers in the game tree to explore for fixed-depth search. (i.e., a
        depth of one (1) would only explore the immediate sucessors of the
        current state.)

    score_fn : callable (optional)
        A function to use for heuristic evaluation of game states.

    timeout : float (optional)
        Time remaining (in milliseconds) when search is aborted. Should be a
        positive value large enough to allow the function to return before the
        timer expires.
    """
    def __init__(self, search_depth=3, score_fn=custom_score, timeout=10.):
        self.search_depth = search_depth
        self.score = score_fn
        self.time_left = None
        self.TIMER_THRESHOLD = timeout


class MinimaxPlayer(IsolationPlayer):
    """Game-playing agent that chooses a move using depth-limited minimax
    search. You must finish and test this player to make sure it properly uses
    minimax to return a good move before the search time limit expires.
    """
    def get_move(self, game, time_left):
        """Search for the best move from the available legal moves and return a
        result before the time limit expires.

        **************  YOU DO NOT NEED TO MODIFY THIS FUNCTION  *************

        For fixed-depth search, this function simply wraps the call to the
        minimax method, but this method provides a common interface for all
        Isolation agents, and you will replace it in the AlphaBetaPlayer with
        iterative deepening search.

        Parameters
        ----------
        game : `isolation.Board`
            An instance of `isolation.Board` encoding the current state of the
            game (e.g., player locations and blocked cells).

        time_left : callable
            A function that returns the number of milliseconds left in the
            current turn. Returning with any less than 0 ms remaining forfeits
            the game.

        Returns
        -------
        (int, int)
            Board coordinates corresponding to a legal move; may return
            (-1, -1) if there are no available legal moves.
        """

        self.time_left = time_left

        # Initialize the best move so that this function returns something
        # in case the search fails due to timeout
        best_move = (-1, -1)

        try:
            # The try/except block will automatically catch the exception
            # raised when the timer is about to expire.
            legal_moves = game.get_legal_moves()
            next_move =  self.minimax(game, self.search_depth) if len(legal_moves) else (-1, -1)
            return next_move
        except SearchTimeout:
            pass  # Handle any actions required after timeout as needed

        # Return the best move from the last completed search iteration
        return best_move

    def minimax(self, game, depth):
        """Implement depth-limited minimax search algorithm as described in
        the lectures.

        This should be a modified version of MINIMAX-DECISION in the AIMA text.
        https://github.com/aimacode/aima-pseudocode/blob/master/md/Minimax-Decision.md

        **********************************************************************
            You MAY add additional methods to this class, or define helper
                 functions to implement the required functionality.
        **********************************************************************

        Parameters
        ----------
        game : isolation.Board
            An instance of the Isolation game `Board` class representing the
            current game state

        depth : int
            Depth is an integer representing the maximum number of plies to
            search in the game tree before aborting

        Returns
        -------
        (int, int)
            The board coordinates of the best move found in the current search;
            (-1, -1) if there are no legal moves

        Notes
        -----
            (1) You MUST use the `self.score()` method for board evaluation
                to pass the project tests; you cannot call any other evaluation
                function directly.

            (2) If you use any helper functions (e.g., as shown in the AIMA
                pseudocode) then you must copy the timer check into the top of
                each helper function or else your agent will timeout during
                testing.
        """

        def max_value(game, the_depth):
            if self.time_left() < self.TIMER_THRESHOLD:
                raise SearchTimeout()

            legal_moves = game.get_legal_moves()
            if the_depth == 0  or not legal_moves:
                score = self.score(game, self)
                return score

            best_score = float("-inf")
            for m in legal_moves:
                next_game = game.forecast_move(m)
                score = min_value(next_game, the_depth - 1)
                if score > best_score:
                    best_score = score
            return best_score

        def min_value(game, the_depth):
            if self.time_left() < self.TIMER_THRESHOLD:
                raise SearchTimeout()

            legal_moves = game.get_legal_moves()
            if the_depth == 0 or not legal_moves:
                score = self.score(game, self)
                return score

            best_score = float("inf")
            for m in legal_moves:
                next_game = game.forecast_move(m)
                score = max_value(next_game, the_depth - 1)
                if score < best_score:
                    best_score = score
            return best_score

        best_score = float("-inf")
        best_move = (-1, -1)
        for move in game.get_legal_moves():
            score = min_value(game.forecast_move(move), depth - 1)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move


class AlphaBetaPlayer(IsolationPlayer):
    """Game-playing agent that chooses a move using iterative deepening minimax
    search with alpha-beta pruning. You must finish and test this player to
    make sure it returns a good move before the search time limit expires.
    """

    def get_move(self, game, time_left):
        """Search for the best move from the available legal moves and return a
        result before the time limit expires.

        Modify the get_move() method from the MinimaxPlayer class to implement
        iterative deepening search instead of fixed-depth search.

        **********************************************************************
        NOTE: If time_left() < 0 when this function returns, the agent will
              forfeit the game due to timeout. You must return _before_ the
              timer reaches 0.
        **********************************************************************

        Parameters
        ----------
        game : `isolation.Board`
            An instance of `isolation.Board` encoding the current state of the
            game (e.g., player locations and blocked cells).

        time_left : callable
            A function that returns the number of milliseconds left in the
            current turn. Returning with any less than 0 ms remaining forfeits
            the game.

        Returns
        -------
        (int, int)
            Board coordinates corresponding to a legal move; may return
            (-1, -1) if there are no available legal moves.
        """
        self.time_left = time_left
        best_move = (-1, -1)
        alpha = float("inf")
        beta = float("-inf")
        try:
            # The try/except block will automatically catch the exception
            # raised when the timer is about to expire.
            legal_moves = game.get_legal_moves()
            if legal_moves:
                #next_move =  self.alphabeta(game, self.search_depth, alpha, beta)
                for i in range(ADD_DEPTH):
                    next_move =  self.alphabeta(game, self.search_depth+i, alpha, beta)
                    if next_move != (-1, -1):
                        best_move = next_move
                # return next_move

        except SearchTimeout:
            pass  # Handle any actions required after timeout as needed

        # Return the best move from the last completed search iteration
        return best_move

    def alphabeta(self, game, depth, alpha=float("-inf"), beta=float("inf")):
        """Implement depth-limited minimax search with alpha-beta pruning as
        described in the lectures.

        This should be a modified version of ALPHA-BETA-SEARCH in the AIMA text
        https://github.com/aimacode/aima-pseudocode/blob/master/md/Alpha-Beta-Search.md

        **********************************************************************
            You MAY add additional methods to this class, or define helper
                 functions to implement the required functionality.
        **********************************************************************

        Parameters
        ----------
        game : isolation.Board
            An instance of the Isolation game `Board` class representing the
            current game state

        depth : int
            Depth is an integer representing the maximum number of plies to
            search in the game tree before aborting

        alpha : float
            Alpha limits the lower bound of search on minimizing layers

        beta : float
            Beta limits the upper bound of search on maximizing layers

        Returns
        -------
        (int, int)
            The board coordinates of the best move found in the current search;
            (-1, -1) if there are no legal moves

        Notes
        -----
            (1) You MUST use the `self.score()` method for board evaluation
                to pass the project tests; you cannot call any other evaluation
                function directly.

            (2) If you use any helper functions (e.g., as shown in the AIMA
                pseudocode) then you must copy the timer check into the top of
                each helper function or else your agent will timeout during
                testing.
        """

        def max_value(game, alpha,  beta, the_depth ):
            if self.time_left() < self.TIMER_THRESHOLD:
                raise SearchTimeout()

            legal_moves = game.get_legal_moves()
            if the_depth == 0 or not legal_moves:
                return  self.score(game, self)

            best_score = float("-inf")
            for m in legal_moves:
                next_game = game.forecast_move(m)
                score = min_value(next_game, alpha, beta, the_depth - 1)
                if score > best_score:
                    if score >= beta:
                        return score
                    best_score = score
                    alpha = max (alpha, score)
            return best_score

        def min_value(game, alpha, beta, the_depth):
            if self.time_left() < self.TIMER_THRESHOLD:
                raise SearchTimeout()

            legal_moves = game.get_legal_moves()
            if the_depth == 0 or not legal_moves:
                return self.score(game, self)

            best_score = float("inf")
            for m in legal_moves:
                next_game = game.forecast_move(m)
                score = max_value(next_game, alpha, beta, the_depth - 1)
                if score < best_score:
                    if score <= alpha:
                        return score
                    best_score = score
                    beta = min(beta, score)
            return best_score

        best_score = float("-inf")
        best_move = (-1, -1)
        for move in game.get_legal_moves():
            next_game = game.forecast_move(move)
            score = min_value(next_game, alpha, beta, depth - 1)
            if score > best_score:
                best_score = score
                best_move = move
                alpha = max (alpha, score)
        return best_move
