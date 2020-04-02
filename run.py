#!/usr/bin/env python3

from Cta_Loader import load_automata
from Golang_generator import generate_go_lang
from File_writer import write_golang
# for using console/shell:
import sys

_automata_array = None
# check if this has been run from shell
if len(sys.argv) < 2:
    print('No arguments given, using program defaults.')
    # _automata_array = ['Init u0;u0 UW!int(x < 10,{x}) u1;u1 AU?string(x <= 200) u2;']
    # _automata_array = ['Init u0;u0 UW!int(x < 10,{x}) u1;u1 AU?string(x <= 200) u2;',
    #                    'Init q0;q0 MW!log(x < 2,{x}) q1;q1 WM?data(x >= 3 && x < 9) q3;q1 MW!end(9 <= x <= 15,{x}) q2;q3 MW!log(x <= 15,{x}) q1;']
    _automata_array = ['Cta U = Init u0;u0 UW!int(x < 10,{x}) u1;u1 AU?string(x <= 200) u2;',
                       'Cta Q = Init q0;q0 MW!log(x < 2,{x}) q1;q1 WM?data(x >= 3 && x < 9) q3;q1 MW!end(9 <= x <= 15,{x}) q2;q3 MW!log(x <= 15,{x}) q1;']

    # for report:
    # _automata_array = ['Cta A = Init a0;a0 B!2(true) a1;']
    # _automata_array = ['Cta A = Init a0;a0 B?string(true) a1;']
    # _automata_array = ['Cta A = Init a0;a0 B?string(true) a1;', 'Cta B = Init b0;b0 A!string(true) b1;']
    # _automata_array = ['Cta A = Init a0;a0 (x = 5) a1;']
else:
    _automata_array = sys.argv

print('The program will run with the following arguments: \n\t' + '\n\t'.join(_automata_array) + '\n Starting...')

# load notation into automata structures
_automata_list = load_automata(''.join(_automata_array))

# generate golang code from automata structures
_golang_line = generate_go_lang(_automata_list,_automata_array)
print('Finished generating Go code.\n\n')

# write golang code to file
write_golang(_golang_line)

print('Program finished.')
