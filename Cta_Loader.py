#!/usr/bin/env python3

"""CTA Loader

Given a list of automata notations, loads them in the data structures defined in Automata_Structures.
TODO:keep track of multiple outward transitions
"""

from log import log
from Automata_Structures import *

_automata_list = []

# loads a string automata (multiple)
def load_automata(_automata_string):
    log('loading automata', 1)
    # iterate through string to look for 'Init '
    log('find automata indexes', 1)
    log(_automata_string)
    _automata_indexes = []
    i = 0
    while i + 4 < len(_automata_string):
        _init_scan = _automata_string[i:i+4]
        # if its indicator
        if _init_scan == 'Cta ':
            # _automata_label = _automata_string[i+7:]
            _automata_indexes.append(i)
            log(' ' * i + '^:' + str(i))
        i += 1
    log(str(len(_automata_indexes)) + ' automata found', -1)

    # parse each automata
    log('parse each automata', 1)
    # _automata_list = []
    _index = 0
    while _index < len(_automata_indexes):
        # for each automata
        _automata_index         = _automata_indexes[_index]

        # separate automata from string
        if _index == len(_automata_indexes)-1:
            _current_automata       = _automata_string[_automata_index:]
        else:
            _current_automata       = _automata_string[_automata_index:_automata_indexes[_index+1]]

        _end_clause             = seek_seq(_current_automata,'=')
        _automata_label         = _current_automata[4:_end_clause-1]
        _end_clause             = seek_seq(_current_automata,';')
        _initial_state          = _current_automata[13:_end_clause]
        _state_list             = []
        _transition_dictionary  = {}
        # move along index
        _automata_index = _end_clause

        # find all transitions in this automata
        log('find all transitions in ' + str(_index+1), 1)
        _start_clause           = _end_clause+1
        _transition_index       = _end_clause + seek_seq(_current_automata[_end_clause+1:],';')+1
        while _transition_index < len(_current_automata):
            _current_transition = _current_automata[_start_clause:_transition_index+1]
            log('current transition: ' + _current_transition, 1)
            # log(str(_transition_index) + ' < ' + str(len(_current_automata)))

            # transition consists of:
            # - start state
            # - send/recieve
            # - condition
            # - end state

            _start_clause = seek_seq(_current_transition, ' ')
            _current_transition_start_state = _current_transition[:_start_clause]
            _start_clause += 1
            log("start state: " + _current_transition_start_state)

            _current_transition_communication_content = _current_transition[_start_clause:seek_seq(_current_transition, '(')]
            if '?' in _current_transition_communication_content:
                _current_transition_communication_type = 'receive'
            else:
                _current_transition_communication_type = 'send'
            log("communication type: " + _current_transition_communication_type)

            # patch communication content and split
            if _current_transition_communication_type == 'receive':
                _current_transition_communication_other = _current_transition_communication_content[:seek_seq(_current_transition_communication_content,'?')]
            else:
                _current_transition_communication_other = _current_transition_communication_content[:seek_seq(_current_transition_communication_content,'!')]
            _current_transition_communication_content = _current_transition_communication_content[(len(_current_transition_communication_other)+1):]

            _start_clause = seek_seq(_current_transition, '(')+1
            log("communication content: " + _current_transition_communication_content)
            log("communication other: " + _current_transition_communication_other)

            _current_transition_condition = _current_transition[_start_clause:seek_seq(_current_transition, ')')]
            _start_clause = seek_seq(_current_transition, ')')+2
            # check if there is a reset x
            if ',{x}' in _current_transition_condition:
                _current_transition_reset_x = True
                _current_transition_condition = _current_transition_condition[:-4]
            else:
                _current_transition_reset_x = False
            log("condition: " + _current_transition_condition)

            _current_transition_end_state = _current_transition[_start_clause:seek_seq(_current_transition, ';')]
            log('end state: ' + _current_transition_end_state)

            # build data tuple
            # namedtuple('Transition', ['start_state', 'communication_type', 'communication_content', 'communication_other','condition', 'reset_x', 'end_state'])
            _current_transition = Transition(_current_transition_start_state,
                                             _current_transition_communication_type + _current_transition_communication_content + _current_transition_communication_other,
                                             (_current_transition_communication_type,
                                                 _current_transition_communication_content,
                                                 _current_transition_communication_other),
                                             _current_transition_condition,
                                             _current_transition_reset_x,
                                             _current_transition_end_state)
            # add state to list
            if _current_transition_start_state not in _state_list:
                log('added new state to list')
                _state_list.append(_current_transition_start_state)
            # make sure end state is added to state list
            if _current_transition_end_state not in _state_list:
                log('added new state to list')
                _state_list.append(_current_transition_end_state)
            # update dictionary
            if _current_transition_start_state not in _transition_dictionary.keys():
                log('adding ' + str(_current_transition_start_state) + ' to dictionary')
                _transition_dictionary[_current_transition_start_state] = [_current_transition]
            else:
                log('already exists ' + str(_current_transition_start_state) + ' in transition dictionary') #  + str(_transition_dictionary[_current_transition_start_state])
                _transition_dictionary[_current_transition_start_state].append(_current_transition)
            log('new ' + str(_current_transition_start_state) + ' transition dictionary: ' + str(_transition_dictionary[_current_transition_start_state]))


            _start_clause       = _transition_index+1
            _transition_index   += seek_seq(_current_automata[_transition_index+1:],';')+1
            log('', -1)
            # time.sleep(1)
        log('finished transitions in automata ' + str(_index), -1)

        _end_state = ''
        for _state in _state_list:
            if _state not in _transition_dictionary:
                log(str(_state) + 'must be end state, no outward transitions')
                _end_state = _state

        _au = Automata(_automata_label, _initial_state, _end_state, _state_list, _transition_dictionary, _current_automata)
        _automata_list.append(_au)

        log('finished creating automata:')
        log(str(_au))
        _index += 1

    log('finished parsing', -1)
    log('finished loading all ' + str(len(_automata_indexes)) + ' automata', -1)

    return _automata_list

# finds the first instance of character
def seek_seq(_string, _seq):
    # log('seeking end: ' + _string)
    index = 0
    while index < len(_string) and _string[index:index+len(_seq)] != _seq:
        # log(' stuck | ' + str(index) + ' | ' + _string[index:] + ' | ' + _string)
        index += 1
    # log('found: |' + _string[index:index+1] + '|')
    return index