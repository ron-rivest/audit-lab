# groups.py
# Ronald L. Rivest
# July 25, 2017 (rev Sept. 21, 2017)
# python3

"""
This module implements "contest groups" for the post-election audit program
"OpenAuditTool.py".  
"""

import warnings


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

    The reason for using ordered lists here (as opposed to sets)
    is that this may reflect the order in which the contests appear 
    on a ballot.
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
    gid in 0 or more steps.  Main output of interest
    is the input list "cids", which has all reachable
    contests appended to it.  

    This works even if the graph contains cycles.
    Algorithm is depth-first search (DFS).
    """

    if gid in gids:
        if gid in stack:
            warnings.warn("Group id {} is in a cycle!".format(gid))
        return
    gids.add(gid)
    for cgid in e.cgids_g[gid]:
        # Note: 'cgid' means 'contest or group id'
        if cgid in e.cids:
            cids.append(cgid)
        else:
            stack.append(gid)
            reachable_from(e, cgid, gids, cids, stack)
            stack.pop()


def expand_gids_in_list(e, L):
    """
    Return list L with all gids replaced by their cid-list equivalent.

    Here L is a list of mixed cid and gid identifiers.
    Duplicates removed in output, of course.
    The operation preserves the order of the portions 
    (like a contest-free grammar, if there are no cycles).
    """

    ans = []
    for cgid in L:
        if cgid in e.cids:
            ans.append(cgid)
        else:
            for cid in e.cids_g[cgid]:
                ans.append(cid)
    return ans



