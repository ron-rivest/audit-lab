[![Build Status](https://travis-ci.org/evanlimanto/audit-lab.svg?branch=master)](https://travis-ci.org/evanlimanto/audit-lab)
[![Coverage Status](https://coveralls.io/repos/github/evanlimanto/audit-lab/badge.svg?branch=master)](https://coveralls.io/github/evanlimanto/audit-lab?branch=master)

Note: This repo "audit-lab" was created initially 2017-09-04
as a copy of
www.github.com/ron-rivest/2017-bayes-audit/2017-code
As of 2017-09-04, nothing else has been changed.  It is
just a copy.  This repo was initialized with the python code
this README, and some data files.  But it does not contain
the git history of how it got to this point.  If you are
interested in that, or more links on Bayesian audits,
see the original repo (which is public)
www.github.com/ron-rivest/2017-bayes-audit 

This repo will be used by students in a Fall 2017 UC Berkeley
course taught by Philip Stark.

Copied material starts here.

# Documentation for multi.py (Bayesian audit support program)

``multi.py`` is Python3 software (or suite of programs) to support
the post-election auditing of elections with multiple contests and
multiple separately-managed collections of paper ballots.

The software is designed to be helpful for auditing elections such as
the November 2017 Colorado election, which has hundreds of contests
spread across 64 counties.

**This README file is a *design document*, not a description of what
the code does yet.  The code here is still in progress  and only partially
implements this design.**

## Table of contents

* [Overview](#overview)
* [Election and audit](#election-and-audit)
* [Scanning of cast paper ballots](#scanning-of-cast-paper-ballots)
* [Auditing](#auditing)
* [Audit workflow](#audit-workflow)
  * [Pre-election](#pre-election)
  * [Election](#election)
  * [Audit](#audit)
  * [Setup audit](#setup-audit)
  * [Start audit](#start-audit)
* [Implementation notes: identifiers, votes, file names, and directory structure](#implementation-notes-identifiers-votes-file0names-and-directory-structure)
  * [Identifiers](#identifiers)
  * [Votes](#votes)
  * [File formats](#file-formats)
  * [Directory structure](#directory-structure)
* [(Pre-election) Election specification.](#pre-election-election-specification)
  * [Election specification general file](#election-specification-general-file)
  * [Contests file](#contests-file)
  * [Contest groups file](#contest-groups-file)
  * [Collections file](#collections-file)
* [Reported data (ballot manifests, CVRs and outcomes)](#reported-data-ballot-manifests-cvrs-and-outcomes)
  * [Reported ballot manifest files](#reported-ballot-manifest-files)
  * [Reported CVRs file](#reported-cvrs-file)
  * [Reported outcomes file](#reported-outcomes-file)
* [Audit details](#audit-details)
  * [Audit setup](#audit-setup)
    * [Global audit parameters](#global-audit-parameters)
    * [Contest audit parameters](#contest-audit-parameters)
    * [Collection audit parameters](#collection-audit-parameters)
    * [Audit seed file](#audit-seed-file)
  * [Dialogue between Audit Central and Collection Managers](#dialogue-between-audit-central-and-collection-managers)
    * [Audit order file](#audit-order-file)
    * [Audited votes](#audited-votes)
    * [Output file formats (per stage](#output-file-formats-per-stage)
      * [Audit snapshot file](#audit-snapshot-file)
      * [Audit output file(s)](#audit-output-file-s)
      * [Audit plan file](#audit-plan-file)
* [Command-line interface](#command-line-interface)
* [Appendix: File names](#appendix-file-names)
* [Appendix (Possible future work)](#appendix-possible-future-work)
  * [Compression](#compression)


## Overview 

The system described here is a collection of Python 3 modules
to support post-election audits, especially "risk-limiting" audits
of both the Bayesian and frequentist style.

On the one hand, this is an experimental platform designed to
facilitate research into post-election audits.  It is an "election
lab" (a term suggested by Philip Stark) that can be easily extended
or configured to run experiments.

On the other hand, we hope that the code will be robust, usable, and
scalable enough that it can be adapted or ported for use in real
post-election audits.

The code emphasizes the case (as in Colorado 2017) where there is
an Audit Central (run by the Secretary of State) coordinating audits
all across a state, where the paper ballots are in collections managed
by county-level election officials.  For contests that span several
counties, the audit needs to guide the relevant county-level election
officials regarding the random sampling of ballots from their collections,
to aggregate the resulting audit data, and to compute whether the desired
risk limits have been met.

The current design is "file-based": CSV (comma-separated values) format
files are used as the main interface data structure for all data, as
it is both human and machine readable, and commonly used in the election
community.

The code has the capability of generating large and complex "synthetic"
data sets for testing and experimental purposes.

Some of the planned experiments include:
* comparing different approaches for choosing Bayesian priors,
* comparing frequentist and Bayesian risk-limiting audit methods, and
* testing the scalability of the Bayesian approach.

[Back to TOC](#table-of-contents)


## Election and audit

We assume the following:
* a number of **contests** (for now, all plurality contests),
* a number of **voters**,
* a single **paper ballot** from each voter,
* paper ballots organized into a set of disjoint **collections**
      (for example, one or a few collections per county),
* a **collection manager** for each collection (may be the same
  manager for several collections),
* all ballots in a collection need not have the same **ballot style** (that is,
  they need not show the same contests on each ballot in the collection),
* for a given contest, there may be one or several collections having ballots
  showing that contest.

We assume that the election has the following phases:
1. ("_Pre-election_") Election specification and setup.
2. ("_Election_") Vote-casting, interpretation and preliminary reporting.
3. ("_Post-election_") Audit.
4. ("_Certification_") Certification.

[Back to TOC](#table-of-contents)


## Scanning of cast paper ballots

We assume that the paper ballots in each collection have been **scanned** by
an **optical scanner**.  There may be a different scanner for each collection.
There may even be several scanners used for a single collection.

We distinguish two types of collections, according to the type of information
produced by the scanner(s):
* in a "**CVR collection**", the scanner produces an electronic **cast vote
  record** (CVR) for each paper ballot scanned, giving the choices made for each
  contest on that paper ballot.
* in a "**noCVR collection**", the scanner does not produce a separate
  electronic record for each paper ballot scanned; it only produces a summary
  tally for the collection showing for each contest and each possible choice (vote) on that
  contest, how many ballots in the collection showed the given choice.

Note that some contests may be associated with collections of both types:
some CVR collections as well as some noCVR collections. It is an
interesting technical challenge to audit such contests efficiently.

We assume that the vote-casting, scanning, and subsequent storage
process yields a "**ballot manifest**" for each collection,
specifying how many paper ballots are in the collection, how they are
organized, and how they are stored.  The ballot manifest defines the
population of paper ballots in the collection that will be sampled
during the audit.

Some elections have so many contests that the ballot is comprised of
two or more separate "cards".  
We treat this situation in the same manner as having a collection
consisting of two or more "ballot styles."

[Back to TOC](#table-of-contents)

## Auditing

A post-election audit provides statistical assurance that the reported
outcomes are correct (if they are), using computations based on a small
random sample of the cast paper ballots.  Audits are often several
orders of magnitude more efficient than doing a full manual recount of
all cast paper ballots.

``Multi.py`` supports "Bayesian" audits, a form of post-election auditing
proposed by 
[Rivest and Shen (2012)](http://people.csail.mit.edu/rivest/pubs.html#RS12z).
It also supports "frequentist" risk-limiting audits, as explained by
[Lindeman and Stark (2012)](https://www.stat.berkeley.edu/~stark/Preprints/gentle12.pdf).
(Or will; this code isn't written yet.)
Our emphasis and strongest interest is in Bayesian audits, but the
``multi.py`` framework allows multiple approaches to co-exist and even
be used simultaneously.

A Bayesian audit provides an answer to the question:

> What is the probability that the reported election outcome is wrong?

We call this probability the **Bayesian risk** perceived for the reported
outcome, given the audit data.

A Bayesian audit continues to draw ballots at random for manual
examination and interpretation, until the estimated Bayesian risk
drops below a prespecified risk limit (such as 5%) for all contests
under audit.
With typical contests, only a small number of ballots may need to be
examined before the risk limit is reached and the audit stops.
Contests that are very close, however, may require extensive sampling
before their risk limits are reached.

See Rivest (''Bayesian audits: Explained and Extended'', draft
available from author) for an expanded discussion of Bayesian audits.

Bayesian risk-limiting audits are subtly different than the
"frequentist" risk-limiting audits promulgated by Lindeman and Stark
[Lindeman and Stark (2012)](https://www.stat.berkeley.edu/~stark/Preprints/gentle12.pdf).
Details omitted here, but Bayesian audits provide additional
capabilities and flexibility, at the cost of some additional (but
still very reasonable) computation during the audit.

We assume the existence of an **Audit Coordinator** who coordinates
the audit in collaboration with the collection managers.
The Coordinator might be from the Secretary of State's office; we
also call the Audit Coordinator by the name ``Audit Central``.

[Back to TOC](#table-of-contents)


## Audit workflow

This section describes the audit workflow, from the point of
view of the audit participants (AC coordinator, collection manager,
observer).

[Back to TOC](#table-of-contents)

### Pre-election

On the  Audit Central file system, 
the Audit Coordinator
creates a directory (folder) for
this election.  
This directory may be on a server that is publicly readable, but
only writable by Audit Central.

The Audit Coordinator gives the election specification in four files,
one for each of:

* **global parameters** (such as the name and date of the election)

* **contests** (describing the contests in this election)

* **contest groups** (giving some organization to the contests)

* **paper ballot collections** (saying how the paper ballots will be collected and organized).

These four files are put into the subdirectory:

    1-election-spec/

within the main directory for this election.

[Back to TOC](#table-of-contents)


### Election

After the polls have closed, and the paper ballots
have been scanned:

* Election officials organize the paper ballots in each collection, 
  and produce a ballot manifest for each collection describing how the
  paper ballots are stored (e.g. in boxes numbered a certain way).

* If the scanners produced a cast vote record for each
  ballot, collection managers (or the tabulation equipment)
  produce a "reported-cvrs" CSV file for each
  collection, having one row for each vote.
  Otherwise, they produce one file for each collection
  giving the tally of votes in that collection.

* Audit Central determines and publishes the 
  reported outcome for each contest.

  Audit Central puts this information into directories and files:

      2-reported/
        21-reported-ballot-manifests/
        22-reported-cvrs/
        23-reported-outcomes.csv


### Audit

* Audit Central produces an "audit specification" consisting of:

  * A file with any necessary **global** audit parameters.

  * A detailed list of **which contests will be
    audited**, and to **what risk limits**.  
    Each contest has a specified **initial status**,
    which will be updated as the audit progresses.

  * A **random audit seed**, which may have been produced by
    rolling twenty ten-sided dice at a public ceremony.

  * An initial "**audit order**" for each paper ballot
    collection, saying what randomly-chosen ballots should
    be audited first.

  * Audit Central puts this information into the following
    directories and files:

        3-audit/
           31-audit-spec/
              audit-spec-global.csv
              audit-spec-contest.csv
              audit-spec-collection.csv
              audit-spec-seed.csv
    
           32-audit-orders/
              audit-order-PBCID1.csv
              audit-order-PBCID2.csv
              ...

* Each collection manager begins auditing the
  ballots specified in his "audit order" file, and
  ships the results back to Audit Central, who
  stores them in the following directory:

        3-audit/
           33-audited-votes/
             audited-votes-PBCID1.csv
             audited-votes-PBCID2.csv
             ...

* Audit Central processes the received audited
  votes files, and frequently send back to each
  collection manager additional audit orders, as well as status
  reports on how each contest audit is progressing (including
  an estimate as to how much work remains to be done).  

  Audit Central announces when each contest has been
  sufficiently audited, and when the overall audit is complete.

  From a collection manager's point of view, the whole process
  is largely **asynchronous** with the operations of Audit Central.
  A collection manager can update
  her audited votes file whenever she is ready to do so.

  These updates do **not** need to be synchronized with the
  operations of Audit Central.
  (Note that each updated audited-votes
  file contains *all* of the audited votes from the collection;
  they are cumulative.) (For non-Bayesian risk measurement
  methods, the uploads may need to be synchronized.)

[Back to TOC](#table-of-contents)


## Implementation notes: identifiers, votes, file names, and directory structure

This section describes some low-level but essential details regarding
the use of identifiers in ``multi.py``, the way in which votes in a contest are
represented as a sets of identifiers, 
use of CSV file formats,
how transparency and reproducibility
are supported by the use of file names that include version labels, and
how ``multi.py`` structures information in a directory.

[Back to TOC](#table-of-contents)

### Identifiers

The data structures for ``multi.py`` use identifiers extensively.
Identifiers are more-or-less arbitrary strings of characters.

We have several types of identifiers:

* **Contest Identifiers** (example: ``**"DenverMayor"**``)
  A contest identifier may contain blanks or punctuation.
  A contest identifier is called a ``"cid"`` in the code.

* **Selection Identifiers** (examples: ``**"Yes"**`` or ``**"JohnSmith"**``)
  A selection identifier is called a ``"selid"`` in the code.
  **Roughly speaking, there should be one selection identifier for each
  optical scan bubble**.

  If bubble are arranged in a matrix, for
  preferential voting, then each selid should have the form
  ``**"rank-candidate"**``, as in ``**"1-Jones"**`` or ``**"2-Smith"**`` (for the
  first and second candidates preferred by the voter).

  For score voting or 3-2-1 voting, the selid should have the
  form ``**"score-candidate"**``, as in ``**"17-Smith"**`` or ``**"Excellent-Jones"**``.

  In other cases of bubbles arranged in a matrix, the
  selid should have the form ``**"rowid-columnid"**``.

  A **write-in** selection has a selection id beginning with a plus
  sign (example: ``**"+BobWhite"**``).

  Other potentially useful selection ids include the following.  Selection
  ids beginning with a minus sign are used to signal special conditions,
  and may not win a contest.  

    1. **``"-Unknown"``**: Nothing is known about the ballot. It might
       not even contain the desired contest.
    2. **``-NoSuchContest``**: The contest is missing from the ballot. Perhaps
       the wrong ballot was pulled, or the contest doesn't appear on every
       ballot in the paper ballot collection.
    3. **``-NoRecord``**: The ballot contains the desired contest, but
       the voter's selection was not recorded.  Perhaps useful if the
       desired contest is no longer being audited.
    4. **``-Invalid``**: The voter selections were invalid somehow.
    5. **``-NoBallot``**: The ballot doesn't exist.  Perhaps it only exists
       in electronic form.  (Suggested by Neal McBurnett, as NoVVPR)

* **Paper Ballot Collection Identifiers** (example: ``**"BoulderPBC25"**``)
  A paper ballot collection identifier is called a ``"pbcid"`` in the code.

* A **Ballot Identifier** is a unique identifier assigned to a particular
  paper ballot (example: ``**"25-72"**``).
  A ballot id is called a ``"bid"`` in the code.

  Ballots within a collection must have unique bids, but it is not
  necessary that ballots in different collections have different
  bids.

  A ballot id may encode the physical storage location of
  the ballot (e.g. the box number and position within box), but
  need not do so.  The ballot id might or might not include the
  pbcid. The ballot id might be generated when the ballot
  is printed, when it is scanned, or when it is stored.  The
  ballot ids need not be "sequential".

  (CO remark: A ballot id (or at least the ballot location) may consist of
  a four-tuple (TabulatorId, BatchId, RecordId, CountingGroupId).)

All identifiers are converted to "reduced" form when first encountered, by
removing any initial or final whitespace characters, and converting
any internal subsequence of two or more whitespace characters to a
single blank.

When an identifier (usually a paper ballot collection identifier)
is used as part of a filename, all characters in the identifier
other than

    A-Z   a-z   0-9  plus (+) hyphen(-) underscore(_)

are removed.

[Back to TOC](#table-of-contents)

### Votes

A **vote** is what is indicated by a voter on a paper ballot for a
particular contest.  A vote is a (possibly empty) **set** of selection
ids for a contest.

A vote is more specific than a ballot, as a ballot may contain
many contests.

On the other hand, a vote is a larger notion than a selection,
since the voter may indicate more than one selection for a
contest.  (Either by mistake, with an overvote, or intentionally
when it is allowed, as for approval voting.)

Thus, a vote is a **set** of selections.  Possibly empty,
possibly of size one, possibly of greater size.
With plurality voting, the set is of size one for
a valid selection, but it may be of size zero (an undervote)
or of size greater than one (an overvote).

Implementation note: Within Python, we represent a vote as a
tuple, such as

    ()               the empty set is represented by the length-zero tuple

    ("AliceJones",)  a vote with only one selection is represented by a length-one tuple

    ("AliceJones", "+BobSmith")  a vote with two or more selections is represented
                     by a tuple with two or more selection ids; in this example one of
                     the selections is a write-in for Bob Smith.

We use a Python tuple rather than a Python set, since the tuple
is hashable.  But the intent is to represent a set, not a sequence.
To that end, the default order of a vote is with the selids
sorted into increasing lexicographic order (as strings).

[Back to TOC](#table-of-contents)


### File formats

``Multi.py`` uses CSV (comma-separated values) format for files;
a single header row specifies the column labels, and each subsequent line of
the file specifies one spreadsheet row.  A compressed format is
suggested in the Appendix below (this is not yet implemented).

Files representing audited votes are intended to be **append-only**;
new data is added to the end, but previous data is never changed.

[Back to TOC](#table-of-contents)


###  Directory structure

The information for an election is kept in a single directory
structure in the public Audit Central election server, as documented
here.

Information for a different election would be kept in a separate
similar (but disjoint) directory structure.

Flexible version labels in file names are supported (but only 
occasionally illustrated here) here.
Typically a version label is a date-time stamp inserted just before
the final period, so that the filename
    ``election-spec-general.csv``
may become
    ``election-spec-general-2017-11-08-08-23-11.csv``
See [Appendix: File names](#appendix-file-names) for details of
version labels.

The top-level directory for a particular election
might be named something like
``./elections/CO-2017-general-election``.

The contents of that directory might look as follows.  Here PCBID1
etc.  would be the identifiers for paper ballot collections, such
as "DEN-A01".  In addition, all of these files would likely have
version labels that are date-time stamps, such as
"-2017-11-08-10-14-23".

    1-election-spec/
       election-spec-general.csv
       election-spec-contests.csv
       election-spec-contest-groups.csv
       election-spec-collections.csv

    2-reported/
       21-reported-ballot-manifests/
          reported-ballot-manifest-PCBID1.csv
          reported-ballot-manifest-PCBID2.csv
          ...
       22-reported-cvrs/
          reported-cvrs-PCBID1.csv
          reported-cvrs-PCBID2.csv
          ...
       23-reported-outcomes.csv

    3-audit/
       31-audit-spec/
          audit-spec-global.csv
          audit-spec-contest.csv
          audit-spec-collection.csv
          audit-spec-seed.csv
       32-audit-orders/
          audit-order-PCBID1.csv
          audit-order-PCBID2.csv
          ...
       33-audited-votes/
          audited-votes-PCBID1.csv
          audited-votes-PCBID2.csv
          ...
       34-audit-output/
          audit-output-contest-status.csv
          audit-output-collection-status.csv
          audit-output-snapshot.csv
          audit-output-detail.csv
          audit-output-plan.csv
          audit-output-saved-state.json

Once again: these files may have several **versions**, not shown
here, but distinguished by a datetime-stamp version labels as in

    audit-output-saved-state-2017-11-20-11-08-13.json

See [``Appendix: File names](#appendix-file-names) for details on version labels.
Generally, the latest version is the "operative" one.

[Back to TOC](#table-of-contents)


## (Pre-election) Election specification.

The election specification phase answers the questions:
* What contests are there?
* For each contest, what selections (choices) may the voter mark?
* For each contest, what **voting method** will be used to determine the
  outcome?
* How many collections of cast paper ballots will there be?
* For each such collection, who will be the collection manager?
* For each collection, which contests may be on the ballots in
  that collection?
* How will the paper ballots in each collection be scanned?
* For each collection, will it be a CVR collection or a noCVR
  collection?

Election officials answer these questions with four CSV files:
a "**general file**", 
a "**contests file**", 
a "**contest groups file**",
and a "**collections file**".  
These four
election-specification files may be produced from similar files used
by vendor-supplied equipment for the election itself.

[Back to TOC](#table-of-contents)


### Election specification general file

The election specification general file is a CSV file, prepared by
election officials, with the name

    1-election-spec/election-spec-general.csv

(possibly with a version label, such as a date-time stamp, as in

    1-election-spec/election-spec-general-2017-09-08-12-00-00.csv

See [``Appendix: File names](#appendix-file-names) for details on version labels.)

An election specification
**general file** gives a few high-level attributes of the election.

| Attribute         | Value                                   |
| ---               | ---                                     |
| Election name     | Colorado 2017 General Election          |
| Election dirname  | CO-2017-11-07                           |
| Election date     | 2017-11-07                              |
| Election URL      | https://sos.co.gov/election/2017-11-07/ |


The election dirname is the name of the directory where information
about this election is held.  This directory is within some
"standard directory where election information is held", such
as "./elections".  In this example, the election data is held
in the directory:

    ./elections/CO-2017-11-07

[Back to TOC](#table-of-contents)


### Contests file

The **election spec contests file**
is a CSV file, prepared by election officials, with the name

    1-election-spec/election-spec-contests.csv

(possibly with a version label).

Such a **contests file** specifies the contests
in the election, their type (e.g. plurality), 
any additional parameters the outcome rule may have
(such as, for a plurality contest, the number of winners if greater than one),
whether write-ins are allowed (and if so, whether they may be arbitrary, or whether
write-in candidates
must be pre-qualified), and the officially allowed selections
(which may be listed in any order).
If Params has more than one parameter, then they may be separated by
semicolons within the field.

| Contest         | Contest type | Params    |Write-ins  | Selections |           |            |            |
| ---             | ---          | ---       |---        | ---        | ---       |---         |---         |
| Denver Prop 1   | Plurality    |           | No        | Yes        | No  
| Denver Prop 2   | Plurality    |           | No        | Yes        | No   
| Denver Mayor    | Plurality    |           | Qualified | John Smith | Bob Cat   | Mary Mee   |+Jack Frost 
| Denver Clerk    | Plurality    |           | No        | Yet Again  | New Guy
| Logan Mayor     | Plurality    |           | Arbitrary | Susan Hat  | Barry Su  | Benton Liu 
| Logan Water     | Plurality    |           | No        | Yes        | No
| U.S. President  | Plurality    |           | Arbitrary | Don Brown  | Larry Pew
| U.S. Senate 1   | Plurality    |           | Qualified | Deb O'Crat | Rhee Pub  | Val Green  | +Tom Cruz 
| U.S. Senate 2   | Plurality    |           | Qualified | Term Three | Old Guy   | +Hot Stuff
| CO Prop A       | Plurality    |           | No        | Yes        | No


If the contest only allows write-ins that are (pre-)qualified, then those qualified
write-in names (with preceding "+" signs) are given on the contest row, but
not printed on the ballot.  Example: ``+Jack Frost`` for Denver Mayor
above.

Although plurality is the only contest type shown here, additional contest types,
such as IRV, will be supported as needed.

[Back to TOC](#table-of-contents)


### Contest groups file

A **contest groups specification file** has a file name of the form

    1-election-spec/election-spec-contest-groups.csv

(possibly with a version label).

Such a contest groups file specifies a number of **``contest groups``**
that may be used later to simplify the election specification.
Contest groups are used to generalize the familiar notion of a ``ballot style``.

A **contest group** has a name (id) and is defined as an (ordered) set
of contests.

A contest group id must not be the same as any contest id.
For clarity, we always write a contest group id in caps,
as in "**FEDERAL**" or "**STATEWIDE**", although this is not
required.

The ``multi.py`` program supports a generalization of the notion of
a "ballot style" (a set of contests that may occur on a ballot)
via the notion of "contest groups", and the notions of "required
contests" and "possible contests."

The use of contest groups may provide clarity, as it provides organization
for the set of contests.  In many places, one may specify a contest
group name instead of having to list all of its contests.  This provides
compactness.

A contest group is defined by listing the contests it contains and/or the
other groups it includes.

The *order* of the contests in the definition is important, as it may reflect the order
in which the contests are presented on a ballot; this order may be used
in the user interface used by the auditors.

| Contest group    | Contest(s) or group(s)  |               |                |                |         | 
| ---              | ---              | ---                  | ---            | ---            | ---     |
| FEDERAL          |U.S. President    |U.S. Senate 1         |U.S. Senate 2
| STATE            |CO Prop A
| FED STATE        |FEDERAL           |STATE
| DENVER LOCAL     |Denver Mayor      |Denver Clerk| Denver Prop 1| Denver Prop 2
| DENVER           |FED STATE         |DENVER LOCAL
| LOGAN REQ        |FED STATE         |Logan Mayor 
| LOGAN POSS       |Logan Water

In this example, ``FED STATE`` includes all of the contests in group
``FEDERAL``, plus (followed by) all contests in group ``STATE``.

For Logan county, this example define two contest groups: those that are required (``LOGAN REQ``),
and those that are possible (``LOGAN POSS``); the latter includes the former.  See
the [Collections file](#collections-file) section for an example of their use.

In other input files, a contest group name
may be used as shorthand for a set of alternative contests.
For example, one may specify a risk limit of five percent for all FEDERAL contests.

[Back to TOC](#table-of-contents)


### Collections file

A **collections specification file**, defined by election officials,
has a file name of the form

    1-election-spec/election-spec-collections.csv

(possibly with a version label).

Such a **collections file** specifies the various
collections of paper ballots, contact info for the collection
manager, collection type (CVR or noCVR),
contest groups specifying which contests are required and which are
possible for ballots in that collection.


| Collection    | Manager          | CVR type  | Required Contests  | Possible Contests |
| ---           | ---              | ---       | ---                | ---               |
| DEN-A01       | abe@co.gov       | CVR       | DENVER             | DENVER            |
| DEN-A02       | bob@co.gov       | CVR       | DENVER             | DENVER            |
| LOG-B13       | carol@co.gov     | noCVR     | LOGAN REQ          | LOGAN POSS        |


The possible ``ballot styles`` in a collection are constrained by the
``Required Contests`` and ``Possible Contests`` contest groups.  Every ballot in a collection
must contain every contest in the ``Required Contests`` contest group, and may contain any
contest in the ``Possible Contests`` contest group.  (Every required contest is automatically
a possible contest, so there is no need include the required contest group in the
definition of the possible contest group.)

In this example, every ballot in collection ``DEN-A01`` must contain all
and only those contests in the ``DENVER`` contest group.
The ballots in collection ``LOG-B13`` must contain every contest in
the ``LOGAN REQ`` contest group, and may contain any contest in the
``LOGAN POSS`` contest group.

If the ``Possible Contests`` contest group doesn't introduce any new
contests above and beyond what is already in the ``Required Contests``
group, then ballots in that collection have a common ballot style (set
of contests occurring on those ballots).

If a collection (as for mail-in ballots)
may hold ballots of several different ballot styles
styles, then the ``Required Contests`` field may show a contest group giving
the contests **common** to all possible ballots in the collection, while
the ``Possible Contests`` field may show a contest group listing the contests
that may occur on **any* ballot in the collection (that is, the union of
the possible ballot styles).

If the ``Required Contests`` field is empty, then no contest is required.
If the ``Possible Contests`` field is empty, then any contest is possible.

[Back to TOC](#table-of-contents)


## Reported data: (ballot manifests, CVRs, and outcomes)

When the election is run, paper ballots are cast and scanned.  The
electronic results are organized in "**reported (data) files**".
The paper ballots are organized into collections and stored.
A "**ballot manifest**" is produced for each paper ballot collection,
describing the collection and enabling random sampling from that
collection. 
A "**reported votes**" file lists the votes as reported by the scanner(s).
A "**reported outcomes**" file lists the reported
outcome for each contest.

[Back to TOC](#table-of-contents)

### Reported ballot manifest files

A ballot manifest file has a filename of the form

    21-reported-ballot-manifests/reported-ballot-manifest-PBCID.csv``

where PBCID is replaced with the paper ballot collection id (e.g. DEN-A01).
The file name may also include a version label.

Such a **``ballot manifest file``** lists all of the ballots in a given collection.

It should be produced in a trustworthy manner (e.g. manually by
election officials), as it is used to define the "sample space" for
the audit, and its accuracy is critical for the trustworthiness of the
audit.

Each ballot may be described explicitly, or, if some ballots are organized
into a batch (box) with sequential ballot ids, the first ballot id of the batch and
the number of ballots in the batch may be given.

The ballot manifest file indicates the physical location of each
ballot (giving a box id and position within box), any "stamp" or other
identification imprinted on the ballot, and any additional comments
about specific ballots.

The **``Collection``** field specifies the collection id for the ballot manifest.
This should the same for all rows in the ballot manifest file.

The **``Box``** field gives the box identifier for the box containing
the ballot(s) described in that row.  The box id should be unique
within the paper ballot collection.  If it is omitted, a box id is
assumed to be equal to the collection id. (Maybe there are no "boxes"
for this collection.)  The box id may be used flexibly---for example,
it might encode both a box-id and batch-within-box-id.  For example,
the box id might be ``Box45-Batch2``.

The **``Position``** field gives the position (starting with 1) of the ballot within
the box.  The auditor may find a particular ballot by counting to the right position
in the box.  It is assumed that the order of ballots within a box is never
changed.

The **``Stamp``** field, if used, gives the "stamp" that may have been
impressed (imprinted) on the ballot when it was scanned or organized
into boxes.  It is assumed that the stamps values are unique within a
box.  They may be increasing in order within a box, but need not be.
The stamps do not need to be numeric.  If stamps are used, the auditor
knows she has the desired ballot if it has the expected stamp value.
If no stamp value is specified, a value of ``""`` (the empty string)
is assumed.  If both the **``Position``** field and the **``Stamp``** field are
used, the **``Position``** field is used only as a hint as to where the ballot
with the right stamp value is in the box.  The **``Stamp``** and the
**``Comments``** are the only optional fields.

The **``Ballot id``** gives a ballot id for the ballot described
in that row.  It should be unique within all ballots of the collection.
It may encode information (such as the box id) within it, but need not.
If the row describes multiple ballots, via the "Number of ballots" feature
about to be described, then those ballots should all have (generated)
ballot ids that are unique within the collection.

The **``Number of ballots``** field enables compact encoding of
boxes of ballots for the manifest.

If the **``Number of ballots``** field should be equal to 1 if the row represents
a single ballot.  This is perhaps the typical case.

if the **``Number of ballots``** field is greater than one, then the given
row represents a batch of ballots of size "Number of ballots".  
Typically, the row would represent all ballots in a particular box.

In this case, the fields of the row describe the *first* ballot in the
batch.  To generate the other rows, the **``Position``**, **``Stamp``**
(if present), and **``Ballot id``** fields are increased by one for
each successive newly-generated ballot.
Other fields are just copied for the newly-generated rows.
This compact format may not be used if the ballot stamps are present
but not sequential.

The auto-incrementing for position, stamp, and ballot-id increments
just the number given in the trailing digit sequence of the position, stamp, or
ballot-id, and preserves the length of that trailing digit sequence if
possible (so ``"B-0001"`` increments to ``"B-0002"`` and not ``"B-2"``, but
``"XY-9"`` increments to ``"XY-10"``).  If the given ballot id does not
contain a trailing digit sequence, then a trailing digit sequence of
``"1"`` is generated for the first ballot of the generated set.

The size of the collection is just the sum of the values in the
"Number of ballots" field.

The **``Number of ballots``** feature is just for compactness and
convenience; when the ballot manifest file is read in by ``multi.py``,
it expands such rows representing multiple ballots into individual
rows as described above.  So, the compact format is just "shorthand" for the
official fully-expanded one-ballot-per-row format.

The **``Required Contests``** and **``Possible Contests``** fields work much
as they do for a collections file.  Any additional required or possible contests
specified in a row of the ballot manifest file are understood to be added to those already
specifed in the collections file, for the ballots described in that row of the
ballot manifest file.

Here is an example of a ballot manifest file.

| Collection    | Box       | Position  | Stamp     | Ballot id | Number of ballots | Required Contests | Possible Contests  | Comments      |
|---            | --        | ---       | ---       | ---       | ---               | ---               | ---                | ---           |
| LOG-B13       | B         | 1         | XY04213   | B-0001    |  1                |                   |                    |               |
| LOG-B13       | B         | 2         | XY04214   | B-0002    |  1                |                   |                    |               |
| LOG-B13       | B         | 3         | XY04215   | B-0003    |  1                |                   |                    |               |
| LOG-B13       | C         | 1         | QE55311   | C-0001    |  3                | FEDERAL           | FEDERAL            |               |
| LOG-B13       | D         | 1         |           | D-0001    |  50               |                   |                    |               |
| LOG-B13       | E         | 1         | FF91320   | E-0200    |  50               |                   |                    |               |
| LOG-B13       | F         | 1         | JS23334   | F-0001    |  1                |                   |             | See Doc. #211 |

Box B has three ballots, which are individually described, one row per ballot.
Box C also has three ballots, but the compact format is used here.  The positions
of the three ballots are 1,2,3; the stamps are ``QE55311``, ``QE55312``, and ``QE55313``;
and the ballot ids are ``C-0001``, ``C-0002``, and ``C-0003``. 
(The ballot ids here just encode the box id and position; they need not do so, as
we see for box E.)
Ballots in box C all have the FEDERAL contests, and only the FEDERAL contests, on them.
Box D has 50 unstamped ballots, in positions
1--50, and ballot ids ``D-0001`` to ``D-0050``.
Box F has a single ballot, with a comment (perhaps it was a provisional ballot).

If ballot stamps are not used, or if ballot stamps are sequential, then the
ballot manifest might be easy to create by hand, thus removing the need to
trust vendor software to create the ballot manifest.  The auditor will need
to create one line of the ballot manifest file per box in the collection.

If the ``Required Contests`` field is missing,
no contests are assumed to be required.
If the ``Possible Contests`` field is missing, 
all contests are assumed to be possible.
(These requirements and possibilities are additional
requirements and possibilities, above and beyond what may be
required or possible as described in the collections file.)


[Back to TOC](#table-of-contents)


### Reported CVRs file

A reported cvrs file has a name of the form

    2-reported/22-reported-cvrs/reported-cvrs-PBCID.csv

where PBCID is the paper ballot collection id.
This file name may also have a version label.  An example filename: ``reported-cvrs-DEN-A01.csv``.
This file may be produced by the tabulation equipment.

A **reported cvrs file** is a CSV format file containing a number of
rows, where (for a CVR collection) each row represents a voter's choices for a
particular contest. These are the **cast vote records** (CVRs) of the election.

The format is capable of representing votes in more
complex voting schemes, like approval or instant runoff (IRV),
where a single vote may contain several selections.

Here are the fields of a row of a reported cvrs file:

1. **Collection** (pbcid)
   Typically, all rows in a reported cvrs file will have the same paper ballot
   collection identifer (pbcid).

2. **Scanner**: This field gives an id of the device that scanned this ballot.
   May be blank.

3. **Ballot identifier** (bid)

4. **Contest** (cid) 
   An identifier (cid) for the contest.)

5. **Selections** (vote): Columns 5 and on are to record the voter's choices
   for that contest.  A typical plurality election will only have one
   choice, so the selection id (selid) is entered in column 4 and the later
   columns are blank.

   For other contest types (e.g. approval voting) there may be more than
   one selection, so they are listed in columns 5, 6, ...
   In general, each selection id corresponds to a single bubble that
   the voter has filled in on the paper ballot.

   The order of the selections doesn't matter; a vote is just a **set**
   of selection ids, and the vote is treated as if the selection ids
   were given in a canonical sorted order.

   Preferential voting can also be handled with these fields, using
   selection ids of the form ``1-John Smith`` (John Smith is the voter's
   first choice), ``2-Mary Jones``, and so on.
   
   Other voting methods, such as approval voting or vote-for-k voting,
   can also be handled.

   An undervote for a plurality vote will have columns 4-... blank,
   whereas an overvote will have more than one such column filled in.

   Implementation note: the voter's selections are combined into
   a python "tuple".  An empty vote is the zero-length python
   tuple ``()``.  The python representation uses tuples, not lists,
   since tuples are hashable and so may be used as keys in
   python dictionaries.  The tuple has its selection ids given
   in sorted order.

For a noCVR collection, the format is the same except that the "Ballot ID" field
is replaced by a "Tally" field.

**Example:** A reported vote file table from a scanner in a CVR collection.  Here
each row represents a single vote of a voter in a contest.  There are three voters
(ballot ids ``B-231``, ``B-777``, and ``B888``) and three
contests.


|Collection      | Scanner  | Ballot id   | Contest        | Selections     |           |
|---             |---       | ---         | ---            | ---            | ---       |
|DEN-A01         |FG231     | B-231       | Denver Prop 1  | Yes            |           |
|DEN-A01         |FG231     | B-231       | Denver Prop 2  |                |           |
|DEN-A01         |FG231     | B-231       | U.S. Senate 1  | Rhee Pub       | Deb O'Crat |
|DEN-A01         |FG231     | B-777       | Denver Prop 1  | No             |           |
|DEN-A01         |FG231     | B-777       | Denver Prop 2  | Yes            |           |
|DEN-A01         |FG231     | B-777       | U.S. Senate 1  | +Tom Cruz      |           |
|DEN-A01         |FG231     | B-888       | U.S. Senate 1  | -Invalid       |           |


The second row is an undervote, and the third row is an overvote.  The sixth
row has a write-in for qualified candidate Tom Cruz.  The last row represents a vote that
is invalid for some unspecified reason.

If the reported vote file is for a noCVR collection, the ``Selections`` field lists
just ``-noCVR`` instead of any particular selection(s).

[Back to TOC](#table-of-contents)


### Reported outcomes file

A reported outcomes file has a filename of the form

     2-reported/23-reported-outcomes.csv

(possibly with a version label).  This file may be produced by the
tabulation equipment.

A "**reported outcomes file**" gives the reported outcome for every
contest as a single id or a sequence of ids.

| Contest         | Winner(s)  |            |           |             |
| ---             |  -         | ---        |---        |---          |
| Denver Prop 1   | Yes        |            |           |             |
| Denver Prop 2   | No         |            |           |             |
| Denver Mayor    | John Smith |            |           |             |
| CO Prop A       | Yes        |            |           |             |

For a plurality election with a single winner, the file shows in
column 2 the selection id for that winner.  This will be a selection
id that does not begin with a minus sign (``-``), as such selection
ids correspond to special situations (such as ``-Invalid``) that can
not "win elections".  The winner may be a selection id that starts
with a plus sign (``+``), which denotes a write-in candidate.

When a contest outcome gives multiple winners, they are listed in
additional columns.  We assume that if there are multiple winners,
that the order of these winners is important.

A contest outcome need not be a single selection id, or a sequence of
selection ids.  It may be a sequence of ids that don't appear on the
ballot, representing special situations, such as

    -Tied,    John Smith,    Mary Jones

Or perhaps the outcome could be very different than the selection ids.
Perhaps the outcome is a food type, such as ``Chinese``, when the votes
are the number of calories desired (why not?).

The only operation the (Bayesian) audit cares about is "testing for
equality" -- whether the computed election outcome for a sample is the
same as the reported election outcome, or whether it is the same as
computed for some other sample.  Other than that, details don't matter
for the audit.  To test for equality of outcome, the audit just looks
at the sequence of ids produced (order matters).

This file shows only the reported winners, it does not show tally
information, or additional information about how the winner(s) was/were
computed (such as intermediate IRV round information, or tie-breaking
decisions).  Additional output files may include this information.  But
since this information is not relevant for the audit, we do not describe
it here.


[Back to TOC](#table-of-contents)

## Audit details

The audit process begins with a single "audit setup" phase,
in which a random "**audit seed**" is generated, and an initial
"**audit order**" is then produced for each collection.

Following that is the actual audit, which involves coordinated
work between the various collection managers and Audit Central.

The collection managers arrange for the retrieval of paper ballots in
the order prescribed by the audit order for their collection.  At
predetermined times (or when possible or convenient) the collection
manager will send to Audit Central an "**audited votes file**"
describing (in a cumulative way) the hand-to-eye interpretations of
all ballots retrieved so far in that collection.  Each new upload
must have a larger (later) version label.

Audit Central will process the uploaded sample data, and determine for
each contest (measurement) whether the audit is complete or not.
Audit Central then provides guidance to the collection mangers (in the
form of a "**plan**") that details the work yet to be done.

(For contests whose ballots are entirely within one collection, the
``multi.py`` software may in principle also be run by the collection manager,
if desired, to give faster evaluation of the audit progress. But the audited
votes data should nonetheless be uploaded to Audit Central.)

[Back to TOC](#table-of-contents)


### Audit setup

The audit setup determines the "**audit seed**", a long random number,
and then from the audit seed an initial "**audit order**" for each collection,
listing (some of) the ballots of that collection in a scrambled order.

An **audit parameters** file gives parameters used in the audit.  
There are *four* such files: one for the audit seed,
one for global parameters, one for
parameters by contest, and one for parameters by collection.

[Back to TOC](#table-of-contents)

#### Global audit parameters

The filename is of the form:

    3-audit/31-audit-spec/audit-spec-global.csv

(A version label could also be included in the filename.)

The **global audit parameters file** is simple.

| Global Audit Parameter | Value               |
| ---                    | ---                 |
| Max audit stage time   | 9999-12-31-23-59-59 |


This value specifies a time when the audit will be over.  No
auditing will be undertaken after this time.

[Back to TOC](#table-of-contents)

#### Contest audit parameters

A **``contest audit parameters file``**
has a filename of the form

    3-audit/31-audit-spec/audit-spec-contest-2017-11-22.csv

This example shows a version label that is a date-time stamp.

The **``contest audit parameters file``** shows the audit measurements
and risk limits that will be applied to contests.  

Each row specifies a risk measurement specific to a particular contest.
The measured risk quantifies, on a scale from 0.0 (no risk) to 1.0
(extreme risk), the risk associated with stopping the audit now and
accepting the reported election outcome as correct.

Audit Central determines when each risk measurement is performed.

The measured risk is compared against a specified **risk limi** (such as 0.05);
if the measured risk is less than the specified risk limit, we say
the test **passes**.

The measured risk is also compared against a specified
**risk upset threshold** (such as 0.99).
If the measured risk *exceeds* the specified risk upset threshold, then
we say the test **signals an upset** , as the measured risk is so high
as to provide strong evidence that the reported election outcome is
incorrect.

Normally, each contest has exactly one row in the file, specifying
a risk measurement to be performed.  But a contest may have no row
in the file, in which case risk is not measured for that contest.
Or, a contest may have more than one row, meaning that risk on that
contest is measured in more than one way.  (This latter capability
is perhaps most useful for research purposes, but is noted here.)


Here is a sample contest audit parameters file:

| Measurement id | Contest              | Risk Measurement Method | Risk Limit | Risk Upset Threshold       | Sampling Mode | Initial Status | Param 1 | Param 2 |
|---             | ---                  | ---                     | ---        | ---                        |---            | ---            | ---     | ---     |
| 1              | Denver Prop 1        | Bayes                   | 0.05       | 0.99                       | Active        | Open           |         |         |
| 2              | Denver Prop 2        | Bayes                   | 1.00       | 1.00                       | Opportunistic | Open           |         |         |
| 3              | DEN-mayor            | Bayes                   | 0.05       | 0.99                       | Active        | Open           |         |         |
| 4              | LOG-mayor            | Bayes                   | 0.05       | 0.99                       | Active        | Off            |         |         |
| 5              | U.S. Senate 1        | Bayes                   | 0.05       | 0.99                       | Active        | Open           |         |         |
| 6              | Boulder-clerk        | Bayes                   | 1.00       | 0.99                       | Active        | Open           |         |         |
| 7              | Boulder-council      | Bayes                   | 1.00       | 0.99                       | Active        | Open           |         |         |
| 8              | Boulder-council      | Frequentist             | 0.05       | 1.00                       | Opportunistic | Open           |         |         |


Each row describes a risk measurement that will be done on the
specified contest (given in the second column).

The third column specifies the risk measurement method.  The example
shows using ``Bayes`` and ``Frequentist`` as risk measurement methods.
Each such method invokes a specific software module for measuring the
risk, given the reported outcome and the tally of votes in the sample
for that contest.  The method may also use additional method-specific
parameters, as specified in the later columns of the row.

The measured risk will be a value between 0.00 and 1.00, inclusive;
larger values correspond to more risk.

The fourth column specifies the **risk limit** for that measurement.  If the
measured risk is at most the specified risk limit, then that measurement **passes**.
When all risk measurements pass, the audit may stop.

If the risk limit is 1.00, then the measurement is still made, but
the test always passes.  

The fifth column specifies the **risk upset threshold**.  If the measured
risk reaches or exceeds the risk upset threshold, then test **signals an upset**
for that contest, and the auditing program may cease
to sample more ballots in order to measure the risk of this contest, since it is
apparent that the reported outcome is incorrect and a full hand count should be
performed.

The sixth column specifies the **sampling mode** for that test, which should
be one of ``Active`` or ``Opportunistic``.  If the test specifies active
sampling, then requests will be made to collection managers to draw samples
that will shed light on the risk measurement and test.  Otherwise, if
the sampling mode is opportunistic, then no active sampling will be done, but
sample data will be obtained only by "piggybacking" on active sampling done
for other tests, since a pulled ballot may have the votes for several
contests recorded.

The seventh column specifes the **initial status** of the test.
The status of a test will always be one of

* ``Open``
* ``Off``.  
* ``Passed``
* ``Upset``
* ``Exhausted``

In general, The status of a test describes depends upon the most recent risk
measurement.  

Normally all tests start with an ``Open`` or ``Off`` status, and the audit proceeds to
sample for the still-open ``Active`` tests until they are all ``Passed``, ``Upset``,
or ``Exhausted``.
(The ``Exhausted`` status means that all relevant ballots have been audited.)
The ``Off`` status is for administrative use, to designate and turn off tests that
aren't being exercised in the current audit; a test that is ``Off``
isn't measured and remains off.  An uncontested contest may also have an initial
status of ``Off``.

(For example, when running an audit in
a county only on local contests, only the local contests may be
specified as ``Open``; others are turned ``Off``.)

The audit may stop when no ``Active`` tests remain ``Open``.

Columns eight and later specify additional parameters that might be needed for the
specified risk measurement method.  (None shown here, but something like
a gamma value for the frequentist method might be a possible example.)

Minor remark: We note again that **a contest can participate in more
than one risk measurement**.  In the example shown above, the last contest
(Boulder-council) has *two* measurements specified: one by a Bayes method
and one by a frequentist (RLA) method.  This flexibility may allow more
convenient testing and comparison of different risk-measurement methods.
(Although it should be noted that the notions of ``risk'' may differ, so
that this is a bit of an apples-and-oranges comparison.)
This feature may also enable the simultaneous use of different Bayesian
priors (say one for each candidate), as explained in
[Rivest and Shen (2012)](http://people.csail.mit.edu/rivest/pubs.html#RS12z).

[Back to TOC](#table-of-contents)

#### Collection audit parameters

A **collection audit parameters file** gives audit parameters that
are specific to each collection.


| Collection     | Max audit rate  |
|---             |---              |
|  DEN-A01       | 50              |
|  DEN-A02       | 50              |
|  LOG-B13       | 30              |


At this point, we only have one collection-specific audit parameter:
the *max audit rate*, which is the maximum number of
ballots that can be examined per day for that collection.

The filename for a collection audit parameters file is of the form

    12-audit-parameters-collection-2017-11-22.csv

(showing a year-month-day version label).

[Back to TOC](#table-of-contents)


#### Audit seed file

The **audit seed file** has a filename of the form

    3-audit/31-audit-spec/audit-spec-seed-2017-11-20.csv

This example shows a version label to record the date, but the audit
seed should only be determined once.

The audit seed file gives the audit seed used to control the random
sampling of the audit.

| Audit seed           |
|---                   | 
| 13456201235197891138 |

The audit seed should be made by rolling a decimal die twenty or more
times.  **It is important that this be done *after* the reported votes have been
collected and published by Audit Central**,
so as prevent an Adversary from modified cast vote records with foreknowledge
as to which votes will be aduited.

The generation of the audit seed should preferably be done in a
videotaped public ceremony.


[Back to TOC](#table-of-contents)


### Dialogue between Audit Central and Collection Managers

After the initial audit setup, we view the actual audit as a two-way
dialogue between AC (Audit Central) and the various collection
managers (CMs, one per collection) during the audit.

AC provides a sequence of specific auditing requests (orders): ballots
to be pulled, and contests from those pulled ballots for which the
collection manager (or her delegate) should record the voter's
selection(s).

A CM responds with the requested information, in the order requested.

For each paper ballot collection, an **audit order file** gives the
cumulative list of the audit requests made by AC for ballots in that
collection.

AC thus sends each CM a sequence of audit order files; each of which is
progressively longer than the previous one, as each is a cumulative list
of all auditing requests made so far to that CM.

Each audit order file will have a version label (date-time stamp) that is
greater than the version label of the previous audit order.

Correspondingly, the collection manager will transmit every so often to AC an
**audited votes file** giving the details of what was found on the
audited votes examined so far.

Each audited votes file is an extension of the previously-sent audited votes
file: new records will be added to the end, but the previously-sent records
will be repeated in the new file.

The new audited votes filel will have a greater version label than the previously-sent
audited votes file.

(While have the audit orders and audited votes files cumulative may seem wasteful;
the audit will normally terminate before these files get very large.)

We can view the two sorts of files as giving one side of a *transcript* (or logs) of the
two-way dialogue between AC and the CM.

The conversation is **asynchronous**; either party may add additional
records to its log, and transmit the resulting file to the other party
at any time.

The **``audit-order``** file may be dynamically computed as the audit
progress, which is why it need not be specified "all at once" before the audit
begins.  For example, it may be determined that a particular scanner has
a high error rate, and so later sampling may emphasize ballots scanned
with that scanner.  All the same, the AC should provide sufficient
"advance notice" of auditing requests that CMs can "work ahead" if they
wish, for example by combining requests for ballots from the same box.


[Back to TOC](#table-of-contents)

#### Audit order file

An **audit order file** lists a sequence of ballots requested for audit
from a collection.

An audit order file has a filename of the form

   3-audit/32-audit-orders/audit-order-<pbcid><version-label>.csv``

where ``<pbcid>`` is replaced with the paper ballot collection id, and
``<version-label>`` is replaced with a version label (e.g. a date-time
stamp).   An example of an audit order file name for collection ``DEN-A01``
is:

    audit-order-DEN-A01-2017-11-20-13-05-47.csv

Audit Central may send a collection manager a sequence of such audit
order files; each such file is a cumulative summary of all ballots requested
to be audited.  Each audit order file is an append-only list of requests
made so far by AC to that CM.

The audit order files thus become longer as the audit progresses. 

The order of the requests is determined "randomly" but
cryptographically, depending the audit seed.  The order should be
unpredictable to an adversary, which is why the audit seed should be
determined only **after** the reported votes for all the collections
are recorded and filed.

The sample order field indicates the order in which they must be
examined during the audit.  Ballots may not be skipped during the
audit.  (Technically, it is OK if the ballots audited may be re=ordered
to form the order given in the audit order file.  That is, the auditor
should make sure to audit any skipped ballots before reporting the results
of the audit to AC.)

When a ballot is audited, the auditor should report the voter's selection(s)
for all contests that are open status and either active or opportunistic sampling
mode.  Other contests should not be reported.

The audit order file can be viewed as an initial segment of a permuted
ballot manifest file.  The differences are that
* The ballots are given numbers giving their positions in the audit order.
* Each line represents a single ballot; no batching of lines is allowed.
* AC may determine the order dynamically, depending on what is seen during
  the audit.  While AC could in principle and perhaps in fact just be requesting ballots that
  form an initial segment of some fixed predetermined scrambled ballot
  manifest file, the AC could alternatively dynamically determine how to
  extend the audit order file as the audit progresses.

Here is an example audit order file, specifying the first seven ballots to be
audited from collection LOG-B13.

|Ballot order | Collection    | Box       | Position  | Stamp     | Ballot id |  Comments |
|---          |---            | --        | ---       | ---       | ---       |  ---      |
| 1           | LOG-B13       | B         | 3         | XY04213   | B-0003    |           |
| 2           | LOG-B13       | C         | 2         | QE55312   | C-0002    |           |
| 3           | LOG-B13       | F         | 1         | JS23334   | F-0001    | See Doc #211 |
| 4           | LOG-B13       | D         | 7         |           | D-0007    |           |
| 5           | LOG-B13       | B         | 1         | XY04211   | B-0001    |           |
| 6           | LOG-B13       | D         | 39        |           | D-0039    |           |


The auditor may naturally group the requests for ballots from box B,
and those from box D.

Sampling is done without replacement.  Each ballot in the collection
appears at most once in the audit order file.  The audit order file
may grow to include all ballots in the collection.

To produce the audit order, ``multi.py`` feeds the audit seed,
followed by a comma, the collection id, another comma, and a decimal
counter value, into a cryptographic random number function
(specifically, SHA256 used in counter mode, starting with counter
value 1).  The Fisher-Yates algorithm is then used to produce a random
permutation of the ballots, using these random numbers.  This reference
random order is what is used if no dynamic determination of audit order
is used.  Otherwise, the order used will be a subsequence or otherwise
closely related to this random order.

The audit order file and the reported cvrs file may be used
with an appropriate UI interface to generate the audited votes
file. 

[Back to TOC](#table-of-contents)


#### Audited votes

An **``audited votes file``** will have a name of the form

    3-audit/33-audited-votes/audited-votes-<pbcid><version-label>.csv

where ``<pbcid>`` is replaced with the paper ballot collection is, and
``<version-label>`` is replaced with a version label, such as a date-time
stampe.  An example audited votes filename for collection ``DEN-A01`` is

    audited-votes-DEN-A01-2017-11-21-09-30-55.csv

As noted, if the sample is expanded, then the new sample vote file
will contain records for not only the newly examined ballots, but also
for the previously examined ballots.

For example, the file

    audited-votes-DEN-A01-2017-11-22-10-14-21.csv

will be an augmented version of the previously shown file.

An **audited votes file** represents a set of votes that have been
sampled and audited during an audit.  It is similar in format to a
reported vote file (for a CVR collection), but the scanner field is
omitted.

Here is an example of a sample vote file for the ``DEN-A01`` collection, for
two ballots and three contests each.
 
 
|Collection      | Ballot id   | Contest        | Selections     |           |
|---             | ---         | ---            | ---            | ---       |
|DEN-A01         | B-231       | Denver Prop 1  | Yes            |           |
|DEN-A01         | B-231       | Denver Prop 2  | No             |           |
|DEN-A01         | B-231       | U.S. Senate 1  | Rhee Pub       | Val Green |
|DEN-A01         | B-777       | Denver Prop 1  | No             |           |
|DEN-A01         | B-777       | Denver Prop 2  | Yes            |           |
|DEN-A01         | B-777       | U.S. Senate 1  | +Tom Cruz      |           |


Compared to the reported vote file above, we note a discrepancy in the
interpretation of contest ``Denver Prop 2`` for ballot ``B-231``: the scanner showed
an undervote, while the hand examination showed a ``No`` vote.

[Back to TOC](#table-of-contents)


#### Output file formats

The outputs include a file ``audit-snapshot.csv`` that gives the SHA256
hashes of the files used as inputs to the computations of that stage.
This is a "snapshot" of the current directory structure.  It is used
if/when re-running a audit stage computation.

The output file ``audit-output-detail.csv`` gives the detailed audit outputs
for the most recent audit computation.

The file ``audit-output-plan.csv`` gives the workload estimates and auditing
plan (broken down by collection) for the next stage.

[Back to TOC](#table-of-contents)

##### Audit snapshot file

The **audit snapshot** file lists the all files currently
in the directory for the election, together with their
SHA256 hash values.
The audit snapshot file is an *output* of the audit program, not an
input to the program.  It lists the files that the audit program
will use for the computation of this stage.  The SHA-256 hashes
are there for definiteness, allowing at a later time for you to check that you still
have the correct input files, if you want to check the audit program by re-running it.
(If the audit stage is re-run, it will use the same files, even if files
with later version labels have been added to the directory structure.)


| Filename                   | Hash |
|---                         |---                  |
| ``11-general-2017-09-08.csv``           | ``ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb`` |
| ``12-contests-2017-09-08.csv``           | ``3e23e8160039594a33894f6564e1b1348bbd7a0088d42c4acb73eeaed59c009d`` |
| ``14-collections-2017-09-08.csv``        | ``2e7d2c03a9507ae265ecf5b5356885a53393a2029d241394997265a1a25aefc6`` |
| ...                                  | ...                                                              |
| ``audited-votes-LOG-B13-2017-11-22.csv`` | ``18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4`` |
| ``23-reported-outcomes-2017-11-07.csv`` | ``252f10c83610ebca1a059c0bae8255eba2f95be4d1d7bcfa89d7248a82d9f111`` |
| ...
| ``12-audit-parameters-collection-2017-11-22.csv`` | ``3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca046dea`` |


[Back to TOC](#table-of-contents)


##### Audit output file(s)

The **audit outputs** file(s) give the measured risks.

The computation of Audit Central determines which measurements
have now reached their risk limits, so that certain collection
managers may be told that their work is completed.

Format: TBD

[Back to TOC](#table-of-contents)


##### Audit plan file

The **audit plan** file gives estimated workloads (amount of work
remaining) for each collection manager, and provides guidelines
on how to allocate the work between collections (if there is
an exploitable tradeoff, to reduce overall workload). (Some
optimization may be applied here.)

| Collection             | Audited so far | Next stage increment request  | Estimated total needed |
|---                     |---             |---                            |---                     |
|  DEN-A01               | 150            | 50                            | 300                    |
|  DEN-A02               | 150            | 50                            | 300                    |
|  LOG-B13               |  90            | 30                            | 150                    |


The sum of "audited-so-far" and "next stage increment request" should equal the
size of the "audit-order" file.

[Back to TOC](#table-of-contents)


## Command-line interface

This section sketches the command-line interface to ``multi.py``.
Here we assume the election data is in the directory
``./elections/CO-2017-11``.

| Command                                             | Action                              |
|---                                                  |---                                  |
| ``python3 multi.py --read_election_spec CO-2017-11``| Reads and checks election spec
| ``python3 multi.py --read_reported CO-2017-11``     | Reads and checks reported data      |
| ``python3 multi.py --read_seed CO-2017-11``         | Reads and checks audit seed         |
| ``python3 multi.py --make_audit orders CO-2017-11`` | Produces initial audit order files  |
| ``python3 multi.py --read_audited CO-2017-11``      | Reads and checks audited votes      |
| ``python3 multi.py --audit CO-2017-11``             | Runs audit                          |
| ``python3 multi.py --audit --pause CO-2017-11``     | Runs audit, pausing after each stage |

You can also run

    python3 multi.py --help

to get usage instructions.

The program ``multi.py`` will be run by Audit Central for each stage.

It may also be run by an audit observer, since no data is ever lost.  That is,
inputs to each audit stage computation are still available for re-doing any
of the audit computations.  (The snapshots file may need to be used here to
assist in obtaining the correct input files.)

Because of the way ``multi.py`` works, the program can be run by Audit
Central, or by a local collection manager.  For the latter use, the audit
parameters should to be adjusted to only those audit contests local to the collection, 
by setting the risk limits to all other contests to 1.00.

In addition to ``multi.py``, there is another program called ``syn.py``, for
generating sythetic data sets.
Run

    python3 syn.py --help

to get usage instructions.


[Back to TOC](#table-of-contents)

## Appendix: File names

During an audit, data may be augmented or improved somehow.  We
use a file naming scheme that doesn't overwrite older data.

We support the principles of "**transparency**" and
"**reproducibility**": the information relied upon by the audit, and
the information produced by the audit, should be identifiable,
readable by the public, and usable to confirm the audit computations.
To support this principle, information is never changed in-place;
the older version is kept, but a newer version is added.

This is done by interpreting part of the filename as a
"version label".  When looking for a file, there may be
several files that differ only in the version label portion of
their filename.  If so, the system uses the one with the
version label that is (lexicographically) greatest.
The version label is arbitrary text; it may encode a
date, time, or some other form of version indicator.

When the system searches for a file in a given directory,
it looks for a file with a filename having a given "prefix"
(such as "data") and a given "suffix" (such as ".csv"). A
file with filename

    data.csv

matches the search request, but has no version label (more precisely,
a zero-length string as a version label).  A file
with filename

    data-v005.csv

also matches the search request, but has ``"-v005"`` as the version
label (for that search).  Similarly a filename:

    data-2017-11-07.csv

has ``"-2017-11-07-08"`` as its version label for this search.

Note that version labels are compared as **strings**, not as **numbers**.
For good results:
* For numbers, use _fixed-width_ numeric fields, since the comparisons
  are lexicographic.  Don't be bitten by thinking that ``"-v10"`` is
  greater than ``"-v5"`` -- it isn't!
* For dates, used fixed-field numeric fields for each component, and
  order the fields from most significant to least significant (e.g.
  year, month, day, hour, minute, second), as is done in the ISO 8601
  standard, so lexicographic comparisons give the desired result.

Note that having no version label means having the empty string
as the version label, which compares "before" all other strings,
so your first version might have no version label, with later
versions having increasing version labels.

Within a directory, if two or more files differ only in their version labels,
then the file with the greatest version label is operative, and the
others are ignored (but may be kept around for archival purposes).

In our application, version labels are used as follows.  When
an audit sample is augmented, a new file is created to contain
**all** of the sampled ballot data (previously sampled, and the
new data as well).  The new file is given a version label that is
greater than the previous version label.  

If this sample is augmented, the above file is not changed, but
a new file with a later date is just added to the directory.
The earlier file may be deleted, if desired.


[Back to TOC](#table-of-contents)



## Appendix (Possible Future Work)

[Back to TOC](#table-of-contents)

### Compression

As the reported votes files are certain to be the largest files used by ``multi.py``,
some form of compression may be useful.

Here is a suggestion (for possible later implementation), suitable for compressing
CSV files.  Call this format ``redundant row compression`` (RRC), and give the
compressed file a name ``foo.csv.rrc``.

An RRC file compresses each row, using the previous rows if
possible.  An RRC cell entry of the form **&c^b** means "copy c cell
contents, starting with the current column, from the row b rows
previous to this one.  Either &c or ^b may be omitted, and these can
be given in either order.  They both default to 1 if either ^ or & is
present, so **^** means copy the corresponding cell from the previous row, **&4**
means copy the next four corresponding cells from the previous row, and **&3^9**
means copy the next three cells from the row nine rows earlier.

Example:  The following file:

|Collection id   | Scanner  | Ballot id   | Contest     | Selections     |           |
|---             |---       | ---         | ---         | ---            | ---       |
|DEN-A01         |FG231     | B-231       | Denver Prop 1  | Yes            |           |
|DEN-A01         |FG231     | B-231       | Denver Prop 2  |                |           |
|DEN-A01         |FG231     | B-231       | U.S. Senate 1 | Rhee Pub       | Val Green |
|DEN-A01         |FG231     | B-777       | Denver Prop 1  | No             |           |
|DEN-A01         |FG231     | B-777       | Denver Prop 2  | Yes            |           |
|DEN-A01         |FG231     | B-777       | U.S. Senate 1 | +Tom Cruz      |           |
|DEN-A01         |FG231     | B-888       | U.S. Senate 1 | -Invalid       |           |

can be compressed to the RRC CSV file:

```
Collection id,Scanner,Ballot id,Contest,Selections
DEN-A01,FG231,B-231,Denver Prop 1,Yes
&3,Denver Prop 2
&3,U.S. Senate 1,Rhee Pub,Val Green
&2,B-777,^3,No
&3,^3,Yes
&3,^2,+Tom Cruz
&2,B-888,^,-Invalid
```

[Back to TOC](#table-of-contents)









