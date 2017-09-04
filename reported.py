# reported.py
# Ronald L. Rivest (with Karim Husayn Karimi)
# August 19, 2017
# python3

"""
Code that works with multi.py for post-election audit support.
This code reads and checks the "reported" results: votes
and reported outcomes.

The directory format is illustrated by this example from
README.md:

    2-reported
       21-reported-ballot-manifests
          reported-ballot-manifest-DEN-A01.csv
          reported-ballot-manifest-DEN-A01.csv
          reported-ballot-manifest-LOG-B13.csv
       22-reported-cvrs
          reported-cvrs-DEN-A01-2017-11-07.csv
          reported-cvrs-DEN-A02-2017-11-07.csv
          reported-cvrs-LOG-B13-2017-11-07.csv
       23-reported-outcomes-2017-11-07.csv

The 2-reported directory is a subdirectory of the main
directory for the election.

There are three file types here:
   reported-ballot-manifests
   reported-cvrs
   reported-outcomes

See associated file README for file formats.
"""


import os


import multi
import csv_readers
import ids
import utils


##############################################################################
# Election data I/O and validation (stuff that depends on cast votes)
##############################################################################


def read_reported(e):

    read_reported_ballot_manifests(e)
    read_reported_cvrs(e)
    read_reported_outcomes(e)
    
    finish_reported(e)
    check_reported(e)
    show_reported(e)


def read_reported_ballot_manifests(e):
    """
    Read ballot manifest file 21-reported-ballot-manifests and expand rows if needed.
    """

    election_pathname = os.path.join(multi.ELECTIONS_ROOT, e.election_dirname)
    specification_pathname = os.path.join(election_pathname,
                                          "2-reported",
                                          "21-reported-ballot-manifests")
    fieldnames = ["Collection", "Box", "Position", "Stamp", 
                  "Ballot id", "Number of ballots",
                  "Required Contests", "Possible Contests", "Comments"]
    for pbcid in e.pbcids:
        safe_pbcid = ids.filename_safe(pbcid)
        filename = utils.greatest_name(specification_pathname,
                                       "manifest-" + safe_pbcid,
                                       ".csv")
        file_pathname = os.path.join(specification_pathname, filename)
        rows = csv_readers.read_csv_file(file_pathname, fieldnames, varlen=False)
        for row in rows:
            pbcid = row["Collection"]
            boxid = row["Box"]
            position = row["Position"]
            stamp = row["Stamp"]
            bid = row["Ballot id"]
            try:
                num = int(row["Number of ballots"])
            except ValueError:
                utils.myerror("Number {} of ballots not an integer.".format(num))
            if num<=0:
                utils.mywarning("Number {} of ballots not positive.".format(num))
            req = row["Required Contests"]
            poss = row["Possible Contests"]
            comments = row["Comments"]

            bids = utils.count_on(bid, num)
            stamps = utils.count_on(stamp, num)
            positions = utils.count_on(position, num)

            for i in range(num):
                # utils.nested_set(e.bids_p, [pbcid, bids[i]], True)
                if pbcid not in e.bids_p:
                    e.bids_p[pbcid] = []
                e.bids_p[pbcid].append(bids[i])
                utils.nested_set(e.boxid_pb, [pbcid, bids[i]], boxid)
                utils.nested_set(e.position_pb, [pbcid, bids[i]], position[i])
                utils.nested_set(e.stamp_pb, [pbcid, bids[i]], stamps[i])
                utils.nested_set(e.required_gid_pb, [pbcid, bids[i]], req)
                utils.nested_set(e.possible_gid_pb, [pbcid, bids[i]], poss)
                utils.nested_set(e.comments_pb, [pbcid, bids[i]], comments)
                          

def read_reported_cvrs(e):
    """
    Read reported votes 22-reported-cvrs/reported-cvrs-PBCID.csv.
    """

    election_pathname = os.path.join(multi.ELECTIONS_ROOT, e.election_dirname)
    specification_pathname = os.path.join(election_pathname,
                                          "2-reported","22-reported-cvrs")
    fieldnames = ["Collection", "Scanner", "Ballot id",
                  "Contest", "Selections"]
    for pbcid in e.pbcids:
        safe_pbcid = ids.filename_safe(pbcid)
        filename = utils.greatest_name(specification_pathname,
                                       "reported-cvrs-" + safe_pbcid,
                                       ".csv")
        file_pathname = os.path.join(specification_pathname, filename)
        rows = csv_readers.read_csv_file(file_pathname, fieldnames, varlen=True)
        for row in rows:
            pbcid = row["Collection"]
            scanner = row["Scanner"]
            bid = row["Ballot id"]
            cid = row["Contest"]
            vote = row["Selections"]
            vote = tuple(sorted(vote))     # put vote selids into canonical order
            utils.nested_set(e.rv_cpb, [cid, pbcid, bid], vote)
            utils.nested_set(e.votes_c, [cid, vote], True)


def read_reported_outcomes(e):

    election_pathname = os.path.join(multi.ELECTIONS_ROOT, e.election_dirname)
    specification_pathname = os.path.join(election_pathname,
                                          "2-reported")
    fieldnames = ["Contest", "Winner(s)"]
    filename = utils.greatest_name(specification_pathname,
                                   "23-reported-outcomes",
                                   ".csv")
    file_pathname = os.path.join(specification_pathname, filename)
    rows = csv_readers.read_csv_file(file_pathname, fieldnames, varlen=True)
    for row in rows:
        cid = row["Contest"]
        winners = row["Winner(s)"]
        utils.nested_set(e.ro_c, [cid], winners)


def check_reported_selids(e):
    
    # make sure e.selids_c[cid] contains all +/- selids seen in reported votes
    # and that e.votes_c[cid] contains all reported votes
    for cid in e.cids:
        for pbcid in e.possible_pbcid_c[cid]:
            for bid in e.bids_p[pbcid]:
                if bid in e.rv_cpb[cid][pbcid]:
                    rv = e.rv_cpb[cid][pbcid][bid]
                else:
                    rv = ("-NoSuchContest",)
                utils.nested_set(e.votes_c, [cid, rv], True)
                for selid in rv:
                    if ids.is_writein(selid) or ids.is_error_selid(selid):
                        e.selids_c[cid][selid] = True

def compute_rn_cpr(e):
    """ Set e.rn_cpr[cid][pbcid][rv] to number in pbcid with reported vote rv. """

    for cid in e.cids:
        e.rn_cpr[cid] = {}
        for pbcid in e.possible_pbcid_c[cid]:
            e.rn_cpr[cid][pbcid] = {}
            for rv in e.votes_c[cid]:
                e.rn_cpr[cid][pbcid][rv] = len([bid for bid in e.bids_p[pbcid]
                                                if bid in e.rv_cpb[cid][pbcid] and \
                                                e.rv_cpb[cid][pbcid][bid] == rv])


def compute_rn_c(e):    
    """ 
    Compute e.rn_c[cid] as number of reported votes cast in contest cid. 

    (From e.rn_cpr)
    """
    
    for cid in e.cids:
        e.rn_c[cid] = sum([e.rn_cpr[cid][pbcid][rv]
                           for pbcid in e.rn_cpr[cid]
                           for rv in e.votes_c[cid]])


def compute_rn_p(e):
    """ Compute e.rn_p[pbcid] as number of reported votes cast in collection pbcid. """

    for pbcid in e.pbcids:
        e.rn_p[pbcid] = sum([e.rn_cpr[cid][pbcid][rv]
                             for cid in e.rn_cpr
                             for rv in e.votes_c[cid]])        


def compute_rn_cr(e):
    """ 
    Compute  e.rn_cr[cid][rv] as reported number cast for 
    reported vote rv in cid. 
    """
    
    for cid in e.cids:
        e.rn_cr[cid] = {}
        for pbcid in e.rn_cpr[cid]:
            for rv in e.votes_c[cid]:
                if rv not in e.rn_cr[cid]:
                    e.rn_cr[cid][rv] = 0
                if rv not in e.rn_cpr[cid][pbcid]:
                    e.rn_cpr[cid][pbcid][rv] = 0
                e.rn_cr[cid][rv] += e.rn_cpr[cid][pbcid][rv]


def finish_reported(e):
    """ 
    Compute election data attributes that are derivative from others. 
    or that need conversion (e.g. strings-->tuples from json keys).
    """

    check_reported_selids(e)

    compute_rn_cpr(e)
    compute_rn_c(e)    
    compute_rn_p(e)
    compute_rn_cr(e)


def check_reported(e):

    if not isinstance(e.rn_cpr, dict):
        utils.myerror("e.rn_cpr is not a dict.")
    for cid in e.rn_cpr:
        if cid not in e.cids:
            utils.mywarning("cid `{}` not in e.cids.".format(cid))
        for pbcid in e.rn_cpr[cid]:
            if pbcid not in e.pbcids:
                utils.mywarning("pbcid `{}` is not in e.pbcids.".format(pbcid))

    for cid in e.rn_cpr:
        for pbcid in e.rn_cpr[cid]:
            for rv in e.rn_cpr[cid][pbcid]:
                for selid in rv:
                    if selid not in e.selids_c[cid] and selid[0].isalnum():
                        utils.mywarning(
                            "selid `{}` is not in e.selids_c[{}]."
                            .format(selid, cid))

    for cid in e.rn_cpr:
        for pbcid in e.rn_cpr[cid]:
            for rv in e.rn_cpr[cid][pbcid]:
                if not isinstance(e.rn_cpr[cid][pbcid][rv], int):
                    utils.mywarning("value `e.rn_cpr[{}][{}][{}] = `{}` is not an integer."
                              .format(cid, pbcid, rv, e.rn_cpr[cid][pbcid][rv]))
                if not (0 <= e.rn_cpr[cid][pbcid][rv] <= e.rn_p[pbcid]):
                    utils.mywarning("value `e.rn_cpr[{}][{}][{}] = `{}` is out of range 0:{}."
                              .format(cid, pbcid, rv, e.rn_cpr[cid][pbcid][rv],
                                      e.rn_p[pbcid]))
                if not (0 <= e.rn_cpr[cid][pbcid][rv] <= e.rn_c[cid]):
                    utils.mywarning("value `e.rn_cpr[{}][{}][{}] = `{}` is out of range 0:{}."
                              .format(cid, pbcid, rv, e.rn_cpr[cid][pbcid][rv],
                                      e.rn_p[pbcid]))
    for cid in e.cids:
        for rv in e.votes_c[cid]:
            if e.rn_cr[cid][rv] != \
                sum([e.rn_cpr[cid][pbcid][rv] for pbcid in e.rn_cpr[cid]]):
                utils.mywarning("sum of e.rn_cpr[{}][*][{}] is not e.rn_cr[{}][{}]."
                              .format(cid, rv, cid, rv))

    for cid in e.cids:
        if cid not in e.rn_cpr:
            utils.mywarning("cid `{}` is not a key for e.rn_cpr".format(cid))
        for pbcid in e.possible_pbcid_c[cid]:
            if pbcid not in e.rn_cpr[cid]:
                utils.mywarning(
                    "pbcid {} is not a key for e.rn_cpr[{}].".format(pbcid, cid))
            # for selid in e.selids_c[cid]:
            #     assert selid in e.rn_cpr[cid][pbcid], (cid, pbcid, selid)
            # ## not necessary, since missing selids have assumed count of 0

    if not isinstance(e.rn_c, dict):
        utils.myerror("e.rn_c is not a dict.")
    for cid in e.rn_c:
        if cid not in e.cids:
            utils.mywarning("e.rn_c key `{}` is not in e.cids.".format(cid))
        if not isinstance(e.rn_c[cid], int):
            utils.mywarning("e.rn_c[{}] = {}  is not an integer.".format(
                cid, e.rn_c[cid]))
    for cid in e.cids:
        if cid not in e.rn_c:
            utils.mywarning("cid `{}` is not a key for e.rn_c".format(cid))

    if not isinstance(e.rn_cr, dict):
        utils.myerror("e.rn_cr is not a dict.")
    for cid in e.rn_cr:
        if cid not in e.cids:
            utils.mywarning("e.rn_cr key cid `{}` is not in e.cids".format(cid))
        for vote in e.rn_cr[cid]:
            for selid in vote:
                if (not ids.is_writein(selid) and not ids.is_error_selid(selid)) \
                   and not selid in e.selids_c[cid]:
                    utils.mywarning("e.rn_cr[{}] key `{}` is not in e.selids_c[{}]"
                              .format(cid, selid, cid))
            if not isinstance(e.rn_cr[cid][vote], int):
                utils.mywarning("e.rn_cr[{}][{}] = {} is not an integer."
                          .format(cid, vote, e.rn_cr[cid][vote]))
    for cid in e.cids:
        if cid not in e.rn_cr:
            utils.mywarning("cid `{}` is not a key for e.rn_cr".format(cid))

    if not isinstance(e.bids_p, dict):
        utils.myerror("e.bids_p is not a dict.")
    for pbcid in e.pbcids:
        # if not isinstance(e.bids_p[pbcid], dict):
        #     utils.myerror("e.bids_p[{}] is not a dict.".format(pbcid))
        if not isinstance(e.bids_p[pbcid], list):
            utils.myerror("e.bids_p[{}] is not a list.".format(pbcid))

    if not isinstance(e.rv_cpb, dict):
        utils.myerror("e.rv_cpb is not a dict.")
    for cid in e.rv_cpb:
        if cid not in e.cids:
            utils.mywarning("e.rv_cpb key `{}` is not in e.cids.".format(cid))
        for pbcid in e.rv_cpb[cid]:
            if pbcid not in e.pbcids:
                utils.mywarning("e.rv_cpb[{}] key `{}` is not in e.pbcids."
                          .format(cid, pbcid))
            if not isinstance(e.rv_cpb[cid][pbcid], dict):
                utils.myerror("e.rv_cpb[{}][{}] is not a dict.".format(cid, pbcid))
            bidsset = set(e.bids_p[pbcid])
            for bid in e.rv_cpb[cid][pbcid]:
                if bid not in bidsset:
                    utils.mywarning("bid `{}` from e.rv_cpb[{}][{}] is not in e.bids_p[{}]."
                              .format(bid, cid, pbcid, pbcid))
    for cid in e.cids:
        if cid not in e.rv_cpb:
            utils.mywarning("cid `{}` is not a key in e.rv_cpb.".format(cid))
        for pbcid in e.possible_pbcid_c[cid]:
            if pbcid not in e.rv_cpb[cid]:
                utils.mywarning(("pbcid `{}` from e.possible_pbcid_c[{}] "
                                 "is not a key for e.rv_cpb[{}].")
                                .format(pbcid, cid, cid))

    if not isinstance(e.ro_c, dict):
        utils.myerror("e.ro_c is not a dict.")
    for cid in e.ro_c:
        if cid not in e.cids:
            utils.mywarning("cid `{}` from e.rv_cpb is not in e.cids".format(cid))
    for cid in e.cids:
        if cid not in e.ro_c:
            utils.mywarning("cid `{}` is not a key for e.ro_c.".format(cid))

    if utils.warnings_given > 0:
        utils.myerror("Too many errors; terminating.")


def check_audited_votes(e):
    """
    old code; was in check_reported, but moved here temporarily
    """

    if not isinstance(e.av_cpb, dict):
        utils.myerror("e.av_cpb is not a dict.")
    for cid in e.av_cpb:
        if cid not in e.cids:
            utils.mywarning("e.av_cpb key {} is not in e.cids.".format(cid))
        for pbcid in e.av_cpb[cid]:
            if pbcid not in e.pbcids:
                utils.mywarning("e.av_cpb[{}] key `{}` is not in e.pbcids"
                          .format(cid, pbcid))
            if not isinstance(e.av_cpb[cid][pbcid], dict):
                utils.myerror("e.av_cpb[{}][{}] is not a dict.".format(cid, pbcid))
            bidsset = set(e.bids_p[pbcid])
            for bid in e.av_cpb[cid][pbcid]:
                if bid not in bidsset:
                    utils.mywarning("bid `{}` from e.av_cpb[{}][{}] is not in e.bids_p[{}]."
                              .format(bid, cid, pbcid, pbcid))

    for cid in e.cids:
        if cid not in e.av_cpb:
            utils.mywarning("cid `{}` is not a key for e.av_cpb.".format(cid))
        for pbcid in e.possible_pbcid_c[cid]:
            if pbcid not in e.av_cpb[cid]:
                utils.mywarning("pbcid `{}` is not in e.av_cpb[{}]."
                          .format(pbcid, cid))




def show_reported(e):

    utils.myprint("====== Reported election data ======")

    utils.myprint("Total reported votes for each vote by cid and pbcid (e.rn_cpr):")
    for cid in e.cids:
        for pbcid in sorted(e.possible_pbcid_c[cid]):
            utils.myprint("    {}.{}: ".format(cid, pbcid), end='')
            for vote in sorted(e.rn_cpr[cid][pbcid]):
                utils.myprint("{}:{} ".format(
                    vote, e.rn_cpr[cid][pbcid][vote]), end='')
            utils.myprint()

    utils.myprint("Total votes cast for each cid (e.rn_c):")
    for cid in e.cids:
        utils.myprint("    {}: {}".format(cid, e.rn_c[cid]))

    utils.myprint("Total cast for each vote for each cid (e.rn_cr):")
    for cid in e.cids:
        utils.myprint("    {}: ".format(cid), end='')
        for vote in sorted(e.rn_cr[cid]):
            utils.myprint("{}:{} ".format(vote, e.rn_cr[cid][vote]), end='')
        utils.myprint()

    utils.myprint("Reported outcome for each cid (e.ro_c):")
    for cid in e.cids:
        utils.myprint("    {}:{}".format(cid, e.ro_c[cid]))

