# test_scalability.py
# Ronald L. Rivest with Huasyn Karimi

import logging
import syn2
import time
import structure

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def tester(se):

    # copy code here from syn2.test; modify as needed
    se.seed = 9

    syn2.generate_election_structure(se)
    structure.finish_election_structure(se)
    syn2.generate_contests(se)
    syn2.generate_contest_groups(se)
    syn2.generate_collections(se)

    syn2.generate_reported(se)
    syn2.generate_ballot_manifest(se)

    syn2.generate_audited_votes(se)

    
    for key in sorted(vars(se)):
        logger.info(key)
        logger.info("    ", vars(se)[key])
    

    logger.info("Checking structure:", structure.check_election_structure(se))
    
    syn2.write_structure_csvs(se)
    syn2.write_reported(se)
    syn2.write_audit(se)

def scale_test(k):

    """
    For various values of k = 3, 4, ... 
    generate an election with
     10**k voters
     10**(k-3) pbcids
     10**(k-2) cids
     10 selids / cid
     """
    # start timer
    start = time.time() 

    # ... set parameters here based on k
    se = syn2.SynElection()
    se.min_n_bids_per_pbcid = 10**3
    se.max_n_bids_per_pbcid = 10**3
    se.n_pbcids = 10**(k-3)
    se.min_n_selids_per_cid = 10
    se.max_n_selids_per_cid = 10

    # run "test"
    tester(se) 

    # stop timer; print k and elapsed time
    end = time.time() 

    logger.info("For k=", k, ",", end-start, "seconds elapsed.")


for k in range(3, 8):
    scale_test(k)

    
    
