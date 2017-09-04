# write_csv.py
# Ronald L, Rivest
# August 5, 2017
# python3

"""
Routines for writing CSV files.

Part of the audit support package "multi.py";; see
    https://github.com/ron-rivest/2017-bayes-audit

"""


import os

import audit_orders
import ids
import multi
import utils


def write_election_spec_csv(e):

    write_election_spec_general_csv(e)
    write_election_spec_contests_csv(e)
    write_election_spec_contest_groups_csv(e)
    write_election_spec_collections_csv(e)


def write_election_spec_general_csv(e):

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "1-election-spec")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath,
                            "election-spec-general.csv")
    with open(filename, "w") as file:
        file.write("Attribute,Value\n")
        file.write("Election name,"+e.election_name+"\n")
        file.write("Election dirname,"+e.election_dirname+"\n")
        file.write("Election date,"+e.election_date+"\n")
        file.write("Election URL,"+e.election_url+"\n")


def write_election_spec_contests_csv(e):

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "1-election-spec")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath, "election-spec-contests.csv")

    with open(filename, "w") as file:
        fieldnames = ["Contest", "Contest type", "Params", "Write-ins", "Selections"]
        file.write(",".join(fieldnames))
        file.write("\n")
        for cid in e.cids:
            file.write(cid+",")
            file.write("{},".format(e.contest_type_c[cid].title()))
            file.write("{},".format(e.params_c[cid]))
            file.write("{},".format(e.write_ins_c[cid].title()))
            file.write(",".join(e.selids_c[cid]))
            file.write("\n")
        

def write_election_spec_contest_groups_csv(e):

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "1-election-spec")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath,
                            "election-spec-contest-groups.csv")

    with open(filename, "w") as file:
        fieldnames = ["Contest group", "Contest(s) or group(s)"]
        file.write(",".join(fieldnames))
        file.write("\n")
        for gid in e.gids:
            file.write(gid+",")
            file.write(",".join(sorted(e.cgids_g[gid])))
            file.write("\n")


def write_election_spec_collections_csv(e):

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "1-election-spec")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath,
                            "election-spec-collections.csv")

    with open(filename, "w") as file:
        fieldnames = ["Collection", "Manager", "CVR type",
                      "Required Contests", "Possible Contests"]
        file.write(",".join(fieldnames))
        file.write("\n")
        for pbcid in e.pbcids:
            file.write("{},".format(pbcid))
            file.write("{},".format(e.manager_p[pbcid]))
            file.write("{},".format(e.cvr_type_p[pbcid]))
            file.write("{},".format(e.required_gid_p[pbcid]))
            file.write("{}".format(e.possible_gid_p[pbcid]))
            file.write("\n")



def write_reported_csv(e):

    write_21_ballot_manifests_csv(e)
    write_22_reported_cvrs_csv(e)
    write_23_reported_outcomes_csv(e)


def write_21_ballot_manifests_csv(e):
                           
    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "2-reported",
                           "21-reported-ballot-manifests")
    os.makedirs(dirpath, exist_ok=True)

    for pbcid in e.pbcids:
        safe_pbcid = ids.filename_safe(pbcid)
        filename = os.path.join(dirpath, "manifest-"+safe_pbcid+".csv")
        with open(filename, "w") as file:
            fieldnames = ["Collection", "Box", "Position",
                          "Stamp", "Ballot id", "Number of ballots",
                          "Required Contests", "Possible Contests",
                          "Comments"]
            file.write(",".join(fieldnames))
            file.write("\n")
            for bid in e.bids_p[pbcid]:
                file.write("{},".format(pbcid))
                file.write("{},".format(e.boxid_pb[pbcid][bid]))
                file.write("{},".format(e.position_pb[pbcid][bid]))
                file.write("{},".format(e.stamp_pb[pbcid][bid]))
                file.write("{},".format(bid))
                file.write("1") # number of ballots
                file.write("{},".format(""))
                file.write("{},".format(""))
                # no comments
                file.write("\n")


def write_22_reported_cvrs_csv(e):

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "2-reported",
                           "22-reported-cvrs")
    os.makedirs(dirpath, exist_ok=True)

    scanner = "scanner1"
    for pbcid in e.pbcids:
        # handle cvr pbcids
        if e.cvr_type_p[pbcid]=="CVR": 
            safe_pbcid = ids.filename_safe(pbcid)
            filename = os.path.join(dirpath,
                                    "reported-cvrs-" + safe_pbcid+".csv")
            with open(filename, "w") as file:
                fieldnames = ["Collection", "Scanner", "Ballot id",
                              "Contest", "Selections"]
                file.write(",".join(fieldnames))
                file.write("\n")
                for bid in e.bids_p[pbcid]:
                    for cid in e.cids:
                        if cid in e.rv_cpb:
                            if bid in e.rv_cpb[cid][pbcid]:
                                vote = e.rv_cpb[cid][pbcid][bid]
                                file.write("{},".format(pbcid))
                                file.write("{},".format(scanner))
                                file.write("{},".format(bid))
                                file.write("{},".format(cid))
                                file.write(",".join(vote))
                                file.write("\n")
        # handle noCVR pbcids
        else:
            assert False, "FIX: add write-out of noCVR reported cvrs."


def write_23_reported_outcomes_csv(e):

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "2-reported")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath,
                            "23-reported-outcomes.csv")

    with open(filename, "w") as file:
        fieldnames = ["Contest", "Winner(s)"]
        file.write(",".join(fieldnames))
        file.write("\n")
        for cid in e.cids:
            file.write("{},".format(cid))
            file.write(",".join(e.ro_c[cid]))
            file.write("\n")


def write_audit_csv(e):

    write_31_audit_spec_csv(e)
    write_32_audit_orders_csv(e)
    write_33_audited_votes_csv(e)


def write_31_audit_spec_csv(e):

    write_audit_spec_global_csv(e)
    write_audit_spec_contest_csv(e)
    write_audit_spec_collection_csv(e)
    write_audit_spec_seed_csv(e)
    

def write_audit_spec_global_csv(e):

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "3-audit",
                           "31-audit-spec")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath,
                            "audit-spec-global-"+utils.start_datetime_string+".csv")
    with open(filename, "w") as file:
        fieldnames = ["Global Audit Parameter",
                      "Value"]
        file.write(",".join(fieldnames))
        file.write("\n")
        file.write("Max audit stage time,")
        file.write(e.max_stage_time)
        file.write("\n")


def write_audit_spec_contest_csv(e):

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "3-audit",
                           "31-audit-spec")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath,
                            "audit-spec-contest-"+utils.start_datetime_string+".csv")
    with open(filename, "w") as file:
        fieldnames = ["Measurement id",
                      "Contest",
                      "Risk Measurement Method",
                      "Risk Limit",
                      "Risk Upset Threshold",
                      "Sampling Mode",
                      "Initial Status",
                      "Param 1",
                      "Param 2"]
        file.write(",".join(fieldnames))
        file.write("\n")
        for mid in e.mids:
            file.write("{},".format(mid))
            file.write("{},".format(e.cid_m[mid]))
            file.write("{},".format(e.risk_method_m[mid]))
            file.write("{},".format(e.risk_limit_m[mid]))
            file.write("{},".format(e.risk_upset_m[mid]))
            file.write("{},".format(e.sampling_mode_m[mid]))
            file.write("{},".format(e.initial_status_m[mid]))
            params = ",".join(e.risk_measurement_parameters_m[mid])
            file.write("{}".format(params))
            file.write("\n")


def write_audit_spec_collection_csv(e):

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "3-audit",
                           "31-audit-spec")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath,
                            "audit-spec-collection-"+utils.start_datetime_string+".csv")
    with open(filename, "w") as file:
        fieldnames = ["Collection",
                      "Max audit rate"]
        file.write(",".join(fieldnames))
        file.write("\n")
        for pbcid in e.pbcids:
            file.write("{},".format(pbcid))
            file.write("{},".format(e.max_audit_rate_p[pbcid]))
            file.write("\n")


def write_audit_spec_seed_csv(e):
    """ Write 3-audit/31-audit-spec/audit-spec-seed.csv """

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "3-audit",
                           "31-audit-spec")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath,
                            "audit-spec-seed-"+utils.start_datetime_string+".csv")
    with open(filename, "w") as file:
        file.write("Audit seed\n")
        file.write("{}\n".format(e.audit_seed))


def write_32_audit_orders_csv(e):
    """ Write 3-audit/32-audit-orders/audit_orders-PBCID.csv """

    audit_orders.write_audit_orders(e)


def write_33_audited_votes_csv(e):
    """ Write 3-audit/33-audited-votes/audited-votes-PBCID.csv """

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "3-audit",
                           "33-audited-votes")
    os.makedirs(dirpath, exist_ok=True)

    pbcids = [pbcid for cid in e.av_cpb for pbcid in e.av_cpb[cid]]
    for pbcid in pbcids:
        safe_pbcid = ids.filename_safe(pbcid)
        filename = os.path.join(dirpath, "audited-votes-" + safe_pbcid+".csv")
        with open(filename, "w") as file:
            fieldnames = ["Collection", "Ballot id", "Contest", "Selections"]
            file.write(",".join(fieldnames))
            file.write("\n")
            for cid in e.av_cpb:
                if pbcid in e.av_cpb[cid]:
                    for bid in e.av_cpb[cid][pbcid]:
                        vote = e.av_cpb[cid][pbcid][bid]
                        file.write("{},".format(pbcid))
                        file.write("{},".format(bid))
                        file.write("{},".format(cid))
                        selections = ",".join(vote)
                        file.write("{}".format(selections))
                        file.write("\n")



def write_csv(e):

    write_election_spec_csv(e)
    write_reported_csv(e)
    write_audit_csv(e)
