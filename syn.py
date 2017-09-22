# syn.py
# Ronald L. Rivest (with Karim Husayn Karimi)
# August 3, 2017
# python3

"""
Routines to generate a synthetic test election dataset for multi.py.

Calls data generation routines in syn1.py for elections "of type 1",
and calls routines in syn2.py for elections "of type 2".
"""


import argparse
import copy
import numpy as np
import os
import shutil

import cli_syn
import multi
import audit_orders
import election_spec
import ids
import outcomes
import reported
import syn1
import syn2
import utils
import csv_writers

class Syn_Params(object):
    """ An object we can hang synthesis generation parameters off of. """

    pass


##############################################################################
## random choices

def geospace(start, stop, num=7):
    """
    Return a list of up to num distinct integer values,
    from start, start+1, ..., stop, inclusive, geometrically spread out.

    A bit like numpy.linspace, but geometrically spread
    out rather than linearly spread out, and only integers returned.
    >>> geospace(0,1)
    [0, 1]
    >>> geospace(0,10)
    [0, 1, 2, 3, 5, 7, 10]    
    >>> geospace(20, 10000)
    [20, 56, 159, 447, 1260, 3550, 10000]    
    >>> geospace(1, 64)
    [1, 2, 4, 8, 16, 32, 64]

    This should presumably be replaced by numpy.logspace !
    (although duplicates need to be removed...)
    """

    answer = {start, stop}
    start = max(start, 1)
    for i in range(1, num-1):
        answer.add(int(np.rint(start*(stop/start)**(i/(num-1)))))
    return sorted(answer)


def geospace_choice(e, syn, start, stop, num=7):
    """ 
    Return a random element from geospace(start, stop, num), 
    based on syn.RandomState.
    """

    elts = geospace(start, stop, num)
    return syn.RandomState.choice(elts)


def generate_segments(e, syn, low, high):
    """ 
    Return list of random segments (r, s) where low <= r < s <= high. 

    Number of segments returned is (high-low).

    Since r<s, does not return segments of the form (k, k).

    Intent is that cids are integers in range low <= cid <= high,
    and each segment yields a contest group covering cids r..s (inclusive).

    The segments "nest" -- given any two segments, either they
    are disjoint, or they are equal, or one contains the other.
    """

    assert low <= high
    L = []
    if low!=high:
        L.append((low, high))
        mid = syn.RandomState.choice(range(low, high))
        L.extend(generate_segments(e, syn, low, mid))
        L.extend(generate_segments(e, syn, mid+1, high))
    return L



if __name__=="__main__":

    e = multi.Election()
    args = cli_syn.parse_args()
    cli_syn.process_args(e, args)

