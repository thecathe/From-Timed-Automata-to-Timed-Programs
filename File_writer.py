#!/usr/bin/env python3

"""File writer

Takes a list of strings and writes them to a file.
TODO:let the user define the file name to output them to
"""

from log import log

def write_golang(program):
    finished_golang = open('golang_automata.go', 'w+')
    finished_golang.write(program)
    finished_golang.close()
    print('file is written @ /golang_automata.go')