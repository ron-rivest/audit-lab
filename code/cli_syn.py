# cli_syn.py: Command-line arguments for syn.py

import argparse
import logging
import os
import shutil
import warnings

import ids
import OpenAuditTool
import syn1
import syn2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():

    parser = argparse.ArgumentParser(description=\
                                     ("syn.py: "
                                      "Generates synthetic elections for "
                                      "OpenAuditTool.py, a Bayesian post-election "
                                      "audit program for an election with "
                                      "multiple contests and multiple paper "
                                      "ballot collections."))

    # Mandatory argument: dirname

    parser.add_argument("election_dirname",
                        help=('The name of a subdirectory within the elections '
                              'root directory, where the output of this program '
                              'will be placed.  '
                              'A parameter value of "" gets the default '
                              'of TestElection followed by datetime.  '
                              'A file with name foo.csv within subdirectory syn2_specs '
                              'gives the synthetic election specification for '
                              'syn_type 2, where foo is the election_dirname.  '))

    # All others are optional

    parser.add_argument("--syn_type",
                        help="Type of synthetic election. (1 or 2)",
                        default='1')

    args = parser.parse_args()
    return args




def dispatch(e, args):

    e.election_dirname = ids.filename_safe(args.election_dirname)
    e.election_name = e.election_dirname

    dirpath = os.path.join(OpenAuditTool.ELECTIONS_ROOT, e.election_dirname)

    if os.path.exists(dirpath):
        warnings.warn("Erasing previous contents of directory {}.".format(dirpath))
        subdirs = ["1-election-spec",
                   "2-reported",
                   "3-audit"]
        for subdir in subdirs:
            dirpathx = os.path.join(dirpath, subdir)
            if os.path.exists(dirpathx):
                shutil.rmtree(dirpathx)
                warnings.warn("Directory {} erased.".format(dirpathx))

    if args.syn_type == '1':
        syn1.generate_syn_type_1(e, args)
    elif args.syn_type == '2':
        syn2.generate_syn_type_2(e, args)
    else:
        logger.info("Illegal syn_type:", args.syn_type)

    logger.info("  Done. Synthetic election written to: %s", dirpath)

