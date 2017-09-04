# multi.py
# Ronald L. Rivest
# (with help from Karim Husayn Karimi and Neal McBurnett)
# July 27, 2017

# python3
# clean up with autopep8
#   autopep8 -i multi.py
#   (updates in place; see https://github.com/hhatto/autopep8)

"""
Prototype code for auditing an election having both multiple contests and
multiple paper ballot collections (e.g. multiple jurisdictions).
Possibly relevant to Colorado state-wide post-election audits in Nov 2017.

Some documentation for this code can be found here:
    https://github.com/ron-rivest/2017-bayes-audit.git
    in the 2017-code README.md
"""

""" 
This code corresponds to the what Audit Central needs to do, although
it could also be run locally in a county.
"""

# MIT License

import datetime
import json
import numpy as np
import os
import sys

import audit
import cli
import election_spec
import outcomes
import planner
import reported
import snapshot
import utils

##############################################################################
# Elections
##############################################################################

ELECTIONS_ROOT = "./elections"


class Election(object):

    """
    All relevant attributes of an election and an audit are stored within 
    an Election object.

    For compatibility with json, an Election object should be viewed as 
    the root of a tree of dicts, where all keys are strings, and the leaves are
    strings or numbers, or lists of strings or numbers.

    In comments: 
       dicts: an object of type "cids->int" is a dict mapping cids to ints,
                and an object of type "cids->pcbids->selids->int" is a nested 
                set of dicts, the top level keyed by a cid, and so on.
       lists: an object of type [bids] is a list of ballot ids.

    Glossary:

        cid    a contest id (e.g. "Den-Mayor")

        gid    a contest group id (e.g. "FEDERAL")

        pbcid  a paper-ballot collection id (e.g. "Den-P24")

        bid    a ballot id (e.g. "Den-12-234")
               This should be unique within a pbc.

        selid  a selection id (e.g. "Yes" or "JohnSmith"). A string.
               If it begins with a "+", it denotes a write-in (e.g. "+BobJones")
               If it begins with a "-", it denotes an error (e.g. "-Invalid" or
               "-NoSuchContest" or "-noCVR").  Errors for overvotes and undervotes
               are indicated in another way.  Each selid naively corresponds to
               one bubble filled in on an optical scan ballot.  If a ballot doesn't
               contain a contest, its reported vote (from the scanner) and its
               actual vote (from the audit) will be (-NoSuchContest).  (See the
               next paragraph about votes.)

        vote   a tuple of selids, e.g. ("AliceJones", "BobSmith", "+LizardPeople").
               An empty vote (e.g. () ) is an undervote (for plurality).
               A vote with more than one selid is an overvote (for plurality).
               The order may matter; for preferential voting a vote of the form
               ("AliceJones", "BobSmith", "+LizardPeople") indicates that Alice
               is the voter's first choice, Bob the second, etc.               



    It is recommended (but not required) that ids not contain anything but
             A-Z   a-z   0-9  -   _   .   +
    and perhaps whitespace.
    """

    def __init__(self):

        e = self

        # *** Notation

        # We use nested dictionaries extensively.
        # variables may be named e.de_xyz
        # where x, y, z give argument type
        # (and there may be one or more of these):

        # c = contest id (cid)
        # g = contest group id (gid)
        # p = paper ballot collection id (pbcid)
        # r = reported vote (rv)
        # a = actual vote (av)
        # b = ballot id (bid)
        # t = audit stage_time (time audit started, used as stage id)
        # m = risk measurement id (mid) from audit_parameters_contest

        # and where de may be something like:
        # rn = reported number (from initial scan)
        # sn = sample number (from given sample stage)
        # but may be something else.
        #
        # Example:
        # e.rn_cr = reported number of votes by contest
        # and reported vote r, e.g.
        # e.rn_cr[cid][r]  gives such a count.

        # *** Election specification

        # There is a standard directory ELECTIONS_ROOT where "all information
        # about elections is held", defaulting to "./elections".
        # This can be changed with a command-line option.

        # *** General

        e.election_dirname = ""
        # input (11-general.csv)
        # Dirname of election (e.g. "CO-Nov-2017")
        # Used as a directory name within the elections root dir.
        # so e.g. election data for CO-Nov-2017
        # is all in "./elections/CO-Nov-2017"

        e.election_name = ""
        # input (11-general.csv)
        # A human-readable name for the election, such as
        # "Colorado November 2017 General Election"

        e.election_date = ""
        # input (11-general.csv)
        # In ISO8601 format, e.g. "2017-11-07"

        e.election_url = ""
        # input (11-general.csv)
        # URL to find more information about the election

        # *** Contests

        e.cids = []
        # input (12-contests.csv)
        # list of contest ids (cids)
        # Order is important: contests will be printed in this order.

        e.contest_type_c = {}
        # input (12-contests.csv)
        # cid->contest type  (e.g. "plurality" or "irv")

        e.params_c = {}
        # input (12-contests.csv)
        # cid->int
        # additional parameters (such as number of winners in contest for plurality)

        e.write_ins_c = {}
        # input (12-contests.csv)
        # cid->str  (e.g. "no" or "qualified" or "arbitrary")

        e.selids_c = {}
        # input (from 12-contests.csv, reported votes, and audited votes)
        # cid->selids->True
        # dict of some possible selection ids (selids) for each cid
        # note that e.selids_c is used for both reported selections
        # (from votes in e.rv) and for actual selections (from votes in e.av)
        # it also increases when new selids starting with "+" or "-" are seen.

        # *** Contest groups

        e.gids = []
        # input (13-contest-groups.csv)
        # list of contest group ids (gids)

        e.cgids_g = {}
        # input (13-contest-groups.cs)
        # gid->[cgids]
        # e.cgids_g[gid] list of contest and/or group ids that
        # define contest group gid.

        e.cids_g = {}
        # computed from e.cgids_g
        # gid-> set of cids
        # e.cids_g[gid] is list of cids for given gid.
        # This is the expanded-out version of e.cgids_g[gid],
        # so all contest groups are replaced by their contest sets.

        # *** Collections

        e.pbcids = []
        # input (14-collections.csv)
        # list of paper ballot collection ids (pbcids)

        e.manager_p = {}
        # input (14-collections.csv)
        # pbcid->manager
        # Gives name and/or contact information for collection manager

        e.cvr_type_p = {}
        # input (14-collections.csv)
        # pbcid-> "CVR" or "noCVR"

        e.required_gid_p = {}
        e.possible_gid_p = {}
        # input (14-collections.csv)
        # pbcid->gid
        # e.required_gid_p[pbcid] is a contest group id for contests that *must* be on ballot.
        # e.possible_gid_p[pbcid] is a contest group id for contests that *may* be on ballot.
        #    The list of contest ids for the second gid must include all of those for the first.
        # The first gives a *lower bound* saying what contests must be present.
        # The second gives an *upper bound* saying what contests may be present.
        # If no gid is given (i.e. gid = ""), then any ballot style is allowed.
        # From collections file.

        e.required_cid_p = {}
        e.possible_cid_p = {}
        # Computed from e.required_gid_p and e.cids_g)
        # Computed from e.possible_gid_p and e.cids_g)
        # pbcid->cid->"True"
        # Necessary relevance; every ballot in pbcid must contain the cid.

        e.required_pbcid_c = {}
        e.possible_pbcid_c = {}
        # Computed from e.required_cid_p
        # Computed from e.possible_cid_p
        # cid->pbcid->"True"
        # Possible relevance; only relevant pbcids in e.possible_pbcid_c[cid]
        # True means the pbcid *might* contains ballots relevant to cid

        # *** election data (manifests, reported votes, and reported outcomes)

        # *** Ballot manifests

        e.bids_p = {}
        # input (21-reported-ballot-manifests/reported-ballot-manifest-PBCID.csv)
        # pbcid->[bids]
        # e.bids_p[pbcid] is list of ballot ids (bids) in that pbcid
        # from ballot manifest "Ballot id" column (as expanded for batches)
        # order is preserved from ballot manifest file.
        # No need for "Number of ballots" field (always implicitly 1 now).

        e.boxid_pb = {}
        # input (21-reported-ballot-manifests/reported-ballot-manifest-PBCIDcsv)
        # pbcid->bid->boxid
        # from ballot manifest "Box id" field

        e.position_pb = {}
        # input (21-reported-ballot-manifests/reported-ballot-manifest-PBCID.csv)
        # pbcid->bid->position (an int)
        # from ballot manifest "Position" field

        e.stamp_pb = {}
        # input (21-reported-ballot-manifests/reported-ballot-manifest-PBCID.csv)
        # pbcid->bid->stampt (a string)
        # from ballot manifest "Stamp" field (same as "imprint")

        # Note that the "Number of ballots" field of a ballot manifest
        # is not captured here; we assume that any rows in an input
        # manifest with "Number of ballots">1 is expanded into multiple rows
        # first.

        e.required_gid_pb = {}
        e.possible_gid_pb = {}
        # input (21-reported-ballot-manifests/reported-ballot-manifest-PBCID.csv)
        # pbcid->bid->gid
        # e.required_gid_pb[pbcid][bid] is a contest group id for contests that *must* be on ballot.
        # e.possible_gid_pb[pbcid][bid] is a contest group id for contests that *may* be on ballot.
        # The list of contest ids for the second gid must include all of those for the first.
        # The first gives a *lower bound* saying what contests must be present.
        # The second gives an *upper bound* saying what contests may be present.
        # If no gid is given (i.e. gid = ""), then any ballot style is allowed.
        # From ballot manifest.

        e.comments_pb = {}
        # input (21-reported-ballot-manifests/reported-ballot-manifest-PBCID.csv)
        # pbcid->bid->comments (string)
        # from ballot manifest "Comments" field

        # *** Reported votes

        e.rv_cpb = {}
        # input (22-reported-cvrs/reported-cvrs-PBCID.csv)
        # cid->pbcid->bid->vote
        # vote in given contest, paper ballot collection, and ballot id
        # e.rv_cpb is like e.av, but reported votes instead of actual votes

        e.votes_c = {}
        # input (from selids_c, reported votes, and actual otes)
        # cid->vote->True
        # e.votes_c[cid] gives all the distinct votes ever seen for cid,
        # reported or actual. (These are the different possible votes,
        # not the count.  So e.votes_c[cid] is the domain for tallies of
        # contest cid.)

        # Computed from the above

        e.rn_cpr = {}
        # Computed from e.rv_cpb
        # cid->pbcid->rvote->count
        # reported number of votes by contest, paper ballot collection,
        # and reported vote.

        e.rn_p = {}
        # Computed from e.rv_cpb
        # pbcid -> count
        # e.rn_p[pbcid] number ballots reported cast in collection pbcid

        e.rn_c = {}
        # Computed from e.rn_cpr.
        # cid->int
        # reported number of votes cast in contest
        # dict mapping cid to int (reported number of votes cast in contest)

        e.rn_cr = {}
        # Computed from e.rn_cpr.
        # cid->votes->int
        # reported number of votes for each reported vote in cid
        # dict mapping cid and reported vote to int (reported number)

        # *** Reported outcomes

        e.ro_c = {}
        # input (23-reported-outcomes.csv)
        # cid->outcome
        # reported outcome by contest
        # dict mapping cid to outcome (which is arbitrary hashable object)

        # *** Audit setup

        e.audit_seed = None
        # input (31-audit-spec/audit-spec-seed.csv)
        # seed for pseudo-random number generation for audit
        # string or int

        e.mids = []
        # input (31-audit-spec/audit-spec-contest.csv)
        # list of measurement ids (typically one per contest being audited)
        # list of strings

        e.cid_m = {}
        # input (31-audit-spec/audit-spec-contest.csv)
        # The contest being measured in a given measurement.
        # dict mapping mids to strings

        e.risk_method_m = {}
        # input (31-audit-spec/audit-spec-contest.csv)
        # mid->{"Bayes", "Frequentist"}
        # The risk-measurement method used for a given measurement.
        # Right now, the options are "Bayes" and "Frequentist", but this may
        # change.
        # dict mapping mids to strings

        e.risk_limit_m = {}
        # input (31-audit-spec/audit-spec-contest.csv)
        # mid->reals
        # risk limit for each measurement (from [0,1])
        # dict mapping mids to floats

        e.risk_upset_m = {}
        # input (31-audit-spec/audit-spec-contest.csv)
        # mid->reals
        # risk upset threshold for each measurement (from [0,1])
        # dict mapping mids to floats

        e.sampling_mode_m = {}
        # input (31-audit-spec/audit-spec-contest.csv)
        # mid->{"Active", "Opportunistic"}
        # dict mapping mids to strings

        e.initial_status_m = {}
        # initial status of test, should be one of
        #    "Open", "Off"
        # (Later they may change to "Passed" or "Upset" or "Exhausted".)
        # dict mapping mids to strings

        e.risk_measurement_parameters_m = {}
        # input (31-audit-spec/audit-spec-contest.csv)
        # additional parameters that may be needed by the risk measurement method
        # These are are represented as a *tuple* for each measurement.
        # dict mapping mids to tuples of strings

        e.max_audit_rate_p = {}
        # input (31-audit-spec/audit-spec-collection.csv)
        # pbcid->int
        # max number of ballots that can be audited per day in a pcb

        # *** Audit orders

        # TBD

        # *** Fixed audit parameters

        e.pseudocount_base = 0.5
        # Fixed parameter

        # base-level pseudocount (hyperparameter)
        # to use for Bayesian priors
        # (0.5 for Jeffrey's distribution)

        e.pseudocount_match = 50.0
        # Fixed parameter
        # hyperparameter for prior distribution to use
        # for components where reported_vote==actual_vote
        # This higher value reflects prior knowledge that
        # the scanners are expected to be quite accurate.

        e.n_trials = 100000
        # number of trials used to estimate risk in compute_contest_risk

        e.shuffled_indices_p = {}
        e.shuffled_bids_p = {}
        # computed in audit_orders.py (but probably will be replaced)
        # sampling order for bids of each pbcid

        # *** stage-related items
        # We don't give sequence numbers to stages; we just identify
        # them by their "stage_time" (when they started, as in
        # "2017-11-10-14-03-21" )

        e.stage_time = "0000-00-00-00-00-00"
        # Current audit stage time (in progress) or last stage completed.
        # Note that stage is a string representing a datetime string.
        # Stage time identifies the audit stage.

        e.max_stage_time = "9999-12-31-23-59-59"
        # maximum stage time (starting time) allowed for any audit
        # string

        # stage time input is stage time when value or file is computed
        # stage time is denoted t here

        e.status_tm = {}
        # mid->{"Open", "Passed", "Upset", "Exhasuted", "Off"}
        # status for a measurement for a given stage
        # dict mapping mids to strings

        e.plan_tp = {}
        # stage_time->pbcid->float
        # sample size wanted after next draw
        # note stage_time is time stage is computed, not stage
        # time when it will be effective.
        # dict mapping stage_time and pbcid to floats

        e.risk_tm = {}
        # stage_time->measurement->reals
        # risk = probability that e.ro_c[e.cid[mid]] is wrong
        # dict mapping stage_time and mid to floats

        e.election_status_t = {}
        # stage_time->list of measurement statuses, at most once each
        # dict mapping stage_time to string

        # sample info

        e.sn_tp = {}
        # stage_time->pbcid->ints
        # number of ballots sampled so far

        e.av_cpb = {}
        # cid->pbcid->bid->vote
        # (actual votes from sampled ballots)

        # computed from the above sample data

        e.sn_tcpra = {}
        # sampled number: stage_time->cid->pbcid->rvote->avote->count
        # first vote r is reported vote, second vote a is actual vote

        e.sn_tcpr = {}
        # sampled number stage_time->cid->pbcid->vote->count
        # sampled number by stage_time, contest, pbcid, and reported vote

        # *** saved-state ***
        # see saved-state.py
        e.saved_state = {}


def main():

    utils.myprint_switches = ["std"]   # [] to suppress printing

    print("multi.py -- Bayesian audit support program.")

    utils.start_datetime_string = utils.datetime_string()
    print("Starting date-time:", utils.start_datetime_string)

    args = cli.parse_args()
    e = Election()
    try:
        cli.process_args(e, args)
    finally:
        utils.close_myprint_files()


if __name__ == "__main__":
    main()
