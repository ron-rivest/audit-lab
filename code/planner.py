# planner.py
# Ronald L. Rivest (with Karim Husayn Karimi)
# August 1, 2017
# python3

"""
Routines to work with OpenAuditTool.py on post-election audits.
Specifically, to produce an "audit plan" for the next stage,
given what has been done already, and the results obtained
from the previous stage.
"""
import copy
import random

import outcomes
import risk_bayes


##############################################################################
# Compute audit plan for next stage

def update_correct(xs, pbcids_to_adjust, nonsample_sizes, num_winners, risk_limit):
    """
    Update how much to extend the county's sampling by.

    With probability 1 - (1-alpha)^(num_winners), we decrease the sampling since all
    the winners are correct. If not, keep the same value.
    """
    update = {}
    for pbcid in xs:
        if xs[pbcid] == 0:
            update[pbcid] = xs[pbcid]
        elif random.random() < 1-(1-risk_limit)**num_winners:
            update[pbcid] = (xs[pbcid]-1)
        else:
            update[pbcid] = (xs[pbcid])
    return update

def update_incorrect(xs, pbcids_to_adjust, nonsample_sizes, num_winners, risk_limit):
    """
    Update how much to extend the county's sampling by.

    With probability (1-alpha)^(num_winners), we increase the sampling since not all
    the winners are correct. If not, keep the same value.
    """

    update = {}
    for pbcid in xs:
        if xs[pbcid] == nonsample_sizes[pbcid]:
            update[pbcid] = (xs[pbcid])
        elif random.random() < (1-risk_limit)**num_winners:
            update[pbcid] = (xs[pbcid]+1)
        else:
            update[pbcid] = (xs[pbcid])
    return update

def random_naive(pbcids):
    """
    Randomly choose which county to extend the audit for.
    """
    return random.sample(pbcids, 1)[0]

def random_min_var(pbcids, actual_votes, xs, nonsample_sizes):
    """
    Choose the county to audit by choosing the county that minimizes the 
    variance for the estimated number of final votes for A in that county.

    This formula uses the normal approximation as seen in Rivest's estimation
    audit paper: in particular, we estimate the variance of n_a, using the formula
    (n^2*p_a*q_a) / (s-1).
    """
    best_pbcid, best_var = None, None
    for pbcid in actual_votes:
        candidate = list(actual_votes[pbcid].keys())[0]
        actual_sample_size = sum([actual_votes[pbcid][k] for k in actual_votes[pbcid]])
        new_unsampled = nonsample_sizes[pbcid] - xs[pbcid]
        # Is this reasonable? Currently not being triggered, since all counties have
        # 40 ballots sampled to start with.
        if actual_sample_size <= 1:
            return pbcid
        stratum_size = new_unsampled + actual_sample_size + xs[pbcid]
        frac_vote = float(actual_votes[pbcid][candidate]) / actual_sample_size
        # Extend fractional vote linearly
        var_before = (stratum_size**2 * frac_vote * (1.-frac_vote)) / (actual_sample_size + xs[pbcid] - 1)
        updated_sample_size = actual_sample_size + 1
        var_after = (stratum_size**2 * frac_vote * (1.-frac_vote)) / (updated_sample_size + xs[pbcid] - 1)
        if best_pbcid is None or (var_after - var_before) < best_var:
            best_pbcid = pbcid
            best_var = (var_after - var_before)
    return best_pbcid

def get_sample_size(e, pbcids_to_adjust, init_x=1, pick_pbcid_func=random_min_var):
    """
    Get sample size, for a given county, given how many ballots have been sampled before, and the number left
    to audit, as well as the required risk limit.
    """
    num_winners = e.num_winners
    max_num_it = e.max_num_it
    for mid in e.cid_m:
        cid = e.cid_m[mid]
        sample_tallies = {}
        nonsample_sizes = {}
        xs = {}

        actual_votes = {}

        # First, we create a dictionary of actual votes, where 
        # actual_votes maps a county to a dictionary of possible candidates
        # and actual_votes[county][candidate] gives the actual number of votes
        # that we have sampled for the candidate so far.
        for pbcid in pbcids_to_adjust:
            for possible_candidate in e.votes_c[cid]:
                if possible_candidate == ('-noCVR',):
                    continue
                for rv in e.sn_tcpra[e.stage_time][cid][pbcid]:
                    # create actual votes
                    if pbcid not in actual_votes:
                        actual_votes[pbcid] = {}
                    if possible_candidate not in actual_votes[pbcid]:
                        actual_votes[pbcid][possible_candidate] = 0
                    if possible_candidate in e.sn_tcpra[e.stage_time][cid][pbcid][rv]:
                        actual_votes[pbcid][possible_candidate] += (e.sn_tcpra[
                            e.stage_time][cid][pbcid][rv][possible_candidate])
            # Initialize the x's for a county to be init_x and keep track of the 
            # sample size and non-sample size for the county.
            xs[pbcid] = init_x
            stratum_size = e.rn_p[pbcid]
            sample_size = sum([actual_votes[pbcid][k] for k in actual_votes[pbcid]])
            nonsample_size = stratum_size - sample_size
            nonsample_sizes[pbcid] = nonsample_size

        # For max_num_it iterations, we first choose a county, then, we extend the county
        # by x. Then, given this extended sample, we use it to extend the entire contest to
        # n votes. We calculate the winner of the extended contest - if all the winners are
        # correct, then we update the x for that pbcid, by possibly decreasing it. If not,
        # with some probability, we increase x for that county.
        for i in range(max_num_it):
            current_sample = copy.deepcopy(actual_votes) # pbcid -> av -> count
            if pick_pbcid_func == random_min_var:
                pbcid = pick_pbcid_func(pbcids_to_adjust, actual_votes, xs, nonsample_sizes)
            else:
                pbcid = pick_pbcid_func(pbcids_to_adjust)
            for av in current_sample[pbcid]:
                if current_sample[pbcid][av] == 0:
                    current_sample[pbcid][av] += 50 # pseudocount
            dirichlet_dict = risk_bayes.dirichlet(current_sample[pbcid])
            extended_sample = risk_bayes.multinomial(xs[pbcid], dirichlet_dict)
            for av in current_sample[pbcid]:
                current_sample[pbcid][av] += extended_sample[av]

            for k, pbcid in enumerate(pbcids_to_adjust):
                dirichlet_dict = risk_bayes.dirichlet(current_sample[pbcid])
                extended_sample = risk_bayes.multinomial(nonsample_sizes[pbcid] - xs[pbcid], dirichlet_dict)
                for av in current_sample[pbcid]:
                    current_sample[pbcid][av] += extended_sample[av]

            merged_sample = {}
            for pbcid in pbcids_to_adjust:
                for av in current_sample[pbcid]:
                    if av not in merged_sample:
                        merged_sample[av] = 0
                    merged_sample[av] += current_sample[pbcid][av]

            winners = []
            for k in range(num_winners):
                winners.append(outcomes.compute_outcome(e, cid, merged_sample))
            if len(set(winners)) == 1 and winners[0] == e.ro_c[cid]:
                xs = update_correct(xs, [pbcid], nonsample_sizes, num_winners, e.risk_limit_m[mid])
            else:
                xs = update_incorrect(xs, [pbcid], nonsample_sizes, num_winners, e.risk_limit_m[mid])
    return xs

def compute_plan(e):
    """ 
    Compute a sampling plan for the next stage.
    Put in e.plan_tp[e.stage_time] a dict of target sample sizes 
    keyed by pbcid. 
    Only input is contest statuses, pbcid audit rates, pbcid current
    sample size, and pcbid size.
    """

    # for now, use simple strategy of looking at more ballots
    # only in those paper ballot collections that are still being audited
    e.plan_tp[e.stage_time] = e.sn_tp[e.stage_time].copy()
    pbcids_to_adjust = set()
    for mid in e.mids:
        cid = e.cid_m[mid]
        for pbcid in e.possible_pbcid_c[cid]:
            if e.status_tm[e.stage_time][mid] == "Open":
                pbcids_to_adjust.add(pbcid)
    for i, pbcid in enumerate(pbcids_to_adjust):
        # if contest still being audited do as much as you can without
        # exceeding size of paper ballot collection
        # CHECK: is e.rn_p[pbcid] right number to use here?

        # If this flag is not true, then we keep the sample size the same, for
        # each county, throughout the audit.
        if e.sample_by_size:
            sample_size = get_sample_size(e, list(pbcids_to_adjust))
            e.plan_tp[e.stage_time][pbcid] = \
                min(
                    e.sn_tp[e.stage_time][pbcid] + sample_size[pbcid],
                    e.rn_p[pbcid])
        else:
            e.plan_tp[e.stage_time][pbcid] = \
                min(
                    e.sn_tp[e.stage_time][pbcid] + e.max_audit_rate_p[pbcid],
                    e.rn_p[pbcid])
    return


