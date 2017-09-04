# saved_state.py
# Ronald L. Rivest
# August 1, 2017
# Routines to save and restore some stage between audit stages.

import json
import os

import multi
import utils


def write_initial_saved_state(e):
    """
    Write the first saved-state, after the election-spec has been read."
    """

    initial_stage_time = "0000-00-00-00-00-00" # stage_time for initial saved-state

    e.sn_tp[initial_stage_time] = {}
    for pbcid in e.pbcids:
        # no sampling done yet
        e.sn_tp[initial_stage_time][pbcid] = 0      

    e.plan_tp[initial_stage_time] = {}
    for pbcid in e.pbcids:
        e.plan_tp[initial_stage_time][pbcid] = int(e.max_audit_rate_p[pbcid])

    e.status_tm[initial_stage_time] = {}
    for mid in e.mids:                                
        # initial contest state
        e.status_tm[initial_stage_time][mid] = e.initial_status_m[mid]

    ss = {}                 # saved state dict, to be written out

    ss["stage_time"] = initial_stage_time
    ss["sn_tp"] = e.sn_tp             # sample sizes, by stage and pbcid
    ss["status_tm"] = e.status_tm     # measurement statuses, by stage and mid
    ss["plan_tp"] = e.plan_tp         # plan for next stage of audit

    write_state(e, ss)


def write_intermediate_saved_state(e):
    """
    Write an intermediate saved-state, 
    after the election-spec has been read and the first audit stage done.
    """

    ss = {}                 # saved state dict, to be written out

    ss["stage_time"] = e.stage_time
    ss["sn_tp"] = e.sn_tp             # sample sizes, by stage and pbcid
    ss["status_tm"] = e.status_tm     # measurement statuses, by stage and mid
    ss["plan_tp"] = e.plan_tp         # plan for next stage of audit

    write_state(e, ss)


def write_state(e, ss):
    """ 
    Save some state to 3-audit/34-audit-output/audit-output-saved-state.json 

    Data ss saved is needed in the next audit stage.
    ss is a dict with the saved-state information, including
    the stage_time.
    """

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "3-audit",
                           "34-audit-output")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath,
                            "audit-output-saved-state-"+ss["stage_time"]+".json")

    with open(filename, "w") as file:
        json.dump(ss, file, indent=2)


def read_saved_state(e):
    """
    Read state from latest 3-audit/34-audit-output/audit-output-saved-state.json 
    """

    dirpath = os.path.join(multi.ELECTIONS_ROOT,
                           e.election_dirname,
                           "3-audit",
                           "34-audit-output")
    filename = utils.greatest_name(dirpath,
                                   "audit-output-saved-state",
                                   ".json")
    file_pathname = os.path.join(dirpath, filename)
    file = open(file_pathname, "r")

    e.saved_state = json.load(file)

    
if __name__ == "__main__":

    pass
