#!/usr/bin/env python3

from log import log

def write_golang(_lines):
    _finished_golang = open('golang_automata.go', 'w+')
    _finished_golang.writelines(_lines)
    _finished_golang.close()
    log('file is written @ /golang_automata.go')