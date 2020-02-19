#!/usr/bin/env python3

"""Automata Structures

Defines the structures use to represent each automata

An automata has a label, initial state, end state, states, transitions, and a notation.
The states are stored as a list.
The transitions are stored in a dictionary with the key being the state for which they are outward.
TODO:change end_state to end_states once implemented
"""

from collections import namedtuple

Automata = namedtuple('Automata', ['label','initial_state', 'end_state', 'state_list', 'transition_dictionary','text'])
# transition dictionary: given a state label, returns a list of transitions it can make
# state list: list of all the automatas state labels
# initial state: first state

Transition = namedtuple('Transition', ['start_state','communication_all','communication_details','condition','reset_x','end_state'])
# start state
# communication. details are : 'communication_type','communication_content','communication_other'
# condition
# end state