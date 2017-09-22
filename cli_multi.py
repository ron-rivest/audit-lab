# cli_multi.py
# Ronald L. Rivest
# July 22, 2017 (rev. September 21, 2017)
# python3

"""
Command-line parser and dispatch for multi.py
"""


import argparse


import multi
import election_spec
import ids
import audit
import reported


##############################################################################
# Command-line arguments

def parse_args():

    parser = argparse.ArgumentParser(description="""multi.py: A Bayesian post-election audit program for an
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

    args = parser.parse_args()
    # print("Command line arguments:", args)
    return args


def dispatch(e, args):

    e.election_dirname = ids.filename_safe(args.election_dirname)

    e.election_name = args.election_name

    multi.ELECTIONS_ROOT = args.elections_root

    if args.set_audit_seed != None:
        audit.set_audit_seed(e, args.set_audit_seed)

    if args.read_election_spec:
        print("read_election_spec")
        election_spec.read_election_spec(e)

    elif args.read_reported:
        print("read_reported")
        election_spec.read_election_spec(e)
        reported.read_reported(e)

    elif args.make_audit_orders:
        print("make_audit_orders")
        audit_orders.compute_audit_orders(e)

    elif args.read_audited:
        print("read_audited--NO-OP-TBD")

    elif args.audit:
        election_spec.read_election_spec(e)
        reported.read_reported(e)
        audit.audit(e, args)



