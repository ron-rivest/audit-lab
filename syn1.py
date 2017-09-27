# syn1.py
# Ronald L. Rivest
# August 5, 2017
# python3

"""
Routines to generate synthetic elections of "type 1".
Called from syn.py.
"""

"""
e is of type multi.Election
synpar is an object of type syn.Syn_Parameters
"""

import copy
import logging
import numpy as np

import audit_orders
import election_spec
import outcomes
import reported
import syn
import utils
import csv_writers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


"""
Routines work with the following parameters (defaults in brackets):

    cids = # number of contests [2]
    n_cids_wrong = # number of contests with wrong reported outcome [0]
    min_n_selids_per_cid = minimum number of selids per contest [2]
    max_n_selids_per_cid = maximum number of selids per contest [5]
    n_pbcids = # number of pbcids [2]
    n_pbcids_nocvr = # number of collections with no CVRs [0]
    min_n_bids_per_pbcid = minimum number of bids per pbcid [10]
    max_n_bids_per_pbcid = maximum number of bids per pbcid [20]
    box_size = max number of ballots in a box [100]
    min_pbcids_per_cid = minimum number of pbcids per contest [1]
    max_pbcids_per_cid = maximum number of pbcids per contest [1]
    dropoff = rate at which votes drop off with selection (geometric) [0.9]
    error_rate = rate at which reported votes != actual votes [0.005]
    seed = random number seed (for reproducibility) [1]
    RandomState = state for random number generator

    ### following are then computed ###
    ### in e:
    cids = list of cids (of length n_cids)
    cids_wrong = list of cids that will have wrong output
    pbcids = list of pbcids (of length syn_n_pbcids)
    cvr_type_p = mapping of pbcid to "CVR" or "noCVR"
    ### in syn:
    n_bids_p = mapping from pbcid to number of bids in that pbcid
    
We fill in the values of the fields of election e as if they
had been read in, or else we (optionally) output the values as csv files.
"""

def default_parameters(synpar):

    synpar.n_cids = 2
    synpar.n_cids_wrong = 0
    synpar.min_n_selids_per_cid = 2
    synpar.max_n_selids_per_cid = 5
    synpar.n_pbcids = 2
    synpar.n_pbcids_nocvr = 0
    synpar.min_n_bids_per_pbcid = 200
    synpar.max_n_bids_per_pbcid = 200
    synpar.box_size = 100
    synpar.min_pbcids_per_cid = 1
    synpar.max_pbcids_per_cid = synpar.n_pbcids
    synpar.dropoff = 0.9
    synpar.error_rate = 0.005
    synpar.seed = 1
    synpar.RandomState = np.random.RandomState(synpar.seed)
    synpar.margin = 0.01

##############################################################################
## election specification

def generate_election_spec(e, synpar):
    """ 
    e = multi.Election()
    synpar = Syn_Params()
    synpar supplies additional paramters as noted above;
    add to e values that would be otherwise read in,
    e.g. via election_spec.py 
    (read_election_spec_general, 
     read_election_spec_contests,
     read_election_spec_contest_groups, 
     read_election_spec_collections)
    """

    generate_election_spec_general(e, synpar)
    generate_election_spec_contests(e, synpar)
    generate_election_spec_contest_groups(e, synpar)
    generate_election_spec_collections(e, synpar)
    election_spec.finish_election_spec(e)
    election_spec.check_election_spec(e)


def generate_election_spec_general(e, synpar):

    # reset syn.RandomState from synpar.seed
    synpar.RandomState = np.random.RandomState(synpar.seed)

    dts = utils.datetime_string()
    e.election_name = "TestElection-"+dts
    if e.election_dirname=="":
        e.election_dirname = "TestElection-"+dts
    e.election_date = dts                  
    e.election_url = "None"            


def generate_election_spec_contests(e, synpar):

    # check number of contests
    assert isinstance(synpar.n_cids, int) and synpar.n_cids >= 1
    # make cid for each contest
    e.cids = set("con{}".format(i+1) for i in range(synpar.n_cids))

    # generate contest types as plurality and additional parameters
    # no write-ins
    for cid in e.cids:
        e.contest_type_c[cid] = "plurality"
        e.params_c[cid] = ""
        e.write_ins_c[cid] = "no"

    # check number of cids with wrong reported outcome
    assert isinstance(synpar.n_cids_wrong, int)
    assert 0 <= synpar.n_cids_wrong <= synpar.n_cids
    # determine which, if any, cids have wrong reported outcome
    cids_list = list(e.cids)
    synpar.RandomState.shuffle(cids_list)    # in-place
    synpar.cids_wrong = cids_list[:synpar.n_cids_wrong]

    # generate selids for each cid
    e.n_selids_c = {}
    e.selids_c = {}
    for cid in e.cids:
        e.n_selids_c[cid] = syn.geospace_choice(e,
                                                synpar,
                                                synpar.min_n_selids_per_cid,
                                                synpar.max_n_selids_per_cid)

        e.selids_c[cid] = {"sel{}".format(i):True for i in range(1, e.n_selids_c[cid]+1)}

    # generate possible votes for each cid
    for cid in e.cids:
        if e.contest_type_c[cid] == "plurality":
            for selid in e.selids_c[cid]:
                utils.nested_set(e.votes_c, [cid, (selid,)], True)
        else:
            raise ValueError(("Contest {} is not plurality---"
                              "Can't generate votes for it.")
                              .format(cid))


def generate_election_spec_contest_groups(e, synpar):
    """ 
    Greate synpar.n_cids-1 'random' contest groups. 

    They get ids like 'gid2-6' meaning they cover cids 2 to 6 inclusive.
    """

    e.gids = []
    cids_list = sorted(list(e.cids))
    for (low, high) in syn.generate_segments(e, synpar, 1, synpar.n_cids):
        gid = "gid{}-{}".format(low, high)
        e.cgids_g[gid] = cids_list[low:high+1] 


def generate_election_spec_collections(e, synpar):

    # generate list of pbcids
    assert isinstance(synpar.n_pbcids, int) and synpar.n_pbcids >= 1
    e.pbcids = ["pbc{}".format(i) for i in range(1, synpar.n_pbcids+1)]

    # add managers
    for pbcid in e.pbcids:
        e.manager_p[pbcid] = "Nobody"

    # number of pbcids with no CVR
    assert isinstance(synpar.n_pbcids_nocvr, int) and \
        0 <= synpar.n_pbcids_nocvr <= synpar.n_pbcids

    # identify which pbcids have types CVR or noCVR
    e.cvr_type_p = {}
    while len(e.cvr_type_p) < synpar.n_pbcids_nocvr:
        e.cvr_type_p[synpar.RandomState.choice[e.pbcids]] = "noCVR"
    for pbcid in e.pbcids:
        if pbcid not in e.cvr_type_p:
            e.cvr_type_p[pbcid] = "CVR"

    # record randomly chosen required and possible contest groups for each pbcid
    for pbcid in e.pbcids:
        if len(e.gids)>0:
            e.required_gid_p[pbcid] = synpar.RandomState.choice(e.gids)
            e.possible_gid_p[pbcid] = synpar.RandomState.choice(e.gids)
        else:
            e.required_gid_p[pbcid] = ""
            e.possible_gid_p[pbcid] = ""

    election_spec.finish_election_spec_contest_groups(e)
    

##############################################################################
## reported results

def generate_reported(e, synpar):

    generate_n_bids_p(e, synpar)
    generate_bids_p(e, synpar)
    generate_cids_b(e, synpar)
    generate_rv_cpb(e, synpar)
    generate_reported_ballot_manifests(e, synpar)
    compute_reported_stats(e, synpar)


def generate_n_bids_p(e, synpar):
    """ Generate number of bids for each pbcid. """
    
    synpar.n_bids_p = {}
    for pbcid in e.pbcids:
        synpar.n_bids_p[pbcid] = syn.geospace_choice(e,
                                                     synpar,
                                                     synpar.min_n_bids_per_pbcid,
                                                     synpar.max_n_bids_per_pbcid)


def generate_bids_p(e, synpar):
    """ 
    Generate list of ballot ids for each pbcid: bid1, bid2, ...  .

    Note that these need only be unique within a pbcid, not globally.
    """

    synpar.n_bids = 0
    e.bids_p = {}
    for pbcid in e.pbcids:
        e.bids_p[pbcid] = []
        for i in range(synpar.n_bids_p[pbcid]):
            synpar.n_bids += 1
            bid = "bid{}".format(synpar.n_bids)
            e.bids_p[pbcid].append(bid)


def generate_cids_b(e, synpar):
    """
    Determine what contest(s) are on the ballot for each bid and pbcid 
    Determine if contest is CVR or not 
    draw from selection 

    Also sets: synpar.required_gid_b 
               synpar.possible_gid_b 

    Assumes we already have the bids that correspond to the given paper ballot 
    collections.  What we want to do is assign contests to those ballot 
    ids based on what contests are in the given pbcids as well as assign 
    selections based on the possible selections for each contest.
    """

    # synpar.cids_b
    synpar.cids_b = {}
    for pbcid in e.pbcids:
        synpar.required_gid_b = {}
        synpar.possible_gid_b = {}
        for bid in e.bids_p[pbcid]:
            if len(e.gids) > 0:
                synpar.required_gid_b[bid] = synpar.RandomState.choice(e.gids)
                synpar.possible_gid_b[bid] = synpar.RandomState.choice(e.gids)
                required_cids_b = set(e.cids_g[e.required_gid_b[bid]])
                possible_cids_b = set(e.cids_g[e.possible_gid_b[bid]])
            else:
                synpar.required_gid_b[bid] = ""     # means no contests required
                synpar.possible_gid_b[bid] = ""     # means any contest is possible
                required_cids_b = set()
                possible_cids_b = set(e.cids)

            # now determine cids for this ballot, i.e. synpar.cids_b[bid]
            synpar.cids_b[bid] = set()
            required_cids_p = set(e.required_cid_p[pbcid])
            required_cids = required_cids_p.union(required_cids_b)
            for cid in required_cids:
                synpar.cids_b[bid].add(cid)

            possible_cids_p = set(e.possible_cid_p[pbcid])
            possible_cids = possible_cids_p.intersection(possible_cids_b)
            for cid in possible_cids:
                if synpar.RandomState.choice([True, False]):
                    synpar.cids_b[bid].add(cid)

            synpar.cids_b[bid] = list(synpar.cids_b[bid])


def generate_rv_cpb(e, synpar):
    """ Generate the reported selection for each contest and ballot.

        That is, populate rv_cpb, by drawing from selids_c[cid] for each cid.
    """

    e.rv_cpb = {}
    for pbcid in e.pbcids:
        for bid in e.bids_p[pbcid]:
            for cid in synpar.cids_b[bid]:
                selids = list(e.selids_c[cid])
                if e.contest_type_c[cid] == 'plurality':
                    # give min(selids) an "edge" (expected margin) for winning
                    if synpar.RandomState.uniform() <= synpar.margin:
                        selection = min(selids)
                    else:
                        selection = synpar.RandomState.choice(selids)
                    rv = (selection,)
                    utils.nested_set(e.rv_cpb, [cid, pbcid, bid], rv)
                else:
                    # assume otherwise that vote is permutation of selids
                    # (This will need refinement later presumably.)
                    rv = list(selids)
                    synpar.RandomState.shuffle(rv)
                    utils.nested_set(e.rv_cpb, [cid, pbcid, bid], rv)
                    

def compute_reported_stats(e, synpar):

    reported.compute_rn_cpr(e)
    reported.compute_rn_c(e)
    reported.compute_rn_p(e)
    reported.compute_rn_cr(e)
    outcomes.compute_ro_c(e)


def generate_reported_ballot_manifests(e, synpar):
    """
    Generate synthetic ballot manifest data.

    This procedure must be run *after* generate_reported.
    """

    for pbcid in e.pbcids:
        for i, bid in enumerate(e.bids_p[pbcid]):
            boxid = 1+((i+1)//synpar.box_size)
            position = 1+(i%synpar.box_size)
            stamp = "stmp"+"{:06d}".format((i+1)*17)
            utils.nested_set(e.boxid_pb, [pbcid, bid], "box{}".format(boxid))
            utils.nested_set(e.position_pb, [pbcid, bid], position)
            utils.nested_set(e.stamp_pb, [pbcid, bid], stamp)
            utils.nested_set(e.required_gid_pb, [pbcid, bid], "")
            utils.nested_set(e.possible_gid_pb, [pbcid, bid], "")
            utils.nested_set(e.comments_pb, [pbcid, bid], "")


##############################################################################
## audit

def generate_audit(e, synpar):

    generate_audit_spec(e, synpar)
    generate_audit_orders(e, synpar)
    generate_audited_votes(e, synpar)

    # (audit stages will be generated by audit itself)


def generate_audit_spec(e, synpar):

    generate_audit_spec_global(e, synpar)
    generate_audit_spec_contest(e, synpar)
    generate_audit_spec_collection(e, synpar)
    generate_audit_spec_seed(e, synpar)


def generate_audit_spec_global(e, synpar):

    e.max_stage_time = "9999-12-31-23-59-59"


def generate_audit_spec_contest(e, synpar):

    # Generate one measurement per contest
    # Audit all contests

    for i, cid in enumerate(e.cids):
        mid = "M{}-{}".format(i, cid)
        e.mids.append(mid)
        e.cid_m[mid] = cid
        e.risk_method_m[mid] = "Bayes"
        e.risk_limit_m[mid] = 0.05
        e.risk_upset_m[mid] = 0.98
        e.sampling_mode_m[mid] = "Active"
        e.initial_status_m[mid] = "Open"
        e.risk_measurement_parameters_m[mid] = ()


def generate_audit_spec_collection(e, synpar):

    DEFAULT_MAX_AUDIT_RATE = 40
    for pbcid in e.pbcids:
        e.max_audit_rate_p[pbcid] = DEFAULT_MAX_AUDIT_RATE


def generate_audit_spec_seed(e, synpar):
    """ 
    Generate a pseudo-random audit_seed.

    Here audit_seed has limited range (2**32 possible values)
    but this is only for synthetic elections, so 
    this isn't so important.
    """

    e.audit_seed = synpar.RandomState.randint(0, 2**32-1)


def generate_audit_orders(e, synpar):

    audit_orders.compute_audit_orders(e)


def generate_audited_votes(e, synpar):

    e.av_cpb = {}
    for cid in e.rv_cpb:
        for pbcid in e.rv_cpb[cid]:
            for bid in e.rv_cpb[cid][pbcid]:
                rv = e.rv_cpb[cid][pbcid][bid]
                av = e.rv_cpb[cid][pbcid][bid]  # default no error
                if (synpar.RandomState.uniform() <= synpar.error_rate):
                    selids = list(e.selids_c[cid])     
                    if rv in selids and len(selids)>1:    
                        selids.remove(rv)
                    av = (synpar.RandomState.choice(selids),)
                utils.nested_set(e.av_cpb, [cid, pbcid, bid], av)


##############################################################################
##

def generate_syn_type_1(e, args):

    synpar = copy.copy(args)
    default_parameters(synpar)

    generate_election_spec(e, synpar)
    generate_reported(e, synpar)
    generate_audit(e, synpar)

    debug = False
    if debug:
        for key in sorted(vars(e)):
            logger.info(key)
            logger.info("    ", vars(e)[key])
    
    csv_writers.write_csv(e)


