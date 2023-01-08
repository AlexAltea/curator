#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

import shutil
import numpy

ALIGN_LEFT = 1
ALIGN_RIGHT = 2

# Helpers
def print_field(string, length, align=ALIGN_LEFT):
    lpad = ' '
    rpad = ' '
    if len(string) <= length:
        if align == ALIGN_LEFT:
            rpad += ' ' * (length - len(string))
        if align == ALIGN_RIGHT:
            padr += ' ' * (length - len(string))
        return lpad + string + rpad
    else:
        return lpad + string[:length-3] + '...' + rpad

def compute_width(table, maxwidth=80):
    widths = [] # (width, avgw, maxw, fixed)
    table = numpy.transpose(table)
    for column in table:
        lengths = list(map(len, column))
        average = numpy.average(lengths)
        maximum = max(lengths)
        if maximum <= 4:
            widths.append((maximum, average, maximum, True))
        else:
            widths.append((maximum, average, maximum, False))

    # Account for padding and borders
    maxwidth = maxwidth - 3*len(table) + 1

    # Reduce column size if overflow
    curwidth = sum(map(lambda x: x[0], widths))
    if curwidth > maxwidth:
        removal = curwidth - maxwidth 
        fixwidth = sum(map(lambda x: x[0], filter(lambda x: x[3], widths)))
        movwidth = sum(map(lambda x: x[0], filter(lambda x: not x[3], widths)))
        ratio = (movwidth-removal)/movwidth
        for i in range(len(widths)):
            width = widths[i]
            if width[3]: continue
            widths[i] = (int(width[0] * ratio - 1),) + width[1:]
    return list(map(lambda x: x[0], widths))
        
def print_plan(thead, tbody):
    # Add ID column
    thead = ("#",) + thead
    for i in range(len(tbody)):
        tbody[i] = (str(i+1),) + tbody[i]

    # Compute width for each column
    termsize = shutil.get_terminal_size()
    table = [thead] + tbody
    widths = compute_width(table, termsize.columns)
    
    # Print table
    print('┌' + '┬'.join(list(map(lambda w: '─'*(w+2), widths))) + '┐')
    print('│' + '│'.join(list(map(lambda x: print_field(*x), zip(thead, widths)))) + '│')
    print('├' + '┼'.join(list(map(lambda w: '─'*(w+2), widths))) + '┤')
    for row in tbody:
        print('│' + '│'.join(list(map(lambda x: print_field(*x), zip(row, widths)))) + '│')
    print('└' + '┴'.join(list(map(lambda w: '─'*(w+2), widths))) + '┘')
