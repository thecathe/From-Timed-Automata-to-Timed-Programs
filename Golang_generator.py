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

from Automata_Structures import *


def generate_go_lang(automata):
    print('\n\nStarting the generation of the Go code.')

    # initialise program tuple
    program = Program
    # name program
    program.name = input('Please enter the name of this program.\t')
    program.imports = ['time', 'math/rand', 'fmt']
    program.main = []
    program.goroutines = []


    # generate each goroutine
    for a in automata:
        print('\n\nCurrently generating goroutine for: ' + a.label)
        # initialise goroutine
        current_goroutine = Goroutine(a.label, a.initial_state, a.end_states, [], [])

        # go through each state -> get case states
        for current_state in a.state_list:
            print('\n\tCurrently generating state: ' + current_state)

            # only do the following if it has outward transitions (not an end state)
            if current_state in a.transition_dictionary.keys():

                current_state_case = {
                    'case': 'case "' + current_state + '":',
                    'transitions': [],
                    'transition_priorities': {
                        '0': [],  # wait
                        'z': [],  # after
                        'i': []  # rank int
                    },
                    'priority_lookup': {}
                }
                print('\t\tHow to decide which transition to take from this state needs to be defined:'
                      '\n\t0: Wait for this transition to stop being possible before taking others.'
                      '\n\tz: Take this transition as soon as possible, once higher priorities have been exhausted. (Absolute lowest priority)'
                      '\n\ti: Provide any positive integer to rank against other transitions. (Lower the rank, the earlier it will be considered)')

                # go through each transition at this state
                for current_transition in a.transition_dictionary[current_state]:
                    print('\t\tCurrently generating transition:\n\t\t\t' + str(current_transition))

                    if not current_state_case['transitions']:
                        print('\tThis is the first transition at this state to be evaluated.')
                    else:
                        # print out all current transition priorities
                        print('Below are all of the prioritised transitions:')
                        for transition_priority in current_state_case['transition_priorities']:
                            for t in current_state_case['transition_priorities'][transition_priority]:
                                # check if i
                                if transition_priority == 'i':
                                    print('\t' + transition_priority + ': ' + t[0] + ': ' + str(current_state_case['transitions'][t[1]]))
                                else:
                                    print('\t' + transition_priority + ': ' + str(current_state_case['transitions'][t]))

                    # ask the user
                    answer = input(
                        'To decide the behaviour of this transition, please input one of the following: 0, z, i\t')
                    while True:
                        if answer in ['0', 'z', 'i']:  # add to transition list
                            current_state_case['transitions'].append({
                                'start': current_transition.start_state,
                                'end': current_transition.end_state,
                                'condition': current_transition.condition,
                                'reset_clock': current_transition.reset_x,
                                'communication': current_transition.communication_details,
                                'channel': None
                            })
                            ct_index = len(current_state_case['transitions']) - 1
                            # add index of transition to appropriate priority list
                            if answer == '0':
                                current_state_case['transition_priorities']['0'].append(
                                    len(current_state_case['transitions']) - 1)
                                current_state_case['priority_lookup'][ct_index] = '0'
                            elif answer == 'z':
                                current_state_case['transition_priorities']['z'].append(
                                    len(current_state_case['transitions']) - 1)
                                current_state_case['priority_lookup'][ct_index] = 'z'
                            elif answer == 'i':
                                # what rank should it be given
                                user_rank = input('What rank should this transition be given?\t')
                                while True:
                                    try:
                                        # checks if int
                                        int(user_rank)
                                        current_state_case['transition_priorities']['i'].append(
                                            (user_rank, len(current_state_case['transitions']) - 1))
                                        current_state_case['priority_lookup'][ct_index] = user_rank
                                        break
                                    except ValueError:
                                        user_rank = input('ERROR: did not recognise as integer. Try again.')

                            print('\t\tSuccessfully set priority of: ' + str(
                                current_state_case['priority_lookup'][ct_index])
                                  + '\n\t\t\t\tfor: ' + str(current_state_case['transitions'][ct_index]))
                            break
                        else:
                            answer = input('ERROR: not answered correctly. ' + str(['0', 'z', 'i']) + '\t')
                current_goroutine.case_states.append(current_state_case)
            else:
                print('\t\tThis is an end state.')
        program.goroutines.append(current_goroutine)
        print('There are now ' + str(len(program.goroutines)) + ' goroutines in the program.')
        for gr in program.goroutines:
            print('\t' + str(gr.name))

    # go through and sort out channels
    print('\n\nNow the channels need to be defined.')
    for gr in program.goroutines:
        print('Current gorourtine: ' + gr.name)
        for cs in gr.case_states:
            print('\n\tCurrent state: ' + cs['case'])
            for t in cs['transitions']:
                print('\t\tCurrent transition: ' + str(t['start']) + ' to ' + str(t['end'])
                      + ' |-> ' + str(t['communication']))

                user_already_defined = input('Has the channel needed to fulfil the transition above already been defined? y/n?\t')
                while True:
                    if user_already_defined == 'y':
                        # find out what it was and add to this transition
                        print('Please select the an option that fulfils this transition from below:')
                        channel_index = 0
                        for c in gr.channels:
                            print('\t' + str(channel_index) + ': ' + c['name'])
                            channel_index += 1
                        user_channel = input('\tx: Go back, there is not a channel that fulfils the transition.\t')
                        channel_chosen = False
                        while True:
                            if user_channel == 'x':
                                # go back and make channel
                                user_already_defined = 'n'
                                break
                            else:
                                # check if int in range
                                try:
                                    if 0 <= int(user_channel) < channel_index:
                                        t['channel'] = gr.channels[int(user_channel)]
                                        channel_chosen = True
                                        break
                                    else:
                                        print('ERROR: Answer was not in the range of options.')
                                except ValueError:
                                    print('ERROR: Answer was not in the range of options.')
                        if channel_chosen:
                            print('Channel chosen. Moving on.\n')
                            break

                    elif user_already_defined == 'n':
                        # all transitions use a channel
                        channel = {
                            'name': None,
                            'users': [gr.name],
                            'data_type': t['communication']['content']
                        }

                        # get user to define name for channel
                        user_channel_name = input('For the channel used above, what should it be called?\t')
                        while True:
                            if user_channel_name == '':
                                user_channel_name = input('ERROR: Enter a proper name.\t')
                            else:
                                channel['name'] = user_channel_name
                                print('\tChannel name set.')
                                break

                        # set type used
                        print('For channel: ' + str(channel['name']) + ', the type is assumed to be: ' + str(channel['data_type']))
                        user_type = input('\tPress ENTER to use this, or enter the alternative\t')
                        if user_type != '':
                            channel['data_type'] = user_type

                        # ask user which other automata use this
                        print('For channel: ' + str(channel['name']) + ', please enter any other users.')
                        other_users = input('\tEnter one of the users now, if there are no more, press ENTER.\t')
                        while True:
                            if other_users == '':
                                print('No more users in this channel. Moving on.\n')
                                break
                            elif other_users not in channel['users']:
                                channel['users'].append(other_users)
                            other_users = input('Enter the next user, or press ENTER.\t')

                        # add channel
                        gr.channels.append(channel)
                        t['channel'] = channel

                        # go through other goroutines that use this channel
                        for user in channel['users']:
                            if user != gr.name:
                                # check all goroutines for a name of this
                                found_name = False
                                for gr_name_check in program.goroutines:
                                    if gr_name_check.name == user:
                                        gr_name_check.channels.append(channel)
                                        found_name = True
                                        break
                                if not found_name:
                                    print('ERROR: Was unable to find: "' + str(user) + '" in this program. Moving on.')
                        break
                    else:
                        user_already_defined = input('Please enter y or n.\t')

    # using the new data structures. generate the code
    print('\n\n\n\n\nFinished channels, not onto code gen')

    print_program_struct(program)


# def generate_main()

def generate_goroutine(goroutine, index):
    # set up var
    gr_clock = goroutine.name + '_clock'
    gr_tag = str(index) + ': ' + goroutine.name

    # determine parameters
    parameters = ''
    for param in goroutine.channels:
        if param == '':
            parameters = str(param)
        else:
            parameters += ', ' + str(param)

    # create ending condition if
    end_condition = 'if '
    for end in goroutine.end_states:
        end_condition += 'current_state == ' + end + ' || '
    # remove trailing ||
    end_condition = end_condition[:3] + '{'

    # initialise program lines
    p = ['func automata_' + goroutine.name + '(' + str(parameters) + ') {',
         '\n\t// initialise current state',
         '\tcurrent_state := "' + goroutine.initial_state + '"',
         '\n\t// set up clock',
         '\tx := ' + gr_clock,
         '\n\t// until an end state is reached',
         '\tfor {',
         '\t\t// update clock',
         '\t\tx = ' + gr_clock,
         '\t// check if end state has been reached',    #pos 10
         '\t' + end_condition,
         '\t}',
         '\n\tfmt.Println("' + gr_tag + ': finished")'
         '}']

    # generate case states
    case_state_lines = []
    for cs in goroutine.case_states:
        case_lines = [_t(2) + str(cs['case'])]
        # check for priority 0
        if len(cs['transition_priorities']['0']) > 0:
            case_lines.extend([
                _t(3) + '// checking those with priority 0',
                _t(3) + 'valid_p0_transitions := []'
            ])
            # go through each
            p0_transition_lines = []
            p0_random_end = [
                _t(3) + '// randomly choosing from any valid priority 0 transition',
                _t(3) + 'switch valid_p0_transitions[rand.Intn(len(valid_p0_transitions) - 1)] {'
            ]
            transition_index = 0
            for p0 in cs['transitions'][cs['transition_priorities']['0']]:
                if len(p0_transition_lines) > 0:
                    p0_transition_lines[len(p0_transition_lines) - 1] = _t(3) + '} else if ' + str(p0['condition']) + ' {',
                else:
                    p0_transition_lines.append(_t(3) + 'if ' + str(p0['condition']) + ' {')
                # add the rest
                p0_transition_lines.extend([
                    _t(4) + 'select {',
                    _t(5) + 'case x, ok := <- ' + p0['channel'] + ':',
                    _t(6) + 'if ok {',
                    _t(7) + '// transition waiting, adding to valid transitions',
                    _t(7) + 'append(valid_p0_transitions, "' + str(transition_index) + '")',
                    _t(6) + '} else {',
                    _t(7) + 'fmt.Println("' + gr_tag + ': ERROR, channel closed for: ' + p0['start'] + ' to ' + p0['end'] + '")',
                    _t(6) + '}',
                    _t(5) + 'break',
                    _t(4) + '}',
                    _t(3) + '}'
                ])

                # for the random choice at the end
                p0_random_end.append(_t(4) + 'case "' + gr_tag + '":')
                if p0['communication']['type'] == 'receive':
                    p0_random_end.append(_t(5) + 'var_' + str(p0['communication']['content']) + ' <- ' + str(p0['channel']))
                elif p0['communication']['type'] == 'send':
                    p0_random_end.append(_t(5) + str(p0['channel']) + ' <- ' + str(p0['communication']['content']))
                else:
                    print('ERROR: communication type (send/receive) is unknown.')
                p0_random_end.append(_t(5) + 'current_state = "' + str(p0['end']) + '"')
                # check if reset x
                if p0['reset_clock']:
                    p0_random_end.append(_t(5) + gr_clock + ' = 0')
                p0_random_end.append(_t(5) + 'fmt.Println("' + gr_tag + ': moved from ' + p0['start'] + ' to ' + p0['end'] + '.")')

                transition_index += 1
            case_lines.extend(p0_transition_lines)
            p0_random_end.append(_t(3) + '}')

            # randomly select from valid transitions
            case_lines.extend(p0_random_end)
            case_state_lines.extend(case_lines)

        # check for ranked priorities
        if len(cs['transition_priorities']['i']) > 0:
            case_lines.append(_t(3) + '// checking those with ranked priorities')
            # go through each
            ranked_transitions = None
            for pr in cs['transition_priorities']['i']:
                current_rank = cs['transitions'][pr[0]]
                current_transition = cs['transitions'][pr[1]]
                transition_lines = [_t(3) + 'if ' + str(current_transition['condition']) + ' {', _t(3) + '}']

                # add to ranked
                t_added = False
                if ranked_transitions is None:
                    ranked_transitions = [(current_rank, transition_lines)]
                    t_added = True
                else:
                    for t in ranked_transitions:
                        if current_rank < t[0]:
                            ranked_transitions.insert(ranked_transitions.index(t), (current_rank, transition_lines))
                            t_added = True
                            break
                if not t_added:
                    ranked_transitions.append((current_rank, transition_lines))






def print_program_struct(program):
    print('\nName: ' + str(program.name))
    print('\nImports: ' + str(program.imports))
    print('\nMain: ' + str(program.main))

    for gr in program.goroutines:
        print('\nGoroutine: ' + str(gr.name))
        print('\tInitial state: ' + str(gr.initial_state))
        print('\tEnd states: ' + str(gr.end_states))
        # channels
        print('\tChannels: ')
        for chan in gr.channels:
            print('\t\tName: ' + str(chan['name']))
            print('\t\t\tUsers: ' + str(chan['users']))
            print('\t\t\tData type: ' + str(chan['data_type']))
        # case states
        print('\tCase states: ')
        for cs in gr.case_states:
            print('\t\t' + str(cs['case']))
            print('\t\t\tTransitions: ' + str(len(cs['transitions'])))
            for t in cs['transitions']:
                print('\t\t\tPriority: ' + str(cs['priority_lookup'][cs['transitions'].index(t)]))
                print('\t\t\t\tStart: ' + str(t['start']))
                print('\t\t\t\tEnd: ' + str(t['end']))
                print('\t\t\t\tChannel: ' + str(t['channel']))
                print('\t\t\t\tCondition: ' + str(t['condition']))
                print('\t\t\t\tReset clock: ' + str(t['reset_clock']))
                print('\t\t\t\tCommunication: ' + str(t['communication']))


# # from log import log
# from Automata_Structures import *
#
# # keep track of which channels go where and which type
# # dictionary of automata returns list where it is used, some redundant data but is easier
# channel_dictionary = {}
# channel_lookup = []
# # how the channels should be designed
# channel_uni = True
#
#
# # returns a list of lines
# def generate_go_lang(automata, automata_text):
#     print('\n\nStarting the generation of Go code.')
#
#     global channel_uni
#     global channel_dictionary
#     global channel_lookup
#
#     user_choice = input('Please input how channels should be constructed, and press ENTER:'
#                         '\n\ta. Unidirectional\n\tb. Bidirectional\t\t')
#     while True:
#         if user_choice == 'a':
#             print('Channels will be unidirectional')
#             channel_uni = True
#             break
#         elif user_choice == 'b':
#             print('Channels will be bidirectional')
#             channel_uni = False
#             break
#         else:
#             user_choice = input(
#                 '\nThe options are:\n\ta. Unidirectional\n\tb. Bidirectional\t\t')
#
#     # head of go file
#     file_head = 'package main\n\nimport (\n\t"time"\n\t"math/rand"\n)\n\n'
#     # head annotation
#     head_annotation = '/* for the automata:\n\t' + '\n\t'.join(automata_text) + '\n*/\n\nx_ := 0\n\n'
#
#     functions = []
#     # generate each function
#     for a in automata:
#         print('Current automaton: ' + str(a))
#
#         # set up initial state
#         initial_state = a.initial_state
#         end_states = a.end_states
#
#         # helpers
#         state_list = a.state_list
#         transition_dictionary = a.transition_dictionary
#
#         # below has the x lock
#         current_automata_string = '/* Function of the automata:\n\t' + str(a.text) + '\n*/\nfunc f_' + str(a.label) \
#                                   + '() {\n\t// initial state\n\tcurrent_state := "' + initial_state \
#                                   + '"\n\tfmt.Println("' + str(a.label) + ': initial state: %s, current_state)' \
#                                   + '\n\t// used to capture x at each pass\n\tx := 0\n\t' \
#                                     '// repeat until a final state is reached\n\trepeat {'\
#                                     '\n' + _t(2) + 'x = x_\n' \
#                                   + _t(2) + 'switch current_state {\n'
#
#         # for each state
#         for state in state_list:
#             # if state has no transitions, that is end state
#             if state in transition_dictionary:
#                 # current state vars
#                 state_transitions = transition_dictionary[state]
#                 current_automata_string += _t(3) + 'case "' + state + '":\n'
#
#                 # # # # # # #
#                 # go through each transition, ask use how it should work
#                 # # # # # # #
#
#                 # ordered list of transitions
#                 priority_stack = []
#                 # list of random transitions
#                 random_stack = []
#                 # all transitions in stack
#                 stacked_transitions = []
#                 # given a transitions, points to index in a stack
#                 stack_pointer = {}
#
#                 print('Generating outward transitions of state: ' + str(state))
#                 # for each transition
#                 for t in state_transitions:
#                     t_index = str(state_transitions.indexOf(t))
#                     # send / receive
#                     t_type = t.communication_details['type']
#                     # data to communicate
#                     t_content = t.communication_details['content']
#                     # communicating with
#                     t_other = t.communication_details['other']
#
#                     # ask user how this should be ordered\
#                     user_response = ask('\tCurrent transition: ' + str(t.communication_all) + '\n'
#                                         '\t\t1. Prioritise this transition.'
#                                         '\t\t2. Only carry this out if possible.',
#                                         ['1', '2'])
#
#                     if user_response == '1':
#                         # find out how it should prioritise
#                         if len(priority_stack) == 0:
#                             # add to stack
#                             priority_stack.append(t_index)
#                             stacked_transitions.append(t_index)
#                             stack_pointer[t_index] = {
#                                 'stack': 'priority',
#                                 'index': 0
#                             }
#                         else:
#                             # ask where to append it to
#                             p_index = 1
#                             p_options = []
#                             p_string = ''
#                             for p in priority_stack:
#                                 p_string += '\t\t' + str(p_index) + '. ' + str(
#                                     state_transitions[p].communication_all) + '\n'
#                                 p_options.append(str(p_index))
#                                 p_index += 1
#                             user_response = ask(
#                                 '\tPlease select the position within the priority stack should this go:\n' + p_string,
#                                 p_options)
#                             priority_stack.insert(int(user_response), t_index)
#
#                     elif user_response == '2':
#                         # add to stack
#                         random_stack.append(t_index)
#                         stacked_transitions.append(t_index)
#                         stack_pointer[t_index] = {
#                             'stack': 'random',
#                             'index': len(random_stack) - 1
#                         }
#
#                     else:
#                         print('ERROR: outside of receive transition options.')
#
#                 # do priority transitions first
#                 for p in priority_stack:
#                     #
#
#                 # do random transitions after
#                 for r in random_stack:
#                     #
#
#
#
#
#
#
#                 if len(state_transitions) > 1:
#                     send_transitions = []
#                     receive_transitions = []
#                     send_options = []
#                     receive_options = []
#                     int_index = 0
#                     for c in state_transitions:
#                         if c.communication_details['type'] == 'send':
#                             send_string = '\t\t' + str(int_index) + '. ' + str(c.communication_details['type']) \
#                                            + ' ' + str(c.communication_details['content']) + ' ' \
#                                            + str(c.communication_details['other']) + '\n'
#                             send_transitions.append(c)
#                             send_options.append(send_string)
#                             int_index += 1
#                         else:
#                             receive_transitions.append(c)
#                             receive_string = '\t\t' + str(int_index) + '. ' + str(c.communication_details['type']) \
#                                            + ' ' + str(c.communication_details['content']) + ' ' \
#                                            + str(c.communication_details['other']) + '\n'
#                             receive_options.append(receive_string)
#
#                     wait_for_receive = False
#                     priority_transitions = []
#                     receive_option = None
#                     send_option = None
#
#                     print('\nGenerating how outward transitions are decided.'
#                           '\n\tAny receives are handled first, and sends are handled after. '
#                           'Options on how this works are given below')
#
#                     # if both send and receive
#                     # 1. wait for receives
#                     # 2. take first possible
#                     if len(receive_transitions) > 0:
#                         print('\tThere are multiple RECEIVE transitions at this state: ' + str(state))
#                         user_input_string = '\tPlease select from the following options on how they should be handled:\n' \
#                                             '\t\t1. Wait until RECEIVE transitions are no longer possible.\n' \
#                                             '\t\t2. Take the first outward transition possible.\n'
#                         user_index = input(user_input_string)
#                         while True:
#                             if user_index == 1:
#                                 priority_string = '\tPlease order the priority of transitions, shown below, ' \
#                                                   'by entering their index in order. (Highest priority first)'
#                                 priority_index = 1
#                                 for t in send_options:
#                                     priority_string += '\t\t' + str(priority_index) + '. ' + t + '\n'
#                                 for t in receive_options:
#                                     priority_string += '\t\t' + str(priority_index) + '. ' + t + '\n'
#                                 user_priority = input(priority_string)
#                                 while True:
#                                     if len(user_priority.split()) == len(state_transitions):
#                                         priority_transitions = user_priority.split()
#                                         send_option = 'priority'
#                                         break
#                                     else:
#                                         print('\tERROR: Priorities entered incorrectly.')
#
#                                 wait_for_receive = True
#                                 receive_option = 'wait receive'
#                                 break
#                             elif user_index == 2:
#                                 receive_option = 'first possible'
#                                 break
#                             else:
#                                 user_index = input(user_input_string)
#
#                     # multiple possible
#                     # 1. random
#                     # 2. prioritise
#                     if len(send_transitions) > 1:
#                         print('\tThere are multiple SEND transitions at this state: ' + str(state))
#                         user_input_string = '\tIf there are multiple possible transitions at the same time, ' \
#                                             'how should a transition be chosen:' \
#                                             '\n\t1. Randomly' \
#                                             '\n\t2. Prioritise them'
#                         user_index = input(user_input_string)
#
#                         while True:
#                             if user_index == 1:
#                                 choose_randomly = True
#                                 send_option = 'randomly'
#                                 break
#                             elif user_index == 2:
#                                 priority_string = '\tPlease order the priority of transitions, shown below, ' \
#                                                   'by entering their index in order. (Highest priority first)'
#                                 priority_index = 1
#                                 for t in send_options:
#                                     priority_string += '\t\t' + str(priority_index) + '. ' + t + '\n'
#                                 for t in receive_options:
#                                     priority_string += '\t\t' + str(priority_index) + '. ' + t + '\n'
#                                 user_priority = input(priority_string)
#                                 while True:
#                                     if len(user_priority.split()) == len(state_transitions):
#                                         priority_transitions = user_priority.split()
#                                         send_option = 'priority'
#                                         break
#                                     else:
#                                         print('\tERROR: Priorities entered incorrectly.')
#                                 break
#                             else:
#                                 user_index = input(user_input_string)
#
#
#                     if receive_option == 'wait receive':
#                         outward_transition = _t(5) + '// if all receives have been '
#                         # check if any receives are possible
#                         outward_transition += _t(5) + 'if !('
#                         for r in receive_transitions:
#                             outward_transition += '(' + r.condition + ') && '
#                         # remove last &&
#                         outward_transition.lstrip(' && ')
#                         outward_transition += ' {\n' + _t(6) + '// if no receives are possible'
#                         # sends
#                         if send_option == 'randomly':
#                             outward_transition += _t(5) + '// outward transitions: ' + str(len(state_transitions)) + '\n ' \
#                                                  + _t(5) + 'outward_transition_indexes := []' \
#
#                         elif send_option == 'priority':
#
#
#                         outward_transition += _t(5) + '} else {\n'
#                         # receives
#
#                         outward_transition += _t(5) + '}\n'
#
#                     elif send_option == 'randomly':
#
#
#
#                     elif send_option == 'priority':
#
#                     # choose randomly
#                     if choose_randomly == '':
#                         # loop through all possibilities.
#                         # if more than once is possible, choose randomly
#                         # switch case the result
#                         outward_transition = _t(5) + '// outgoing transitions: ' + str(len(state_transitions)) + '\n' \
#                                              + _t(5) + 'outward_transition_indexes := []\n\n'
#                         transition_index_counter = 0
#                         for c in state_transitions:
#                             outward_transition += _t(5) + '// outgoing index: ' + str(
#                                 transition_index_counter) + '\n' \
#                                                   + _t(5) + 'if ' + c.condition + ' {\n' + _t(6) \
#                                                   + 'append(outward_transition_indexes, ' + str(
#                                 transition_index_counter) \
#                                                   + ')\n' + _t(5) + '}\n\n'
#                             transition_index_counter += 1
#
#                         # generate random number for however many is in the outwards transition list
#                         outward_transition += _t(5) + '// randomly picks a valid outwards transition\n' + _t(5) \
#                                               + 'switch outgoing_transition_indexes[rand.Intn(len(outward_transition_indexes))] {\n'
#
#                         # loop through and provide a case for each possible transition
#                         transition_index_counter = 0
#                         for c in state_transitions:
#                             outward_transition += _t(6) + 'case ' + str(transition_index_counter) + ':\n' + _t(7) \
#                                                   + '// for the ' + str(c.communication_details['type']) + ' of ' \
#                                                   + str(c.communication_details['content']) + ' with ' \
#                                                   + str(c.communication_details['other']) + '\n' + _t(7) \
#                                                   + str(channel_communication(a.label, c)) + '\n' + _t(7) \
#                                                   + '// transition to next state\n' \
#                                                   + _t(7) + 'current_state = "' + c.end_state + '"\n' \
#                                                   + _t(7) + 'fmt.Println("' + str(a.label) \
#                                                   + ': moved to state: %s", current_state)\n'
#                             # check for x  reset
#                             if c.reset_x:
#                                 outward_transition += _t(7) + '// the notation specified that x needs to be reset\n' + _t(7) + 'x_ = 0\n'
#                             transition_index_counter += 1
#                         current_automata_string += outward_transition + _t(5) + '}\n' + _t(4) + '}\n'
#                 else:
#                     # only one outward transition
#                     print('only  1 outward transition')
#
#                     ############################################
#
#         # add end of method
#         current_automata_string += _t(2) + '}\n\t} until current_state = '
#
#         for state in end_states:
#             current_automata_string += '"' + state + '"'
#             # if not the last one
#             if end_states.index(state) is not len(end_states) - 1:
#                 current_automata_string += ' || '
#
#         current_automata_string += '\n}\n\n'
#
#         functions += current_automata_string
#         # log('finished automata', -1)
#         # log('finished automata:\n' + _current_automata_string, -1)
#
#     # log('creating main function', 1)
#
#     ##############################
#     # main declaration
#     main_function = 'func main() {\n\n\t// initialises random gen with seed\n\trand.Seed(time.now().UnixNano())\n\n' \
#                     '\t// channels: buffer of 2 by default\n'
#
#     print('Creating channels.\n\t'
#           'WARNING: variable types for these are not checked and take the placeholder names from the notation')
#     # create channels
#     for a in automata:
#         current_channels = channel_dictionary[a.label]
#         for chan in current_channels:
#             main_function += '\n\t/* Channel for:' \
#                              + _t(2) + str(chan['other']) \
#                              + _t(2) + str(chan['type']) \
#                              + _t(2) + str(chan['content']) + \
#                              '\t*/\n\t' + str(chan['name']) + ' := make(chan ' + str(chan['content']) + ', 2)\n'
#
#     main_function += '\n\t// goroutine declaration\n'
#     # declare goroutines
#     for a in automata:
#         create_goroutine_line = 'go f_' + str(a.label) + '()'
#         main_function += '\t' + create_goroutine_line + '\n'
#
#     # add x
#     main_function += '\n\t// time goes on indefinitely\n\tfor {\n' + _t(2) \
#                      + 'time.Sleep(time.second)\n' + _t(2) + 'x_++\n\t}\n'
#
#     main_function += '}\n\n'
#
#     final_list_of_lines = [file_head, head_annotation, main_function]
#     final_list_of_lines.extend(functions)
#
#     return final_list_of_lines


# def random_transitions(send_transitions, receive_transitions, indent):
#     code_lines = ''
#
#
# def order_transitions(order, transitions, i):
#     code_lines = ''
#     # for each in transition
#     for t in order:
#         current_transition = transitions[t]
#         if current_transition.communication_details['type'] == 'receive':
#             # if receive
#
#         elif current_transition.communication_details['type'] == 'send':
#             # if send
#
#         else:
#             print('ERROR: in order transitions')
#
#
# # the same as order, but waits on each receive transition
# def wait_transitions():
#     code_lines = ''



def ask(question, options):
    answer = input(question)
    while True:
        if answer in options:
            # find out the answer
            return answer
        else:
            answer = input('ERROR: not answered correctly\n' + options)


def _t(indent):
    return str('\t' * indent)

# # helper function for setting up channels
# # returns the code needed to implement the communication
# def channel_communication(automata_label, transition):
#     global channel_dictionary
#     global channel_lookup
#     global channel_uni
#     print('Verifying communication channel for transition: ' + str(transition))
#     # transition stuff
#     transition_start = transition.start_state
#     transition_end = transition.end_state
#     transition_condition = transition.condition
#     # communication stuff
#     transition_communication_all = transition.communication_all
#     # details
#     transition_communication_details = transition.communication_details
#     transition_comm_type = transition_communication_details['type']
#     transition_comm_content = transition_communication_details['content']
#     transition_comm_other = transition_communication_details['other']
#
#     proposed_channel_name = 'channel_' + automata_label + '_' + transition_comm_other + '_' + transition_comm_content
#     # log('proposed channel name: ' + _proposed_channel_name)
#
#     # get this automatons channels
#     if automata_label not in channel_dictionary:
#         # list of channel details
#         channel_dictionary[automata_label] = []
#
#     # go through each channel this automaton has, check if it corresponds to this communication
#     already_created = False
#     already_created_chan = None
#     for chan in channel_dictionary[automata_label]:
#         if chan['other'] == transition_end and chan['type'] == transition_comm_type:
#             already_created = True
#             already_created_chan = chan
#
#     if not already_created:
#         print('\tAdding channel for:\n'
#               '\t\tCommunicating with: ' + str(transition_comm_other) + '\n\t\tCommunication type: '
#               + str(transition_comm_type) + '\n\t\tCommunication data: ' + str(transition_comm_content) + '\n')
#         # show user default
#         print('\tAuto-generated name for this comm channel is:\t\t ' + str(proposed_channel_name))
#         user_response = input('Press ENTER to use this, or enter an alternate name.\t\t')
#         if user_response != '':
#             proposed_channel_name = 'channel_' + automata_label + '_' + user_response + '_' + transition_comm_content
#         # add name
#         channel_lookup.append(proposed_channel_name)
#
#         channel_dictionary[automata_label].append({
#             'other': transition_comm_other,
#             'type': transition_comm_type,
#             'content': transition_comm_content,
#             'name': proposed_channel_name
#         })
#         if not channel_uni:
#             # also append to counterpart
#             user_given_other = input('\tPlease give the label of the automata being communicated with:\t\t')
#             if user_given_other not in channel_dictionary:
#                 channel_dictionary[user_given_other] = []
#
#             channel_dictionary[user_given_other].append({
#                 'other': transition_start,
#                 'type': transition_comm_type,
#                 'content': transition_comm_content,
#                 'name': proposed_channel_name
#             })
#     else:
#         print('\tChannel needed for this has already been created:\n\t\t' + str(already_created_chan['name']) +
#               '\n\tWhich communicates\t with: ' + str(transition_comm_other) + '\n'
#                                                                                '\t\t\t\t\t' + str(
#             transition_comm_type) + '\n'
#                                     '\t\t\t\t\t' + str(transition_comm_content) + '\n')
#
#     # make assumption of channel
#     if 'send' in transition_comm_type:
#         channel_string = proposed_channel_name + ' <- ' + transition_comm_content
#     else:
#         channel_string = transition_comm_content + ' <- ' + proposed_channel_name
#
#     # channel_lookup[proposed_channel_name] = transition_communication_details
#
#     return channel_string
