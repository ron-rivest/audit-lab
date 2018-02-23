# election_spec.py
# Ronald L. Rivest (with Karim Husayn Karimi)
# August 2, 2017
# python3

"""
Routines to work with OpenAuditTool.py, to read in the
CSV files containing information about the specification
of an election.  They are in the directory
   1-election-spec
with filenames:
   election-spec-general.csv
   election-spec-contests.csv
   election-spec-contest-groups.csv
   elections-spec-collections.csv

They represent information with csv files of the form (examples):

election-spec-general.csv:
  Attribute        , Value                                   
  Election name    , Colorado general election               
  Election dirname , CO-2017-11-07,
  Election date    , 2017-11-07                              
  Election URL     , https://sos.co.gov/election/2017-11-07/ 

elections-spec-contests.csv:
   Contest         , Contest type , Params    ,Write-ins  , Selections 
   Denver Prop 1   , Plurality    ,           , No        , Yes        , No  
   Denver Prop 2   , Plurality    ,           , No        , Yes        , No   
   Denver Mayor    , Plurality    ,           , Qualified , John Smith , Bob Cat   , Mary Mee   ,+Jack Frost 
   Denver Clerk    , Plurality    ,           , No        , Yet Again  , New Guy
   Logan Mayor     , Plurality    ,           , Arbitrary , Susan Hat  , Barry Su  , Benton Liu 
   Logan Water     , Plurality    ,           , No        , Yes        , No
   U.S. President  , Plurality    ,           , Arbitrary , Don Brown  , Larry Pew
   U.S. Senate 1   , Plurality    ,           , Qualified , Deb O'Crat , Rhee Pub  , Val Green  , Sarah Day   , +Tom Cruz 
   U.S. Senate 2   , Plurality    ,           , Qualified , Term Three , Old Guy   , +Hot Stuff
   CO Prop A       , Plurality    ,           , No        , Yes        , No

election-spec-contest-groups.csv
   Contest group id , Contest(s) or group(s)
   FEDERAL          , U.S. President   , U.S. Senate 1        ,U.S. Senate 2
   STATE            , CO Prop A
   FED STATE        , FEDERAL          , STATE
   DENVER LOCAL     , Denver Mayor     , Denver Clerk, Denver Prop 1, Denver Prop 2
   DENVER           , FED STATE        , DENVER LOCAL
   LOGAN REQ        , FED STATE        , Logan Mayor 
   LOGAN POSS       , Logan Water

election-spec-collections.csv
Collection , Manager          , CVR type  , Required Contests, Possible Contests
DEN-A01    , abe@co.gov       , CVR       , DENVER,            DENVER
DEN-A02    , bob@co.gov       , CVR       , DENVER,            DENVER
LOG-B13    , carol@co.gov     , noCVR     , LOGAN REQ,         LOGAN POSS

The values are sanity checked, and put into the Election data structure (e)
from OpenAuditTool.py
"""

import logging
import os
import warnings

import OpenAuditTool
import csv_readers
import groups
import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_election_spec_general(e, election_dirname):
    """ 
    Read file 1-election-spec/election-spec-general.csv, put results into Election e.
    election_dirname is the name of the directory for the election 
        (e.g. "CO-2017-11") with ELECTIONS_ROOT
    """
    
    election_pathname = os.path.join(OpenAuditTool.ELECTIONS_ROOT, election_dirname)
    spec_pathname = os.path.join(election_pathname, "1-election-spec")
    filename = utils.greatest_name(spec_pathname, "election-spec-general", ".csv")
    file_pathname = os.path.join(spec_pathname, filename)
    fieldnames = ["Attribute", "Value"]
    rows = csv_readers.read_csv_file(file_pathname, fieldnames)
    for row in rows:
        if "Election name" == row["Attribute"]:
            e.election_name = row["Value"]
        elif "Election dirname" == row["Attribute"]:
            new_election_dirname = row["Value"]
            if new_election_dirname != election_dirname:
                warnings.warn("Inconsistent election_dirname {} ignored in file {}."
                              .format(new_election_dirname, file_pathname))
            else:
                pass # everything OK
        elif "Election date" == row["Attribute"]:
            e.election_date = row["Value"]
        elif "Election URL" == row["Attribute"]:
            e.election_url = row["Value"]
    for attribute in ["election_name", "election_dirname",
                      "election_date", "election_url"]:
        if attribute not in vars(e):
            warnings.warn("Attribute {} not present in 11-general.csv."
                          .format(attribute))


def test_read_election_spec_general(e):

    # logger.info("test_read_election_spec_general")
    read_election_spec_general(e, "ex1")


def read_election_spec_contests(e):
    """
    Read file election-spec-contests.csv, put results into Election e.
    """

    election_pathname = os.path.join(OpenAuditTool.ELECTIONS_ROOT, e.election_dirname)
    spec_pathname = os.path.join(election_pathname, "1-election-spec")
    filename = utils.greatest_name(spec_pathname, "election-spec-contests", ".csv")
    file_pathname = os.path.join(spec_pathname, filename)
    fieldnames = ["Contest", "Contest type", "Params", "Write-ins",
                  "Selections"]
    rows = csv_readers.read_csv_file(file_pathname, fieldnames, varlen=True)
    for row in rows:

        cid = row["Contest"]
        
        e.cids.append(cid)
        
        e.contest_type_c[cid] = row["Contest type"].lower()
        
        e.params_c[cid] = row["Params"]
        
        e.write_ins_c[cid] = row["Write-ins"].lower()

        e.selids_c[cid] = {}
        for selid in row["Selections"]:
            e.selids_c[cid][selid] = True


def test_read_election_spec_contests(e):

    # logger.info("test_read_election_spec_contests")
    read_election_spec_contests(e)


def read_election_spec_contest_groups(e):
    """
    Read file election-spec-contest-groups.csv, put results into Election e.
    """

    election_pathname = os.path.join(OpenAuditTool.ELECTIONS_ROOT, e.election_dirname)
    spec_pathname = os.path.join(election_pathname, "1-election-spec")
    filename = utils.greatest_name(spec_pathname, "election-spec-contest-groups", ".csv")
    file_pathname = os.path.join(spec_pathname, filename)
    fieldnames = ["Contest group", "Contest(s) or group(s)"]
    rows = csv_readers.read_csv_file(file_pathname, fieldnames, varlen=True)

    for row in rows:
        gid = row["Contest group"]
        if gid in e.cids:
            raise ValueError("Contest group id {} must not also be a contest id.".format(gid))
        e.gids.append(gid)
        e.cgids_g[gid] = row["Contest(s) or group(s)"]


def test_read_election_spec_contest_groups(e):    

    # logger.info("test_read_contest_groups")
    read_election_spec_contest_groups(e)


def read_election_spec_collections(e):
    """
    Read file 14-collections.csv, put results into Election e.
    """

    election_pathname = os.path.join(OpenAuditTool.ELECTIONS_ROOT, e.election_dirname)
    spec_pathname = os.path.join(election_pathname, "1-election-spec")
    filename = utils.greatest_name(spec_pathname, "election-spec-collections", ".csv")
    file_pathname = os.path.join(spec_pathname, filename)
    fieldnames = ["Collection", "Manager", "CVR type",
                  "Required Contests", "Possible Contests"]
    rows = csv_readers.read_csv_file(file_pathname, fieldnames, varlen=False)
    for row in rows:

        pbcid = row["Collection"]
        e.pbcids.append(pbcid)
        e.manager_p[pbcid] = row["Manager"]
        e.cvr_type_p[pbcid] = row["CVR type"]
        e.required_gid_p[pbcid] = row["Required Contests"]
        e.possible_gid_p[pbcid] = row["Possible Contests"]


def test_read_election_spec_collections(e):

    # logger.info("test_read_collections")
    read_election_spec_collections(e)


def read_election_spec(e):
    with warnings.catch_warnings(record=True) as w:
        read_election_spec_general(e, e.election_dirname)
        if len(w) > 0:
            raise RuntimeError("Too many errors; terminating.")
    read_election_spec_contests(e)
    read_election_spec_contest_groups(e)
    read_election_spec_collections(e)
    finish_election_spec(e)
    with warnings.catch_warnings(record=True) as w:
        check_election_spec(e)
        if len(w) > 0:
            raise RuntimeError("election_spec.check_election_spec: Too many errors or warnings; terminating.")
    show_election_spec(e)


def finish_election_spec(e):

    finish_election_spec_contest_groups(e)
    finish_election_spec_votes(e)

    
def finish_election_spec_contest_groups(e):

    groups.expand_contest_group_defs(e)

    for pbcid in e.pbcids:
        e.possible_cid_p[pbcid] = {}
        e.required_cid_p[pbcid] = {}
    for cid in e.cids:
        e.possible_pbcid_c[cid] = {}
        e.required_pbcid_c[cid] = {}

    for pbcid in e.pbcids:
        req_gid = e.required_gid_p[pbcid]
        poss_gid = e.possible_gid_p[pbcid]
        for cid in e.cids:
            # "" req_gid means nothing is required.
            if req_gid!="" and cid in e.cids_g[req_gid]:
                utils.nested_set(e.required_cid_p, [pbcid, cid], "True")
                utils.nested_set(e.required_pbcid_c, [cid, pbcid], "True")
            # enforce that possible contests includes all contests
            # "" poss_gid means everything is possible
            if poss_gid=="" or cid in e.cids_g[poss_gid] or cid in e.cids_g[req_gid]:
                utils.nested_set(e.possible_cid_p, [pbcid, cid], "True")
                utils.nested_set(e.possible_pbcid_c, [cid, pbcid], "True")


def finish_election_spec_votes(e):

    noCVRvote = ("-noCVR",)
    for cid in e.cids:
        e.votes_c[cid] = {}
        for selid in e.selids_c[cid]:
            e.votes_c[cid][(selid,)] = True
    for pbcid in e.pbcids:
        if e.cvr_type_p[pbcid] == "noCVR":
            for cid in e.required_cid_p[pbcid]:
                e.votes_c[cid][noCVRvote] = True            


def check_id(id, check_for_whitespace=False):

    if not isinstance(id, str) or not id.isprintable():
        warnings.warn("id is not string or is not printable: {}".format(id))
    if check_for_whitespace:
        for c in id:
            if c.isspace():
                warnings.warn("id `id` contains whitespace.")
                break


def check_election_spec(e):

    if not isinstance(e.cids, (list, tuple, set)):
        raise ValueError("e.cids is not a set.")
    if len(e.cids) == 0:
        raise ValueError("e.cids is an empty list of contests.")
    for cid in e.cids:
        check_id(cid)

    if not isinstance(e.pbcids, (list, tuple)):
        raise ValueError("e.pbcids is not a list or a tuple.")
    if len(e.pbcids) == 0:
        raise ValueError("e.pbcids is an empty list of pbcids.")
    for pbcid in e.pbcids:
        check_id(pbcid)

    for cid in e.selids_c:
        if cid not in e.cids:
            raise ValueError("e.selids_c has a key `{}` not in e.cids.".format(cid))
        for selid in e.selids_c[cid]:
            check_id(selid)
    for cid in e.cids:
        if cid not in e.selids_c:
            warnings.warn("cid `{}` should be key in e.selids_c".format(cid))

    if not isinstance(e.cvr_type_p, dict):
        raise ValueError("e_cvr_type is not a dict.")
    for pbcid in e.cvr_type_p:
        if pbcid not in e.pbcids:
            warnings.warn("pbcid `{}` is not in e.pbcids".format(pbcid))
        if e.cvr_type_p[pbcid] not in ["CVR", "noCVR"]:
            warnings.warn("e.cvr_type_p[{}]==`{}` is not CVR or noCVR".format(pbcid, e.cvr_type_p[pbcid]))
    for pbcid in e.pbcids:
        if pbcid not in e.cvr_type_p:
            warnings.warn("pbcid `{}` not key in e.cvr_type_p.".format(pbcid))


def show_election_spec(e):
    logger.info("====== Election spec ======")
    logger.info("Election name: (e.election_name):")
    logger.info("    {}".format(e.election_name))
    logger.info("Election dirname (e.election_dirname):")
    logger.info("    {}".format(e.election_dirname))
    logger.info("Election date (e.election date):")
    logger.info("    {}".format(e.election_date))
    logger.info("Election URL (e.election_url):")
    logger.info("    {}".format(e.election_url))
    logger.info("Number of contests:")
    logger.info("    {}".format(len(e.cids)))
    logger.info("Contest ids with contest type, additional parameters, and write-ins mode")
    logger.info("(e.cids, e.contest_type_c, e.params_c, e.write_ins_c):")
    for cid in e.cids:
        logger.info("    {} ({}, {} winner(s), {} write-ins)"
                      .format(cid, e.contest_type_c[cid], e.params_c[cid], e.write_ins_c[cid]))
    logger.info("Valid selection ids for each cid (e.selids_c):")
    for cid in e.cids:
        logger.info("    {}: {}".format(cid, ", ".join(sorted(e.selids_c[cid]))))
    logger.info("Number of paper ballot collections:")
    logger.info("    {}".format(len(e.pbcids)))
    logger.info("Paper ballot collection ids (e.pbcids), CVR types (e.cvr_type_p), and managers (e.manager_p):")
    for pbcid in sorted(e.pbcids):
        logger.info("    {} ({}, Manager:{})"
                    .format(pbcid, e.cvr_type_p[pbcid], e.manager_p[pbcid]))
    logger.info("Required pbcids for each cid (e.required_pbcid_c):")
    for cid in e.cids:
        logger.info("    {}: {}".format(cid, ", ".join(sorted(e.required_pbcid_c[cid]))))
    logger.info("Possible pbcids for each cid (e.possible_pbcid_c):")
    for cid in e.cids:
        logger.info("    {}: {}".format(cid, ", ".join(sorted(e.possible_pbcid_c[cid]))))


def test():
    e = OpenAuditTool.Election()
    test_read_election_spec_general(e)
    test_read_election_spec_contests(e)
    test_read_election_spec_contest_groups(e)
    test_read_election_spec_collections(e)    


if __name__=="__main__":

    test()
