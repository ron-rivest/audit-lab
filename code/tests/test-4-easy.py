""" test-4-easy.py
    test for synthesizing (wtth syn2.py) and running audit on election '4-easy'.
"""

import sys
sys.path.append("../..")

import cli_syn
import cli_multi
import multi
import warnings


class Args(object):
    """ Class subclassed from object so we can hang attributes off of it.
    """
    pass


def test_4_easy():
    """ Generate election 4-easy using syn2 then run audit on it with multi.
    """
    with warnings.catch_warnings(record=True):
        # Generate election from object storing pseudo command-line arguments.
        e = multi.Election()
        syn_args = Args()
        syn_args.election_dirname = '4-easy'
        syn_args.syn_type = '2'
        cli_syn.dispatch(e, syn_args)

        # Audit election
        e = multi.Election()
        multi_args = Args()
        multi_args.election_dirname = '4-easy'
        multi_args.election_name = '4-easy'
        multi_args.elections_root = './elections'
        multi_args.set_audit_seed =  42
        multi_args.read_election_spec = False
        multi_args.read_reported = False
        multi_args.make_audit_orders = False
        multi_args.read_audited = False
        multi_args.audit = True
        multi_args.pause = False
        cli_multi.dispatch(e, multi_args)
