# groups.py
# Ronald L. Rivest
# July 25, 2017
# python3

"""
This module implements "contest groups" for the post-election audit program
"multi.py".  
"""

import multi
import utils


def expand_contest_group_defs(e):
    """
    Expand contest group definitions so that we have a definition
    for each contest group purely in terms of its contests.

    The input definitions are in e.cgids_g, which gives definition
    of each contests group as an ordered list of cids and gids, 
    for each gid.

    The output goes into e.cids_g, which gives just an ordered list
    e.cids_g[gid] for the cids in each group.

    This is a simple reachability computation in a directed graph,
    using repeated depth-first search starting from each gid node.

    A warning is printed if the gid graph has any cycles.

    When the graph is acyclic, this is just like doing a derviation of
    a string in a context-free grammar, where the cids are the "terminals"
    and the gids are the "nonterminals".  Each gid generates exactly one
    string.

    The reason for using ordered lists here is that this may reflect the
    order in which the contests appear on a ballot.
    """

    e.cids_g = {}

    for gid in e.gids:
        gids = set()
        cids = []
        stack = []
        reachable_from(e, gid, gids, cids, stack)
        e.cids_g[gid] = cids


def reachable_from(e, gid, gids, cids, stack):
    """
    Find all gids and cids reachable from initial 
    gid in 0 or more steps.

    This works even if the graph contains cycles.
    """

    if gid in gids:
        if gid in stack:
            utils.mywarning("Group id {} is in a cycle!".format(gid))
        return
    gids.add(gid)
    for cgid in e.cgids_g[gid]:
        if cgid in e.cids:
            cids.append(cgid)
        else:
            stack.append(gid)
            reachable_from(e, cgid, gids, cids, stack)
            stack.pop()

def test_expand():

    e = multi.Election()
    e.gids = [1, 2, 3, 4, 5, 6, 7]
    e.cids = [11, 22, 33, 44, 55, 66, 77]
    e.cgids_g[1] = [11, 2]
    e.cgids_g[2] = [22, 3, 4]
    e.cgids_g[3] = [33]
    e.cgids_g[4] = [44, 5]
    e.cgids_g[5] = [55, 4]
    e.cgids_g[6] = [66, 1, 7]
    e.cgids_g[7] = [77, 3]

    print("Input:")
    print("  cids:", e.cids)
    print("  gids:", e.gids)
    for gid in e.gids:
        print("    {}->{}".format(gid, e.cgids_g[gid]))

    expand_contest_group_defs(e)

    print("Output:")
    for gid in e.gids:
        print("    {}->{}".format(gid, e.cids_g[gid]))

def test_expand_2():

    e = multi.Election()
    e.gids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    e.cids = [110, 220, 330, 440, 550, 660, 770, 880, 990, 10100, 11110, 12120]
    e.cgids_g[1] = [110, 2, 5, 6]
    e.cgids_g[2] = [220, 3, 11, 12]
    e.cgids_g[3] = [330, 4, 9, 10]
    e.cgids_g[4] = [440, 1, 7, 8]
    e.cgids_g[5] = [550]
    e.cgids_g[6] = [660]
    e.cgids_g[7] = [770]
    e.cgids_g[8] = [880]
    e.cgids_g[9] = [990]
    e.cgids_g[10] = [10100]
    e.cgids_g[11] = [11110]
    e.cgids_g[12] = [12120]


    print("Input:")
    print("  cids:", e.cids)
    print("  gids:", e.gids)
    for gid in e.gids:
        print("    {}->{}".format(gid, e.cgids_g[gid]))

    expand_contest_group_defs(e)

    print("Output:")
    for gid in e.gids:
        print("    {}->{}".format(gid, e.cids_g[gid]))


def expand_gids_in_list(e, L):
    """
    Return list L with all gids replaced by their cid-list equivalent.

    Here L is a list of mixed cid and gid identifiers.
    Duplicates removed in output, of course.
    The operation preserves the order of the portions 
    (like a contest-free grammar, if there are no cycles).
    """

    L = []
    for cgid in L:
        if cgid in e.cids:
            L.append(cgid)
        else:
            for cid in e.cids_g[cgid]:
                L.append(cid)
    return L


if __name__ == "__main__":

    test_expand()
    test_expand_2()

