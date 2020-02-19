#!/usr/bin/env python3

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