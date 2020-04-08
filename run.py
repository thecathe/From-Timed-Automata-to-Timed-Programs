#!/usr/bin/env python3

from Cta_Loader import load_automata
from Golang_generator import generate_go_lang
from File_writer import write_golang
import Automata_Structures
# for using console/shell:
import sys


# check if this has been run from shell
if len(sys.argv) < 2:
    print('no arguments given, will use the defaults.')
    # _automata_array = ['Init u0;u0 UW!int(x < 10,{x}) u1;u1 AU?string(x <= 200) u2;']
    # _automata_array = ['Init u0;u0 UW!int(x < 10,{x}) u1;u1 AU?string(x <= 200) u2;',
    #                    'Init q0;q0 MW!log(x < 2,{x}) q1;q1 WM?data(x >= 3 && x < 9) q3;q1 MW!end(9 <= x <= 15,{x}) q2;q3 MW!log(x <= 15,{x}) q1;']
    # automata_array = ['Cta U = Init u0;u0 UW!int(x < 10,{x}) u1;u1 AU?string(x <= 200) u2;',
    #                    'Cta Q = Init q0;q0 MW!log(x < 2,{x}) q1;q1 WM?data(x >= 3 && x < 9) q3;q1 MW!end(9 <= x <= 15,{x}) q2;q3 MW!log(x <= 15,{x}) q1;']

    automata_array = ['Cta Q = Init q0;q0 z!a(x <= 2) q1;', 'Cta Z = Init z0;z0 q?a(x <= 2) z1;']

    # for report:
    # _automata_array = ['Cta A = Init a0;a0 B!2(true) a1;']
    # _automata_array = ['Cta A = Init a0;a0 B?string(true) a1;']
    # _automata_array = ['Cta A = Init a0;a0 B?string(true) a1;', 'Cta B = Init b0;b0 A!string(true) b1;']
    # _automata_array = ['Cta A = Init a0;a0 (x = 5) a1;']
else:
    print('will run the program with the following arguments:' + '\n'.join(sys.argv) + '\n Starting...')
    automata_array = sys.argv

# load notation into automata structures
automata_list = load_automata(automata_array)
# generate golang code from automata structures
golang_line = generate_go_lang(automata_list)
# write golang code to file
write_golang(golang_line)


# other automata examples from the 2018 CTA refinement paper:
# Init q0;q0 MW!log(x < 2,{x}) q1;q1 WM?data(x >= 3 and x < 9) q3;q1 MW!end(9 <= x <= 15,{x}) q2;q3 MW!log(x <= 15,{x}) q1;


# TODO LIST:
# - find out what to do with the vars. parameters?
#