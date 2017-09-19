# syn2.py
# Ronald L. Rivest
# August 5, 2017
# python3

"""
Routines to generate synthetic elections of "type 2".
Called from syn.py.
In support of multi.py audit support program.
"""

import copy
import numpy as np
import os

import multi
import csv_readers
import audit_orders
import syn
import syn1
import utils
import csv_writers


def process_spec(e, synpar, L):
    """
    Initialize Election e according to spec in list L.

    Here e is of type multi.Election

    Here synpar is of type syn.Syn_Parameters

    Each item in L has the form:
        (cid, pbcid, rv, av, num)
    where 
        cid = contest id
        pbcid = paper ballot collection id
        rv = reported vote
             (may be ("-noCVR",) if pbcid is noCVR type
        av = actual vote
        num = number of ballots of this type
    Either or both of rv and av may be
        ("-NoSuchContest",)
        ("-Invalid",)
        or other such votes with selection ids starting with "-",
        signifying that they can't win the contest.
    The votes rv and av are arbitrary tuples, and may contain
    0, 1, 2, or more selection ids.
    """

    for (cid, pbcid, rv, av, num) in L:
        print("    ", cid, pbcid, rv, av, num)

        if cid not in e.cids:
            e.cids.append(cid)
            e.contest_type_c[cid] = "plurality"
            e.params_c[cid] = ""
            e.write_ins_c[cid] = "no"
            e.selids_c[cid] = {}
            e.ro_c[cid] = ("Alice",)     # FIX
            mid = "M{}-{}".format(len(e.cids), cid)
            e.mids.append(mid)
            e.cid_m[mid] = cid
            e.risk_method_m[mid] = "Bayes"
            e.risk_limit_m[mid] = 0.05
            e.risk_upset_m[mid] = 0.98
            e.sampling_mode_m[mid] = "Active"
            e.initial_status_m[mid] = "Open"
            e.risk_measurement_parameters_m[mid] = ("","")

        for selid in rv:
            if selid not in e.selids_c[cid]:
                e.selids_c[cid][selid] = True
        for selid in av:
            if selid not in e.selids_c[cid]:
                e.selids_c[cid][selid] = True

        if pbcid not in e.pbcids:
            e.pbcids.append(pbcid)
            e.manager_p[pbcid] = "Nobody"
            e.cvr_type_p[pbcid] = "CVR"
            e.required_gid_p[pbcid] = ""
            e.possible_gid_p[pbcid] = ""
            e.bids_p[pbcid] = []
            e.boxid_pb[pbcid] = {}
            e.position_pb[pbcid] = {}
            e.stamp_pb[pbcid] = {}
            e.max_audit_rate_p[pbcid] = 40
            e.comments_pb[pbcid] = {}

        for pos in range(1, int(num)+1):
            bid = "bid{}".format(1+len(e.bids_p[pbcid]))
            utils.nested_set(e.rv_cpb, [cid, pbcid, bid], rv)
            utils.nested_set(e.av_cpb, [cid, pbcid, bid], av)
            e.bids_p[pbcid].append(bid)
            e.boxid_pb[pbcid][bid] = "box1"
            e.position_pb[pbcid][bid] = pos
            e.stamp_pb[pbcid][bid] = ""
            e.comments_pb[pbcid][bid] = ""

def shuffle_votes(e, synpar):

    # shuffle rv, av lists
    for cid in e.rv_cpb:
        for pbcid in e.rv_cpb[cid]:
            # sorted need in following line for reproducible results
            bids = [bid for bid in sorted(e.rv_cpb[cid][pbcid])]
            L = [(e.rv_cpb[cid][pbcid][bid],
                  e.av_cpb[cid][pbcid][bid])
                 for bid in bids]
            synpar.RandomState.shuffle(L)           # in-place
            for i in range(len(bids)):
                bid = bids[i]
                (rv, av) = L[i]
                e.rv_cpb[cid][pbcid][bid] = rv
                e.av_cpb[cid][pbcid][bid] = av
    

##############################################################################
##

def read_syn2_csv(e, synpar):
    """ 
    Read file defining syn2 synthetic election spec. 
    """

    syn2_pathname = os.path.join(multi.ELECTIONS_ROOT, 
                                 "syn2_specs")
    filename = utils.greatest_name(syn2_pathname,
                                   synpar.election_dirname,
                                   ".csv")
    file_pathname = os.path.join(syn2_pathname, filename)
    fieldnames = ["Contest",
                  "Collection",
                  "Reported Vote",
                  "Actual Vote",
                  "Number"
                 ]
    rows = csv_readers.read_csv_file(file_pathname,
                                     fieldnames,
                                     varlen=False)
    return [(row["Contest"],
             row["Collection"],
             (row["Reported Vote"],),
             (row["Actual Vote"],),
             row["Number"])
            for row in rows]

# following test cases may be replaced by reading csv files
LCVR = [("cid1", "pbcid1", ("Alice",), ("Alice",), 3100),
        ("cid1", "pbcid1", ("Bob",), ("Bob",), 3000),
        ("cid1", "pbcid1", ("Alice",), ("Bob",), 3)
        # ("cid1", "pbcid2", ("Bob",), ("Bob",), 5)
       ]
LnoCVR = [("cid1", "pbcid1", ("-noCVR",), ("Alice",), 3100),
          ("cid1", "pbcid1", ("-noCVR",), ("Bob",), 3000),
          ("cid1", "pbcid1", ("-noCVR",), ("Bob",), 3)
          # ("cid1", "pbcid2", ("-noCVR",), ("Bob",), 5)
         ]

def generate_syn_type_2(e, args):

    synpar = copy.copy(args)
    rows = read_syn2_csv(e, synpar)
    process_spec(e, synpar, rows)
    e.audit_seed = 1
    synpar.RandomState = np.random.RandomState(e.audit_seed)
    shuffle_votes(e, synpar)
    audit_orders.compute_audit_orders(e)

    # generate_audit(e, synpar)

    debug = False
    if debug:
        for key in sorted(vars(e)):
            print(key)
            print("    ", vars(e)[key])

    csv_writers.write_csv(e)


