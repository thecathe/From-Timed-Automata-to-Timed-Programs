#!/usr/bin/env python3

"""File writer

Takes a list of strings and writes them to a file.
"""

from log import log

def write_golang(_lines):
    file_name = 'golang_automata.go'
    print('\tDefault name for files is: golang_automata.go')
    user_response = input('Press ENTER to use this, or enter an alternate name.\t\t')
    if user_response != '':
        file_name = user_response + '.go'

    _finished_golang = open(file_name, 'w+')
    _finished_golang.writelines(_lines)
    _finished_golang.close()

    print('\nFinished writing golang to file: ' + str(file_name))