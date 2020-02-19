#!/usr/bin/env python3

"""File writer

Takes a list of strings and writes them to a file.
TODO:let the user define the file name to output them to
"""

from log import log

def write_golang(_lines):
    _finished_golang = open('golang_automata.go', 'w+')
    _finished_golang.writelines(_lines)
    _finished_golang.close()
    log('file is written @ /golang_automata.go')