# cli_OpenAuditTool.py
# Ronald L. Rivest
# July 22, 2017 (rev. September 21, 2017)
# python3

"""
Command-line parser and dispatch for OpenAuditTool.py
"""


import argparse
import logging

import audit_orders
import OpenAuditTool
import election_spec
import ids
import audit
import reported

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

##############################################################################
# Command-line arguments

def parse_args():

    parser = argparse.ArgumentParser(description="""OpenAuditTool.py: A Bayesian post-election audit program for an
            election with multiple contests and multiple paper ballot 
            collections.""")

    # Mandatory argument: dirname
    parser.add_argument("election_dirname", help="""
                        The name for this election of the subdirectory within the elections root directory.""")

    # All others are optional

    parser.add_argument("--election_name",
                        help="Human-readable name of the election.",
                        default="TestElection")

    parser.add_argument("--elections_root",
                        help=("The directory where the subdirectory for the"
                              "election is to be found.  Defaults to './elections'."),
                        default="./elections")

    parser.add_argument("--set_audit_seed",
                        help=("Seed for the random number generator used for"
                              "auditing (arbitrary nonnegative integer)."
                              "(If omitted, sets from file, else clock.)"))

    parser.add_argument("--read_election_spec",
                        action="store_true",
                        help="Read and check election spec.")

    parser.add_argument("--read_reported",
                        action="store_true",
                        help="Read and check reported election data and results.")


    parser.add_argument("--make_audit_orders",
                        action="store_true",
                        help="Make audit orders files.")

    parser.add_argument("--read_audited",
                        action="store_true",
                        help="Read and check audited votes.")

    parser.add_argument("--audit",
                        action="store_true",
                        help="Run audit based on current info.")

    parser.add_argument("--pause",
                        action="store_true",
                        help="Pause after each audit stage to obtain confirmation before proceedings.")

    parser.add_argument("--sample_by_size",
                        help="If true, then use sampling schemes, which use varying sample sizes on each"
                        " county, based on Dirichlet-Multinomial simulations.",
                        default=False)

    parser.add_argument("--num_winners",
                        help="When doing a sampling scheme with different sample sizes per county, "
                        "the number of winners required to consider a single "
                        "iteration as correct.",
                        default=2)
    parser.add_argument("--max_num_it",
                        help="When doing a sampling scheme with different sample "
                        "sizes per county, the number of iterations to run a random walk "
                        "to find how much to extend a county's sample by.",
                        default=100)

    args = parser.parse_args()
    return args


def dispatch(e, args):
    e.election_dirname = ids.filename_safe(args.election_dirname)

    e.election_name = args.election_name

    e.num_winners = int(args.num_winners)
    e.max_num_it = int(args.max_num_it)
    e.sample_by_size = args.sample_by_size

    OpenAuditTool.ELECTIONS_ROOT = args.elections_root

    if args.set_audit_seed != None:
        audit.set_audit_seed(e, args.set_audit_seed)

    if args.read_election_spec:
        logger.info("read_election_spec")
        election_spec.read_election_spec(e)

    elif args.read_reported:
        logger.info("read_reported")
        election_spec.read_election_spec(e)
        reported.read_reported(e)

    elif args.make_audit_orders:
        logger.info("make_audit_orders")
        audit_orders.compute_audit_orders(e)

    elif args.read_audited:
        logger.info("read_audited--NO-OP-TBD")

    elif args.audit:
        election_spec.read_election_spec(e)
        reported.read_reported(e)
        audit.audit(e, args)



