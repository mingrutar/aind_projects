import os.path
from time import time
import logging

from aimacode.logic import PropKB
from aimacode.planning import Action
from aimacode.search import (
    Node, Problem,
)
from aimacode.utils import expr
from lp_utils import (
    FluentState, encode_state, decode_state,
)
from my_planning_graph import PlanningGraph, show_pg_statics

from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(os.path.basename(__file__))

class AirCargoProblem(Problem):
    run_hfunc_time = {"h_1": 0, "h_ignore_preconditions": 0, "h_pg_levelsum": 0}

    def __init__(self, cargos, planes, airports, initial: FluentState, goal: list):
        """

        :param cargos: list of str
            cargos in the problem,   ['C1', 'C2']
        :param planes: list of str   
            planes in the problem     ['P1', 'P2']
        :param airports: list of str
            airports in the problem   ['JFK', 'SFO']
        :param initial: FluentState object: 
            positive and negative literal fluents (as expr) describing initial state
          pos: [At(C1, SFO), At(C2, JFK), At(P1, SFO), At(P2, JFK)]
          neg: [At(C2, SFO), In(C2, P1), In(C2, P2), At(C1, JFK), In(C1, P1), In(C1, P2), At(P1, JFK), At(P2, SFO)]
        :param goal: list of expr   
            literal fluents required for goal test,  [At(C1, JFK), At(C2, SFO)]
        """
        #pos & neg state => self.initial_state_TF (all states) and self.state_map (T or F)
        self.state_map = initial.pos + initial.neg
        self.initial_state_TF = encode_state(initial, self.state_map)
        Problem.__init__(self, self.initial_state_TF, goal=goal) #Problem only has TFs
        self.cargos = cargos
        self.planes = planes
        self.airports = airports
        self.actions_list = self.get_actions()

    def get_actions(self):
        """
        This method creates concrete actions (no variables) for all actions in the problem
        domain action schema and turns them into complete Action objects as defined in the
        aimacode.planning module. It is computationally expensive to call this method directly;
        however, it is called in the constructor and the results cached in the `actions_list` property.

        Returns:
        ----------
        list<Action>
            list of Action objects
        """

        # concrete actions definition: specific literal action that does not include variables as with the schema
        # for example, the action schema 'Load(c, p, a)' can represent the concrete actions 'Load(C1, P1, SFO)'
        # or 'Load(C2, P2, JFK)'.  The
        def load_actions():
            """Create all concrete Load actions and return a list
            :return: list of Action objects
            """
            loads = []
            for cargo in self.cargos:
                for plane in self.planes:
                    for ap in self.airports:
                        precond_pos = [expr("At({}, {})".format(cargo, ap)), expr("At({}, {})".format(plane, ap))]
                        precond_neg = []
                        effect_add = [expr("In({}, {})".format(cargo, plane))]
                        effect_rem = [expr("At({}, {})".format(cargo, ap))]
                        load = Action(expr("Load({}, {}, {})".format(cargo, plane, ap)),
                                      [precond_pos, precond_neg],
                                      [effect_add, effect_rem])
                        loads.append(load)
            return loads

        def unload_actions():
            """Create all concrete Unload actions and return a list
    
            :return: list of Action objects
            """
            unloads = []
            for cargo in self.cargos:
                for plane in self.planes:
                    for ap in self.airports:
                        precond_pos = [expr("In({}, {})".format(cargo, plane)), expr("At({}, {})".format(plane, ap))]
                        precond_neg = []
                        effect_add = [expr("At({}, {})".format(cargo, ap))]
                        effect_rem = [expr("In({}, {})".format(cargo, plane))]
                        unload = Action(expr("Unload({}, {}, {})".format(cargo, plane, ap)),
                                      [precond_pos, precond_neg],
                                      [effect_add, effect_rem])
                        unloads.append(unload)
            return unloads

        def fly_actions():
            """Create all concrete Fly actions and return a list
            :return: list of Action objects
            """
            flys = []
            for fr in self.airports:
                for to in self.airports:
                    if fr != to:
                        for p in self.planes:
                            precond_pos = [expr("At({}, {})".format(p, fr))]
                            precond_neg = []
                            effect_add = [expr("At({}, {})".format(p, to))]
                            effect_rem = [expr("At({}, {})".format(p, fr))]
                            fly = Action(expr("Fly({}, {}, {})".format(p, fr, to)),
                                         [precond_pos, precond_neg],
                                         [effect_add, effect_rem])
                            flys.append(fly)
            return flys
        return load_actions() + unload_actions() + fly_actions()

    def actions(self, state: str) -> list:
        """ Return the actions that can be executed in the given state.

        :param state: str
            state represented as T/F string of mapped fluents (state variables)
            e.g. 'FTTTFF'
        :return: list of Action objects
        """
        logger.debug("actions: state=", state)
        possible_actions = []
        kb = PropKB()
        #kb.tell(decode_state(state, self.state_map).pos_sentence())
        decoded_state = decode_state(state, self.state_map)
        kb.tell(decoded_state.pos_sentence())
        logger.debug("actions: decoded_state=", decoded_state, ", pos_sentence()=", decoded_state.pos_sentence())
        for action in self.actions_list:
            is_possible = True
            for clause in action.precond_pos:
                if clause not in kb.clauses:
                    is_possible = False
            for clause in action.precond_neg:
                if clause in kb.clauses:
                    is_possible = False
            if is_possible:
                possible_actions.append(action)
        logger.debug("actions: state=", state,",pos_sentence()=",decoded_state.pos_sentence(),",possible_actions=",possible_actions)
        return possible_actions

    def result(self, state: str, action: Action):
        """ Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state).

        :param state: state entering node
        :param action: Action applied
        :return: resulting state after action
        """
        new_state = FluentState([], [])
        old_state = decode_state(state, self.state_map)
        for fluent in old_state.pos:
            if fluent not in action.effect_rem:
                new_state.pos.append(fluent)
        for fluent in action.effect_add:
            if fluent not in new_state.pos:
                new_state.pos.append(fluent)
        for fluent in old_state.neg:
            if fluent not in action.effect_add:
                new_state.neg.append(fluent)
        for fluent in action.effect_rem:
            if fluent not in new_state.neg:
                new_state.neg.append(fluent)
        encoded_state = encode_state(new_state, self.state_map)
        logger.debug("result: state=", state, ", action=", action, ",new_state=", new_state,",encoded_state=",encoded_state)
        return encoded_state

    def goal_test(self, state: str) -> bool:
        """ Test the state to see if goal is reached
        :param state: str representing state
        :return: bool
        """
        kb = PropKB()
        kb.tell(decode_state(state, self.state_map).pos_sentence())
        for clause in self.goal:
            if clause not in kb.clauses:
                return False
        logger.debug("goal_test: FOUND: state=", state, ",kb.clauses=", kb.clauses, ", self.goal=", self.goal)
        return True

    def h_1(self, node: Node):
        # note that this is not a true heuristic
        stime = time()
        h_const = 1
        self.run_hfunc_time['h_1'] += time() - stime
        return h_const

    @lru_cache(maxsize=8192)
    def h_pg_levelsum(self, node: Node):
        """This heuristic uses a planning graph representation of the problem
        state space to estimate the sum of all actions that must be carried
        out from the current state in order to satisfy each individual goal
        condition.
        """
        # requires implemented PlanningGraph class
        stime = time()
        pg = PlanningGraph(self, node.state)
        pg_levelsum = pg.h_levelsum()
        self.run_hfunc_time["h_pg_levelsum"] += time() - stime
        return pg_levelsum

    # @lru_cache(maxsize=8192)
    # def h_ignore_preconditions(self, node: Node):
    #     stime = time()
    #     found_goals = set()
    #     for action in self.actions_list:
    #         for clause in self.goal:
    #             if clause in action.effect_add:
    #                 found_goals.add(clause)
    #     self.run_hfunc_time["h_ignore_preconditions"] += time() - stime
    #     return len(found_goals)

    @lru_cache(maxsize=8192)
    def h_ignore_preconditions(self, node: Node):
        count = 0
        kb = PropKB()
        kb.tell(decode_state(node.state, self.state_map).pos_sentence())
        for clause in self.goal:
            if clause not in kb.clauses:
                count += 1
        return count

    def show_statics(self, h_str):
        print("total time spent in %s in %.2f sec" % (h_str, self.run_hfunc_time[h_str]))
        if ('h_pg_levelsum' == h_str ):
            show_pg_statics()


def air_cargo_p1() -> AirCargoProblem:
    ''' Problem 1  '''
    cargos = ['C1', 'C2']
    planes = ['P1', 'P2']
    airports = ['JFK', 'SFO']
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           ]
    neg = [expr('At(C2, SFO)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('At(C1, JFK)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('At(P1, JFK)'),
           expr('At(P2, SFO)'),
           ]
    init = FluentState(pos, neg)
    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            ]
    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p2() -> AirCargoProblem:
    ''' Problem 2 '''
    cargos = ['C1', 'C2', 'C3']
    planes = ['P1', 'P2', 'P3']
    airports = ['JFK', 'SFO', 'ATL']
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(C3, ATL)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           expr('At(P3, ATL)'),
           ]
    neg = [expr('At(C3, SFO)'),
           expr('At(C3, JFK)'),
           expr('In(C3, P1)'),
           expr('In(C3, P2)'),
           expr('In(C3, P3)'),
           expr('At(C2, SFO)'),
           expr('At(C2, ATL)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('In(C2, P3)'),
           expr('At(C1, JFK)'),
           expr('At(C1, ATL)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('In(C1, P3)'),
           expr('At(P1, JFK)'),
           expr('At(P1, ATL)'),
           expr('At(P2, SFO)'),
           expr('At(P2, ATL)'),
           expr('At(P3, SFO)'),
           expr('At(P3, JFK)'),
           ]
    init = FluentState(pos, neg)
    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            expr('At(C3, SFO)'),
            ]
    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p3() -> AirCargoProblem:
    cargos = ['C1', 'C2', 'C3', 'C4']
    planes = ['P1', 'P2']
    airports = ['JFK', 'SFO', 'ATL', 'ORD']
    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(C3, ATL)'),
           expr('At(C4, ORD)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)'),
           ]
    neg = [expr('At(C4, SFO)'),
           expr('At(C4, JFK)'),
           expr('At(C4, ATL)'),
           expr('In(C4, P1)'),
           expr('In(C4, P2)'),
           expr('At(C3, SFO)'),
           expr('At(C3, JFK)'),
           expr('At(C3, ORD)'),
           expr('In(C3, P1)'),
           expr('In(C3, P2)'),
           expr('At(C2, SFO)'),
           expr('At(C2, ATL)'),
           expr('At(C2, ORD)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('At(C1, JFK)'),
           expr('At(C1, ATL)'),
           expr('At(C1, ORD)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('At(P1, JFK)'),
           expr('At(P1, ATL)'),
           expr('At(P1, ORD)'),
           expr('At(P2, SFO)'),
           expr('At(P2, ATL)'),
           expr('At(P2, ORD)'),
           ]
    init = FluentState(pos, neg)
    goal = [expr('At(C1, JFK)'),
            expr('At(C3, JFK)'),
            expr('At(C2, SFO)'),
            expr('At(C4, SFO)'),
            ]
    return AirCargoProblem(cargos, planes, airports, init, goal)