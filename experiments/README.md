# Experiments directory (within audit-lab)

This directory contains "experiments" that may be run within the
audit-lab.

Each such experiment lives in its own subdirectory; the name of
the subdirectory should begin with a date, e.g.

        2017-09-22-irv-test

or the like.

Within the subdirectory lives the top-level code for the experiment
and the results of running the experiment.

Such an experiment might be used to produce a figure, chart, or statistic
for a paper.

Note that for the top-level experiment code to import the audit-lab
code that is in the "grandparent" directory, the experiment code should
include something like

        import sys
        sys.path.append("../..")

before importing the desired audit-lab modules:

        import multi
        import utils
        ...




