# risk_bayes.py
# Ronald L. Rivest (with Karim Husayn Karimi)
# August 11, 2017 (rev. April 4, 2018)
# python3

"""
Routines to compute Bayes risk for a contest, or for a set of contests.

Called by audit.py

This is designed to be compatible only with sampling by pbcid;
more elaborate sampling regimes, such as sampling by card number
(for multicard ballots) or by reported vote, are yet to be 
implemented, and may require a significant change to the code base.  
(Some thoughts, albeit primitive, are sketched in risk_bayes_2.py.)
"""

import copy
import logging
import numpy as np

import audit
import outcomes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

##############################################################################
# Probability distributions

# Gamma distribution
# https://docs.scipy.org/doc/numpy-1.11.0/reference/generated/numpy.random.gamma.html
# from numpy.random import gamma
# To generate random gamma variate with mean k:
# gamma(k)  or rs.gamma(k) where rs is a numpy.random.RandomState object
# This routine is used primarily to allow efficient generation of Dirichlet
# posterior distributions.


def gamma(k, rs=None):
    """ 
    Return sample from gamma distribution with mean k using random state rs.

    Differs from standard gamma distribution implementation
    in that that it allows k==0, and returns 0 in that case.
    Parameter rs, if present, is a numpy.random.RandomState object.
    """

    if rs == None:
        rs = audit.auditRandomState
    if k <= 0.0:
        return 0.0
    else:
        return rs.gamma(k)


# Dirichlet distribution

def dirichlet(tally):
    """ 
    Given tally dict mapping votes (tuples of selids) to counts, 
    return dict mapping those votes to elements of Dirichlet distribution sample on
    those votes, where tally values are used as Dirichlet hyperparameters.
    The values produced sum to one.

    Input:
        tally     dict mapping votes (tuples of selids) 
                  to counts (nonnegative reals, often ints, but not necessarily)

    Output:
        dir       dict mapping votes (tuples of selids) to reals (probabilities)
                  probabilities are real and sum to one.
                  The domain of dir is identical to the domain of tally.
    """

    # Use 'sorted' to make sure order of applying gamma is deterministic,
    # for reproducibility, since gamma is randomized.
    dir = {vote: gamma(tally[vote]) for vote in sorted(tally)}

    total = sum(dir.values())
    dir = {vote: dir[vote] / total for vote in dir}
    return dir


# Multinomial distribution

def multinomial(n, ps):
    """
    Given nonnegative value n (typically an int) and a dict ps of probabilities, 
    return sample of size n drawn according to multinomial distribution defined with the 
    given probabilities.

    This is similar to numpy.random.multinomial (which it uses), but
        -- its input (ps) is a dict rather than an array
           the input domain is a set of votes (tuples of selids) and
           the output range are probabilities.
        -- the output (freq) is a dict rather than an array, mapping
           votes (tuples of selids) to frequencies.  The domain of freq
           is equal to the domain of ps.  The values in freq are nonnegative
           and sum to n.
        -- The standard definition of a multinomial distribution only allows for
           sample sizes n that are integers, and only gives frequencies that
           are integers.  The current routine encompasses this as a special case:
           when n is an integer the frequencies are integers distributed according
           to the standard multinomial definition.

           But when n is not an integer, this routine still returns a 
           meaningful result (although there is no definition I could find in the
           literature for a multinomial distribution with non-integral values of n).
           This result is accomplished by adding, to each vote, the
           fractional part of n multiplied by the given probability for that vote.
           This extension ensures that risk_bayes will give reasonable results 
           even in situations (like, perhaps weighted STV voting) where votes are
           present with non-integral frequencies.  (This feature is not yet used.)

    Example:
           multinomial(100.5, {'A':0.6, 'B':0.4}) ==> {'A':70.3, 'B':30.2}

    """

    n_floor = int(n)
    n_frac = n - n_floor
    # Use 'sorted' here to ensure that computations are reproducible --
    # randomization happens in the same order each time.
    # (Such considerations deal with internals of np.random.multinomial...)
    votes_sorted = sorted(ps)
    ps_sorted = [ps[vote] for vote in votes_sorted]
    multinomial_freqs_sorted = np.random.multinomial(n_floor, ps_sorted)
    freq = {vote: vote_freq
            for (vote, vote_freq)
            in zip(votes_sorted, multinomial_freqs_sorted)}
    if n_frac>0:
        for vote in votes_sorted:
            freq[vote] += n_frac * ps[vote]
    return freq


##############################################################################
# Dict operations

def add_dicts(d1, d2):
    """ 
    Update d1 by adding in values found in d2.

    Input: d1   dict mapping votes to reals
           d2   dict mapping votes to reals
                domain(d2) need not be a subset of domain (d1);
                missing values in d1 are treated as 0.
    Output: None
            Has side effect of modifying values in d1.
    """

    for av in d2:
        d1[av] = d1.get(av, 0) + d2[av]


def compute_prior_pseudocounts(vs, rv, pseudocount_base, pseudocount_match):
    """
    Make pseudocounts dict.

    Input:  vs                 a list of votes (domain of prior)
            rv                 a particular vote (e.g. the reported vote)
            pseudocount_base   a prior pseudocount  (e.g. 0.5)
            pseudocount_match  a prior pseudocount  (e.g. 50.0)

    Output: prior_pseudocounts  a dict mapping votes to prior pseudocounts.

    Method: Each entry in dict is pseudocount_base, 
            except that for key rv we have pseudocount_match.

    Remark: This approach of having prior defined by exactly two
            pseudocounts is intended to allow prior to reflect 
            belief that scanners are largely accurate, by having
            pseudocount_match be large, while preserving symmetry 
            among kinds of errors, by having all other entries only
            equal to pseudocount_base.

            Note that vote rv does not need to be in vs, in which 
            case all entries are equal to pseudocount_base.
    """

    prior_pseudocounts = {}
    for av in vs:
        prior_pseudocounts[av] = (pseudocount_match if av==rv
                                  else pseudocount_base)
    return prior_pseudocounts
    

def draw_nonsample_tally(sample_tally, prior_pseudocounts, nonsample_size):
    """
    Draw from Bayesian posterior on nonsample tallies, given sample tally and prior.

    Input: sample_tally       a dict mapping votes to nonnegative reals
           prior_pseudocounts a dict mapping votes to nonnegative reals (pseudocounts)
           non_sample_size    a nonnegative integer

    Output: nonsample_tally   a dict mapping votes to nonnegative reals
    """

    tally = sample_tally.copy()
    add_dicts(tally, prior_pseudocounts)

    # Obtain Dirichlet probability distribution corresponding to
    # hyperparameters given in the tally, indexed by av
    dirichlet_dict = dirichlet(tally)

    # Get multinomial sample with given probability distribution
    # (This is Dirichlet-multinomial distribution, after all.)
    # This has little effect if nonsample_size is large, as it
    # often is.  But when nonsample_size is small, it can matter.
    # (By providing more variance.)
    # This also forces frequencies to be integer, assuming
    # nonsample_size is integer.
    nonsample_tally = multinomial(nonsample_size, dirichlet_dict)

    return nonsample_tally


##############################################################################
# Risk measurement (Bayes risk, or posterior lost)

def compute_risk(e, mid, sn_tcpra, trials=None):
    """ 
    Compute (estimate) Bayesian risk (chance that reported 
    outcome is wrong for contest e.cid_m[mid]).
    sn_tcpra is sampled number: stage_time->cid->pbcid->rvote->avote->count
    We take sn_tcpra here as argument rather than just use e.sn_tcpra so
    we can call compute_contest_risk with modified sample counts.
    (This option not yet used, but might be later, when optimizing
    workload.)
    Here sn_tcpra is identical in structure to (and may in fact be
    identical to) e.sn_tcpra.
    Here trials is the number of trials to run to obtain the desired
    precision in the risk estimate.

    This method is the heart of the Bayesian post-election audit method.
    But it could be replaced by a frequentist approach instead, at
    least for those outcome rules and mixes of collection types for
    which a frequentist method is known.

    The comparison and ballot-polling audits are blended here; the
    reported election data just records a ("-noCVR",) vote for the 
    reported vote in a noCVR paper ballot collection.

    This means that ballot-polling audits have a prior of pseudocount_base,
    while comparison audits have a prior of pseudocount_base for off-diagonal
    (non-equal reported and actual) vote pairs, but a prior of pseudocount_match
    for equal reported-vote and actual-vote pairs.

    Note also that for ballot-polling audits, the vote of ("-noCVR",) is part
    of e.votes_c[cid], so that the test tallies include an estimated tally for
    this vote.  This should be conservative, but might be something to be
    eliminated someday.
    """

    cid = e.cid_m[mid]
    wrong_outcome_count = 0
    if trials == None:
        trials = e.n_trials
    vs = e.votes_c[cid]
    for trial in range(trials):
        test_tally = {vote: 0 for vote in vs}
        for pbcid in sorted(e.possible_pbcid_c[cid]):
            # Draw from posterior for each paper ballot collection, sum over pbcids.
            # Stratify by reported vote rv within each pbcid.
            for rv in sorted(sn_tcpra[e.stage_time][cid][pbcid]):

                # Obtain stratum_size, sample_size, nonsample_size
                stratum_size = e.rn_cpr[cid][pbcid][rv]
                sample_size = sum([sn_tcpra[e.stage_time][cid][pbcid][rv][av]
                                   for av in sn_tcpra[e.stage_time][cid][pbcid][rv]])
                nonsample_size = stratum_size - sample_size     # need not be an int

                # Compute sample_tally as dict of count of votes per
                # av (actual vote) in this stratum sample, add to test_tally.
                sample_tally = sn_tcpra[e.stage_time][cid][pbcid][rv].copy()
                add_dicts(test_tally, sample_tally)

                # Add pseudocounts for prior
                prior_pseudocounts = \
                    compute_prior_pseudocounts(vs,
                                               rv,
                                               e.pseudocount_base,
                                               e.pseudocount_match)

                # Draw nonsample_tally from posterior, add it to test tally.
                nonsample_tally = draw_nonsample_tally(sample_tally,
                                                       prior_pseudocounts,
                                                       nonsample_size)
                add_dicts(test_tally, nonsample_tally)

        if e.ro_c[cid] != outcomes.compute_outcome(e, cid, test_tally):  
            wrong_outcome_count += 1

    risk = wrong_outcome_count / e.n_trials
    e.risk_tm[e.stage_time][mid] = risk
    return risk


def compute_risks(e, st, trials=None):
    """
    Compute risks via all measurement approaches, for current sample.
    """

    for mid in e.mids:
        compute_risk(e, mid, st, trials)


def compute_slack_p(e):
    """
    Return dictionary mapping pbcids to the amount by which 
    sample in that pbcid can be increased.
    """

    # sampling so far doesn't depend on mid, so just use first one.
    mid = e.mids[0]         
    cid = e.cid_m[mid]
    slack_p = {}
    for pbcid in e.pbcids:
        slack_p[pbcid] = 0
        for rv in e.rn_cpr[cid][pbcid]:
            slack_p[pbcid] += e.rn_cpr[cid][pbcid][rv]
            slack_p[pbcid] -= e.sn_tcpr[e.stage_time][cid][pbcid][rv]
    return slack_p

def compute_risk_with_tweak(e, mid, slack_p, tweak_p, trials):
    """
    Return computed risk for given mid 
    if sample sizes were tweaked (increased).

    Here tweak_p is a dict mapping pbcids to how much
    to increase sample size by in each pbcid.  We must have
        0 <= tweak_p[pbcid] <= slack_p[pbcid]
    for all pbcids.
    """

    for pbcid in e.pbcids:
        assert 0 <= tweak_p[pbcid] <= slack_p[pbcid]

    cid = e.cid_m[mid]

    # Compute sn_tcp, as it is not otherwise defined.
    # (Perhaps this should be computed elsewhere/earlier?)
    sn_tcp = {}
    sn_tcp[e.stage_time] = {}
    sn_tcp[e.stage_time][cid] = {}
    for pbcid in e.pbcids:
        sn_tcp[e.stage_time][cid][pbcid] = 0
        for rv in e.sn_tcpra[e.stage_time][cid][pbcid]:
            for av in e.sn_tcpra[e.stage_time][cid][pbcid][rv]:
                sn_tcp[e.stage_time][cid][pbcid] += \
                    e.sn_tcpra[e.stage_time][cid][pbcid][rv][av]

    # compute sn_tcpra as "tweaked" version of e.sn_tcpra
    sn_tcpra = copy.deepcopy(e.sn_tcpra)
    for pbcid in e.pbcids:
        for rv in sn_tcpra[e.stage_time][cid][pbcid]:
            for av in e.sn_tcpra[e.stage_time][cid][pbcid][rv]:
                sn_tcpra[e.stage_time][cid][pbcid][rv][av] += \
                    tweak_p[pbcid] * sn_tcpra[e.stage_time][cid][pbcid][rv][av] / \
                                     sn_tcp[e.stage_time][cid][pbcid]

    return compute_risk(e, mid, sn_tcpra, trials)


def compute_risks_with_tweak(e, slack_p, tweak_p, trials):
    """
    Compute bayes risks for *all* measurements for given 
    tweak_p (sample size increments per pbcid).
    Here slack_p[pbcid] gives the upper bound on the tweak_p
    (increment) size for pbcid.  So we must have
        0 <= tweak_p[pbcid] <= slack_p[pbcid]
    Returned value is a dict risk_m mapping mids to risk
    values (real numbers in the interval [0,1]).

    In one planning strategy, based on random walks in tweak space,
    the value of "trials" might always be equal to one.  In this
    case, risk_m[mid] is always 0 or 1.  This is OK.
    """

    risk_m = {}
    for mid in e.mids:
        risk_m[mid] = compute_risk_with_tweak(e,
                                              mid,
                                              slack_p,
                                              tweak_p,
                                              trials)
    return risk_m


def tweak_all(e, mid):   # unused ??
    """
    Test routine to try all possible tweaks.  That is,
    systematically vary each possible sample size.
    This was written as means of approximating gradient
    descent, which we might no longer do.
    Untested.
    """

    return   # because this routine is unused; a stub/wip

    risk = compute_risk(e, mid, e.sn_tcpra)
    logger.info("Risk (no change):", risk)
    slack_p = compute_slack_p(e)
    cid = e.cid_m[mid]
    tweak = 0.1

    # Compute sn_tcp, as it is not otherwise defined.
    # (Perhaps this should be computed elsewhere/earlier?)
    sn_tcp = {}
    sn_tcp[e.stage_time] = {}
    sn_tcp[e.stage_time][cid] = {}
    for pbcid in e.pbcids:
        sn_tcp[e.stage_time][cid][pbcid] = 0
        for rv in e.sn_tcpra[e.stage_time][cid][pbcid]:
            for av in e.sn_tcpra[e.stage_time][cid][pbcid][rv]:
                sn_tcp[e.stage_time][cid][pbcid] += \
                    e.sn_tcpra[e.stage_time][cid][pbcid][rv][av]

    for pbcid in e.pbcids:
        for rv in e.sn_tcpra[e.stage_time][cid][pbcid]:
            for av in e.sn_tcpra[e.stage_time][cid][pbcid][rv]:
                if sn_tcp[e.stage_time][cid][pbcid] > 0:
                    e.sn_tcpra[e.stage_time][cid][pbcid][rv][av] += \
                        min(100,                                                               
                            slack_p[pbcid] *\
                            e.sn_tcpra[e.stage_time][cid][pbcid][rv][av] / \
                            sn_tcp[e.stage_time][cid][pbcid])
        risk = compute_risk_with_tweak(e, mid, slack_p, tweak)
        logger.info("Risk (change {}):".format(pbcid),
              risk)
                                                                                    

if __name__ == "__main__":

    pass


