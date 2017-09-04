# outcomes.py
# Ronald L. Rivest (with Karim Husayn Karimi)
# July 7, 2017
# python3

"""
Tally and outcome computations.
Code to compute an election outcome, given a sequence of votes and a contest type.
Also known as "social choice functions".

An outcome is always a *tuple* of ids, even if there is only one winner.
"""

# TBD: Tie-breaking, etc.


import ids


def compute_tally(vec):
    """
    Here vec is an iterable of hashable elements.
    Return dict giving tally of elements.
    """

    tally = {}
    for x in vec:
        tally[x] = tally.get(x, 0) + 1
    return tally


def plurality(e, cid, tally):
    """
    Return, for input dict tally mapping votes to (int) counts, 
    vote with largest count.  (Tie-breaking done arbitrarily here.)
    Winning vote must be a valid winner 
    (e.g. not ("-Invalid",) or ("-NoSuchContest",) )
    an Exception is raised if this is not possible.
    An undervote or an overvote can't win.
    """

    max_cnt = -1e90
    max_vote = None
    for vote in tally:
        if tally[vote] > max_cnt and \
           len(vote) == 1 and \
           not ids.is_error_selid(vote[0]):
            max_cnt = tally[vote]
            max_vote = vote
    if max_vote==None:
        assert "No winner allowed in plurality contest.", tally
    return max_vote


def compute_ro_c(e):
    """ 
    Compute reported outcomes ro_c for each cid, from e.rn_cr. 
    """

    e.ro_c = dict()
    for cid in e.rn_cr:
        tally = e.rn_cr[cid]
        e.ro_c[cid] = compute_outcome(e, cid, tally)


def compute_outcome(e, cid, tally):
    """
    Return outcome for the given contest, given tally of votes.
    """

    if e.contest_type_c[cid].lower()=="plurality":
        return plurality(e, cid, tally)
    else:
        # TBD: IRV, etc...
        multi.myerror(("Non-plurality outcome rule {} for contest {}"
                       "not yet implemented!")
                      .format(e.contest_type_c[cid], cid))


def compute_tally2(vec):
    """
    Input vec is an iterable of (a, r) pairs. 
    (i.e., (actual vote, reported vote) pairs).
    Return dict giving mapping from rv to dict
    giving tally of av's that appear with that rv.
    (Used for comparison audits.)
    """

    tally2 = {}
    for (av, rv) in vec:
        if rv not in tally2:
            tally2[rv] = compute_tally([aa for (aa, rr)
                                        in vec if rv == rr])
    return tally2




