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

import multi
import audit_orders
import election_spec
import ids
import outcomes
import reported
import syn1
import syn2
import utils
import write_csv

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


##############################################################################
# Command-line arguments

def parse_args():

    parser = argparse.ArgumentParser(description=\
                                     ("syn.py: "
                                      "Generates synthetic elections for "
                                      "multi.py, a Bayesian post-election "
                                      "audit program for an election with "
                                      "multiple contests and multiple paper "
                                      "ballot collections."))

    # Mandatory argument: dirname

    parser.add_argument("election_dirname",
                        help=('The name of a subdirectory within the elections '
                              'root directory, where the output of this program '
                              'will be placed.  '
                              'A parameter value of "" gets the default '
                              'of TestElection followed by datetime.  '
                              'A file with name foo.csv within subdirectory syn2_specs '
                              'gives the synthetic election specification for '
                              'syn_type 2, where foo is the election_dirname.  '))

    # All others are optional

    parser.add_argument("--syn_type",
                        help="Type of synthetic election. (1 or 2)",
                        default='1')

    args = parser.parse_args()
    return args




def process_args(e, args):

    e.election_dirname = ids.filename_safe(args.election_dirname)
    e.election_name = e.election_dirname

    if args.syn_type == '1':                        
        syn1.generate_syn_type_1(e, args)
    elif args.syn_type == '2':
        syn2.generate_syn_type_2(e, args)
    else:
        print("Illegal syn_type:", args.syn_type)


if __name__=="__main__":

    e = multi.Election()

    args = parse_args()
    process_args(e, args)

    filepath = os.path.join(multi.ELECTIONS_ROOT, e.election_dirname)
    print("  Done. Synthetic election written to:", filepath)


