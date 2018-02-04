# risk_bayes_2.py
# Ronald L. Rivest (with Karim Husayn Karimi)
# August 13, 2017
# python3

"""
Improved code for computing Bayes risks.

Will replace risk_bayes.py, and be called by audit.py.

THIS FILE IS INCOMPLETE.  TO BE THOUGHT THROUGH
MORE CAREFULLY, AND THEN IMPLEMENTED.
"""

"""
These routines are much more flexible and generic, and
will allow Bayes risk sampling and optimization in very
general ways.  For example, you can sample 
    -- different pbcids at different rates
    -- different card types at different rates
       (where the ballot manifest specifies the card type)
    -- different ballots at different rates, based on their
       reported votes.
And so on...
"""

"""
We assume that we are dealing with a single contest 'cid'.

The basic data structure is a finite tree T, representable
as a nonempty set of python tuples.

The empty tuple () represents the root, T.root, of the tree.

The children of a node x = (x1, x2, ..., xk) are tuples
that are one longer:
    T.children(x) = { (x1, x2, ..., xk, x(k+1) }
for some finite set of possibilities for x(k+1).
(Because nodes are python tuples, each possible for
x(k+1) must be 'hashable', such as a string or a 
vote.)

If a node has no children, it is a 'leaf' node.

All of the leaves can be reached by recursively
enumerating the children of every reachable node,
starting with the root node ().

The set of all leaves of T is denoted T.leaves.

The set of all "internal" (non-leaf) nodes is denoted 
    T.internal_nodes.

The set of all nodes (leaf or non-leaf) is denoted
    T.nodes

A 'count' is a python function taking three inputs:
    a tree T
    a node x = (x1, x2, ..., xk) in the tree, and
    a vote v,
and returns
    ***TBD***
     

Every leaf node has a 'count':
    T.count(x)
The count may be an arbitrary real number, but the
semantics are that if
    x = (x1, x2, ..., xk)
is a leaf node, then xk represents a possible 'actual
vote' (av) in contest cid -- that is, a vote that is discovered
during the hand examination of a cast ballot, and the
'count' represents the number of ballots with that actual
vote.

More precisely, the values x1, x2, ..., x(k-1) specify
"meta-information" describing a class of ballots, possibly
including
     -- the reported vote for that contest (rv)
     -- the paper ballot collection (pbcid)
     -- the ballot style or card type as seen on
        the ballot manifest (denoted how??)
     -- the scanner used on that ballot (denoted how??)
and so on.  Then the 'count' is the number of
ballots with the stated actual vote (av) within
the subpopulation of votes with the stated meta-data.

A typical leaf node might look like:
    (cid, pbcid, rv, av)
but other structures are possible.

Associated with any node x, for any av,
we aggregate the count values for all of the avs in
the subtree rooted at x:
    T.get(x, av) = T.count(x)
                   if x in T.leaves
                   else
                   sum([T.get(y,av) for y in T.children(x)])

In our application, there will actually be THREE different
'count' functions:
    T.countA(x)
    T.countR(x)
    T.countP(x)
standing for 'actual', 'reported', and (Bayesian) 'prior'.
We have similar aggregation functions
    T.getA
    T.getR
    T.getP
as well.

The 'A' counts are 'actual' counts, from the audit.

The 'R' counts are 'reported' counts, from the initial
optical scans.

The 'P' counts are the 'prior' (pseudo)-counts, for the
Bayesian modeling.

For the 'R' counts, the av values are taken to be equal
to the rv values, if those are present. ???

Note that different subtrees can have different structure:
one pbcid can be CVR and one noCVR.
EXPLAIN MORE HERE.

The A values are likely to be small, since they are from
the sample.

The R values are large, should sum to values seen in the
ballot manifest.

T.getR((),av) gives the reported vote total for candidate av.
"""
