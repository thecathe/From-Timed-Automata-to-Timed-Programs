#!/usr/bin/env python3

"""Go code generator

This takes processed automata and its notation.
The processed automata is stored in a namedTuple structure denoted in Automata_Structures.

For each automaton in automata, it creates a function in Go. This is designed to be instantiated in a goroutine.
Along with a goroutine for each automaton, a main() method is generated to instantiate the goroutines and crudely setup the channels required for communication.

This can likely deal with all automata as it is designed to deal with communicating timed automata (CTA).

Methodology:
1. Goes through each automaton, generates basic wrappings. For this I decided to avoid the rabbit-hole of all the branching paths and emulate the process of an automaton objectively. I have a current state, and keep iterating through until I reach the end state. (An oversight is that I have not added functionality for multiple end states).
TODO: add multiple end states

2. In the main loop, whilst waiting to reach the end state, I check the outward transitions for the current state I am in. To avoid issues during runtime, I record the value of x (time), at the start of each iteration. This avoids ambiguity for the rare cases where x changes whilst between checking outward transitions.

3. Once an outward transition is possible, it goes about executing the transition. Any data/communications occur and the current state is updated for the next iteration. If there are multiple outward transitions, I check if they are all true. I do this incase there is any ambiguity and to avoid any bias to the generation of the transitions. If all are possible, I randomally choose which one to transition to.

4. This all keeps happening until the end state is reached, when it terminates.
"""

from log import log
from Automata_Structures import *

# keep track of which channels go where and which type
# dictionary of automata returns list where it is used, some redundant data but is easier
_channel_dictionary = {}
_channel_directory = []

# returns a list of lines
def generate_go_lang(_automata,_automata_text):
    log('start golang gen', 1)
    # head of go file
    _file_head = 'package main\n\nimport (\n\t"time"\n\t"math/rand"\n)\n\n'
    # log('file head:\n' + _file_head)
    # head annotation
    _head_annotation = '/* for the automata:\n\t' + '\n\t'.join(_automata_text) + '\n*/\n\nx_ := 0\n\n'
    # log('head annotation:\n' + _head_annotation)

    _functions = []
    # generate each function
    for a in _automata:
        log('current automata: ' + str(a), 1)

        # set up initial state
        _initial_state = a.initial_state
        _end_state = a.end_state

        # helpers
        state_list = a.state_list
        _transition_dictionary = a.transition_dictionary

        #_current_automata_string = 'func f_' + str(a.label) + '() {\n\tcurrent_state = ' + _initial_state + '\n\trepeat {\n\t\tswitch current_state {\n'
        # below has the x lock
        _current_automata_string = 'func f_' + str(a.label) + '() {\n\tcurrent_state := "' + _initial_state + '"\n\t'*1 \
                                   + 'x := x_\n\n\trepeat {\n' + '\t'*2 + 'x = x_\n' + '\t'*2 + 'switch current_state {\n'

        # for each state
        for state in state_list:
            # if state has no transitions, that is end state
            if state in _transition_dictionary:
                # current state vars
                _state_transitions = _transition_dictionary[state]
                _current_automata_string += '\t'*3 + 'case "' + state + '":\n'

                # loop through all possibilities.
                # if more than once is possible, choose randomally
                # switch case the result

                # _outward_transition = '\t'*4 + 'outward_transitions = ' + str(len(_state_transitions)) + '\n' + '\t'*4 \
                #                       + 'for t := 0; t < ' + str(len(_state_transitions)) + '; t++ {\n'
                # _outward_transition += '\t'*5 + 'if '
                #
                # _outward_transition += '\t'*4 + '}'
                _outward_transition = '\t'*4 + '// outgoing transitions: ' + str(len(_state_transitions)) + '\n' \
                                      + '\t'*4 + 'outward_transition_indexes := []\n\n'
                _transition_index_counter = 0
                for c in _state_transitions:
                    _outward_transition += '\t'*4 + '// outgoing index: ' + str(_transition_index_counter) + '\n' \
                                            + '\t'*4 + 'if ' + c.condition + ' {\n' + '\t'*5 \
                                            + 'append(outward_transition_indexes, ' + str(_transition_index_counter)\
                                            + ')\n' + '\t'*4 + '}\n\n'
                    _transition_index_counter += 1

                # generate random number for however many is in the outwards transition list
                _outward_transition += '\t'*4 + '// randomally picks a valid outwards trasition\n' + '\t'*4 \
                                       + 'switch outgoing_transition_indexes[rand.Intn(len(outwrd_transition_indexes))] {\n'

                # loop through and provide a case for each possible transition
                _transition_index_counter = 0
                for c in _state_transitions:
                    _outward_transition += '\t'*5 + 'case ' + str(_transition_index_counter) + ':\n' + '\t'*6 \
                                           + str(channel_communication(a.label, c)) + '\n' + '\t'*6 \
                                           + 'current_state = "' + c.end_state + '"\n'
                    # check for x  reset
                    if c.reset_x:
                        _outward_transition += '\t'*6 + 'x = 0\n'
                    _transition_index_counter += 1

                _current_automata_string += _outward_transition + '\t'*4 + '}\n'

                # # check if there is a branch
                # if len(_state_transitions) > 1:
                #     # create super if
                #     _large_condition = ''
                #     for c in _state_transitions:
                #         log('current transition: ' + str(c))
                #         _large_condition += c.condition + ' && '
                #     _large_condition = _large_condition[:-4]
                #     # super if
                #     _current_automata_string += '\t'*4 + '// just in case all outward transitions are possible\n' \
                #                                 + '\t'*4 + 'if ' + _large_condition + ' {\n'
                #     # for each possible transition, choose randomally
                #     # int ignores 0
                #     _random_switch = '\t'*5 + '// randomally decides, if all are possible\n' + '\t'*5 \
                #                      + 'switch rand.Intn(' + str(len(_state_transitions) - 1) + ') {\n'
                #     for i in range(0, len(_state_transitions)):
                #         _current_transition = _state_transitions[i]
                #         _random_switch += '\t'*6 + 'case ' + str(i) + ':\n' + '\t'*6 \
                #                           + str(channel_communication(a.label,_current_transition)) + '\n' + '\t'*6 \
                #                           + 'current_state = "' + _current_transition.end_state + '"\n'
                #         # check for x  reset
                #         if _current_transition.reset_x:
                #             _random_switch += '\t'*6 + 'x = 0\n'
                #     # finish off
                #     _current_automata_string += _random_switch + '\t'*5 + '}\n'
                #     _current_automata_string += '\t'*4 + '}'
                #     # go through each transition
                #     for transition in _state_transitions:
                #         _current_automata_string += ' else if ' + transition.condition + ' {\n' + '\t'*4 \
                #                                     + str(channel_communication(a.label,transition)) +'\n' + '\t'*6 \
                #                                     + 'current_state = "' + transition.end_state + '"\n'
                #         # check if x reset
                #         if transition.reset_x:
                #             _current_automata_string += '\t'*5 + 'x = 0\n'
                #         _current_automata_string += '\t'*4 + '}'
                #     _current_automata_string += '\n'
                # else:
                #     # just one possibility
                #     _transition = _state_transitions[0]
                #     _current_automata_string += '\t'*4 + 'if ' + _transition.condition + ' {\n' + '\t'*5 \
                #                                 + str(channel_communication(a.label,_transition)) +'\n' + '\t'*5 \
                #                                 + 'current_state = "' + _transition.end_state + '"\n'
                #     # check if x reset
                #     if _transition.reset_x:
                #         _current_automata_string += '\t'*5 + 'x = 0\n'
                #
                #     _current_automata_string += '\t'*4 + '}\n'

        # add end of method
        _current_automata_string += '\t'*2 + '}\n\t} until current_state = "' + _end_state + '"\n}\n\n'

        _functions += _current_automata_string
        log('finished automata', -1)
        # log('finished automata:\n' + _current_automata_string, -1)

    log('creating main function', 1)
    # main declaration
    _main_function = 'func main() {\n\n\t// initialises random gen with seed\n\trand.Seed(time.now().UnixNano())\n\n\t// channels\n'

    # create channels
    for _chan in _channel_directory:
        _current_channel_details = _channel_dictionary[_chan]
        _channel_create_line = str(_chan) + ' := make(chan ' + str(_current_channel_details[1]) + ', 2) \t// buffer of 2 by default'
        _main_function += '\t' + _channel_create_line + '\n'

        # log('current chan: ' + str(_chan) + ' : ' + str(_current_channel_details))
        log('channel line: ' + str(_channel_create_line))

    _main_function += '\n\t// goroutine declaration\n'
    # declare goroutines
    for a in _automata:
        _create_goroutine_line = 'go f_' + str(a.label) + '()'
        _main_function += '\t' + _create_goroutine_line + '\n'

    # MAY NOT BE APPROPRIATE
    # add x
    _main_function += '\n\tfor {\n' + '\t'*2 + 'time.Sleep(time.second)\n' + '\t'*2 + 'x_++\n\t}\n'

    _main_function += '}\n\n'

    log('finished main function', -1)
    log('appending all lines together to one list of lines')

    _final_list_of_lines = [_file_head, _head_annotation, _main_function]
    _final_list_of_lines.extend(_functions)

    log('finished golang gen', -1)

    log('generated program:\n' + str(''.join(_final_list_of_lines)))

    return _final_list_of_lines

# helper function for setting up channels
# returns the code needed to implement the communication
def channel_communication(_automata, _transition):
    # log('new channel com', 1)
    # transition stuff
    _transition_start = _transition.start_state
    _transition_end = _transition.end_state
    _transition_condition = _transition.condition
    # communication stuff
    _transition_communication_all = _transition.communication_all
    # details
    _transition_communication_details = _transition.communication_details
    _transition_communication_type = _transition_communication_details[0]
    _transition_communication_content = _transition_communication_details[1]
    _transition_communication_other = _transition_communication_details[2]
    log('communication details: ' + str(_transition_communication_details))

    _proposed_channel_name = 'channel_' + _automata + '_' + _transition_communication_content
    # log('proposed channel name: ' + _proposed_channel_name)

    if _proposed_channel_name not in _channel_directory:
        _channel_directory.append(_proposed_channel_name)
        log('added ' + str(_proposed_channel_name) + ' to channel directory')
    else:
        log(str(_proposed_channel_name) + ' already used')

    # make assumption of channel
    if 'send' in _transition_communication_type:
        _channel_string = _proposed_channel_name + ' <- ' + _transition_communication_content
    else:
        _channel_string = _transition_communication_content + ' <- ' + _proposed_channel_name

    log('channel use code: ' + str(_channel_string))

    _channel_dictionary[_proposed_channel_name] = _transition_communication_details
    # log('finished channel com', -1)

    return _channel_string
